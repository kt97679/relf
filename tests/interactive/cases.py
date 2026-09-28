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
    # ^C stops the command line (Iteration 571, A31): each of these ran on
    # through it - the signal was consumed between commands and nothing
    # more. Recorded from dash: the loop, the list, the subshell and the
    # command substitution all stop, `after` is never printed, $? is 130.
    # Not here: a loop around a short external command. There a ^C can
    # fall between the child's exit and the shell taking the terminal back,
    # and go to nobody - dash lost it in 3 of 12 runs, bash in 1, this
    # shell in 1 on each engine - so no single-^C case can pass reliably.
    ("intr-loop-builtin", {}, [("while :; do :; done; echo after\n", 'nowait'), 0.5, "INTR", "echo $?\n", ("exit\n", 'nowait')]),
    ("intr-list", {}, [("sleep 5; echo after\n", 'nowait'), 0.5, "INTR", "echo $?\n", ("exit\n", 'nowait')]),
    ("intr-subshell", {}, [("( while :; do :; done ); echo after\n", 'nowait'), 0.5, "INTR", "echo $?\n", ("exit\n", 'nowait')]),
    ("intr-cmdsub", {}, [("x=$(while :; do :; done); echo after\n", 'nowait'), 0.5, "INTR", "echo $?\n", ("exit\n", 'nowait')]),
    # A subshell shares the shell's process group, so a ^C reaches both,
    # and a wait may set the shell's own SIGINT aside (Iteration 572).
    # intr-subshell's fresh line came from that SIGINT alone, and where the
    # wait took it - fury, rage - the prompt was drawn over the ^C: now a
    # child dead of ^C gives it. And a child that SURVIVES the ^C handled
    # it: dash and bash go on with the line, no fresh line - `^Cafter`,
    # $? 0. This one takes 0.3 s to exit, so the shell is always waiting
    # when its SIGINT lands. Recorded from dash.
    ("intr-subshell-trap", {}, [("( trap 'sleep 0.3; exit 3' INT; while :; do :; done ); echo after\n", 'nowait'), 0.5, "INTR", 1.0, "echo $?\n", ("exit\n", 'nowait')]),
    # A runaway word in the forth builtin (571): recorded from this shell,
    # dash having none - and read: no message, `after` not printed, 130.
    ("intr-forth-spin", {}, [("forth ': SPIN BEGIN 0 UNTIL ; SPIN'; echo after\n", 'nowait'), 0.5, "INTR", "echo $?\n", ("exit\n", 'nowait')]),
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
    # Delete, ^D on a non-empty line, and ^K (Iteration 557): three keys
    # coverage found no test pressing - ED-DELETE and ED-KILL-TO-END had
    # never run. Recorded from this shell, and read before keeping: each
    # transcript must show the edited line's result, XY, XY and keep.
    ("edit-delete", {}, ["echo XaY", "\x1b[D\x1b[D", "\x1b[3~", "\n", ("exit\n", 'nowait')]),
    ("edit-ctrl-d-deletes", {}, ["echo XbY", "\x1b[D\x1b[D", "\x04", "\n", ("exit\n", 'nowait')]),
    ("edit-kill-to-end", {}, ["echo keep rubbish", "\x1b[D" * 8, "\x0b", "\n", ("exit\n", 'nowait')]),
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
    # bg on the SECOND of two stopped jobs (Iteration 559): mutation
    # testing found `0 JOB-STATES JOB-SEL @ CELLS + !` could say - for +
    # unnoticed - the same slot for job 1, the wrong one for any other,
    # and the only bg test had one job. Recorded from this shell (dash's
    # job notices are worded otherwise - see KNOWN-DIVERGENT), and read:
    # jobs must list job 2 as running after bg %2. `kill` and `sleep 0.3` on
    # ONE line (Iteration 564): on two, whether the Terminated notice came
    # before the next prompt or after it was a race - recorded one way here,
    # it went the other on fury and rage. On one line the job dies during
    # the sleep, and its notice comes before the next prompt, always.
    ("job-control-bg-second", {}, [("sleep 5\n", 'nowait'), 0.5, "SUSP", ("sleep 6\n", 'nowait'), 0.5, "SUSP",
                                   "bg %2\n", "jobs\n", "kill %1 %2; sleep 0.3\n", ("exit\n", 'nowait')]),
    # A line of blanks at a command's start is no continuation: PS1 again,
    # as dash - the editor's reader made the next prompt PS2 (Iteration
    # 567, found against bash's editor by tools/editor-vs-bash.py).
    ("blank-line-ps1", {}, ["   \n", "echo x\n", ("exit\n", 'nowait')]),
    # Output that ends without a newline stays, the prompt after it
    # (Iteration 574): the editor drew the prompt from column 0 and each
    # redraw went back there, wiping `part` - and the article's own first
    # example, `forth '2 3 + .'`, showed no 5. Recorded from dash; the
    # forth one from this shell, and read: `5 ` and the prompt after it.
    ("partial-line-kept", {}, ["printf part\n", "echo next\n", ("exit\n", 'nowait')]),
    ("partial-line-forth", {}, ["forth '2 3 + .'\n", "echo next\n", ("exit\n", 'nowait')]),
    # The word keys and the kill buffer (Iteration 568, A30): recorded
    # from this shell, each result what bash's readline gives for the
    # same keys (tools/editor-vs-bash.py) - alpha Xbeta gamma, alpha
    # beta, alpha beta gamma (two kills in a row, one yank), beta gamma.
    ("edit-word-motion", {}, ["echo alpha beta gamma", "\x1bb", "\x1bb", "X", "\n", ("exit\n", 'nowait')]),
    ("edit-kill-word-back", {}, ["echo alpha beta gamma", "\x17", "\n", ("exit\n", 'nowait')]),
    ("edit-kills-then-yank", {}, ["echo alpha beta gamma", "\x17", "\x17", "\x19", "\n", ("exit\n", 'nowait')]),
    ("edit-kill-word-fwd", {}, ["echo alpha beta gamma", "\x01", "\x1bf", "\x1bd", "\n", ("exit\n", 'nowait')]),
    ("ps1-literal", {"PS1": "XX> "}, ["echo hi\n", ("exit\n", 'nowait')], 'raw'),
    ("ps2-literal", {"PS1": "XX> ", "PS2": "YY> "}, ["for i in 1\n", "do echo $i\n", "done\n", ("exit\n", 'nowait')], 'raw'),
    # \j and \D{format} (Iteration 476). Only the escapes whose output does
    # not depend on the clock are in the transcript - a literal %, and an
    # unknown specifier kept as written; the date specifiers themselves were
    # checked against `date +FORMAT`, which a golden file cannot do.
    ("ps1-jobs-and-date", {"PS1": "[\\j|\\D{%%}|\\D{x%Qy}]> "}, ["sleep 30 &\n", "echo mark\n", ("exit\n", 'nowait')], 'raw'),
]
