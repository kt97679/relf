---
id: 04-expert-review
when: after the claims settle, before publication
applies-when:
  - a technical write-up is nearly finished
  - you are about to publish claims backed by evidence
skip-when:
  - the claims are still changing
  - the artifact is not yet self-consistent
produces: a verdict, three worst problems with quotes and fixes, smaller issues in document order, an arithmetic check
cost: one review round per pass; returns diminish sharply after about three
---
# 04 — Expert review: attack the claims

**Use it** when a technical write-up is nearly finished and you want its claims
broken before a reader breaks them.

**Why this exists.** Five rounds of this on the project's article found three
real errors: a statement that was flatly contradicted by a table printed
directly above it, a rule stated unconditionally that only held in one of two
regimes, and a "controlled comparison" that quietly bundled three changed
variables. None of those would have survived a reader; all of them survived me.

One round was wasted because the prompt's own summary of the claims had gone
stale, and the reviewer spent three findings attacking wording that had been
fixed two commits earlier. Hence the instruction below that the artifact
governs.

---

```
You are reviewing [ARTIFACT] for publication. Act as a skeptical reviewer in
[FIELD] — the kind who would catch an overclaim in a conference submission.
Find what is wrong, weak, or unsupported. Do not open with praise, do not pad,
and do not rewrite it.

AUDIENCE AND VENUE
[who will read this, what they know, how long it should be]

METHOD AND MODELLING CHOICES
[State how the numbers were produced, and every modelling choice a hostile
reader could attack, including the ones that make the result possible. List
the known caveats. A reviewer who has to discover your assumptions will spend
the review discovering them instead of testing them.]

THE LOAD-BEARING CLAIMS
[List them. These are a paraphrase for convenience: where a paraphrase and the
artifact disagree, THE ARTIFACT GOVERNS — quote the artifact, not this list.
Regenerate this list whenever the artifact changes materially.]

For each claim: does the stated evidence support it? Is it stated more strongly
than the evidence allows? Would a hostile expert have an obvious counterexample
or an "it depends on X" that goes unaddressed? Is any claim true only because
of a modelling choice a reader would not notice?

ALSO REVIEW
- Structure: does it earn its conclusion or assert it? Anything essential
  missing, anything present that could be cut?
- Clarity: mark any sentence that would stop a competent reader; flag jargon
  introduced without definition.
- Tone: flag anything smug, hedged into meaninglessness, or promotional.

OUT OF SCOPE
Do not propose new experiments. Do not change the numbers — if one looks
wrong, say so rather than correcting it. Do not reformat into another genre.

OUTPUT
1. Verdict in two or three sentences.
2. The three most serious problems, worst first: quote the exact text, say
   what is wrong, give a concrete fix.
3. Smaller issues in document order, as quote + problem + fix.
4. Anything factually wrong or internally inconsistent, including arithmetic
   that does not check out.
5. One paragraph on what it does well — last, and only if true.

If it is genuinely sound, say so plainly rather than inventing problems.
```

---

## Notes

**Keep the claims list derived, not remembered.** It drifts. Either regenerate
it from the artifact each time, or update it in the same commit as any material
change, and keep the line telling the reviewer the artifact governs.

**Give the reviewer your modelling choices up front.** The best round of review
this project got came from a reviewer who had the whole repository and checked
the numbers against the source rather than taking them on trust.

**Diminishing returns are real.** By round five the findings had moved from
errors to matters of degree, and the round's headline item turned out to be
arithmetically wrong. Stop when the caveats start outgrowing the findings.

---

## Deliverable

A verdict, three worst problems with quotes and fixes, smaller issues in document order, an arithmetic check.

Produce it as an artifact in the response — a table, a list, a count. Do not
narrate having considered these points. A reader must be able to check that the
step happened by looking at the output, not by trusting a summary of it.
