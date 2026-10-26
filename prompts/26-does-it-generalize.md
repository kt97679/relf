---
id: 26-does-it-generalize
when: before calling the winners of a long optimization or search better - anything selected on fixed benchmarks, on one machine
applies-when:
  - a search, tuner or evolution has picked designs by their scores on a fixed set of workloads
  - every measurement that drove the selection came from one machine
  - the benchmarks are small programs, or the winners are about to be adopted, shipped or written up
skip-when:
  - the workloads are the product's real ones and the machine is the one it ships on
produces: per round, the held-out rank correlation and the designs the selection flatters; per other machine, the rank correlation of the same binaries; the winners' speed as the program grows - or the named reason each is missing
cost: low per round once built; medium to build
---
# 18 — A search finds what its benchmarks reward, on the machine it ran on

**Use it** before trusting what a long optimization found, and every round of
one that keeps running.

**Why this exists.** A genetic search evolved Forth virtual machines for fifty
runs, scoring each design's speed on six small workloads on one laptop, and kept
improving - so the question became whether "better" meant better or meant
better *there*.

* Held-out workloads, never used to select, answered part of it: across three
  runs the selection's ranking and a held-out workload's agreed with rank
  correlation 0.94, and the fastest designs kept their places - but a steady group
  of designs was 2.5 to 2.7 times better on the selection than on the held-out
  one. The selection flattered them: half its workloads were the outer
  interpreter, and designs rich in parsing and lookup operations looked faster
  than they were anywhere else.
* The hardware counters answered another: on the compute workloads the
  instruction cache and the op cache missed under 0.2 times a thousand
  instructions - the whole hot path fitted, and the branch predictors saw few
  contexts. No selected workload pressed the machine as a program of thousands
  of words would.
* And every speed that drove the selection came from one CPU. A first look on a
  second x86 - the same binaries - found the smallest designs keeping their ratio
  to the reference and the JIT designs keeping half their advantage.
* The first held-out computation, written inline, read the column "re-measured"
  - the selection's own speed measured again - and reported a correlation of
  0.999. A number that perfect between two noisy measurements meant the thing
  had been compared with itself.

---

```
Before calling the search's winners better, show what holds outside it.

1. HOLD OUT WORKLOADS, AND LOOK EVERY ROUND. Keep workloads the selection
   never sees. After each round, the rank correlation of the front between
   the selection's scores and the held-out ones, where the selection's best
   rank there, and the designs it flatters most (held-out over selection).
   A falling correlation, or a best design falling down the held-out
   ranking, is the alarm - not a footnote.

2. HOLD OUT A MACHINE. Measure the winners on another microarchitecture, and
   on another instruction set if the work ships there. Compare rankings, not
   absolute numbers: the question is whether the order holds.

3. SHIP THE SAME BINARIES where the instruction set allows. Rebuilt on the
   other machine, a design gets another compiler and other flags, and a moved
   ranking can no longer be told from a changed build. Check first that they
   travel: no -march or -mtune, static or ABI-safe linking.

4. A DESIGN IS ITSELF ONLY IF IT IS THE SAME THERE. What the other host lacks -
   a compiler, a JIT for its instruction set, a word width - silently turns a
   design into another one. Compare what each design expresses there with what
   it expressed here; rank only the ones that are themselves, and name the
   rest.

5. GROW THE PROGRAM. Small benchmarks fit every cache and predictor. Measure
   the winners as the code footprint grows - generated programs of N units,
   run hot and run once - and see whose speed falls off first.

6. KEEP THE CHECKS CHEAP AND OUT OF THE WAY. Run them on the slower machines
   in parallel with the next round of the search, on the round that just
   finished, under a hard time limit, keeping whatever is finished. A host
   that fails is named, never a reason to stop the search.

7. DISTRUST A PERFECT NUMBER. Agreement near 1.0 between two noisy
   measurements means one of them is the other. Read columns by their
   header's name (prompts/19); put the computation in a tracked tool.
```

## Artifact required

A table, one row a round: the held-out rank correlation, where the selection's
best designs rank on the held-out workloads, and the most flattered designs.
For each other machine: the designs measured, how many were themselves there,
and the rank correlation with the same binaries' scores here. And the winners'
speed against program size - or, for each of these, one line naming why it is
missing and when it will exist.
