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
# Home and End, in every dialect a terminal speaks (Iteration 412):
# xterm's ESC [ H / ESC [ F and ESC O H / ESC O F, screen, tmux and the
# Linux console's ESC [ 1 ~ / ESC [ 4 ~, rxvt's ESC [ 7 ~ / ESC [ 8 ~.
def edit_line(seq):
    # keys() returns the whole rendered screen as ONE string here (it is
    # a list in complete-probe.py); the edited line is its last line.
    return keys(seq).rstrip("\n").split("\n")[-1].rstrip()
for home, end, who in (("\x1b[H", "\x1b[F", "xterm"), ("\x1bOH", "\x1bOF", "xterm, application mode"),
                       ("\x1b[1~", "\x1b[4~", "screen, tmux, the console"),
                       ("\x1b[7~", "\x1b[8~", "rxvt")):
    keys("\x15mid")
    got_home = edit_line(home + "<")
    got_end = edit_line(end + ">")
    check("Home and End under %s" % who, got_home == "$ <mid" and got_end == "$ <mid>")
# a sequence with parameters must not leave its tail in the line
keys("\x15ab")
check("^-right leaves no garbage", edit_line("\x1b[1;5C") == "$ ab")
# The prompt's \! counts history entries (Iteration 417), so it must
# advance by one for each line entered at the terminal.
s2 = Session([sh], env=dict(os.environ, PS1='<\\!> ', RELF_PS1='<\\!> '), prompts=('> ',))
s2.wait_prompt(Session.TIMEOUT, 0)
s2.send("echo a\n"); s2.send("echo b\n")
while s2._read(Session.SETTLE + 0.1):
    pass
seen = [l for l in render(s2.out).split("\n") if l.strip()]
nums = [l.split(">")[0].lstrip("<") for l in seen if l.startswith("<")]
check("\\! advances with each entry", len(nums) >= 3 and nums[-3:] == ["1", "2", "3"])
s2.send("exit\n", wait=False)
keys("\x15exit\n")

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    if not ok:
        print("FAIL search-probe: %s" % n)
print("%d search and editing checks, %d failed" % (len(checks), len(failed)))
sys.exit(len(failed))
