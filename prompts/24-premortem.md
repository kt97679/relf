---
id: 24-premortem
when: before building a plan that takes more than a day
applies-when:
  - you are about to start work that takes more than a day, or several sessions
  - the plan exists to prove a claim - a speed-up, a "first", a cost
  - the plan has no point where it can stop and still show something
skip-when:
  - the plan is one step whose failure is cheap and immediately visible
produces: an objections table per reviewer, a ceiling for every claimed gain, the revised plan with its stopping points and its boring-result line
cost: medium
---
# 24 — Pre-mortem: have the plan attacked before it is built

**Use it** before committing days to a plan, above all one meant to prove a
claim. `04-expert-review` attacks a finished write-up; this attacks the plan
while changing it is still cheap.

**Why this exists.** The Paleocomputing project (Habr, 2026) gave its first
plan to five reviewers, each with one domain - schedule, hardware, compiler,
measurement method, user interface - and one shared task: find why this will
not work. Before any code: the "free" opcode bit the plan relied on was one
the processor simply ignored, so every new instruction would have run as the
commonest existing one; the promised 2x speed-up was impossible by the
processor's own cycle table, since even a free instruction cannot remove more
than its share of the time (the real bottleneck was the multiplier, which a
week of measurement later confirmed); the "nobody has measured this" claim
met prior work going back to 1981; the schedule went from 2-4 weeks to 9-13;
and the plan had no intermediate point worth showing. The revised plan kept
two claims and a risk line saying the number would probably be boring - which
it was, and which was the result. This project's habit of pricing a mechanism
before building it (`10-price-before-refactor`) is the same idea applied one
mechanism at a time; this one applies it to a plan.

---

```
Before building this plan, run a pre-mortem and show it.

1. FOUR TO SIX REVIEWERS, ONE DOMAIN EACH. Name them by domain (schedule,
   the hardware or runtime, the toolchain, measurement method, the user's
   side, operations). Each gets the whole plan and one task: find why it
   will not work. Run them independently of each other and of whoever will
   build it; record every objection, even the ones you think are wrong.

2. A CEILING FOR EVERY CLAIMED GAIN. For each speed-up, saving or effect the
   plan promises, compute the most it could possibly be: the share of time,
   bytes or failures the change can touch, from a profile or a table, never
   from hope. A claim above its ceiling is withdrawn before work starts.

3. "FIRST" AND "NOBODY" ARE SEARCH RESULTS. A claim that something has not
   been done is stated as "not found in these sources", with the sources.
   Look before claiming; prior work changes the plan more often than it
   stops it.

4. STOPPING POINTS. Revise the plan so that it can stop at two or three
   points and still show something real. A plan whose only deliverable is
   at the end dies when time runs out.

5. THE BORING-RESULT LINE. Write down what the result will most likely be,
   in numbers, if it is unremarkable - and that this is a result. It keeps
   the work from bending towards the exciting answer.
```

## Artifact required

A table of objections (reviewer, objection, accepted or rejected and why), the
ceiling computed for each claimed gain, and the revised plan with its stopping
points and its boring-result line.
