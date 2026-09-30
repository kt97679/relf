#!/usr/bin/env python3
"""tools/intrfuzz.py [N] [SEED] [SHELL] - Ctrl-C at random moments.

An interactive shell on a pseudo-terminal is given commands that run for
a while - Forth loops and includes that spin or nest, a builtin loaded
from Forth that spins, shell loops, sleep, pipelines, $(...),
subshells, cat and read waiting on the terminal, a trap, a function, a
loop that runs forth - and ^C arrives at a random moment: before the
command starts, in the middle, twice, mid-line, at the prompt. Then the
shell must come back to a prompt, and be whole: a variable intact,
DEPTH 0, a good include working, a loop running, the terminal's modes
and the shell's file descriptors as they were.

The Ctrl-C path had bugs before (the first reviews found several), and
the pty suite tests it at fixed points only. Written in Iteration 598,
after tools/forthfuzz.py (595) did the same for Forth's errors.

Synchronisation: after each step, `echo @@S$((n+1))` - its OUTPUT, n+1
computed, cannot be confused with the terminal's echo of what was typed.
A ^C makes the terminal discard what was typed ahead, so the line is
sent again every two seconds until the timeout.
"""
import os, pty, random, re, select, shutil, signal, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 598
SHELL = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(ROOT, 'relfsh')
TIMEOUT = 12.0
INTR = b'\x03'


class Dead(Exception):
    pass


