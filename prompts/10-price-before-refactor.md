# 10 — price the thing before you refactor it

**Fires when** a profile, a hunch or a code smell is about to justify
restructuring something that currently works.

**Skip when** the change is required for correctness, or the
restructuring is small enough that measuring costs more than doing it.

## Why this exists

A profiler said two words were 10.3% of a program's dispatches. The
obvious conclusion was a refactor across forty-five call sites.

The first attempt to measure the prize was invalid: the bookkeeping was
stripped out to see what the program would cost without it, which made
the program take a different path entirely. It reported a 7% saving that
did not exist.

The second attempt added work instead of removing it — do each thing
twice, behaviour unchanged, and halve the difference. The honest answer
was **1%**. The refactor was cancelled.

Earlier in the same project a cache was built, measured, and reverted:
4.9% fewer dispatches, 0.75% less time. It removed cheap operations and
added an expensive one. The count had been treated as a proxy for time
without checking what kind of work it counted.

## Do this

1. **Measure the prize before paying for it.** The question is not "is
   this hot" but "what would perfect handling of this be worth".

2. **To price something you cannot remove without changing behaviour,
   do it TWICE.** The second copy costs what the first one costs, and
   behaviour is identical, so nothing else moves.

3. **Removing code to measure it is a different program.** If the
   removal changes which branches run, which cache lines are touched, or
   which fast path applies, the number is about that other program.

4. **A proxy metric is a proxy.** Dispatch counts, allocation counts,
   line counts and instruction counts all diverge from time exactly
   where the work per unit differs. Convert the proxy to the real
   quantity at least once, on the change you are about to make.

5. **Report the negative result as a result.** "Built, measured,
   reverted, here is the number" is worth more than silence: it stops
   the next person re-deriving the same disappointment.

## Artifact required

Before the refactor: the measured value of the prize, the method used to
measure it, and one sentence on why that method does not change the
program. After: the achieved value beside the predicted one. If they
differ by more than a factor of two, say what the proxy was counting
that the clock was not.
