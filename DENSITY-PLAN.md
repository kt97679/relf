# DENSITY-PLAN.md — making the image smaller without paying for it

Written after Iteration 130's measurement of what is actually in a
compiled image, and before any code, because the options differ in
risk by an order of magnitude and picking wrong is expensive. Read
`GOALS.md`'s phase 5 (which already rejected one density scheme) and
`PROGRESS.md`'s Iteration 129 first.

## The measurement this rests on

The i386 shell image's compiled colon-word code is **19,506 cells =
78,024 bytes**, in 354 words. Every cell classified:

| | cells | share |
|---|---|---|
| primitive tokens | 9,122 | 46.8% |
| literal operands (the cell after a `LIT`) | 2,178 | 11.2% |
| call offsets | 8,206 | 42.1% |

`LIT` is the most frequent primitive in the image by a wide margin —
2,178 sites, 23.9% of all primitive tokens — and **each one costs two
cells**, so literals alone are 4,356 cells, 22.3% of all compiled
code. 513 of them push the value 0.

## The principle that separates a good option from SOD32's

RelF beat SOD32 despite SOD32's packed opcodes, and the reason
generalizes into a rule for this document:

> **A density scheme is safe when it removes work, and unsafe when it
> adds a decoding step.**

SOD32 packed several opcodes per cell and paid for it on every
instruction with shift/mask/counter work in the dispatch loop. That is
why it lost despite fetching less memory, and it is why `GOALS.md`
rejected byte-granular opcodes here too — that scheme adds a marker
byte and realignment to `CALL`, which is the instruction with *zero*
overhead in the current format.

The three options below are the ones that go with the grain: each
makes the interpreter do **less** work per unit of program, not more.
Options 4 and 5 are recorded because they are large, not because they
are recommended.

---

## Option 1 — immediate literals in the token

**Saves 2,178 cells: 8,712 bytes on i386 (6.5% of the image), 17,424
on x86-64. Predicted to be slightly *faster*.**

The token space is almost entirely unused. Primitive tokens are
`n * CELL + 1` for `n` in 0..67, so with `CELL >= 4` every one of them
is `1 mod 4`; call offsets are cell-aligned, so they are `0 mod 4`.
**The value `3 mod 4` is free**, and gives a clean three-way split at
no cost in the discriminator:

    t & 3 == 0   ->  call offset      (unchanged)
    t & 3 == 1   ->  primitive token  (unchanged)
    t & 3 == 3   ->  immediate literal, value = (signed)t >> 2

Dispatch becomes:

```c
t = CELL(ip); ip += CELL_BYTES;
if (t & 1) {
    if (t & 2) { PUSH((INT64)t >> 2); goto next; }   /* immediate */
    goto *dispatch[(t - 1) >> CELL_SHIFT];
}
RPUSH(ip); ip += t;
```

Why this should be *faster* rather than merely smaller: today `LIT`
costs a dispatch, a second memory fetch, and an `ip` increment. An
immediate costs a shift of a value already in a register — **no memory
access at all**. The price is one extra test on the primitive path,
taken 23.9% of the time and thoroughly predictable.

**Range.** 30 bits signed on i386, 62 on x86-64. The largest literal
in the current image is ~106,000, so every one fits with four orders
of magnitude to spare. `LIT` stays in the engine for anything that
does not, so the compiler can fall back rather than fail.

**Risk: moderate, and concentrated in one known place.** `cross.4`
hand-embeds the primitive-dispatch token numbers for `LIT`, `EXIT`,
`BRANCH`, `0BRANCH` and `R>` — `GOALS.md` warns that getting these
wrong segfaults the *next* engine at whatever primitive lands on the
stale value. This changes how literals are emitted, so it is exactly
that code. Do it with the dictionary-report tool to hand and check the
emitted cells before running anything.

---

## Option 2 — superinstructions for the common pairs

**Saves ~1,588 cells: 6,352 bytes on i386 (4.7%). Predicted faster —
each fused pair removes one dispatch.**

Measured, counting only adjacent pairs where *neither* token carries
an operand (so they can be fused into one token):

| count | pair |
|---|---|
| 163 | `! BRANCH` |
| 157 | `@ <` |
| 150 | `@ +` |
| 140 | `= ?BRANCH` |
| 137 | `< ?BRANCH` |
| 74 | `@ C@` |
| 71 | `+ C@` |
| 66 | `! EXIT` |

