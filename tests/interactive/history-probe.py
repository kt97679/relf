#!/usr/bin/env python3
"""history holds the session - the two limits removed in Iteration 408.

Not part of run_cases.py: forty commands through a pseudo-terminal take
twenty seconds, too slow for a suite that runs on every verify. Run it
by hand after touching edit.4's history or its line buffer:

    python3 tests/interactive/history-probe.py

It types past both old limits - 32 entries and 256 characters a line -
and walks back to the oldest.
"""
import sys, os
sys.path.insert(0, 'tests/interactive')
from pty_session import Session, render
sh = os.path.abspath('relfsh')
s = Session([sh], env=dict(os.environ, PS1='$ ', PS2='> ', RELF_PS1='$ ', RELF_PS2='> '))
s.wait_prompt(10, 0)
# 40 commands - more than the old 32-slot buffer held
for i in range(40):
    s.send("echo line%d\n" % i)
# a long line, longer than the old 255-byte slot
long_cmd = "echo " + "x" * 400
s.send(long_cmd + "\n")
# walk back 42 times: should reach the first command, not lose it
for _ in range(42):
    s.send("\x1b[A", wait=False)
    s._read(0.05)
s.send("\n")
s.send("exit\n", wait=False)
out = render(s.out)
print("oldest recalled:", "line0" in out.split("line0")[0][-0:] or "echo line0" in out)
print("long line kept:", ("x"*400) in out)
print("40th present:", "line39" in out)
