# 16 — a fix is shown by its test failing first

**Fires when** you are about to claim a bug is fixed, or to add a
regression test for one.

**Skip when** there is no claim: a refactor that promises to change
nothing is shown by everything still passing - but a test it adds is
not: see step 5.

## Why this exists

A test that passes after a fix proves nothing about the fix unless it
failed before it. In a shell project, a fix for a file descriptor that
leaked when ^C landed between opening a file and protecting it came
with a probe; the probe was run against the shell without the fix - the
fix stashed, the shell rebuilt - and failed there, and passed with it.
That pairing is what made the claim worth anything.

The same change carried a second claim: that it also cured an outer
command going deaf to ^C after an inner one finished. It had never been
seen failing. The same check - the old shell, the same probe - showed
the old shell handling it fine: the flaw had never existed, and the
claim came out of the commit message, the comments and the log before
anyone else read it. A fix you never saw fail is a guess.

A change that promises to change nothing - an optimisation - adds tests
of its own, and they can pass for nothing. In the same project two of
an optimisation's new tests were run on deliberately broken versions of
the change. One could not see a bound checked one group too late, until
it recorded how far its run had got; the other could not see a
page-boundary check removed at all, because the page after its buffer
is always mapped. Both passed, broken or not, until run that way.

## Do this

1. **Reproduce the failure before fixing it**, with the test you will
   keep. If it cannot be made to fail on demand (a race, a timing
   window), build the case that forces the same state by other means -
   and say that the test forces it, not that it catches it.

2. **After the fix, run the test both ways:** on the build without the
   fix (stash it, rebuild) it must fail; with the fix it must pass.
   Keep the commands; they are the evidence.

3. **Every claim gets its own pair.** A change that fixes two things
   needs two tests that each failed before. A claim with no failing run
   behind it comes out of the message, the comments and the log.

4. **When the old build passes too, say so** - in the log, as a
   correction - and keep the test only as a guard, labelled as one.

5. **For a change that promises to change nothing, break it on
   purpose.** Build two or three wrong versions of the change - an
   off-by-one, a check removed, a bound moved - and run its new tests on
   each. Each should fail. A version that passes is a blind spot: fix the
   test, or write the blind spot down beside it.

## Artifact required

For each claimed fix: the test, its failing run without the fix, its
passing run with it. For each claim that could not be shown failing:
its withdrawal, in the same places it was made. For a change that
promises to change nothing: the broken versions tried and which tests
failed on each; one that passed, with the blind spot it shows.
