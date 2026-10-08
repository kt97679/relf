# 21 — a race needs the conditions it was seen under

**Fires when** you are about to explain, clear or close an intermittent
failure - a flaky test, a hang seen once - above all one seen on another
machine.

**Skip when** the failure reproduces on demand where you are.

## Why this exists

A shell project's interrupt fuzzer once got no answer from the shell, on
a sixteen-core machine, inside a full test run: once in twelve runs. The
next session had one CPU. It ran the failing case 108 times under four
busy loops - no failure - then read the code, found a window in which a
^C could survive to the next command, and wrote that down as the cause.
Probes that sent a ^C into that window on purpose, two ways, found the
shell handling both: the reading was half wrong. And on one CPU the
fuzzer and the shell cannot run at the same moment, which is what the
failure needed. A stress script for the sixteen-core machine - sixteen
fuzzers at once, the failing seed in every round - ran 4,800 cases there
without a failure. Only then was the item closed, as not reproduced under
its own conditions, with the fuzzer now reporting enough to explain it if
it comes back.

The same project carried an older flaky test, failing about one run in
five under load. Measured again under that load: none in 30. Its cause,
found long before, was the test's own wait for the output to go quiet -
the harness racing the program, not the program racing itself.

## Do this

1. **Write down the conditions it was seen under** - cores, load, what
   else ran, how often (once in N runs) - before anything else.

2. **Ask whether your machine can produce them.** A failure that needs
   two things running at the same instant cannot appear where only one
   can run. Then no run here is evidence of absence; say so.

3. **A mechanism found by reading is a hypothesis.** Force the event
   into the window on purpose - a probe that makes the state - before
   fixing anything. If the code handles it, the mechanism is wrong
   (`16`).

4. **Take the test to the conditions.** A stress script for the machine
   that has them - many instances at once, the failing seed among them,
   every failure printed with what would explain it - sent through `19`.

5. **Close on a count, under the conditions.** "0 failures in 4,800
   cases, sixteen at once on sixteen cores" closes; "not seen in 108
   runs on one CPU" does not. Leave the extra reporting in place.

6. **Separate the harness from the program.** A wait for output to go
   quiet races the program under load. Wait for a condition instead, or
   measure the wait first.

## Artifact required

The conditions; whether this machine can produce them, and why; the
probe for any mechanism claimed, with its result; the closing count and
where it ran.
