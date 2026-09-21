# 09 — a baseline you update without looking is not a check

**Fires when** an acceptance run reports a recorded value has changed
and you are about to re-record it.

**Skip when** nothing is recorded — but then ask why not.

## Why this exists

A project recorded about fifty numbers per run — suite counts, byte
sizes, a dead-code count, whether two builds reproduce — and compared
them against a committed baseline. It worked for four hundred
iterations.

Then a change replaced two words and left five variables behind. The run
reported `dead-words 5` where it had said `0` since the file was
written. The baseline was updated in the same breath as the fix, the 5
became the new normal, and the regression shipped. It was found a week
later by someone on another machine, where it appeared in a report as
`ok dead-words 5` — correct against the baseline, and wrong.

The check had been converted into a record of whatever happened last.

## Do this

1. **Every changed line gets a sentence before it is recorded.** Not
   "intended"; *why* it moved, naming the change that moved it. If you
   cannot write the sentence, you do not yet know whether it is a
   regression.

2. **A count that has been constant for a long time deserves more than
   a sentence.** Zero becoming non-zero is the shape of a regression,
   whatever the metric says.

3. **Separate what depends on the code from what depends on the
   machine.** A byte size is the compiler's; a "cases the references
   disagreed on" count is the installed references'; a timing is the
   load's. Compare the first strictly and report the second without
   counting it — and record what produced it, so the comparison can tell
   which it is looking at.

4. **A known open bug is neither.** Give it its own verdict — `known`,
   with a pointer to where it is written down — so it stays visible
   without failing a run. The same difference reported as a failure
   every time trains people to skim.

5. **Update and verify are two commands.** Record, then run the plain
   check and see it pass, then commit both together. A baseline updated
   from a run you did not read is a diff you approved without reading.

## Artifact required

For each changed line: the value, the previous value, one sentence of
cause, and a verdict — regression, intended, or machine-dependent. Then
the output of the plain run showing it passes, and both committed in one
commit whose message lists the changed lines.
