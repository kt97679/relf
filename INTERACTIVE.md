# Testing the interactive shell (Iteration 301)

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

## What it found

Nine cases pass: basic commands, three kinds of multi-line construct, a
function typed over several lines, a quote continued across a newline,
exit status at the prompt, an unknown command, and background jobs.

Seven do not, and each is a real gap:

| case | what dash does | what this shell does |
|---|---|---|
| `ps1-literal` | uses `$PS1` | always prints `$ ` |
| `ps2-literal` | uses `$PS2` for continuations | always prints `$ ` |
| `empty-lines` | a blank line reprompts with PS1 | asks for a continuation |
| `intr-at-prompt` | `^C` discards the line, prompts afresh | keeps the line, no new prompt |
| `intr-during-command` | newline after `^C`, then the prompt | prompt on the same line |
| `eof-exits` | a newline before exiting | none |
| `job-in-background` | `[1] + Done ...` notices | nothing |

`-i` is also unimplemented: `relfsh -i` treats the flag as a file name.
Interactivity is decided by `isatty` alone, so a piped script cannot be
forced interactive and a terminal session cannot be forced not to be.

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
