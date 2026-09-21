---
id: 02-escape-recall
when: before naming any candidate
applies-when:
  - the task asks for the best/optimal/minimal/fastest X
  - you are about to list candidate approaches, architectures or algorithms
  - any answer would name well-known existing systems
skip-when:
  - the user has fixed the candidate set and does not want it questioned
  - the task is to explain or implement one named approach
produces: an axis table with completeness counts, >=3 deliberately unconventional candidates, a uniform random sample, a list of what stayed fixed
cost: high (mechanical enumeration produces mostly unusable candidates; budget a cheap feasibility filter)
---
# 02 — Escape recall: search the space, don't recite it

**Use it** whenever a task is "find the best X", "what is the optimal Y", or
"compare approaches to Z", and you intend to take the answer seriously.

**Why this exists.** In this project I compared SUBLEQ, an accumulator machine,
a PDP-8-alike and Jones's MOVE machine, and reported which won. A reader
pointed out that those are the branches that historically existed, so a model
with the history of computer architecture in its weights was not searching but
recalling. He was right. When I built a mechanical search instead, it found a
better design built on reverse subtract, with no add, no subtract and no
unconditional jump — a machine resembling nothing in the historical record.

Two further things surfaced that are likely to recur. First, my "mechanically
enumerated" pool was not: I claimed it contained a branch for every way of
testing the sign of a result, and it contained six of the seven — the missing
one being the condition used by the very architecture the project was about.
Second, the primitives that made the winning design work were the two I had
added *deliberately because no real machine used them*. Without those two, the
search would have confirmed my original answer and I would have believed it.

---

```
Before you propose candidates for this problem, stop and do the following.
Show your work for each step; do not skip to the answer.

1. NAME THE RECALL. Write the table before writing anything else:

      | candidate you were about to propose | is it a named existing system? | named after/where |

   If every row says yes, you are recalling, not searching. Steps 2-7 are
   then mandatory, not optional. Do not skip this table on the grounds that
   the answer is obvious; writing it is what makes the next steps happen.

2. ENUMERATE THE SPACE MECHANICALLY. Do not list solutions. Identify the
   independent axes the solution space actually has, and generate candidates
   as combinations of points on those axes. Write the axes down explicitly.

3. AUDIT THE ENUMERATION FOR COMPLETENESS. Produce this table:

      | axis | possible values | values I included | missing |

   Compute the counts; do not estimate them. If any row has a non-empty
   "missing" column, either include those values or justify each one in
   writing. Unusual, asymmetric values and ones no familiar system uses are
   the ones a recall-driven enumeration drops, and they are exactly where the
   result changed in the project this prompt came from.

4. ADD DELIBERATE STRANGERS. Include at least three candidates chosen
   specifically because no well-known system uses them, and say for each why
   it was excluded from practice: is it genuinely worse, or merely
   unfashionable, historically contingent, or bad for constraints that no
   longer apply? Keep the ones where you cannot answer.

5. SAMPLE BEFORE YOU OPTIMISE. Draw a uniform random sample of the space and
   evaluate it *before* any local or greedy search. Report the distribution —
   count, range, and where the known-good candidates fall within it — not just
   the best. Local search from a hand-picked start inherits that start's bias;
   the sample is what tells you whether your optimum is a peak or a plateau,
   and whether the space has structure you did not put there.

6. STATE WHAT IS STILL FIXED. Everything you did not vary is an assumption:
   the framework, the representation, the interfaces, the metric. List them.
   For each, say what would change if it were varied. This list is the honest
   scope of your result, and it belongs in the write-up, not in your head.

7. REPORT THE FAILED CANDIDATES. Say which mechanically generated candidates
   could not work and why. A search that only reports its winner is
   indistinguishable from a recommendation.
```

---

## Notes

**The cheapest useful version.** If the full treatment is too expensive, step 4
alone is worth running. Adding candidates chosen *because* nobody uses them
costs one paragraph and is what produced the result here.

**Watch for "mechanically enumerated" as a claim.** It is easy to write and
hard to verify. Step 3 exists because I made exactly that claim and it was
false, and the omission was not random — it was the option that did not fit the
pattern I had in mind.

**Sampling is not optimisation.** Step 5's uniform sample will usually be worse
than local search. That is fine. Its purpose is to characterise the space and
to catch the case where local search is stuck in the neighbourhood of the
answer you started with.

**This prompt is not free.** Mechanical enumeration produces many unusable
candidates — in this project about 98.5% of uniformly drawn ones — so you need
a cheap feasibility filter before the expensive evaluation. Budget for that.

---

## Deliverable

An axis table with completeness counts, >=3 deliberately unconventional candidates, a uniform random sample, a list of what stayed fixed.

Produce it as an artifact in the response — a table, a list, a count. Do not
narrate having considered these points. A reader must be able to check that the
step happened by looking at the output, not by trusting a summary of it.
