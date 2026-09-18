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
    ("ps1-literal", {"PS1": "XX> "}, ["echo hi\n", ("exit\n", 'nowait')], 'raw'),
    ("ps2-literal", {"PS1": "XX> ", "PS2": "YY> "}, ["for i in 1\n", "do echo $i\n", "done\n", ("exit\n", 'nowait')], 'raw'),
]
