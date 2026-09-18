"""tests/interactive/pty_session.py - drive a shell on a pseudo-terminal.

Interactive behaviour is the one part of this shell the other suites
cannot reach: a prompt, a signal typed at the keyboard, end of file from
the terminal, a construct continued over several lines. All of it needs
a terminal on the other end, which is what pty.fork gives us.

Synchronisation is by WAITING FOR THE PROMPT, not by sleeping: a sleep
long enough to be safe makes the suite slow, and one short enough to be
fast makes it flaky. Each step sends its line and then waits until the
shell asks for the next one (or until the timeout, which is a failure).
"""
import os, pty, re, select, signal, time

ESCAPES = re.compile(r'\x1b\[[?0-9;]*[a-zA-Z]|\x1b[()][A-Z0-9]|\x1b.')

def strip_escapes(t):
    """Terminal control sequences are not behaviour. bash turns on
    bracketed paste at every prompt, which otherwise buries the whole
    transcript in \\x1b[?2004h."""
    return ESCAPES.sub('', t)

class Session:
    def __init__(self, argv, env=None, cwd='/tmp', prompts=('$ ', '# ', '> ')):
        self.prompts = prompts
        self.out = ''
        self.pid, self.fd = pty.fork()
        if self.pid == 0:                      # the child IS the shell
            os.chdir(cwd)
            e = dict(os.environ)
            e.pop('PS1', None); e.pop('PS2', None)
            if env: e.update(env)
            os.execve(argv[0], argv, e)

    def _read(self, timeout):
        if not select.select([self.fd], [], [], timeout)[0]:
            return False
        try:
            b = os.read(self.fd, 4096)
        except OSError:
            return False
        if not b:
            return False
        self.out += b.decode('utf8', 'replace')
        return True

    def wait_prompt(self, timeout=5.0, mark=0):
        """Read until the output past `mark` ends with a prompt.

        The mark matters: after sending a line the PREVIOUS prompt is
        still the last thing in the buffer, so a check on the whole
        buffer returns at once and the next line goes out before this
        command has printed anything. Every transcript then depends on
        timing. Waiting for a prompt that arrives AFTER the mark is what
        makes the sessions reproducible.
        """
        end = time.time() + timeout
        while time.time() < end:
            tail = self.out[mark:].replace('\r', '')
            if any(tail.endswith(p) for p in self.prompts):
                return True
            if not self._read(0.1):
                continue
        return False

    def send(self, text, wait=True, timeout=5.0):
        mark = len(self.out)
        os.write(self.fd, text.encode() if isinstance(text, str) else text)
        if wait:
            return self.wait_prompt(timeout, mark)
        return True

    def send_signal_char(self, ch, wait=True):
        return self.send({'INTR': b'\x03', 'EOF': b'\x04', 'QUIT': b'\x1c'}[ch], wait=wait)

    def prompts_from_env(self, env):
        """Use the shell's own PS1/PS2 when the case sets them."""
        p = []
        for k in ('PS1', 'PS2'):
            if env and k in env: p.append(env[k])
        self.prompts = tuple(p) + self.prompts if p else self.prompts
        return self

    def drain(self, timeout=0.4):
        while self._read(timeout):
            timeout = 0.1

    def close(self, timeout=3.0):
        try: os.close(self.fd)
        except OSError: pass
        end = time.time() + timeout
        while time.time() < end:
            try:
                pid, st = os.waitpid(self.pid, os.WNOHANG)
                if pid: return st
            except ChildProcessError:
                return None
            time.sleep(0.05)
        try: os.kill(self.pid, signal.SIGKILL); os.waitpid(self.pid, 0)
        except (ProcessLookupError, ChildProcessError): pass
        return None

    def transcript(self, env=None):
        """The session with the terminal's carriage returns removed and
        each shell's own prompt strings replaced by <PS1>/<PS2>, so two
        shells that prompt differently can be compared. The case's own
        PS1/PS2 are replaced first: they are longer, and a plain "> "
        rule would eat the tail of "P1> "."""
        t = strip_escapes(self.out.replace('\r', ''))
        pairs = []
        if env:
            if 'PS1' in env: pairs.append((env['PS1'], '<PS1>'))
            if 'PS2' in env: pairs.append((env['PS2'], '<PS2>'))
        pairs += [('$ ', '<PS1>'), ('# ', '<PS1>'), ('> ', '<PS2>')]
        for src, dst in sorted(pairs, key=lambda x: -len(x[0])):
            t = t.replace(src, dst)
        # every shell words "not found" differently, and names itself
        t = re.sub(r'(?m)^.*: *(?:command )?not found$', '<NOTFOUND>', t)
        return t

    def raw(self):
        return strip_escapes(self.out.replace('\r', ''))
