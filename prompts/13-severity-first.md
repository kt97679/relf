# 13 — rank failures by what they cost, and look for the worst on purpose

**Fires when** you have a list of failing tests to work through - a
conformance corpus, a CI dashboard, a bug queue - or are deciding
whether a pass count is the thing to raise.

**Skip when** there is one failure and it is already understood.

## Why this exists

A pass count weighs a segmentation fault the same as a reworded error
message. A project with two external conformance corpora (357 and 1775
cases) spent some time raising those counts before asking what the
failures WERE. When it ranked them - crash, hang, wrong result, wrong
wording - the top of the list held four crashes, three of them in
constructs ordinary scripts use: a single-digit case pattern, `getopts`
with `OPTIND=0`, and a `PS4` holding any expansion. Each was worth more
than dozens of the alias edge cases below it.

And the crashes that mattered had each been found by ACCIDENT. A
crash-only fuzzer - mutate snippets from the existing tests, run them
under resource limits, report only what the runtime calls a crash or a
hang the reference implementation does not share - found two more in
its first 200 seconds and two more in its next four minutes. Because it
compares no output, it cannot report a false difference.

## Do this

1. **Classify every failure before fixing any**: crash (the runtime
   says so), hang (timeout, and the reference does not), wrong result,
   wrong wording. Make the test runner print the class, not just a
   count - a failure list with no severity will be worked in whatever
   order it prints.
2. **Work down that list.** Crashes and hangs first; then wrong results
   that ordinary use hits; then edge cases and wording.
3. **Look for crashes on purpose.** Mutate what you already have - test
   inputs, examples - and report only crashes and reference-free hangs.
   Shrink every finding to the smallest input that still reproduces it,
   and keep the reproducers as regression cases.
4. **Get a backtrace in the program's own terms.** For a runtime with
   its own execution model (an interpreter, a VM), a native backtrace
   stops at the dispatcher; map the virtual instruction pointer and
   return stack back to source-level names. Build that tool once.
5. **Watch for timing in the harness itself.** A "hang" on a loaded
   machine may be a slow correct run, and a race in a test is not a bug
   in the program. Re-run a timing failure alone before believing it.

## Artifact required

The failure list with a class on every line, the order you will work
it in, and - for each crash - the shrunken reproducer and its
source-level backtrace.
