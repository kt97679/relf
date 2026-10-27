#!/usr/bin/env python3
"""tests/rill2/prompt-probe.py [IMAGE] - Rill 2's prompt at a terminal (Iteration 835): relfsh's line editor
at it - a line edited with the arrows, the history recalled and edited, a variable kept between lines, a
line that goes on (...> ), ^C dropping a line half typed, ^D at an empty line ending it with status 0. On
a pseudo-terminal, as tests/interactive's probes; run by tests/rill/run with the image it builds.
"""
import os, sys, time
sys.path.insert(0, 'tests/interactive')
from pty_session import Session, render
img = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'kernel64-rill2.img')
s = Session([os.path.abspath('relf64'), img], prompts=('rill2> ', '...> '))
fail = []
def need(ok, what):
    if not ok: fail.append(what)
need(s.wait_prompt(10, 0), 'no first prompt')
s.send('x = 4\n')
s.send('print("wrld")' + '\x1b[D' * 5 + 'o\n')               # five to the left, an o: print("world")
s.send('\x1b[A' + '\x1b[D' * 2 + ' again\n')                  # the history: print("world"), " again" in it
s.send('print(x * 2)\n')
s.send('print("half typed")', wait=False); s.send_signal_char('INTR')   # ^C: the line dropped
s.send('for i in [1, 2] {\n'); s.send('print("item {i}")\n'); s.send('}\n')
s.send_signal_char('EOF', wait=False)                         # ^D at an empty line: the prompt ends
st, end = None, time.time() + 5
while time.time() < end:
    s.drain(0.2)
    pid, w = os.waitpid(s.pid, os.WNOHANG)
    if pid: st = w; break
if st is None: s.close(1.0)
lines = [l.rstrip() for l in render(s.out).split('\n')]
need('world' in lines, 'the line edited: print("world")')
need('world again' in lines, 'the history recalled and edited: world again')
need('8' in lines, 'a variable kept: 8')
need('item 1' in lines and 'item 2' in lines, 'a line that goes on: item 1, item 2')
need(any(l.startswith('...> ') for l in lines), 'the prompt for a line that goes on: ...> ')
need('half typed' not in lines, '^C ran the line half typed')
need(st is not None and os.WIFEXITED(st) and os.WEXITSTATUS(st) == 0, '^D: status %r' % (st,))
if fail:
    print('FAIL rill2 prompt-probe: ' + '; '.join(fail)); print('\n'.join(lines)); sys.exit(1)
print('rill2 prompt-probe: ok')
