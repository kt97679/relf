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
os.mkdir(os.path.join(d, 'my dir'))
for f in ('alpha.txt', 'beta', 'my notes', '.hidden', os.path.join('alpine', 'inner.c'),
          os.path.join('my dir', 'inner file')):
    open(os.path.join(d, f), 'w').close()
# A directory of commands at the front of PATH (Iteration 414): three
# executables whose sorted order is not the order they were made in,
# and one file that is not executable and must never be offered.
bindir = tempfile.mkdtemp(prefix='relf-complete-bin-')
for name, mode in (('zq-gamma', 0o755), ('zq-alpha', 0o755), ('zq-beta', 0o755), ('zq-plain', 0o644)):
    path = os.path.join(bindir, name)
    open(path, 'w').write('#!/bin/sh\n')
    os.chmod(path, mode)

sh = os.path.abspath(os.environ.get('THIS_SH', os.path.join(here, '..', '..', 'relfsh')))
s = Session([sh], env=dict(os.environ, PS1='$ ', RELF_PS1='$ ',
                           PATH=bindir + ':' + os.environ.get('PATH', '')), cwd=d)
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

def keys_until(k, marker):
    # For a slow operation, wait for what it should produce rather than
    # for a quiet moment: TAB on an empty line reads every directory on
    # PATH, and on an ARMv7 board that outlasted the 0.3 s quiet window
    # keys() waits for, so the check read the screen too early and
    # failed (Iteration 416). Session.TIMEOUT is RELF_PTY_TIMEOUT.
    import time
    m = len(s.out)
    s.send(k, wait=False)
    t0 = time.time()
    while marker not in render(s.out[m:]) and time.time() - t0 < Session.TIMEOUT:
        s._read(0.1)
    while s._read(Session.SETTLE + 0.1):
        pass
    lines = render(s.out).split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    return lines

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
keys("\x15cat my\t");   check("a blank in a name comes back escaped", line() == "$ cat my\\ ")
keys("\x15cat .h\t");   check("dot-files are offered to a dot prefix", line() == "$ cat .hidden ")
# A word that already holds an escaped blank (Iteration 418): it is one
# word, and it is unescaped before it is matched - in the name and in
# the directory part alike.
keys("\x15cat my\\ n\t");      check("an escaped blank stays inside the word", line() == "$ cat my\\ notes ")
keys("\x15cat my\\ d\t");      check("... and a directory completes past it", line() == "$ cat my\\ dir/")
keys("\x15cat my\\ dir/in\t"); check("... and so does a name inside that directory", line() == "$ cat my\\ dir/inner\\ file ")
keys("\x15cat zz\t");   check("no candidate leaves the line alone", line() == "$ cat zz")
# command position (Iteration 414)
keys("\x15zq-a\t");        check("a first word completes from PATH", line() == "$ zq-alpha ")
keys("\x15zq-\t")
scr = keys("\t")
check("the listing is sorted, and executables only",
      "zq-alpha  zq-beta  zq-gamma" in " ".join(scr[-3:]) and "zq-plain" not in " ".join(scr[-3:]))
keys("\x15ech\t");         check("a builtin completes too", line() == "$ echo ")
keys("\x15ls; zq-a\t");    check("after ; is command position", line() == "$ ls; zq-alpha ")
keys("\x15if zq-a\t");     check("after a keyword is command position", line() == "$ if zq-alpha ")
keys("\x15./bet\t");       check("a first word with a slash is a path", line() == "$ ./beta ")
scr = keys_until("\x15\t", "candidates")
check("TAB on nothing gives a count, not a flood", "candidates" in " ".join(scr[-3:]))
keys("\x15exit\n")
shutil.rmtree(d, ignore_errors=True)
shutil.rmtree(bindir, ignore_errors=True)

failed = [n for n, ok in checks if not ok]
for n in failed:
    print("FAIL complete-probe: %s" % n)
print("%d completion checks, %d failed" % (len(checks), len(failed)))
sys.exit(len(failed))
