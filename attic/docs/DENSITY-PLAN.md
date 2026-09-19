# attic/docs/DENSITY-PLAN.md — making the image smaller without paying for it

> **Historical.** Written before the encoding work began. Most of it
> was done by CV8 and byte-granular headers; see `CV8.md` and
> PROGRESS.md 211-213. Read it for the reasoning about where image
> bytes go.

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

## The encoding: one test, as now — payload above the index

Iterations 132 and 133 worked through 2-bit tags. Both add a **second
data-dependent test** to the two hottest paths, which is a real cost
against a dispatch loop whose whole virtue is that it has one test.
Iteration 134 avoids it entirely.

The observation: the primitive index field is almost empty. There are
68 primitives and room for billions. So put the payload **above** the
index rather than beside the tag, and let the existing dispatch table
do all the work:

    bits [31..12]  payload (signed)      -524,288 .. 524,287
    bits [11..2]   primitive index       1024 slots
    bits [1..0]    01 = primitive, 00 = call

Three reserved indices carry a payload; every other primitive leaves
it zero:

    LIT      payload = the literal value
    BRANCH   payload = byte offset
    0BRANCH  payload = byte offset

### The dispatch loop

```c
#define IDX_BITS   10                  /* 1024 primitive slots      */
#define PAY_SHIFT  (2 + IDX_BITS)
#define IDX_MASK   ((1u << IDX_BITS) - 1)
#define TOK_PAY(t) ((INT64)(t) >> PAY_SHIFT)   /* arithmetic: signed */

#define NEXT() do { \
        t = CELL(ip); ip += CELL_BYTES; \
        if (t & 1) goto *dispatch[(t >> 2) & IDX_MASK]; \
        RPUSH(ip); ip += t; \
        goto next; \
    } while (0)
```

Against today's

```c
        if (t & 1) goto *dispatch[(t - 1) >> CELL_SHIFT];
```

**one test, one indirect branch, exactly as now.** The difference is
`(t >> 2) & IDX_MASK` in place of `(t - 1) >> CELL_SHIFT` — an `and`
where there was a `sub`, both single-cycle, neither a branch. The
handlers:

```c
L_lit:     PUSH((UNS64)TOK_PAY(t)); NEXT();
L_branch:  ip += TOK_PAY(t); NEXT();
L_0branch: if (DS0) { dsp += CELL_BYTES; }
           else     { dsp += CELL_BYTES; ip += TOK_PAY(t); }
           NEXT();
```

Each is *shorter* than the version it replaces, because the operand
comes from a register instead of a second memory read:

```c
L_lit:     PUSH(CELL(ip)); ip += CELL_BYTES; NEXT();     /* was */
L_branch:  ip += CELL(ip); NEXT();
```

### Why this beats both tag schemes

All three operand-carriers fold into one cell, not just the ones a tag
could reach:

| | cells saved |
|---|---|
| `LIT` -> immediate | 2,178 |
| `0BRANCH` -> folded | 863 |
| `BRANCH` -> folded | 365 |
| superinstructions, K=128, on the resulting stream | 2,161 |
| **total** | **5,567** |

**22,268 bytes on i386, 44,536 on x86-64** — against 17,796 for the
four-tag scheme and 21,488 for the `0BRANCH`-tagged variant, and with
a simpler dispatch loop than either. It also retires the constant
block: a 20-bit immediate covers every literal, so there is no range
to tune.

### Ranges, verified rather than asserted

`IDX_BITS = 10` gives a 20-bit signed payload, **-524,288 .. 524,287**,
against measured maxima of 127,404 for a literal and 2,216 for a
branch offset — two orders of magnitude of headroom on the branch and
four times on the literal. 1,024 primitive slots against 68 today plus
whatever superinstructions are chosen (K=128 would reach 196).

`IDX_BITS` is the one tuning knob: raising it buys primitive slots and
costs payload reach, one bit for one bit. `LIT` remains available as a
two-cell primitive for any literal too wide, so **nothing becomes
unrepresentable** — the compiler picks the short form when it fits.

Encode and decode round-trip, checked including negatives and sign
extension, for every primitive index and for literals at both ends of
the range (`/tmp` scratch test, reproduced in `tools/` if this is
built).

### What it costs

`CALL` is untouched. The `and` replaces a `sub`. The three folded
handlers each lose a memory read. There is no case in this scheme
where the interpreter does more work than it does today — which is
the whole test this document applies, and the first option to pass it
outright rather than on balance.

## The constant block — superseded

Iteration 132 scanned every contiguous range to find the best block of
"push this constant" primitives, landing on `-1..96` for 1,091 cells
net of table cost. **The encoding above retires it**: a 20-bit
immediate covers all 2,178 literal sites for 2,178 cells and no table
at all. Kept as a record of why the question stopped mattering, not as
a plan.

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

## Order, and the interaction

**The encoding first, then re-run the fusion search, then pick K.**
They are not additive and the interaction is large: folding a branch
removes any gain from fusing a pattern that ends in one, and turning
literals into single tokens changes which pairs are adjacent at all.
Measured on the final stream, K=128 fusion is 2,161 cells; the top
pairs become `PUSHK =` (234), `PUSHK EXIT` (172), `@ <` (157),
`! PUSHK` (150), `@ +` (150).

Had these been done in the other order, the second would have looked
like a failure — the fusion figure on today's stream is 2,927, and
nearly all of the difference is patterns the encoding claims first.

### What it comes to

| | cells | i386 | x86-64 |
|---|---|---|---|
| encoding (LIT + BRANCH + 0BRANCH folded) | 3,406 | 13,624 | 27,248 |
| superinstructions, K=128 | 2,161 | 8,644 | 17,288 |
| **total** | **5,567** | **22,268** | **44,536** |

Less whatever the superinstruction bodies add to the engine, which
remains the one figure here that is a guess.

i386 image 134,500 -> about 112,232; total 152,308 -> about **130,040
against `dash`'s 129,784**. Level, near enough, and without giving up
`FIND`.

## Method, non-negotiable

Per Iteration 129: `tests/sizes` before and after, and `tests/bench`
**three runs alternating** on the same machine, because single runs on
this hardware differ by more than these changes will. Both cell
widths, per the standing convention. `tools/dict-report.4` and
`tools/dict-dump.4` exist to check emitted cells *before* running an
engine built against them — the failure mode being guarded against is
a stale token number, which does not produce an error, it produces a
segfault somewhere unrelated.
