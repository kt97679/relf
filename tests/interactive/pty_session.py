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
CSI = re.compile(r'\x1b\[([?0-9;]*)([a-zA-Z])')

def render(stream):
    """What a person would SEE, not what the shell wrote.

    A line editor redraws: it returns to column 0 with a carriage
    return, writes the prompt and the line again, erases to the end of
    the line and moves the cursor back. Dropping the carriage returns
    turns that into a run of half-typed lines; a shell in the terminal's
    cooked mode, which writes each line once, comes out unchanged. So
    the stream is replayed the way a terminal would: CR moves to column
    0, ESC[K erases from the cursor, ESC[nC moves right, and each line
    is finished when a newline arrives.
    """
    lines, cur, col, i = [], [], 0, 0
    def put(ch):
        nonlocal col
        while len(cur) < col: cur.append(' ')
        if col < len(cur): cur[col] = ch
        else: cur.append(ch)
        col += 1
    while i < len(stream):
        c = stream[i]
        if c == '\x1b':
            m = CSI.match(stream, i)
            if m:
                arg, fn = m.group(1), m.group(2)
                if fn == 'K' and arg in ('', '0'):
                    del cur[col:]
                elif fn == 'C':
                    col += int(arg or 1)
                elif fn == 'D':
                    col = max(0, col - int(arg or 1))
                i = m.end(); continue
            i += 2; continue                      # any other escape: skip it
        if c == '\r':
            col = 0
        elif c == '\n':
            lines.append(''.join(cur)); cur, col = [], 0
        elif c == '\b':
            col = max(0, col - 1)
        else:
            put(c)
        i += 1
    if cur: lines.append(''.join(cur))
    return '\n'.join(lines)

def strip_escapes(t):
    """Terminal control sequences are not behaviour. bash turns on
    bracketed paste at every prompt, which otherwise buries the whole
    transcript in \\x1b[?2004h."""
    return ESCAPES.sub('', t)

class Session:
    # How long a "quiet moment" is, and how long to wait for a prompt.
    # Both were fixed constants tuned on an idle container, which is a
    # clock assumption like any other: on a loaded machine the redraw
    # arrives after the quiet moment has passed and the transcript comes
    # out interleaved. An x86 box reported `intr-at-prompt` failing on
    # one run and passing on the next, and the same suite fails here
    # under four busy loops (Iteration 406). Overridable, so a slow or
    # busy machine can say so.
    SETTLE  = float(os.environ.get('RELF_PTY_SETTLE', '0.20'))
    TIMEOUT = float(os.environ.get('RELF_PTY_TIMEOUT', '10.0'))

    def __init__(self, argv, env=None, cwd='/tmp', prompts=('$ ', '# ', '> '), settle=None):
        self.prompts = prompts
        self.settle = self.SETTLE if settle is None else settle
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
            # Rendered, not raw: a line editor finishes its redraw with a
            # cursor-position sequence, so the raw tail is never the prompt.
            tail = render(self.out[mark:])
            looks_done = any(tail.rstrip('\n').endswith(p.rstrip()) or tail.endswith(p)
                             for p in self.prompts)
            if looks_done:
                # ... and STABLE. An editor rewrites its line from column 0
                # on every keystroke, so a read that ends just after the
                # "\r$ " of a redraw renders as a bare prompt while the
                # line is still being typed. Accepting that sent the next
                # line into the middle of the previous one, which is what
                # made job-in-background fail about a third of the time
                # (Iteration 312). A quiet moment tells the two apart.
                before = len(self.out)
                self._read(self.settle)
                if len(self.out) == before:
                    return True
                continue
            if not self._read(0.1):
                continue
        return False

    def send(self, text, wait=True, timeout=None):
        mark = len(self.out)
        os.write(self.fd, text.encode() if isinstance(text, str) else text)
        if wait:
            return self.wait_prompt(self.TIMEOUT if timeout is None else timeout, mark)
        return True

    def send_signal_char(self, ch, wait=True):
        return self.send({'INTR': b'\x03', 'EOF': b'\x04', 'QUIT': b'\x1c',
                          'SUSP': b'\x1a'}[ch], wait=wait)

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
        t = render(self.out)
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
        return render(self.out)
