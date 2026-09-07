# DENSITY-PLAN.md — making the image smaller without paying for it

Written before any code, because the options differ in risk by an
order of magnitude. Read `GOALS.md`'s phase 5 (which already rejected
one density scheme) and `PROGRESS.md`'s Iterations 129-131 first.

**Revised in Iteration 131.** The first version's superinstruction
figures were wrong: the decoder treated only `LIT` as consuming an
inline operand cell, when `BRANCH` and `?BRANCH` do too, and
`S" ..."` compiles to a call to `(S")` followed by an inline counted
string that is not tokens at all. Everything downstream of a branch or
a string was mis-tokenized. The numbers below come from a decoder that
handles all four and accounts for 19,518 of the 19,506 body cells.

Two options in the first version are **withdrawn**, not deferred:
headerless words (extending the shell in Forth requires `FIND`, which
is a real requirement rather than a nice-to-have) and immediate
literals in a tagged cell — see Option A for why the usual objection
to tagging is wrong and the conclusion right anyway.

## What the compiled code is made of

19,518 cells in 354 colon words:

| | cells |
|---|---|
| call offsets | 6,986 |
| operand-carrying tokens and their operands (`LIT`, `BRANCH`, `?BRANCH`) | 6,812 |
| plain primitive tokens | 5,445 |
| unclassified (`DOES>` / `CONSTANT` bodies) | 275 |

**2,178 `LIT` sites**, 251 distinct values, with a very sharp head:
`0` appears 513 times, `-1` 187, `1` 105, `2` 71.

## The principle

> **A density scheme is safe when it removes work, and unsafe when it
> adds a decoding step.**

SOD32 packed several opcodes per cell and paid shift/mask/counter work
on every instruction; RelF beat it anyway. `GOALS.md` rejected
byte-granular opcodes here for the mirror-image reason — that scheme
adds a marker byte and realignment to `CALL`, the one instruction with
zero overhead in the current format. Both options below make the
interpreter do strictly *less* work per unit of program.

---

## The encoding: two tag bits, four classes

Proposed in Iteration 132 and adopted here. The low two bits of a code
cell select the class, and every payload is either cell-aligned (so
its low two bits are free) or a small index:

    t & 3 == 0   CALL     ip += t                  (unchanged, free)
    t & 3 == 1   PRIMITIVE  goto *dispatch[t >> 2]
    t & 3 == 2   BRANCH     ip += (t & ~3)
    t & 3 == 3   0BRANCH    if (TOS) ip += CELL else ip += (t & ~3)

**What this buys over today: the branch offset moves into the branch
cell.** `BRANCH` and `?BRANCH` are ordinary primitives today, each
followed by an offset cell; folding them saves one cell per site.
Measured: **1,228 branch sites, 4,912 bytes on i386, 9,824 on
x86-64.** Offsets are all 4-aligned as required, and the largest in
the image is 2,216 against a 30-bit payload reaching ±536,870,912.

**`CALL` stays free**, which is why two bits is the right width rather
than three or four. Payloads could be shifted to free more tag bits,
but a shift on `CALL` — the single most common class, 6,986 cells —
is exactly the "adds a decoding step" mistake this document is built
to avoid.

A side benefit: primitive tokens become `idx * 4 + 1` on every host
rather than `idx * sizeof(void*) + 1`. That decouples the token stride
from pointer width, which `GOALS.md` currently flags as a hazard —
`cross.4`'s hand-embedded token numbers have to change whenever the
stride does.

## Where `LIT` goes, given the tag space is full

All four tags are spent, so `LIT` cannot have one. Three options,
measured:

**1. Leave `LIT` a primitive with a following value cell, and shrink
its frequency with a constant block inside the primitive index space.
Recommended.** The primitive payload is 30 bits and real primitives
need seven, so indices above the last real primitive are free. Give a
contiguous run of them to "push this constant", with **every entry in
the dispatch table pointing at one shared label** so no test is added
to any path:

```c
/* PUSHK_BASE .. PUSHK_BASE+N all point at this one label */
L_pushk: PUSH((UNS64)(INT64)((t >> 2) - PUSHK_ZERO)); NEXT();
```

The block's width is a real optimisation, because each entry costs
`CELL` bytes of table and buys `CELL` bytes per site it covers. Net
cells saved is `sites(range) - width(range)`, and scanning every
contiguous range gives the optimum:

| range | tokens | sites | gross i386 | table | **net** |
|---|---|---|---|---|---|
| `0..15` | 16 | 758 (34.8%) | 3,032 | 64 | 2,968 |
| `-1..63` | 65 | 1,140 (52.3%) | 4,560 | 260 | 4,300 |
| **`-1..96`** | **98** | **1,189 (54.6%)** | **4,756** | **392** | **4,364** |
| `-16..255` | 272 | 1,219 (56.0%) | 4,876 | 1,088 | 3,788 |
| `-128..1023` | 1,152 | 1,228 (56.4%) | 4,912 | 4,608 | 304 |

