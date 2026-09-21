---
id: 05-reader-review
when: after 04, before publication
applies-when:
  - a technical write-up has passed a correctness review
  - the audience includes anyone who has not done the work
skip-when:
  - the claims have not settled yet -- restructuring a moving argument wastes both passes
produces: the first three places a reader stopped, a one-sentence statement of the investigation, a structure verdict, a repetition list, a comparison-set challenge
cost: low; run it on a human if at all possible
---
# 05 — Reader review: can anyone actually follow this?

**Use it** after a technical write-up has survived a correctness review, and
before you publish it.

**Why this exists.** Five rounds of expert review on this project's article
found three real errors and improved the claims considerably. Not one of them
mentioned that the article had no chapter structure, no statement of what was
being investigated, and repeated the same gate counts six times over. A
non-expert reader said all three in four lines, and also made the single
sharpest observation anyone made about the work itself — that the alternatives
compared were just the famous ones.

Expert reviewers read for whether you are *right*. They will not tell you that
nobody can follow you, because they already know the material and are not
experiencing the difficulty. These are different jobs and they need different
prompts.

---

```
You are reading this as an intelligent non-specialist: you know the general
field but not this specific work, and you have not seen it before. Read it
once, at normal speed, and then answer. Do not check the arithmetic — someone
else is doing that. Your job is whether this is followable, proportionate and
honestly framed.

1. WHERE DID YOU STOP? Name the first place you had to re-read a sentence,
   the first place you lost the thread, and the first place you were tempted
   to stop reading. Quote each. These are the only three quotes I need.

2. WHAT IS THIS INVESTIGATING? Answer in one sentence, from the text alone.
   If you cannot, say so — that means there is no problem statement, and it
   needs one: the question, the method, what counts as an answer.

3. STRUCTURE. Can you navigate it? Could you find a specific claim again
   without re-reading from the start? If it needs chapters or subheadings,
   say where they go.

4. REPETITION. List anything stated more than once — figures, claims,
   phrasings. For each, say which occurrence is load-bearing and which are
   noise. Authors repeat numbers to be helpful and it reads as padding.

5. PROPORTION. Which section is longer than its importance, and which is
   shorter? Is there a caveat that has grown to the size of a finding?

6. THE COMPARISON SET. Look at the alternatives, options or baselines being
   compared. Are they the obvious, famous ones? If so, say it — and name
   something stranger that is missing. This question catches more than it
   should, because writers compare the things that come to mind, and what
   comes to mind is what is famous.

7. WHAT IS UNEXPLAINED? List every term, symbol or assumption introduced
   without definition. Include the ones you guessed correctly; guessing is a
   cost.

8. WOULD YOU FORWARD IT? To whom, and what would you say about it in one
   line? If you would not, say why not.

Be blunt. Do not soften, do not compliment before criticising, and do not
propose rewrites — describe the problem and where it is, and let the author
fix it.
```

---

## Notes

**Run this on a human if you possibly can.** The value here came from an actual
reader with actual impatience. A model asked to simulate a non-specialist will
simulate one that is more patient and better informed than any real reader.

**Question 6 is the one to keep if you keep only one.** It is a readability
question that turns out to be a methodology question, which is why a reader
asking it casually can land harder than a specialist reviewing carefully.

**Expect the fixes to be structural, not verbal.** In this project the response
was six numbered chapters, a methods section, collecting five scattered caveats
into one subsection, and cutting repeated figures — after which the article was
the same length with a new section added, so the existing text had genuinely
tightened.

**Do not run this before the claims are settled.** Restructuring an argument
that is still changing wastes both passes.

---

## Deliverable

The first three places a reader stopped, a one-sentence statement of the investigation, a structure verdict, a repetition list, a comparison-set challenge.

Produce it as an artifact in the response — a table, a list, a count. Do not
narrate having considered these points. A reader must be able to check that the
step happened by looking at the output, not by trusting a summary of it.
