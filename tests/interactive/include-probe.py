#!/usr/bin/env python3
"""tests/interactive/include-probe.py - ^C around INCLUDED (Iteration 617).

Runs with the pty suite, like width-probe.py. Two checks, each in an
interactive shell on a pseudo-terminal:

1. A ^C waiting when INCLUDED opens a file. Since 606 a ^C throws from a
   forth command's start; one landing between OPEN-FILE's return and
   INCLUDED's CATCH unwound past the CATCH that owns the file, and the
   file stayed open (tools/intrfuzz.py, case 4). That window is a few
   instructions - no test lands in it on demand - so this puts a ^C in
   the same place by other means: the route made "caught", the shell
   sends itself SIGINT (kill, through TREE-RUN-TEXT), the route put back,
   and INCLUDED opens a file whose code loops forever. The held ^C must
   be thrown inside INCLUDED's CATCH: status 130, the file closed, the
   shell's descriptors as they were. Before 617 the loop never ended.
2. ^C after a nested forth command: a forth command runs another through
   the shell, then loops, and ^C must stop it - a guard on the route's
   save and restore, which 617 made explicit. (The shell before 617
   passes it too: the inner command did not leave the outer one deaf, as
   was first thought.)

Exit status is the number of checks that failed.
"""
import os, pty, select, sys, tempfile, time

SHELL = os.path.abspath(os.environ.get('THIS_SH', os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'relfsh')).split()[0])


def session(d, steps):
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(d)
        os.execve(SHELL, [SHELL, '-i'], {'PATH': '/usr/bin:/bin', 'PS1': '$ ', 'TERM': 'dumb', 'HOME': d})
    out = b''

    def rd(t):
        nonlocal out
        end = time.time() + t
        while True:
            left = end - time.time()
            if left <= 0:
                return
            r, _, _ = select.select([fd], [], [], left)
            if r:
                try:
                    out += os.read(fd, 65536)
                except OSError:
                    return
    rd(0.5)
    for s, wait in steps:
        os.write(fd, s)
        rd(wait)
    try:
        os.kill(pid, 9)
        os.waitpid(pid, 0)
    except OSError:
        pass
    return out.replace(b'\r', b'').decode('utf-8', 'replace')


checks = []
with tempfile.TemporaryDirectory() as d:
    with open(os.path.join(d, 'spin.4'), 'w') as f:
        f.write(': SPIN BEGIN AGAIN ;\nSPIN\n')
    out = session(d, [
        (b'ls /proc/$$/fd > fd0\n', 0.4),
        (b'forth \'0 INT-ROUTE!  S" kill -INT $$" TREE-RUN-TEXT  -1 INT-ROUTE!  S" spin.4" INCLUDED\'\n', 2.0),
        (b'echo st-$?\n', 0.5),
        (b'ls /proc/$$/fd > fd1; cmp -s fd0 fd1 && echo fds-$((1+1))-same\n', 0.5),
    ])
    checks.append(('a held ^C is thrown inside INCLUDED: status 130', 'st-130' in out))
    checks.append(('and the included file is closed', 'fds-2-same' in out))
    out = session(d, [
        (b'forth \'S" forth 1 DROP" TREE-RUN-TEXT BEGIN AGAIN\'\n', 0.6),
        (b'\x03', 0.6),
        (b'echo back-$((40+2))\n', 0.6),
    ])
    checks.append(('^C stops a loop after a nested forth command', 'back-42' in out))

failed = [n for n, ok in checks if not ok]
for n in failed:
    print("FAIL include-probe: %s" % n)
print("%d include checks, %d failed" % (len(checks), len(failed)))
sys.exit(len(failed))
