# CV8-LEDGER.md - what each change to CV8 gained, and what it cost

Since Iteration 679, at the user's asking: CV8 - the bytecode engine and
its two engines, C and assembly, and the shell they run - takes back what
the native back end learned, item by item, and each item is entered here
with its gain and its cost, so the whole is visible: what we are getting,
and what it costs us. The native shell is the baseline: CV8's distance
from relf's fastest is the last row of every measurement.

## How a row is measured

`tools/cv8-ledger.py BASE` builds BASE in a scratch worktree and measures
the checkout against it on this VM, interleaved: the asm engine's shell
and the C engine's on tools/bench-vm.py's five workloads (SCALE=5; a
ratio under 1 is faster), each engine on bench/langs/bench.4's seven
kernels (best of 3 a round, alternated; their geometric mean), the
engines', shells' and images' bytes, and the asm engine's shell as times
the native shell. A fury pack confirms a batch, as for the native back
end (prompts/19): VM ratios choose, fury's report claims.

**The noise floor (679):** the unchanged tree against itself, 5 rounds -
the asm shell 0.997-1.046, the C shell 0.939-1.075, bench.4 0.97-1.06. A
difference under 5 % on the shell, or 4 % on bench.4, is not a gain at 5
rounds; rows that claim less use more rounds.

## The baseline (Iteration 678)

CV8 as it stands, against the native shell. Fury at 676 (times dash):

| | loop | fn | str | arith | realistic |
|---|---:|---:|---:|---:|---:|
| asm engine's shell | 27.8 | 34.6 | 30.0 | 35.1 | 41.6 |
| C engine's shell | 28.7 | 35.4 | 30.5 | 37.3 | 41.9 |
| native shell | 2.88 | 3.50 | 2.89 | 3.67 | 3.83 |
| asm shell, times native | 9.7 | 9.9 | 10.4 | 9.6 | 10.9 |

On the VM (679's run): the asm shell 13.7, 11.9, 11.8, 12.3, 12.0 times
native. bench.4 on fury: native 0.13 of the asm engine's time, 0.13 of
the C engine's. Bytes: relfasm64 15,856, relf64 45,360, relfshasm64
141,844, relfsh64 171,348, kernel64.img 9,840, kernel64-shell.img 125,972.

## The items (from 678's reply, in order)

1. The asm engine's string primitives - CSTRLEN, SCAN, MOVE, COMPARE,
   FILL - without the microcoded rep and repne instructions for short
   strings, as native-rt.4's since 644, 647 and 652. The asm engine only:
   the C engine calls the C library's.
2. `(S")` as an engine instruction: a string literal in one dispatch,
   where the colon word took a call, five instructions and a return.
3. Grouped saves and restores of locals: one instruction a run, where
   each local took one.
4. Inlining small colon words (OPTIMIZATIONS.md S6).

## Entries

(one per item, newest last: what was built, the ledger's block, the cost
in bytes and source, and fury's figures when a pack has them)

### 679, item 1: the asm engine's string primitives - built, measured, reverted

Built: native-rt.4's MOVE (a byte loop under 16), COMPARE (eight bytes at
a time, then a byte loop), SCAN (a byte loop) and CSTRLEN (one load where
the first eight bytes lie in one page, else aligned eight at a time)
ported into relfasm64.4's handlers - native's rbx and rbp are the asm
engine's r12 and r13 - in place of repne scasb, rep movsb and repe cmpsb.
FILL was native's already. The engines' outputs the same on
tests/native/kernel-str.4 and the other string tests.

| shell, SCALE=5, 7 rounds | loop | fn | str | arith | realistic |
|---|---:|---:|---:|---:|---:|
| asm engine, against 678 | 1.020 | 1.015 | 1.029 | 1.006 | 1.058 |
| C engine, unchanged: the noise | 1.025 | 0.989 | 0.907 | 1.028 | 0.962 |

bench.4: the asm engine's geomean 1.001. Cost: relfasm64 +216 bytes.

**Got nothing; reverted.** Natively the same routines were 6-14 % of the
profile because everything around them had become fast; in CV8 a dozen
dispatches surround each call, and the microcoded instructions' slow
start is lost among them. The lesson for the items after it: the native
back end's profile prices native code, not CV8 - each item is priced on
CV8 itself, by doing its work twice, before it is built.
