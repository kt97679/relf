# 20 — the noise floor before the verdict

**Fires when** you are about to call one build faster or slower than
another: an A/B of two binaries, two configurations, two commits.

**Skip when** the difference is many times any spread ever seen between
builds of one program, or the claim is about correctness, not speed.

## Why this exists

In a shell project with a native compiler, a change that made literal
pushes shorter - fewer bytes, the same work - came out 1 to 4 % slower
on one workload in every A/B, three runs of three, and was held back.
Then the project measured what nobody had: the same program, with only
the code ahead of it padded by 0 to 3,120 bytes, ran anywhere from 0.979
to 1.023 of itself. Where a hot loop fell against the processor's 16-,
32- and 64-byte lines moved the time as much as the change had. Averaged
over four layouts the held-back change was inside that floor, and was
kept. Later the same effect, uncontrolled: a microbenchmark's loop went
from 7 ms to 15 when an unrelated part of the program shrank and moved
the loop across a line. Nothing in the loop had changed.

A hardware project met it in chip area: rewriting a processor's
description in ways that change no logic - brackets, an OR with zero -
moved the synthesised area by as much as the new instruction it was
measuring added.

Repeated runs of one build agree closely and say nothing about this. The
noise lives between builds, not between runs.

## Do this

1. **Measure A against A first.** The same program built twice so that
   only its layout differs - padding where nothing runs - through the
   same harness. Their spread is the floor. Record it, and how it was
   made.

2. **Vary what the change moves, not only what it changes.** A code
   change moves every address after it. Build each side at several
   layouts - padding ahead of the code at a few offsets, the phases of a
   cache line - and compare each side's geometric mean over its
   layouts.

3. **Judge against the floor.** Inside it, the change is neither slower
   nor faster: say "inside the floor", give the floor, and decide on
   other grounds - size, simplicity. Outside it, it is a result, with the
   floor beside it.

4. **Settle in advance what "inside" decides.** In the shell project the
   user ruled that inside the floor counts as not slower; without a
   ruling, every borderline result is argued afresh.

5. **Re-judge what was held back once the floor is known.** A verdict
   reached before the floor was measured was a verdict on layout.

## Artifact required

The A/A spread and how it was produced; each side's figures per layout
and their means; the ratio with the floor beside it; the verdict in
those terms.
