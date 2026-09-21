#!/usr/bin/env python3
"""tests/interactive/search-probe.py - ^R, reverse incremental search.

Runs with the pty suite (tests/interactive/run calls it after
run_cases.py). It is assertion-shaped rather than transcript-shaped
because the transcripts in expected/ are recorded from dash, and dash
has no ^R: there is nothing to record this from but the behaviour
itself, stated as checks (Iteration 409).

Each check names one readline rule the search follows. Exit status is
the number of checks that failed.
"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from pty_session import Session, render

sh = os.environ.get('THIS_SH', os.path.join(here, '..', '..', 'relfsh'))
sh = os.path.abspath(sh)
s = Session([sh], env=dict(os.environ, PS1='$ ', RELF_PS1='$ '))
s.wait_prompt(Session.TIMEOUT, 0)
for w in ("alpha", "beta", "gamma"):
    s.send("echo %s\n" % w)

def keys(k):
    s.send(k, wait=False)
    while s._read(Session.SETTLE + 0.1):
        pass
    return render(s.out)             # the whole screen, rendered

checks = []
def check(name, ok):
    checks.append((name, ok))

scr = keys("\x12al")
check("^R shows the newest match", "(reverse-i-search)'al': echo alpha" in scr)
scr = keys("\r")
check("RETURN accepts and runs it", scr.rstrip().split("\n")[-2] == "alpha")
scr = keys("\x12zz")
check("a pattern that matches nothing says so", "(failed reverse-i-search)'zz'" in scr)
scr = keys("\x07")
check("^G restores the line as it was", scr.rstrip().endswith("$"))
# RETURN above ran `echo alpha` again, so it is the newest entry now.
scr = keys("\x12e")
check("the newest entry wins", "'e': echo alpha" in scr)
scr = keys("\x12")
check("^R again steps to an older match", "'e': echo gamma" in scr)
scr = keys("\x12")
check("... and older again", "'e': echo beta" in scr)
scr = keys("\x1b[D")
check("any other key accepts, then acts", scr.rstrip().endswith("$ echo beta"))
keys("\x15exit\n")

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    if not ok:
        print("FAIL search-probe: %s" % n)
print("%d search checks, %d failed" % (len(checks), len(failed)))
sys.exit(len(failed))
