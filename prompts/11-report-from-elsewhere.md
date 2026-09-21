# 11 — a report is only worth what it contains

**Fires when** you are writing output that someone on another machine
will paste back to you — a test failure, a build error, an acceptance
run — or when you are reading one.

**Skip when** the reader has the machine in front of them.

## Why this exists

Eleven rounds of remote reports, and the time each took was decided by
what the output carried, not by how hard the bug was.

- `tests/run_tests.sh exited 1 - see /tmp/verify-run.log` — the log was
  on their machine. One wasted round.
- A failing comparison printed the first six lines of each side. Every
  case that agrees for six lines and diverges on the seventh looked
  identical and baffling. Several wasted rounds.
- A failure grep matched `error`, which matched **`no errors`** in a
  passing line, and reported that line as the failure.
- `portability: 1 problem` named nothing.
- `interactive:failed 3` named nothing.
- A step failed under `set -e` inside `output=$(...)`, which exits
  before the next line can read the status, so the log ended after the
  last passing step and said nothing at all.

The one report that resolved in a single round contained the assertion
name, the expected value and the actual value. It was fixed in ten
minutes, and the actual value (`$ ` — the default prompt) named the
cause immediately: not a wrong expansion, a variable that never arrived.

## Do this

When writing output someone will send back:

1. **Print the evidence, not the path to it.** Attach the failing lines
   and the tail of the log. A path is a file on a machine you do not
   have.
2. **Show expected and actual, labelled**, and say which side is which.
   `-` and `+` need a legend.
3. **When the two look identical, show bytes.** Trailing whitespace and
   CR are invisible and common.
4. **Name what failed, not how many.** A count with no name costs a
   round trip.
5. **Do not let a failure be silent.** `set -e` around a command
   substitution, a step whose output is captured and then discarded, a
   check whose own timeout fires — each turns a failure into an absence.
   Capture the status locally (`|| status=$?`) and print what you have.
6. **Grep for failures precisely.** `error` matches `no errors`;
   `FAIL` matches `FAILED: 0`.

When reading one:

7. **The actual value usually names the cause.** A default where a
   custom value was expected means it never arrived. A right answer one
   line down means something else wrote to the same stream.
8. **Reproduce before fixing**, even for a machine you do not have: a
   changed shebang, a forced environment variable, an artificial load.
   If the reproduction gives the reporter's exact numbers, the fix can
   be verified without them.

## Artifact required

For a failure you are reporting: the name, the expected value, the
actual value, and the surrounding context — in the output itself. For a
failure you are diagnosing: a local reproduction that produces the same
symptom, or one line saying why it cannot be reproduced and what you
asked for instead.
