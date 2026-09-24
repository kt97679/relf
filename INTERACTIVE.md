# INTERACTIVE.md — the interactive shell, and how it is tested

Everything this shell does at a prompt - the prompt itself, a signal
typed at the keyboard, end of file from the terminal, a construct
continued over several lines - was untested, because none of it happens
without a terminal on the other end. `tests/interactive/` supplies one.

## How it works

`pty.fork()` from Python's standard library gives a pseudo-terminal and
a child attached to it; the child execs the shell, which sees a terminal
on all three descriptors and so runs interactively. The parent types
lines into the master side and reads what comes back.

    tests/interactive/pty_session.py   the session driver
    tests/interactive/cases.py         what to type, and with what PS1/PS2
    tests/interactive/run_cases.py     runner: compare against expected/
    tests/interactive/run              entry point (THIS_SH selects the shell)
    tests/interactive/expected/*.txt   transcripts recorded from dash
    tests/interactive/KNOWN-DIVERGENT  cases this shell does not match yet

**Synchronisation is the whole difficulty.** A first version slept
between steps and its transcripts came out in a different order on
almost every run: the terminal echoes a typed line at once, while the
command's own output arrives later, so a step sent too early interleaves
with the previous one's output. Sleeping long enough to be safe made the
suite slow; short enough to be quick made it flaky.

What works is waiting for the next prompt - but only for a prompt that
arrives AFTER the point where the line was sent. Checking the whole
buffer returns immediately, because the PREVIOUS prompt is still the
last thing in it. With that one change every case became reproducible.

**Comparing shells that prompt differently.** A transcript is normalised:
carriage returns removed, each shell's prompt strings replaced by
`<PS1>`/`<PS2>` (longest first, so a `PS1="P1> "` is not half-eaten by
the rule for `> `), and any "not found" line replaced, since every shell
words it differently and names itself. Two cases opt out of
normalisation entirely (`raw`) to check the prompt STRING: with prompts
normalised away, a shell that ignores `PS1` looks identical to one that
honours it.

Expectations are recorded from dash (`tests/interactive/run --record
/usr/bin/dash`), so the suite says "behave as dash does at a prompt".

## Where it stands (Iteration 493)

24 cases. 23 match their recorded transcripts; one, `job-control`, is
listed in `KNOWN-DIVERGENT`. `^Z`, `jobs`, `bg`, `kill %1` and the
wording of every notice match dash's since Iteration 324; what differs
is WHEN a completion notice appears - this shell reaps in its notice
pass and reports at the first prompt after the job ends, dash one
prompt later. Both are before a prompt, as POSIX asks, and on a slow
machine the two coincide and the case passes.

When the harness was written, at Iteration 301, seven cases did not
match: `PS1`, `PS2`, the blank line and the newline on `^D` (fixed in
302), the job notice and its text (310, 312), and `^C` at the prompt
and during a command (314, 315). Noticing `^C` at all needed an engine
change: `SIGNAL-ACTION` installed handlers with `SA_RESTART`, so the
read was resumed and the interrupt went unseen until the line was
submitted.

`-i` forces an interactive shell - a piped script gets prompts - but
`$-` does not show the `i` (nor the `s`) that dash puts there (GOALS.md).

## Running it

    sh tests/interactive/run                 # against ./relfsh
    THIS_SH=/bin/bash sh tests/interactive/run   # against another shell
    sh tests/interactive/run --record /usr/bin/dash
    sh tests/interactive/run basic multiline-for  # named cases only

`THIS_SH` may carry arguments, which bash needs before it will leave the
environment's `PS1` alone:

    THIS_SH="/bin/bash --norc --noprofile" sh tests/interactive/run

dash is the reference the expectations come from. bash can be driven by
the same harness, but its sessions differ beyond the prompt - it echoes
`exit` back, and reports jobs in its own format - so it is useful for
looking at a behaviour, not for asserting on it.

It needs python3, which the other suites do not; `tests/verify` records
its three numbers alongside the rest.

## The line editor (Iteration 303)

Until 303 an interactive line came from the terminal driver's cooked
mode: it could be typed and backspaced over, and nothing else. An arrow
key arrived as three bytes and went into the command, so correcting
`echo hi` ran `echo h^[[Di`. There was no history.

`edit.4` reads one byte at a time and does the editing itself:

| key | effect |
|---|---|
| left, right, `^B`, `^F` | move the cursor |
| Home, End in every dialect | `ESC [ H`/`F`, `ESC O H`/`F` (xterm), `ESC [ 1 ~`/`4 ~` (screen, tmux, the console), `ESC [ 7 ~`/`8 ~` (rxvt); any other sequence is read whole and ignored rather than typed in (Iteration 412) |
| Home, End, `^A`, `^E` | start and end of the line |
| backspace, Delete, `^D` | delete before, under the cursor |
| `^K`, `^U` | kill to the end, kill the line |
| up, down | walk the history - every line of the session, of any length (Iteration 408; it was 32 lines of 255 characters) |
| TAB | a first word (or one after `;` `|` `&` `(` or a keyword) completes as a command - builtins and executables on PATH (Iteration 414); anything else completes as a path: one candidate whole (with `/` or a blank), several to what they share, a second TAB lists them; special characters come back escaped (Iteration 411) |
| `^R` | reverse incremental search: type to narrow, `^R` for an older match, `^G` to give up, RETURN to run it, any other key to accept and edit (Iteration 409) |
| `^C` | abandon the line, prompt afresh |
| `^D` on an empty line | end of input |

Two engine primitives support it: `TERM-RAW`, which turns off `ICANON`
and `ECHO` while leaving `ISIG` alone - so `^C` still raises a signal -
and `TERM-RESTORE`. Redrawing is a carriage return, the prompt, the
line, an erase-to-end and a cursor move, all to fd 2 where the prompt
goes.

**The harness had to learn to render.** A line editor rewrites its line
on every keystroke, so the raw stream is a run of half-typed lines; the
old transcript, which only removed carriage returns, turned the session
into nonsense. `render()` now replays the stream the way a terminal
would - CR to column 0, `ESC[K` erases from the cursor, `ESC[nC` moves
right, a newline finishes the line - so a transcript is what a person
would SEE. A shell in cooked mode, which writes each line once, renders
unchanged, so dash's recorded expectations still hold.

Six cases cover the editor. They cannot be recorded from dash, which has
no editor at all, so they are recorded from this shell and read as a
description of what it does.
