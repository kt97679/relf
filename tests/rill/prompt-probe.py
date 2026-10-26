#!/usr/bin/env python3
"""tests/rill/prompt-probe.py - the Rill prompt at a terminal (Iteration 825, QUESTIONS.md A38): relfsh's
line editor at Rill's prompt - a line edited with the arrows, the history recalled and added to, a
variable kept between lines, a path completed by TAB, a line that goes on (...> ), ^C dropping a line half typed, ^D at an empty
line ending the prompt with status 0. On a pseudo-terminal, as tests/interactive's probes; run by
tests/rill/run.
"""
import os, sys, time
sys.path.insert(0, 'tests/interactive')
from pty_session import Session, render
s = Session([os.path.abspath('relf64'), os.path.abspath('kernel64-rill.img')], prompts=('rill> ', '...> '))
fail = []
def need(ok, what):
    if not ok: fail.append(what)
need(s.wait_prompt(10, 0), 'no first prompt')
s.send('x = 4\n')
s.send('echo wrld' + '\x1b[D' * 3 + 'o\n')                    # three to the left, an o: echo world
s.send('\x1b[A again\n')                                       # the history: echo world, and " again"
s.send('echo {$x * 2}\n')
s.send('echo /tm\t\n')                                        # TAB: a path completed, /tmp/
s.send('echo half typed', wait=False); s.send_signal_char('INTR')   # ^C: the line dropped
s.send('for i in [1, 2] {\n'); s.send('echo item $i\n'); s.send('}\n')
s.send_signal_char('EOF', wait=False)                          # ^D at an empty line: the prompt ends
st, end = None, time.time() + 5                                # its own exit, before the terminal goes
while time.time() < end:
    s.drain(0.2)
    pid, w = os.waitpid(s.pid, os.WNOHANG)
    if pid: st = w; break
if st is None: s.close(1.0)
lines = [l.rstrip() for l in render(s.out).split('\n')]
need('world' in lines, 'the line edited: echo world')
need('world again' in lines, 'the history recalled and added to: world again')
need('8' in lines, 'a variable kept: 8')
need('/tmp/' in lines, 'TAB: echo /tm completed to /tmp/')
need('item 1' in lines and 'item 2' in lines, 'a line that goes on: item 1, item 2')
need(any(l.startswith('...> ') for l in lines), 'the prompt for a line that goes on: ...> ')
need('half typed' not in lines, '^C ran the line half typed')
need(st is not None and os.WIFEXITED(st) and os.WEXITSTATUS(st) == 0, '^D: status %r' % (st,))
if fail:
    print('FAIL prompt-probe: ' + '; '.join(fail)); print('\n'.join(lines)); sys.exit(1)
print('prompt-probe: ok')
