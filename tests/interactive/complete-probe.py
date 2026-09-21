#!/usr/bin/env python3
"""tests/interactive/complete-probe.py - TAB, filename completion.

Runs with the pty suite, like search-probe.py and for the same reason:
the transcripts in expected/ are recorded from dash, and dash has no
completion to record (Iteration 410). Each check names one rule.

It builds its own scratch directory - two names sharing a prefix, a
directory with a file in it, a name with a blank, a dot-file - so the
answers depend on nothing in the machine's filesystem. Exit status is
the number of checks that failed.
"""
import sys, os, shutil, tempfile
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from pty_session import Session, render

d = tempfile.mkdtemp(prefix='relf-complete-')
os.mkdir(os.path.join(d, 'alpine'))
for f in ('alpha.txt', 'beta', 'my notes', '.hidden', os.path.join('alpine', 'inner.c')):
    open(os.path.join(d, f), 'w').close()

sh = os.path.abspath(os.environ.get('THIS_SH', os.path.join(here, '..', '..', 'relfsh')))
s = Session([sh], env=dict(os.environ, PS1='$ ', RELF_PS1='$ '), cwd=d)
s.wait_prompt(Session.TIMEOUT, 0)

def keys(k):
    s.send(k, wait=False)
    while s._read(Session.SETTLE + 0.1):
        pass
    lines = render(s.out).split("\n")
    while lines and not lines[-1].strip():   # empty trailing lines only:
        lines.pop()                          # a trailing BLANK is the point
    return lines
def line():
    return keys("")[-1]

checks = []
def check(name, ok):
    checks.append((name, ok))

keys("cat bet\t");      check("one candidate is completed, with a blank", line() == "$ cat beta ")
keys("\x15cat alpi\t"); check("a directory gets a slash instead", line() == "$ cat alpine/")
keys("\t");             check("... and completion carries on inside it", line() == "$ cat alpine/inner.c ")
keys("\x15cat al\t");   check("several candidates: what they all share", line() == "$ cat alp")
scr = keys("\t")
tail = " ".join(scr[-3:])
check("... and a second TAB lists them", "alpha.txt" in tail and "alpine" in tail)
check("... with the line redrawn under the list", scr[-1] == "$ cat alp")
keys("\x15cat my\t");   check("a blank in a name comes back escaped", line() == "$ cat my\\ notes ")
keys("\x15cat .h\t");   check("dot-files are offered to a dot prefix", line() == "$ cat .hidden ")
keys("\x15cat zz\t");   check("no candidate leaves the line alone", line() == "$ cat zz")
keys("\x15exit\n")
shutil.rmtree(d, ignore_errors=True)

failed = [n for n, ok in checks if not ok]
for n in failed:
    print("FAIL complete-probe: %s" % n)
print("%d completion checks, %d failed" % (len(checks), len(failed)))
sys.exit(len(failed))
