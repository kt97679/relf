# 18 — the first turn of a session that picks up someone else's work

**Fires when** a session starts on work another session, person or
machine left: a bundle, a checkout, a start message with attachments.

**Skip when** the work starts from nothing - then `01`.

## Why this exists

`07` is written from the sender's side of a handoff. This one is the
receiver's, and every item below happened in one first turn.

A shell project's session began with a git bundle, a benchmark report
from a second machine, and a start message: read the log's index, its
last seven entries, a design section, and the prompt library. It read
all of that first - the library whole, though the library's own index
says to fetch a prompt only when it fires - and the turn ran out of tool
calls with nothing changed. The acceptance suite, nine minutes long,
had been started two-thirds of the way in, and did not finish in that
turn.

The container was fresh. It had no 32-bit toolchain, so half the build
failed, and no commit identity, so the first commit failed. Each was
found by failing.

The start message carried five things the repository did not hold: the
previous remote report's figures, a memory figure, the next candidates'
profile shares, a list of hazards to remember, and - by not mentioning
it - the fact that the attached report was newer than the figures the
message quoted. No report from the second machine had ever been
committed, though every speed claim in the project rested on one.

And one of the message's reminders, "a detached check dies at turn
end", was not true there: the check started in the first turn finished,
with its marker, in the second.

## Do this

1. **Start the long check first, on the inherited state, unchanged.**
   Build, then start the acceptance suite detached (`17`), before
   reading anything but how to run it. It answers "is the starting point
   green here?" A failure found before your first change belongs to the
   environment or to the handoff. The same failure found after it looks
   like yours. Read while the check runs.

2. **Look for what the environment lacks; don't wait to fail on it.**
   Check the toolchains the build names, the reference programs the
   suites compare against, a commit identity (`git config user.email`),
   and the network, if the build fetches. Install or configure what is
   missing, and say so. If something cannot be had, find out which part
   of the suite skips because of it.

3. **Read the dispatchers, not the libraries.** That means the prompt
   library's index, the log's index, and the newest entries of the
   current volume. Everything else waits until it is needed: a prompt
   when it fires, a log entry when a search finds it. Budget the turn
   like a check that outlives it. A change's cycle - build, test,
   measure, the suite, the log, the commit, the handover - has a cost in
   calls, and reading comes out of what is left.

4. **Reconcile the message, the attachments and the repository.** Each
   says where things stand. Where they disagree, the newest measured
   artifact wins, and the disagreement is written down. A figure found
   only in the message goes into the repository, with its source,
   before anything rests on it.

5. **Commit what arrived from elsewhere** (`11`). A report from another
   machine whose figures will be cited goes into the repository as it
   came, named by machine and time. A reminder in the message that the
   repository does not hold - a hazard, a rule, a habit - goes where the
   next session will look first. A reminder carried from one session's
   message to the next is a check nobody wrote (`15`).

6. **Treat environment facts as observations.** "X dies at turn end" and
   "Y is installed" were true where and when someone saw them. Test each
   once here, and record the result with where you saw it (`17`).

## Artifact required

- the baseline check's marker line, read back before the first change;
- one line per gap in the environment: what was missing, how it was
  found, what was done;
- the list of what the message held that the repository did not, and
  where each item went;
- each environmental reminder: tested here, and the result.