1,857 fusable adjacencies in total; the top 32 pairs account for 1,588
of them.

This is gforth's own technique and it is additive: each
superinstruction is one more label and one more dispatch-table entry
at the **end** of both `relf.c` and `kernel.4`'s `PRIMITIVE` list,
which is the only safe place and the same discipline Iterations 120
and 125 already followed. Nothing existing changes meaning.

The compiler side is a peephole pass in `cross.4`: after emitting,
scan for a known pair and replace two cells with one. Branch targets
must be recomputed, which is the fiddly part and the reason this is
option 2 rather than option 1.

**With option 1 landed, more pairs become fusable**: `LIT <n> =` (234
sites) and `LIT <n> EXIT` (182) are the two biggest, currently
unfusable only because `LIT` carries an operand cell.

---

## Option 3 — headerless words

**Saves up to 16,400 bytes (12.3% of the image) at *exactly* zero
runtime cost.**

Dictionary headers — a link cell plus a counted name, per word — are
1,069 entries and 16,400 bytes. They are read **only** by `FIND`, at
compile time and from the interpreter. Nothing in a running shell
touches them. This is the one option where the performance question
does not arise at all.

`cross.4` already carries the alternative, commented out:
`: "HEADER CREATE ALIGN-T ;` "in case the target system is just an
application without headers".

**The cost is real but bounded.** `FIND` stops working for a
headerless word, which breaks the `forth` builtin and interactive use
for those names. It need not be all-or-nothing: keep headers for the
few words that must stay findable and drop them for the ~800 internal
ones. A per-file or per-word marker is the design question, and it is
a smaller one than either option above.

This is `GOALS.md`'s own lever 1, now with a number against it.

---

## Options recorded but not recommended

**Option 4 — a 32-bit code stream on 64-bit hosts.** Code is 156,048
of the x86-64 image's 251,104 bytes (62%), so halving the token width
would take ~31% off that image — by far the largest single lever, and
the direct fix for the 8-byte build being 1.85x the 4-byte one.
Tokens and call offsets both fit in 32 bits comfortably (±2GB of
reach). But it breaks the property `GOALS.md` calls load-bearing —
that a cell is dereferenced directly as a real host pointer — for the
code stream specifically, and complicates `,`, `HERE`, `ALIGN` and
every `@`/`!` into a definition body. That is a large change to the
system's identity for a build that is not the small one anyway. If
64-bit size ever becomes the goal rather than 32-bit size, this is the
option; otherwise it is against goal 3.

**Option 5 — variable-length call offsets.** 74.7% of call offsets fit
in 16 bits and 20.5% in 8, so a near/far encoding could reclaim
several thousand cells. It drags in assembler relaxation — iterating
to a fixed point because shortening one call moves every later target
— which `GOALS.md` already named as real complexity against goal 3
when rejecting byte-granular opcodes. Same verdict, same reason.

---

## Recommended order, and what it adds up to

1. **Option 3 (headerless)** first. Largest saving, zero performance
   risk, and entirely independent of the other two — nothing about it
   constrains what comes later.
2. **Option 1 (immediate literals)** second. Second largest, likely a
   small speed *gain*, and it enlarges option 2's opportunity.
3. **Option 2 (superinstructions)** last, sized against what option 1
   leaves.

All three, on i386: **8,712 + 6,352 + 16,400 = 31,464 bytes**, taking
the image from 134,500 to roughly 103,000 and the total from 152,308
to about **121,000 — below `dash`'s 129,784**, with the speed
prediction pointing the right way rather than the wrong one.

**Measure each separately.** `tests/sizes` before and after, and
`tests/bench` three runs alternating on the same machine, per
Iteration 129's method — the noise on this hardware is wide enough
that a single run of each proves nothing. A density change that does
not move `tests/sizes`, or that moves `tests/bench` the wrong way, is
not worth its complexity; that is the same standard
`PARSE-EXPAND-PLAN.md` sets for Stage 2.

**One interaction to keep in view.** Options 1 and 2 both change what
`cross.4` emits, and Stage 2 of `PARSE-EXPAND-PLAN.md` changes how
often that emitted code runs. Doing density work first means Stage 2's
benchmark baseline moves under it. Either order is defensible;
whichever is chosen, re-baseline rather than comparing across the
change.
