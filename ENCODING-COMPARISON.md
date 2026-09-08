# Engine encoding comparison

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

Compiled word bodies only — not headers, not the engine. 1,060 words,
14,909 operations, 6,596 call sites, 1,842 literals. Macro inlining
(`M:`) is applied to every scheme, selected per scheme by
profitability.

| scheme | cells | i386 B | x86-64 B | vs today |
|---|---|---|---|---|
| RelF today (1 cell/op) | 16862 | 67448 | 134896 | 1.00x |
| SOD32 (5-bit x6, no BRANCH tag) | 14639 | 58556 | 117112 | 0.87x |
| **SOD32 fields + inline literals** | **12338** | **49352** | **98704** | **0.73x** |
| tagged nibble (4-bit x7) | 12692 | 50768 | 101536 | 0.75x |
| tagged byte (8-bit x3/x7) | 12573 | 50292 | 100584 | 0.75x |
| tagged byte + hot-call (15) | 11759 | 47036 | 94072 | 0.70x |
| token-threaded byte stream | — | 25639 | 25639 | 0.38x / **0.19x** |

## What the numbers say

**SOD32's twenty-year-old field layout beats the newer proposals.**
Its authentic encoding — one tag bit, a return bit, six 5-bit
subinstructions — plus a single addition (inline small literals) lands
at 12,338 cells, ahead of the tagged-nibble scheme at 12,692 and level
with tagged bytes at 12,573. `5 bits x 6` is simply a better bit budget
than `4 bits x 7`: 32 opcodes against 16, for the cost of one slot that
the code does not use anyway, because the mean run of packable
primitives is 1.34 and 75.5% of runs are a single operation.

**SOD32 also spends fewer tag classes.** It has no unconditional
branch. `BRANCH` is synthesised as `push0` followed by `JUMPZ` — a
subinstruction instead of a whole tag class, which matters because
unconditional branches are only 365 sites against `?BRANCH`'s 863.
Under goal 3 that is the more minimal design, and it frees a tag class
for something that earns it.

**Only token threading breaks the cell-width coupling.** Every cell
scheme costs twice as much on x86-64 as on i386, because a cell is
twice as wide; the byte stream costs the same on both. That is the
whole ballgame for this project's actual size problem, which is on
x86-64 (1.76x dash) and not on i386 (0.93x dash). No amount of
better packing closes a 4x gap.

**The hot-call index is the weakest idea here** despite showing the
best cell count. It folds a call into spare tag bits, but only 12.9% of
call sites can use it — the rest sit next to another call or a branch,
where the pack is empty and nothing is saved. It needs a two-pass
build, a generated position-independent offset table, and it can never
include a runtime-defined word. That is a lot of machinery, against
goal 3, for a few percent.

## An unresolved finding worth more than any of the above

**45.7% of call sites are pushing a data address.** 2,557 sites across
432 distinct `VARIABLE`/`BUFFER:`/`CONSTANT` words, each paying a call,
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
1,060 dictionary entries today — already over budget, before any of the
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
grounded line in the table; `TOKEN-THREADING.md`'s worked sample is the
better datum for that scheme.
