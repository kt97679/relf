r"""tests/interactive/cases.py - what an interactive session must do.

Each case is a name, the environment, and the steps to type. A step is
either text to send (waiting for the next prompt afterwards), or one of
the control characters INTR (^C), EOF (^D), QUIT (^\), or a number of
seconds to wait. `nowait` sends without waiting for a prompt, for the
steps that end the session.
"""
CASES = [
    ("basic", {}, ["echo one\n", "x=5\n", "echo $x\n", ("exit\n", 'nowait')]),
    ("multiline-for", {}, ["for i in 1 2\n", "do echo $i\n", "done\n", ("exit\n", 'nowait')]),
    ("multiline-if", {}, ["if true\n", "then echo yes\n", "fi\n", ("exit\n", 'nowait')]),
    ("multiline-quote", {}, ['x="a\n', 'b"\n', "echo \"[$x]\"\n", ("exit\n", 'nowait')]),
    ("function-over-lines", {}, ["f() {\n", "echo in-f\n", "}\n", "f\n", ("exit\n", 'nowait')]),
    ("bad-command", {}, ["nosuchcmd\n", "echo $?\n", ("exit\n", 'nowait')]),
    ("status-visible", {}, ["false\n", "echo $?\n", "true\n", "echo $?\n", ("exit\n", 'nowait')]),
    ("intr-at-prompt", {}, ["echo before\n", "INTR", "echo after\n", ("exit\n", 'nowait')]),
    ("intr-during-command", {}, [("sleep 5\n", 'nowait'), 0.5, "INTR", "echo survived\n", ("exit\n", 'nowait')]),
    ("eof-exits", {}, ["echo one\n", ("EOF", 'nowait')]),
    ("ps1-from-env", {"PS1": "P1> ", "PS2": "P2> "}, ["echo hi\n", ("exit\n", 'nowait')]),
    ("ps2-continuation", {"PS1": "P1> ", "PS2": "P2> "}, ["for i in 1\n", "do echo $i\n", "done\n", ("exit\n", 'nowait')]),
    ("empty-lines", {}, ["\n", "\n", "echo after-blanks\n", ("exit\n", 'nowait')]),
    ("job-in-background", {}, ["sleep 0.1 &\n", "wait\n", "echo done\n", ("exit\n", 'nowait')]),
    # raw: the transcript is NOT prompt-normalised, so the prompt string
    # itself is what is being checked - normalising would hide a shell
    # that ignores PS1 altogether.
    # The line editor (Iteration 303). dash has no editor at all - an
    # arrow key reaches it as three bytes and goes into the command - so
    # these expectations cannot come from dash; they are recorded from
    # this shell and read as a description of what it does.
    ("edit-cursor", {}, ["echo XY", "\x1b[D\x1b[D", "Z\n", ("exit\n", 'nowait')]),
    ("edit-backspace", {}, ["echo abc\x7f\x7fZ\n", ("exit\n", 'nowait')]),
    ("edit-home-end", {}, ["echo mid", "\x01", "\x05", "!\n", ("exit\n", 'nowait')]),
    ("edit-kill-line", {}, ["echo rubbish\x15echo kept\n", ("exit\n", 'nowait')]),
    ("history-recall", {}, ["echo first\n", "echo second\n", "\x1b[A\x1b[A", "\n", ("exit\n", 'nowait')]),
    ("history-down", {}, ["echo one\n", "echo two\n", "\x1b[A\x1b[A", "\x1b[B", "\n", ("exit\n", 'nowait')]),
    # job control (Iterations 320-322): ^Z stops the command, jobs shows
    # it, bg resumes it, kill %1 ends it.
    # `sleep 0.3` after the kill so both shells have reaped the job by the
    # next prompt: dash reaps in its wait loop, this shell in the notice
    # pass, so without it the notice lands a prompt apart.
    ("job-control", {}, [("sleep 5\n", 'nowait'), 0.5, "SUSP", "jobs\n", "bg\n",
                         "kill %1\n", "sleep 0.3\n", "echo alive\n",
                         ("exit\n", 'nowait')]),
    ("ps1-literal", {"PS1": "XX> "}, ["echo hi\n", ("exit\n", 'nowait')], 'raw'),
    ("ps2-literal", {"PS1": "XX> ", "PS2": "YY> "}, ["for i in 1\n", "do echo $i\n", "done\n", ("exit\n", 'nowait')], 'raw'),
    # \j and \D{format} (Iteration 476). Only the escapes whose output does
    # not depend on the clock are in the transcript - a literal %, and an
    # unknown specifier kept as written; the date specifiers themselves were
    # checked against `date +FORMAT`, which a golden file cannot do.
    ("ps1-jobs-and-date", {"PS1": "[\\j|\\D{%%}|\\D{x%Qy}]> "}, ["sleep 30 &\n", "echo mark\n", ("exit\n", 'nowait')], 'raw'),
]
