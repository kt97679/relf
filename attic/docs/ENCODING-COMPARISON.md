# Engine encoding comparison

> **Historical.** The Iteration 156-161 comparison of every encoding
> this project considered. The ladder that produced these numbers was
> retired at Iteration 218 - `attic/` has the sources - so the figures
> can be cited but no longer reproduced without reviving it. CV8 won.

Iteration 156. Written because the design work in this area was being
re-derived from scratch: a session proposed a two-tag-bit layout that
Iteration 132 had already measured, and only found out by grepping
`PROGRESS.md` afterwards. Everything below is regenerable —
`tools/encoding-census.py` produces every number in the table, and it
should be re-run rather than trusted, because these move whenever
`shell.4` does.

## The baseline being compared against

`freeze/iter156-encoding-baseline` tags the tree these numbers were
taken from. The committed sizes at that tag:

    size:i386     127684 bytes    (0.93x dash)
    size:x86_64   229160 bytes    (1.76x dash)

RelF's advantage over SOD32 as a comparison subject is that it builds
**both widths from one image**, so a scheme that saves cells can be
told apart from a scheme that saves bytes. SOD32 is 32-bit only, and
that distinction is invisible in it.

## Results

**Regenerated in Iteration 160.** The figures published in 156 were
wrong: the census read an inline counted string's length as a cell when
`(S")` uses `COUNT`, so the length is a byte. Every word containing an
inline string was truncated and the operation count was low by 21.5%
(14,909 against 18,121). Ratios barely moved and no conclusion changed,
but do not quote the 156 numbers.

Compiled word bodies only - not headers, not the engine. 1,059 words,
18,121 operations, 8,120 call sites, 2,329 literals. Macro inlining
(`M:`) is applied to every scheme, selected per scheme by
profitability.

| scheme | cells | i386 B | x86-64 B | vs today |
|---|---|---|---|---|
| RelF today (1 cell/op) | 21075 | 84300 | 168600 | 1.00x |
| SOD32 (5-bit x6, no BRANCH tag) | 18503 | 74012 | 148024 | 0.88x |
| SOD32 fields + inline literals | 15765 | 63060 | 126120 | 0.75x |
| tagged nibble (4-bit x7) | 15958 | 63832 | 127664 | 0.76x |
| tagged byte (8-bit x3/x7) | 15943 | 63772 | 127544 | 0.76x |
| tagged byte + hot-call (15) | 14994 | 59976 | 119952 | 0.71x |
| **uniform 16-bit token** | — | **43706** | **43706** | **0.52x / 0.26x** |
| token-threaded byte stream | — | 32528 | 32528 | 0.39x / 0.19x |

The last two do not scale with cell width, so they cost the same bytes
on both.

## Dispatch cost

Sizes alone cannot choose, and Iteration 134's objection was about
time: a tag plus a packed field adds a second data-dependent test to
the two hottest paths. `tools/pack-bench.c` and
`tools/varint-bench.c` measure it. Identical work, same operation
stream, **dynamic** operation mix rather than static - calls are 46.3%
of the image but 24.9% of execution, `EXIT` 3.6% against 17.3%.

| scheme | dispatch, x86-64 | dispatch, i386 |
|---|---|---|
| RelF today | 1.00 | 1.00 |
| SOD32 packed (5-bit) | 1.21 | 1.68 |
| tagged nibble | 1.65 | 2.05 |
| tagged byte | 1.60 | 1.90 |
| uniform 16-bit token | ~1.00 | — |
| variable-width byte stream | ~1.06 | — |

Varint tokens cost roughly **15% per additional byte**, because the
decode loop's exit is data-dependent: 0.98 / 1.16 / 1.31 at widths
2 / 3 / 4. That is why the scaled-offset variant, whose span is 15 bits
before any growth, sits at ~1.16x rather than the 1.03x a natural mix
suggests.

**Treat these dispatch numbers as weaker than the sizes.**
`varint-bench.c` and `dispatch-bench.c` disagree about their `cell`
baselines and the disagreement is unresolved. Three separate dispatch
results in this line of work turned out to be measuring something other
than dispatch, each time from a single configuration with no
cross-check - most sharply Iteration 157's "token threading costs
nothing", which was a 32MB working set on a 2MB L2 and became ~6% once
the stream size was varied.

## What the numbers say

**SOD32's twenty-year-old field layout beats the newer proposals.** Its
authentic encoding - one tag bit, a return bit, six 5-bit
subinstructions - plus inline small literals lands at 15,765 cells,
ahead of the tagged-nibble scheme and level with tagged bytes. `5 bits
x 6` is a better bit budget than `4 bits x 7`: 32 opcodes against 16,
for one slot the code does not use, because the mean run of packable
primitives is 1.34 and 75.5% of runs are a single operation.

**SOD32 also spends fewer tag classes.** It has no unconditional
branch, synthesising one as `push0` then `JUMPZ` - a subinstruction
rather than a whole tag class, which matters when unconditional
branches are 365 sites against `?BRANCH`'s 863. Under goal 3 that is
the more minimal design.

**But every packed scheme loses on time.** 1.21x to 1.65x on x86-64,
1.68x to 2.05x on i386, and the penalty holds at every working-set size
from 9KB to 18MB, so it is genuine decode cost rather than a cache
artifact. Buying 25-30% of size for 20-65% of dispatch is the wrong
trade for this project. **The packed direction is closed.**