`-1..96` is the measured optimum, and the curve is flat between about
`-1..48` and `-1..128` — anything in that band is within a few hundred
bytes, so pick a round number and move on. The head of the
distribution is what matters: `0`, `-1`, `1` and `2` alone are 40.2%
of all literal sites.

**2. Widen the block past the table with a bounds test.** Anything
beyond the table range needs `if (idx >= PUSHK_BASE)` in the primitive
path. That reaches every literal but puts a test on the hot path to
serve values in the tail, which is precisely the trade option 1
avoids. Not recommended.

**3. Give `LIT` a tag by merging the two branch classes.** `BRANCH`
and `0BRANCH` share tag `10`, distinguished by a bit taken from the
payload — which means the offset must be shifted, so branches pay a
shift on decode. In exchange tag `11` becomes a full 30-bit immediate
covering **every** literal: 2,178 cells, **8,712 bytes on i386**,
against option 1's 4,364 net.

That is a genuine +4,348 bytes on i386 for one shift on the branch
path. Worth having measured; **not recommended anyway**, because
branches are hot in exactly the loops `tests/bench` is 236x `dash` on,
and this document's whole principle is that density must not add
decoding work. Revisit only if the loop benchmark stops being the
constraint.

## Option A — the constant block (details)

**Saves 4,560 bytes on i386 (9,120 on x86-64) for 260 bytes of
dispatch table. Strictly faster: no memory fetch at all.**

Not one primitive per constant hand-picked from this image — that
overfits a token stream which changes every time `shell.4` does.
Instead **one contiguous block of dispatch-table entries, all pointing
at a single label that derives the value from the token index**:

```c
/* PUSHK_BASE .. PUSHK_BASE+64 all point at this one label */
L_pushk:
    PUSH((UNS64)(INT64)(((t - 1) >> CELL_SHIFT) - PUSHK_ZERO));
    NEXT();
```

This is **not cell tagging.** The token is an ordinary primitive token
in the existing `n * CELL + 1` scheme, the discriminator is unchanged,
and no test is added to any path. `LIT` stays exactly as it is for
every value outside the range, so nothing becomes unrepresentable and
the compiler picks the shorter encoding only when it fits.

**Range `-1 .. 63` is the sweet spot**, measured:

| range | tokens | sites covered | saves (i386) | table cost |
|---|---|---|---|---|
| `0..15` | 16 | 758 (34.8%) | 3,032 | 64 |
| `-1..63` | 65 | **1,140 (52.3%)** | **4,560** | **260** |
| `-16..255` | 272 | 1,219 (56.0%) | 4,876 | 1,088 |
| `-128..1023` | 1,152 | 1,228 (56.4%) | 4,912 | 4,608 |

Past `-1..63` it stops paying: `-16..255` buys 316 more bytes of image
for 828 more bytes of table, a **net loss**. The head of the
distribution is so sharp that four values (`0`, `-1`, `1`, `2`)
already account for 40.2% of all literal sites.

*(For the record: hand-picking the top 128 individual values would
cover 84%, because values like `44264` recur 51 times. Rejected —
those are this image's buffer offsets, they change whenever `shell.4`
does, and a constant table tuned to them is a benchmark-specific hack
rather than a compiler improvement.)*

### Why the tagged-cell alternative was dropped, precisely

The usual objection — that a tag limits the literal values that can be
stored — **is not actually true**, and it is worth saying so rather
than accepting a correct conclusion for a wrong reason. `LIT` would
remain in the engine, so the compiler emits an immediate only when the
value fits and falls back otherwise; nothing becomes unrepresentable,
and the payload would have been 30 bits on i386 against a largest
literal in this image of about 127,000.

The real reasons to prefer Option A are two, and they are enough:

1. **Tagging adds a test to the hot path.** It needs a second
   discrimination (`t & 2`) on *every* primitive dispatch in order to
   serve the 24% that are literals. Option A adds nothing — it is a
   table entry.
2. **Tagging changes what `cross.4` emits for literals**, which is the
   code holding the hand-embedded dispatch token numbers `GOALS.md`
   warns about, where a stale value segfaults the *next* engine at
   whatever primitive lands on it. Option A changes literal emission
   too, but additively: a new token range appended at the end, `LIT`
   untouched as the fallback, so a bug shows up as "this literal used
   the long form" rather than as a corrupted engine.

Option A gets 52% of the literal sites for none of that. The tagged
scheme's extra 48% is not worth either cost.

---

## Option B — superinstructions

**Pairs, applied iteratively to a fixed point. Longer n-grams are not
worth searching for explicitly — they fall out for free.**

That is the measured result and it was not obvious going in. Greedy
selection, with patterns cut at branch targets so no fusion can hide a
jump destination:

| max pattern length | K=16 | K=32 | K=64 | K=128 |
|---|---|---|---|---|
| 2 (pairs only) | 1,855 | 2,336 | 2,656 | 2,927 |
| 3 | 1,879 | 2,345 | 2,687 | 2,951 |
| 4 | 1,879 | 2,349 | 2,689 | 2,951 |
| 6 | 1,879 | 2,362 | 2,700 | **2,965** |

*(cells saved; x4 for i386 bytes, x8 for x86-64)*

