# 12 — the log is how you avoid doing it again

**Fires when** you are about to try an approach - an optimisation, a
fix, a redesign, a tool - and whenever an attempt ends, whether it
worked, failed, or was reverted.

**Skip when** the work is a single answer with nothing to try.

## Why this exists

A long project is worked on by many sessions, each starting with no
memory of the others. Without a record of what was TRIED, each session
re-derives the same ideas from the same profile and pays for them
again. The project this came from kept an append-only `PROGRESS.md`,
one entry per iteration, and it earned its keep mostly through the
entries that said "no":

- A variable-lookup cache was built, measured (4.9% fewer dispatches,
  0.75% less time), and reverted. The profile that suggested it never
  changes - variable lookup is always near the top - so without the
  entry, every later session would see the same line and build the
  same cache.
- A refactor of per-word bookkeeping was priced at 1% before a line was
  written, and cancelled. The entry says how it was priced, so the
  price can be checked rather than re-measured.
- A command-tree design replaced argument counting in `test` with a
  grammar (Iteration 317) and lost POSIX's counted rules; a hundred
  iterations later the rules came back (422). Because the log said WHY
  the grammar came in - long `-a`/`-o` chains - the fix kept both
  instead of undoing 317.

And the log can mislead as easily as help. One entry recorded that a
build difference was "sixteen extra zero bytes after TIB"; it was a
false match, and the next session would have chased it for an
afternoon. It was corrected FORWARD - a later entry says what was wrong
and why - rather than silently edited, so a reader of either entry ends
up with the truth.

## Do this

1. **Before trying an approach, search the log for it.** Not only its
   name: the symptom that suggested it, the words you would use for it,
   the file it would touch. `grep -n -i 'cache\|memoi' PROGRESS.md`
   costs a second; rebuilding a rejected cache costs a day. If it was
   tried, read why it stopped, and go ahead only with evidence the
   earlier attempt did not have.

2. **Keep a short register of rejected approaches** where the next
   session will look first - the top of the standing goals file, not
   the middle of a 1 MB log. One line each: what, the number that
   decided it, the iteration where the evidence is. The log holds the
   story; the register is the index into it.

3. **Record the attempts that fail**, with the evidence, in the same
   entry as the ones that work. "Built, measured, reverted: X for Y" is
   the most valuable sentence a log can contain, because it is the one
   nobody would otherwise know.

4. **Say why a design choice was made, next to the code and in the
   log.** A later session that must change it can then keep what the
   choice was protecting instead of reintroducing the problem it fixed.

5. **Correct wrong entries forward.** Append the correction with the
   iteration that found it, and point back. An edited history cannot
   be trusted; a corrected one can.

6. **Keep the log append-only and the goals file current.** The log is
   the past and grows; the goals file is the present and should shrink
   as things are done - stale "where things stand" snapshots belong in
   the log or an archive, not in the file people read to decide what
   to do next.

## Artifact required

Before starting: the search you ran and what it found (or "no prior
attempt"). After finishing: the log entry, with any failed or reverted
attempt stated as such and its deciding number; and, if the approach
was rejected, its one-line entry in the register.
