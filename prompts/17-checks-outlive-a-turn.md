# 17 — a check that outlives a turn

**Fires when** you start a check - an acceptance suite, a long build, a
benchmark - that may run longer than one tool call or one turn is
allowed to.

**Skip when** the check finishes well inside one call.

## Why this exists

An assistant's tool calls have a time limit; a project's acceptance
suite need not respect it. A shell project's suite took ten minutes
against a five-minute limit per call. Run in the foreground it was
killed mid-way; run in the background it sometimes outlived the turn,
and the next turn found a log that stopped at "== the assembly engine
==" - neither a pass nor a failure. Twice a commit was one step away
from being made on such a log, by a script that would have read "no
failures printed" as success.

## Do this

1. **Run it detached, into a file, with an exit marker.** `setsid nohup
   sh -c 'suite > LOG 2>&1; echo status=$? >> LOG' &` - the marker
   line is written only when the suite has finished.

2. **Act only on the marker.** "No failure in the log" is not a pass; a
   cut-off log contains no failures either. Commit on `status=0` and on
   nothing else, and let the commit command itself test for it.

3. **Poll in calls that each fit the limit**, and keep nothing else
   running that the check builds or reads - a parallel build can change
   its inputs under it.

4. **A run interrupted between turns is rerun**, not resumed and not
   trusted for its first half. Restore anything a partial update may
   have written (a baseline file) before rerunning.

5. **Say in the reply what is still running** and what will be checked
   next turn, so a cut-off turn is not mistaken for a finished one.

## Artifact required

The detached command, the log's path, the marker line read back, and the
commit that depended on it - or, for an interrupted run, the rerun.