**Searching up to length 6 beats pairs-only by 1.3%.** The reason is
that iterated pair fusion *composes*: once `LIT = ?BRANCH` exists as a
fused token, `DUP` + that + `DROP` is a pair again and fuses in a
later round. The greedy run's own output shows exactly this —
`DUP <LIT+=+?BRANCH> DROP`, 59 sites, discovered as a pair of pairs.

So the implementation only ever needs to recognise **two adjacent
tokens**, run to a fixed point. Triples and quads arrive with no
n-gram machinery at all, which is a large simplification for 1.3%.

Best individual fusions at K=32:

| saves | sites | pattern |
|---|---|---|
| 266 | 133 | `LIT = ?BRANCH` |
| 228 | 114 | `@ < ?BRANCH` |
| 172 | 172 | `LIT EXIT` |
| 158 | 158 | `@ LIT` |
| 150 | 150 | `! LIT` |
| 150 | 150 | `@ +` |
| 145 | 145 | `! BRANCH` |
| 118 | 59 | `DUP <LIT+=+?BRANCH> DROP` |

### Two things the implementation must get right

**Never fuse across a branch target.** A fused token is atomic; a jump
into what used to be its second half would land inside an instruction.
The analysis above already cuts at targets, which is why its numbers
are achievable rather than optimistic. `BRANCH`/`?BRANCH` offsets are
relative and must be recomputed after any fusion shortens the code
between the branch and its target — that recomputation is the fiddly
part and the reason this is Option B rather than A.

**Fused tokens that end in an operand-carrier keep the operand.**
`LIT = ?BRANCH` fuses three tokens into one but still needs the
literal value and the branch offset in following cells: five cells
become three, saving two, which is what the table counts.

### The counterweight, to be measured and not assumed

Every superinstruction is a dispatch-table entry **and a body in the
engine**. The table is `K * CELL` bytes; the bodies are concatenated
operations, plausibly 30-80 bytes of machine code each. At K=128 that
is roughly 4-10KB of engine growth against 11,708 bytes of image saved
on i386 — still positive, but the margin narrows fast and the estimate
is a guess. **Measure the engine with `tests/sizes` at each K**, not
only the image.

**Size and speed diverge here.** More superinstructions always removes
more dispatches, so speed keeps improving with K, while net size peaks
somewhere and then declines. If the two disagree, `GOALS.md` goal 3
says minimalism wins — but record both and make it a decision rather
than a default.

---

## Order, and the interaction — the schemes are NOT additive

**Folding branches removes most of what superinstructions had to
offer.** Measured, greedy pair fusion to a fixed point:

| stream | K=16 | K=32 | K=64 | K=128 |
|---|---|---|---|---|
| today | 1,855 | 2,336 | 2,656 | 2,927 |
| branches folded (branch patterns excluded) | 1,499 | 1,774 | 1,996 | 2,161 |
| branches folded + constant block | 1,381 | 1,691 | 1,927 | **2,116** |

*(cells saved)*

Once a branch carries its own offset, fusing `X BRANCH` gains
**nothing**: `X` + `BRANCH|off` is two cells, and `<X+BRANCH>` + `off`
is also two. Seven of the ten best fusions in the original table ended
in a branch, which is why K=128 falls from 2,927 to 2,161. The
constant block overlaps a little further, taking it to 2,116.

So the fusion search must **exclude any pattern containing a branch**,
and be re-run after the constant block lands, because `LIT 0 =`
becomes `PUSHK0 =` and changes which pairs are common. The top
fusions on the final stream are `PUSHK =` (204), `@ <` (157),
`PUSHK EXIT` (154), `@ +` (150), `! PUSHK` (121), `@ PUSHK` (109).

### What it comes to

| | cells | i386 | x86-64 |
|---|---|---|---|
| branch folding | 1,228 | 4,912 | 9,824 |
| constant block `-1..96` (net of table) | 1,091 | 4,364 | 8,728 |
| superinstructions, K=128 | 2,116 | 8,464 | 16,928 |
| **total** | **4,435** | **17,740** | **35,480** |

Less whatever the superinstruction bodies add to the engine, which is
the one figure here that is a guess rather than a measurement.

i386 image 134,500 -> about 116,760; total 152,308 -> about **134,568
against `dash`'s 129,784**. Close, and short — the 16,400 bytes of
dictionary headers that would have closed it are what `FIND` costs,
and that was decided.

**Do them in this order**: encoding first (it is the largest single
piece, needs no new primitives, and changes the stream everything else
measures against), then the constant block, then re-run
`tools/superinstr-search.py` and pick K against measured engine
growth.

## Method, non-negotiable

Per Iteration 129: `tests/sizes` before and after, and `tests/bench`
**three runs alternating** on the same machine, because single runs on
this hardware differ by more than these changes will. Both cell
widths, per the standing convention. `tools/dict-report.4` and
`tools/dict-dump.4` exist to check emitted cells *before* running an
engine built against them — the failure mode being guarded against is
a stale token number, which does not produce an error, it produces a
segfault somewhere unrelated.
