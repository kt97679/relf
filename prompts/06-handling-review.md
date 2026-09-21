---
id: 06-handling-review
when: on receipt of feedback, before editing
applies-when:
  - review feedback has arrived, from any source
  - you are about to act on a criticism
skip-when:
  - (none)
produces: a per-finding disposition: accepted and how, or rejected and why, with any refutation shown
cost: low
---
# 06 — Handling review feedback

**Use it** when review feedback arrives, before changing anything.

**Why this exists.** Across seven rounds of feedback on this project, the
correct response varied more than expected: most points were right and
actionable, one was refuted by two lines of arithmetic, one was based on a
stale summary rather than the artifact, and one was a matter of judgement worth
declining and recording. Treating all feedback as automatically correct is as
damaging as treating it as automatically wrong — the difference is that the
first failure mode looks like humility.

The specific trap: I once rejected a valid criticism because it answered a
different question than the one I thought was asked, and accepted it two rounds
later when the same point returned. Recording dispositions with reasons is what
made that visible.

---

```
Review feedback has arrived. Before changing anything:

1. CHECK THE QUOTES EXIST. For each finding, confirm the quoted text is
   actually in the current artifact. Feedback given against a summary, an
   older version, or a paraphrase will attack things that are already fixed.
   If the quotes do not match, say so and fix whatever produced the stale
   version before responding to the content.

2. VERIFY BEFORE ACCEPTING. For every factual or numerical claim in the
   feedback, check it independently. Some criticisms are wrong. A criticism
   you cannot refute in two minutes is probably right; one you can refute
   with arithmetic should be refuted, in writing, with the arithmetic shown.

3. SEPARATE THE THREE KINDS.
   - Errors: something is false. Fix immediately.
   - Overclaims: true but stated too strongly. Rescope; do not delete.
   - Judgement: tone, title, ordering, emphasis. You may decline these, but
     record the reason, because "I declined it" and "I missed it" look the
     same to everyone later.

4. LOOK FOR THE ADJACENT DEFECT. A finding is often a symptom. Fixing the
   named sentence without asking what produced it leaves the cause in place.
   Twice in this project a complaint about a translation turned out to be a
   defect in the original that both languages shared.

5. PROPAGATE IN THE SAME COMMIT. A fix that lands in one document and not in
   the translation, the summary, the README or the reference doc creates a
   contradiction that someone will find and report as a new bug. Search for
   every other place the changed figure or claim appears.

6. RECORD THE DISPOSITION. For each finding: accepted and how, or rejected
   and why. This is the only artifact that distinguishes a considered
   decision from an oversight, and it is what lets you notice when you reject
   the same valid point twice.

7. RE-AUDIT AFTER THE EDIT. Automated edits fail silently. Re-run whatever
   consistency checks you have — figure parity, structure, cross-document
   agreement — and read the changed regions.
```

---

## Notes

**The disposition log is worth more than it looks.** It is how "the reviewer
was right and I had rejected this before" became visible, which was the most
useful single correction in the project.

**Watch for feedback that flatters.** A reviewer who confirms your result
deserves the same verification as one who attacks it. The confirming review is
the one you will not check.

---

## Deliverable

A per-finding disposition: accepted and how, or rejected and why, with any refutation shown.

Produce it as an artifact in the response — a table, a list, a count. Do not
narrate having considered these points. A reader must be able to check that the
step happened by looking at the output, not by trusting a summary of it.