class Pty:
    def __init__(self, d):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(d)
            env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': d,
                   'PS1': '$ ', 'PS2': '> ', 'TERM': 'dumb'}
            os.execve(SHELL, [SHELL, '-i'], env)
        self.out = ''
        self.n = 0

    def send(self, b):
        os.write(self.fd, b if isinstance(b, bytes) else b.encode())

    def read_for(self, secs):
        end = time.time() + secs
        while True:
            left = end - time.time()
            if left <= 0:
                return
            r, _, _ = select.select([self.fd], [], [], left)
            if not r:
                return
            try:
                data = os.read(self.fd, 65536)
            except OSError:
                raise Dead()
            if not data:
                raise Dead()
            self.out += data.decode('utf-8', 'replace')

    def sync(self):
        """Wait until the shell runs a new command line; False on timeout."""
        self.n += 1
        want = '@@S%d' % (self.n + 1)
        start = len(self.out)
        end = time.time() + TIMEOUT
        while time.time() < end:
            self.send('echo @@S$((%d+1))\n' % self.n)
            t2 = time.time() + 2.0
            while time.time() < min(t2, end):
                self.read_for(0.05)
                if want in self.out[start:].replace('\r', ''):
                    return True
        return False

    def ask(self, line, marker):
        """Run a line that prints `marker` then something; return the something."""
        start = len(self.out)
        self.send(line)
        end = time.time() + TIMEOUT
        pat = re.compile(re.escape(marker) + r'\n([^\n]*)\n')
        while time.time() < end:
            self.read_for(0.05)
            m = pat.search(self.out[start:].replace('\r', ''))
            if m:
                return m.group(1)
        return None

    def close(self):
        try:
            os.kill(self.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            os.waitpid(self.pid, 0)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass


def steps_for(rng, d, n):
    """(text to type, when to ^C after it (None: no ^C), a second ^C?)"""
    k = rng.randrange(1000)
    cmds = [
        "forth ': L%d BEGIN 1 DROP AGAIN ; L%d'" % (k, k),
        "forth ': R%d 40000000 0 DO I DROP LOOP ; R%d'" % (k, k),
        "forth 'S\" %s/spin.4\" INCLUDED'" % d,
        "forth 'S\" %s/outer.4\" INCLUDED'" % d,
        "forth ': P%d BEGIN 0 AGAIN ; P%d'" % (k, k),
        "spinb",
        "spinb | cat",
        "y=$(spinb)",
        "while :; do :; done",
        "i=0; while [ $i -lt 300000 ]; do i=$((i+1)); done",
        "sleep 3",
        "sleep 3 | cat",
        "x=$(sleep 3)",
        "x=$(while :; do :; done)",
        "(while :; do :; done)",
        "cat",
        "read v",
        "trap 'echo TRAPPED' INT; sleep 3; trap - INT",
        "f%d() { while :; do :; done; }; f%d" % (k, k),
        "for i in 1 2 3; do forth ': Q%d BEGIN AGAIN ; Q%d'; done" % (k, k),
        "sleep 3 & wait",
        "echo partial-line-no-newline",
        "",
    ]
    out = []
    for _ in range(n):
        c = rng.choice(cmds)
        if c == "echo partial-line-no-newline":
            out.append((c, rng.choice([0.0, 0.05]), False, False))     # ^C mid-line
        else:
            out.append((c + '\n', rng.choice([0.0, 0.01, 0.05, 0.1, 0.3, 0.7]),
                        rng.random() < 0.2, True))
    return out


def run_case(d, steps):
    p = Pty(d)
    try:
        p.read_for(0.5)
        if not p.sync():
            return 'no first prompt', p.out
        p.send('keep=sentinel; forth \'S" %s/spinb.4" INCLUDED\'; stty -g > st0.txt; ls /proc/$$/fd > fd0.txt\n' % d)
        if not p.sync():
            return 'setup did not finish', p.out
        for text, delay, twice, _ in steps:
            p.send(text)
            p.read_for(delay)
            p.send(INTR)
            if twice:
                p.read_for(0.03)
                p.send(INTR)
            p.read_for(0.1)
            if not p.sync():
                return 'no prompt after ^C during: ' + text.strip(), p.out
        checks = [
            ('echo @@K; echo "$keep"\n', '@@K', 'sentinel', 'a variable was lost'),
            ("echo @@D; forth 'DEPTH . CR'\n", '@@D', '0 ', 'DEPTH is not 0'),
            ("echo @@I; forth 'S\" %s/good.4\" INCLUDED GOODWORD . CR'\n" % d, '@@I', '11 ', 'a good include failed'),
            ('echo @@L; for i in a b; do printf $i; done; echo\n', '@@L', 'ab', 'a loop failed'),
            ('stty -g > st1.txt; echo @@T; cmp -s st0.txt st1.txt && echo same || echo differ\n', '@@T', 'same', 'the terminal modes changed'),
            ('ls /proc/$$/fd > fd1.txt; echo @@F; cmp -s fd0.txt fd1.txt && echo same || echo "$(cat fd0.txt | tr \'\\n\' \' \') -> $(cat fd1.txt | tr \'\\n\' \' \')"\n', '@@F', 'same', 'file descriptors changed'),
        ]
        for line, marker, want, why in checks:
            got = p.ask(line, marker)
            if got is None:
                return 'no answer: ' + why, p.out
            if got.strip() != want.strip():
                return '%s (%r)' % (why, got), p.out
        return None, p.out
    except Dead:
        return 'the shell died', p.out
    finally:
        p.close()


def main():
    rng = random.Random(SEED)
    base = tempfile.mkdtemp(prefix='intrfuzz.')
    failures = 0
    try:
        for n in range(N):
            d = os.path.join(base, 'c%d' % n)
            os.mkdir(d)
            files = {'good.4': ': GOODWORD 11 ;\n',
                     'spin.4': ': SPIN BEGIN AGAIN ;\nSPIN\n',
                     'outer.4': '1 2 2DROP\nS" %s/spin.4" INCLUDED\n' % d,
                     'spinb.4': ": SPINB BEGIN AGAIN ;\n' SPINB S\" spinb\" BUILTIN\n"}
            for name, text in files.items():
                with open(os.path.join(d, name), 'w') as fh:
                    fh.write(text)
            steps = steps_for(rng, d, rng.randint(1, 4))
            why, out = run_case(d, steps)
            if why:
                failures += 1
                print('FAIL case %d: %s' % (n, why))
                for s in steps:
                    print('    %-60r ^C after %.2fs%s' % (s[0], s[1], ', twice' if s[2] else ''))
                tail = out[-600:].replace('\r', '')
                print('    --- the last output:\n' + '\n'.join('    | ' + l for l in tail.split('\n')))
        print('intrfuzz: %d cases, %d failures (seed %d, %s)' % (N, failures, SEED, os.path.basename(SHELL)))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
