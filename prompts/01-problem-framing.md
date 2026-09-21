---
id: 01-problem-framing
when: before the first measurement
applies-when:
  - the task is a measurement, comparison, benchmark or optimisation
  - you are about to start producing numbers
  - the user asks which of several things is best/cheapest/fastest
skip-when:
  - the quantity to optimise and the cost model are already fixed and stated
  - the task is implementation of an already-specified design
produces: a written question, cost model, degeneracy check, budget decomposition and falsification criterion
cost: low (one turn)
---
# 01 — Problem framing: find the dominant term, check for degeneracy

**Use it** at the start of any project whose output is a measured comparison or
an optimisation.

**Why this exists.** Two framing errors in this project cost a phase each. The
first: I spent a whole round comparing processor designs before measuring that
the processor was 3% of the machine and an output array — an artefact of how I
had written the benchmark — was 71%. The second: the benchmark admitted a
degenerate answer. Asked for the cheapest machine to run one fixed program, the
true optimum is a hardwired state machine with no instruction set at all, which
is correct, useless, and took a phase to notice.

---

```
Before measuring anything, answer these in writing.

1. THE QUESTION. State it in one sentence, with the quantity to be minimised
   or compared named explicitly and its units given.

2. THE COST MODEL. What exactly is being counted, and what is excluded?
   Name every component of the total, including the ones you expect to be
   small. If any figure will be modelled rather than measured, mark it now
   and decide how you will validate it against something measured.

3. THE DEGENERACY CHECK. What is the stupidest thing that optimises this
   metric perfectly? A lookup table, a hardwired special case, a constant, a
   cached answer, doing nothing. If that thing wins, your metric or your
   benchmark is wrong and no amount of careful measurement will fix it.
   Either change the task so the degenerate answer is excluded on its
   merits, or add the constraint that rules it out and say you added it.

4. THE BUDGET DECOMPOSITION. Before optimising, measure the split. Which
   term dominates? Optimising a 3% term to perfection buys 3%. If the
   dominant term is an artefact of how you set the problem up, fix the setup
   first — that is a different and much larger win than anything the
   comparison will produce.

5. WHAT WOULD CHANGE THE ANSWER? Name the two or three modelling choices the
   result is most sensitive to. State, now, what you expect each to be worth.
   You will be wrong about some of them, and the record of what you expected
   is more useful than the expectation.

6. THE SUCCESS CRITERION. What result would make you abandon the hypothesis?
   If no outcome would, you are not running an experiment.
```

---

## Notes

**Step 3 is the one people skip.** It feels like a formality until the
degenerate answer actually wins, which in this project it did, comprehensively.

**Step 4 changes what you work on, not just how you report it.** Once memory
turned out to be 97% of the machine, the interesting question stopped being
"which instruction set" and became "which kind of memory can the program live
in" — which was the project's actual finding, and it was invisible until the
budget was decomposed.

---

## Deliverable

A written question, cost model, degeneracy check, budget decomposition and falsification criterion.

Produce it as an artifact in the response — a table, a list, a count. Do not
narrate having considered these points. A reader must be able to check that the
step happened by looking at the output, not by trusting a summary of it.
