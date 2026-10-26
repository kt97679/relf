---
id: 03-audit-tooling
when: before reporting any number
applies-when:
  - you are about to report measured numbers
  - a result agrees with what you already expected
  - two numbers from different routes came out equal or suspiciously round
  - a result is credited to an option, flag or feature that was switched on
  - a change moved a figure it cannot touch, or moved it the wrong way
  - an effect is small next to what layout, ordering or build noise could do
skip-when:
  - no figure in the output was produced by tooling you wrote
produces: a modelled-vs-measured table, a calibration against a known case, a direction-of-error statement per approximation
cost: low to medium
---
# 03 — Audit your own tooling before you believe it

**Use it** before reporting any measured result, and especially when a result
confirms what you already believed.

**Why this exists.** Three separate tooling failures in this project, each of
which produced a plausible wrong number rather than an error:

* A statistics parser read one submodule instead of the whole design, so every
  hierarchical measurement was counted from a fragment. It surfaced only
  because two independently computed quantities came out *exactly* equal, which
  is not a coincidence one should accept.
* A cost model priced items at an average where the marginal cost was what
  mattered, and the error ran in the direction of whichever design I was
  currently favouring.
* A code generator charged one family of candidates for a resource they never
  used, a handicap applied only to the candidates that threatened my existing
  answer.

The pattern is that the errors were not random. Each flattered the answer I
held at the time, in both directions across the project — once making a search
look right when it was wrong, once making it look wrong when it was right.

---

```
Before reporting these numbers, run this audit and show the results.

1. MODELLED VERSUS MEASURED. Go through every figure you are about to
   report and mark it modelled or measured. Never place the two in the same
   table, sentence or comparison without labelling. If you must compare
   them, first validate the model against at least two measured points and
   report the error.

2. CALIBRATE ON SOMETHING KNOWN. Run the tool on a case whose answer you
   already know independently. If you have no such case, construct one —
   a trivial input, a hand-computed example, a previously published result.
   A tool that has never reproduced a known answer has not been tested.
   For a tool that compares two things, the known case is a thing against
   itself: identical inputs must come out equal, and their scatter is the
   noise floor every real difference is read against.

3. DIRECTION-OF-ERROR CHECK. For each approximation in your pipeline, ask
   which candidate it favours. If every approximation happens to favour the
   result you expected, treat that as a finding about your pipeline rather
   than about the world.

4. AUDIT THE CONFIRMING RESULT HARDER. You will scrutinise a result that
   contradicts you. Deliberately spend equal effort on the one that agrees
   with you, because that is the one that will ship unexamined. And audit
   a disappointing result as hard as a pleasing one: a comparison that
   finds the model wrong, or the code broken, can itself be the broken
   part (the Paleocomputing project, Habr 2026, nearly published a model
   "16% off" that was a check sampling one cycle early, and nearly
   "fixed" floating-point code that a faulty check had flagged).

5. IMPLAUSIBLE AGREEMENT IS A BUG SIGNAL. If two quantities computed by
   different routes agree exactly, or a ratio comes out suspiciously round,
   find out why before celebrating. Exact agreement between independent
   computations usually means they were not independent. The converse is
   a check you can build: where two routes MUST agree, make them. Count
   one quantity two ways and assert equality - the mismatch is a bug in
   one of them.

6. VERIFY EDITS BY READING, NOT BY EXIT CODE. A search-and-replace that
   matches nothing reports success. A keyword count can be satisfied by
   unrelated occurrences. After any automated edit, read the changed region.

7. DECOMPOSE BEFORE DIAGNOSING. When two results differ, attribute the
   difference to specific components before explaining it. A difference
   blamed on the wrong component produces a confident, wrong story — and a
   story is much harder to retract than a number.

8. ABSENCE OF OUTPUT IS A MEASUREMENT TOO. Before concluding from what
   did NOT appear - no error message, no trace line, nothing printed
   before a crash - show that the path from the program to your eyes
   could have carried it. Output buffered in a process that then
   crashes is lost; a filter you wrote to hide noise hides whatever
   shares a line with the noise; a build step that deletes its own
   inputs makes a manual rerun fail for a different reason.

9. A SWITCH IS NOT A FEATURE. For every option a result is credited to,
   count its footprint in what was actually built or run - sites, bytes,
   executions. Zero means it was not there, and every comparison that
   included it measured its absence. A tool that prints a warning and
   carries on has made that decision for you: count its warnings, or
   make them fatal.

10. NULL REWRITES. Repeating the same input measures run-to-run noise, not
   the noise of the pipeline itself. Before crediting a small effect, also
   rebuild with changes that cannot matter - an expression rewritten, a
   declaration moved, a no-op added - and measure their spread. An effect
   inside it is reported as a bound ("under 1%"), not a value, and picking
   whichever build shows it best is choosing an answer, not measuring one.
   (Paleocomputing: four meaning-preserving rewrites of the processor moved
   the synthesised area as much as the feature did. This project: the same
   430 bytes of code removed from two engines shrank one file by 4,296
   bytes and the other by 72 - the page layout, not the change.)
```

---

## Notes

**Step 5 caught the worst bug in this project.** Nothing else would have; the
numbers were individually plausible and all the tests passed.

**Step 8 came from a shell project's native compiler**, three times in a
week: a crash whose message was in a C engine's output buffer when it died
(the same run on an unbuffered engine printed it); a trace whose lines a
`grep -v` meant for warnings removed, because the trace printed on the
warnings' lines; and a reproduction that failed because the make target
that made its input file deleted it when done. Each time the first reading
was "it dies before it gets that far".

**Step 7 is the newest of the original entries.** I diagnosed a 463-gate difference as expensive
marginal storage, wrote it up, and only later decomposed it properly to find it
was two wasted words of a different kind of storage. The wrong diagnosis had
already been published in three documents.

**Step 9, the converse in step 5 and the A/A case in step 2 came from a
second project** (forth-vm-evolution, an evolutionary search over
interpreter designs; Iteration 13). A converter gave a word its opcode
only after checking the word's body, and features added later rewrote
the bodies it checked: it printed "no exact body match" and carried on.
1,032 of 1,145 living designs had silently lost at least one opcode -
every design on the front four - and every comparison since those
features arrived had measured their absence. It surfaced while pricing
something else: an opcode with zero sites in the image, beside seven
calls to the word it stood for. The same session asserted that a
profiler's per-address and per-pair counts of one quantity agree; they
differed by 8% - two kinds of event counted as dispatches, in a tool
trusted for five rounds of work. And a fix that could only remove work
raised a benchmark's count by 14%: decomposed by kind (step 7), every
extra event was alignment padding, because the image had shrunk by a
number of bytes that was 3 mod 8.

---

## Deliverable

A modelled-vs-measured table, a calibration against a known case, a direction-of-error statement per approximation.

Produce it as an artifact in the response — a table, a list, a count. Do not
narrate having considered these points. A reader must be able to check that the
step happened by looking at the output, not by trusting a summary of it.