**Only the byte and token streams break the cell-width coupling.**
Every cell scheme costs twice as much on x86-64 as on i386; the token
streams cost the same on both. That is the whole ballgame for this
project's actual size problem, which is on x86-64 (1.76x dash) and not
on i386 (0.93x dash). No amount of better packing closes a 4x gap.

**The uniform 16-bit token is the simplest thing that works.** One
aligned load, one compare against 256, one branch - fewer concepts than
the cell scheme it would replace, not more. It gives 0.52x on i386 and
0.26x on x86-64 at parity dispatch, against variable-width's 0.39x /
0.19x at ~1.06x. Iteration 160 translated real compiled bodies through
it and checked the two assumptions it rests on: the highest word number
any call uses is **1,044** against a 65,279 ceiling, and **zero** branch
offsets need more than 16 signed bits.

**The hot-call index is the weakest idea here** despite a good cell
count. Only 12.9% of call sites can fold - the rest sit next to another
call or a branch, where the pack is empty and nothing is saved. It
needs a two-pass build, a generated position-independent offset table,
and it can never include a runtime-defined word.

## Where the word table lives

An indexed scheme needs a table; RelF today needs none, because the
offset *is* the instruction. That table has a cost that grows with the
dictionary, and it is easy to miss. Sweeping word count at a fixed
stream size, an indexed byte scheme goes from 0.735 of cell time at
1,000 words (7KB table) to 0.824 at 65,000 (507KB) - **losing about
12% of its advantage once the table leaves L2**, with the knee between
8,000 and 65,000 words. That is exactly the range a bash-plus-busybox
system would occupy.

The fix is to put the table **outside the image**, where it is derived
data: rebuilt at startup by walking the dictionary link chain, so word
N is the Nth entry and compiler and loader agree for free; never
saved, so `SS-SCRUB` has nothing to clean and the image does not grow;
rebuilt after load, so it can hold absolute addresses and dispatch is
one load with no base add; and grown by `realloc` outside `mem[]`, so
it never collides with `HERE` and a runtime-defined word just appends.

That also answers the ceiling question. A 16-bit token holds 65,280
word numbers against 1,059 today and a plausible 25,000-30,000 at
busybox scale - roughly 2x headroom, with no prefix budget to ration.

## An unresolved finding worth more than any of the above

**37.9% of call sites are pushing a data address.** 3,076 sites across
458 distinct `VARIABLE`/`BUFFER:`/`CONSTANT` words, each paying a call,
a `DOVAR` dispatch and a return to deliver a compile-time constant.

The distribution is flat — the top 15 data words are only 14.9% of
calls, so no small table captures it — but the operation is
structurally uniform and its payload is an address rather than an
identity, so it does not need a table at all. Nothing in the schemes
above addresses it. It is the largest single unexploited regularity
found, and it has not been designed.

This also settles a question that was open: variable references *are*
compiled as calls, so the 452 data words consume call indices. Token
threading's `0x80-0x83` extended call reaches 1,024 targets against
1,082 dictionary entries today — already over budget, before any of the
bash-compatibility or busybox-applet work. A third call width (one
prefix byte plus two index bytes, 65,536 targets) costs one first-byte
value where widening by prefixes costs 256 targets per value.

## Static and dynamic frequency disagree, and both matter

Size depends on how often an operation appears in the image; dispatch
cost depends on how often it executes. Measured over three workloads
(arithmetic, tokenizing, variable expansion) with an instrumented
engine, the profiles are nearly identical to each other and quite
different from the static counts:

| | static | dynamic |
|---|---|---|
| calls | 46.3% | 24.9% |
| `EXIT` | 3.6% | **17.3%** |
| `R>` | 2.1% | 9.1% |
| `@` | 30.6% | 7.4% |
| `DROP` | 5.4% | 0.16% |

Two consequences. `EXIT` is the most-executed operation in the shell,
so the pack return-flag — which SOD32 has and which every scheme here
inherits — removes about one dispatch in six; that is a larger speed
argument than anything in the size table. And `R>` at 9.1% is
`locals.4`'s save/restore discipline, consistent with Iteration 137
having cost 42% of the loop benchmark.

An alphabet chosen on static frequency alone drops `LSHIFT` (rank 28
static, rank 13 dynamic) and keeps `DROP` (rank 6 static, rank 20
dynamic). Twelve opcodes are uncontested either way: `@ + R> ! DUP =
SWAP C@ < >R AND OVER`.

## What is not measured here

**Speed.** Every number above is size. These schemes trade decode work
for density in ways nothing here can see, and Iteration 134's objection
to two-bit tags — that they add a second data-dependent test to the two
hottest paths — is unanswered. Iteration 133 left the experiment
stated: build both and alternate `tests/bench`. That is now runnable at
about +/-4% resolution on a ratio, which it was not before Iteration
155.

**SOD32 as a system.** Modelling its instruction format on RelF's
program compares encodings, not implementations. Its own kernel is a
different program with a different opcode mix, and `README.md`'s
benchmark table measured a different engine on 20-year-old hardware.
`GOALS.md`'s "SOD32 27-51% slower" carries its own caveat: it was
measured against the old assembly engines, and the current C engine is
architecturally closer to SOD32 than to what was benchmarked.

**The token-threading row** uses assumed field widths and is the least
grounded line in the table; `attic/docs/TOKEN-THREADING.md`'s worked sample is the
better datum for that scheme.
