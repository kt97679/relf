# attic/docs/VM-RESEARCH.md — what the literature says, and what of it applies here

Written in Iteration 139, after `attic/docs/DENSITY-PLAN.md` had reached a
design by reasoning from measurements of this image alone. The point
of reading the field afterwards was to find out what had already been
tried and measured elsewhere. Three things in the plan are confirmed
by published numbers, one assumption in `GOALS.md` turns out to be
wrong, and one structural option nobody here had considered is
probably larger than everything in the plan put together.

## 1. Superinstructions — confirmed, with two cautions

Proebsting's superoperators (POPL 1995) are the origin: VM operations
synthesized automatically from smaller ones to avoid per-operation
dispatch overhead, inferred from usage patterns, reported as reducing
executable size and doubling or tripling speed. Piumarta and Riccardi
(1998) reached the same construct from the other direction and the
name "superinstruction" stuck.

Ertl's *Threaded Code Variations and Optimizations* (EuroForth 2001)
is the closest published work to this project, because it is Gforth.
Its measured results:

- Superinstructions gave **up to 2x on large benchmarks** on
  processors with branch target buffers, and the speedup came mainly
  from **fewer mispredicted indirect branches**, not from fetching
  less memory.
- On processors without a BTB the gain was much smaller — a factor of
  1.38 against 1.86 for the same benchmark.
- **Diminishing returns, and eventually negative.** On a machine with
  a small direct-mapped instruction cache, more superinstructions
  produced *slowdowns*, attributed to conflict misses. Building Gforth
  with 800 superinstructions needed ~100MB of memory; 1600 needed
  ~300MB and 1.5 hours.

**Caution for `attic/docs/DENSITY-PLAN.md`'s K=128.** The plan says to measure
engine growth per K. Ertl's result says to measure *speed* per K too,
because the engine's instruction-cache footprint can turn the curve
around before the size curve does.

### The important subtlety, which cuts our way

Ertl's conclusion on size is discouraging at first reading:
superinstructions did not reduce Gforth's code size overall. But the
reason is specific and does not apply here. To make superinstructions
widely applicable, Gforth had to move from traditional indirect
threading to a **primitive-centric** scheme, where a non-primitive
compiles to a primitive plus an inline parameter rather than to a code
field address. That change grew the threaded code by more than
superinstructions later recovered.

**RelF is already primitive-centric, and always has been.** A call is
one cell holding a relative offset; there are no code fields in the
threaded code at all. We would take the saving without having paid the
entry fee. Ertl even names the escape routes — eliminating code fields
and switching to byte code — as what might change the picture. This
project has done the first and the second is section 4 below.

## 2. Factorization — confirmed, and we have less to gain than most

Clausen, Schultz, Consel and Muller (TOPLAS 2000) factor repeated
JVM instruction sequences into *macro* instructions: a new opcode
whose body is the shared sequence, executed as a call. Measured:
memory footprint down to about **85% of original**, with a small
execution-time penalty; their earlier INRIA report gives ~30% on some
instruction sets with a penalty under 30%.

This is exactly what `tools/find-clones.py` looks for, and it is a
different technique from superinstructions despite the family
resemblance: a macro is *one call to a shared body* (smaller, slower
by a call per site), a superinstruction is *one new opcode* (smaller
and faster, at the cost of engine size).

Iteration 135 measured ~6% available here against their 15%, and
Ben Hoyt's *nibbleforth* notes say why in one line worth stealing:
programmers who factor into small words are running a dictionary
compressor by hand. `shell.4` is written that way. Clausen's 15% is
what you get when the source was not.

## 3. Register VMs — settled, and it settles it against us

Shi, Casey, Ertl and Gregg, *Virtual Machine Showdown: Stack Versus
Registers* (TACO 2008): a sophisticated stack-to-register translation
eliminated **over 46% of executed VM instructions**, at the cost of
bytecode **26% larger**.

For a project whose first goal is minimalism that is a closed
question. A register VM buys speed with size, which is the wrong
direction here. Recorded so that nobody spends an iteration
rediscovering it.

## 4. Variable-length encoding — `GOALS.md` assumed this is
## unaffordable, and the measurement says otherwise

`GOALS.md`'s phase 5 records a byte-granular opcode encoding being
considered and rejected, on the grounds that `CALL` — which currently
has *zero* encoding overhead, since the offset is the instruction —
would need a marker byte and realignment. `attic/docs/DENSITY-PLAN.md` inherited
that reasoning and extended it into a principle: a density scheme is
safe when it removes work and unsafe when it adds a decoding step.

That principle is sound. The **quantity** attached to it was a guess,
and the literature has measured it.

Latendresse and Feeley, *Generation of Fast Interpreters for Huffman
Compressed Bytecode* (SCP 2005), encode opcodes with canonical Huffman
codes and give operands custom-sized fields, decoding directly during
execution with no prior decompression. Measured on Java benchmarks:
**about 9% average slowdown, for compression typically between 30% and
60%.** They note explicitly that earlier work had assumed Huffman
decoding would be too slow in software, and that the assumption did not
survive being tested.

Nine percent is not free, but it is a fifth of what Iteration 137's
locals change cost, for several times the saving. **The rejection of
variable-length encoding in `GOALS.md` should be reopened as a
measured question rather than left as a principle.**

## 5. The option nobody here had considered: token threading

This is the largest finding of the review, and it dissolves the
specific objection that killed byte-granular encoding.

RelF spends a **full cell on every call**, because a call *is* a
relative offset. Calls are **6,576 cells, 34% of the compiled code**,
and on x86-64 that is 8 bytes to name one of about 620 words.

In **token threading** a call is not an offset but an *index* into a
table of word addresses. An index into 620 words needs 10 bits, not 64.
The objection in `GOALS.md` — that a byte-granular scheme must widen
`CALL` with a marker and padding — applies to an *offset*. It does not
apply to an index.

Ben Hoyt's *nibbleforth* notes work this out for Forth specifically:
variable-length opcodes at **nibble** granularity, most frequent words
in 4 bits and the next tier in 8, assigned by frequency analysis over
the actual program, with token threading so that **user-defined words
get short codes too, not just primitives**. He also reports the
frequency analysis that makes it work: over Gforth's own programs,
`exit` dominates, with the conditional and unconditional branches next
— which is very close to this image's own profile (`EXIT` 647, `LIT`
2,178, `?BRANCH` 863, `BRANCH` 365).

Lefurgy, Bird, Chen and Mudge (MICRO-30, 1997) is the hardware-side
precedent for the same two ideas — compressing into nibbles, and
rolling common sequences into a call. The commercial precedents for
two-tier instruction encodings are Thumb/Thumb-2, MIPS16 and the
RISC-V C extension: a short form for the common case, a long form for
everything else, decoded with fixed cheap logic rather than a general
decompressor.

### What it would be worth here, roughly

Very rough, on this image's own token census, assuming a byte stream
with a one-byte form for primitives and small values and a two-byte
form for calls and wider operands:

| | count | bytes/token | bytes |
|---|---|---|---|
| calls | 6,576 | 2 | 13,152 |
| primitives | 5,430 | 1 | 5,430 |
| literals | 2,178 | ~2 | 4,356 |
| branches | 1,228 | 2 | 2,456 |
| inline strings | — | — | 644 |
| **total** | | | **~26,000** |

against **78,024 bytes on i386 and 156,048 on x86-64** today. Call it
a **3x reduction on i386 and 6x on x86-64** — and note the second
number, because **a byte stream does not scale with cell width at
all.** Iteration 138 established that the x86-64 build being 1.63x
`dash` is this project's real size problem; this is the only idea
found that addresses it directly.

Against that: ~9% by Latendresse's measurement, plus the loss of
RelF's cheapest property — an offset that needs no table lookup — and
a large change to `cross.4`, `save-system.4` and every position-
independence assumption. It is not a small change. It is the one worth
measuring before concluding.

## 6. Dispatch: a modern result that pays for density work

CPython 3.14 (2025) replaced its computed-goto interpreter with a
**tail-calling** one: each opcode is its own function and dispatch is a
tail call, reported at around **10%** on 64-bit platforms.

The reason matters more than the number. A computed-goto interpreter
is one enormous function; compilers allocate registers badly across it,
and — the specific finding — they **merge the identical `DISPATCH`
tails together**, which is precisely what one does not want, since
having a separate indirect branch per opcode is what gives the branch
predictor context to work with. Separate functions stop the merging.
CPython's own analysis attributes most of the tail-call version's gain
to that alone. The LWN account is worth reading for the caveats: the
first measurements were inflated, and part of the apparent gain was a
GCC 13-15 regression rather than a real speedup.

**`relf.c` is exactly the shape this describes** — one function, one
`NEXT()` macro replicated at every primitive, compiled by GCC. This is
a *speed* lever entirely independent of size, which is what makes it
interesting here: it could pay for the density work rather than
competing with it. It also fits goal 5's portability constraint less
comfortably, since it depends on the compiler honouring tail calls.

## Measured afterwards (Iteration 140)

Three of the recommendations below were cheap to test and were tested.
Two came back decisively, one of them against the literature:

- **Dispatch-site replication buys nothing here.** GCC had merged 68
  `NEXT()` sites into **5**; forcing them apart with a zero-cost unique
  asm marker restored 66, and changed the benchmark by nothing
  measurable. Ertl's BTB mechanism and CPython's tail-call mechanism
  are the same mechanism, and this Xeon does not need it. Item 7 below
  is therefore much less attractive than it looked.
- **Token threading is real and cheap.** A two-tier byte encoding of
  the actual stream is **3.26x smaller on i386 and 6.51x on x86-64**,
  and `tools/dispatch-bench.c` measures it at **0.98-1.03x the speed**
  of the current cell encoding *including* the offset-call it gives
  up. Latendresse and Feeley's ~9% is 2005 hardware and full Huffman;
  a two-tier scheme captures most of the compression - their entropy
  floor is 13,778 bytes against two-tier's 18,937 - for far less
  decoding.

See `PROGRESS.md`'s Iteration 140 entry, including the first version
of the speed benchmark, which reported the byte stream 5x slower
because the harness gave it a comparison chain and the cell encoding a
jump table.

## What to take from this

1. **Keep superinstructions**, and measure speed per K as well as
   size, because Ertl found the curve turns.
2. **Stop worrying that superinstructions cannot pay for themselves in
   size.** Ertl's negative result is about the cost of becoming
   primitive-centric, which this project paid long ago.
3. **Expect ~6% from factorization, not 15%**, because `shell.4` is
   already factored by hand. Iteration 135's number is consistent with
   the literature once that is accounted for.
4. **Do not chase register VMs.** Measured: 26% bigger for 46% fewer
   executed instructions. Wrong direction for goal 3.
5. **Reopen variable-length encoding.** The rejection was reasoned,
   not measured, and the published measurement is 9%.
6. **Investigate token threading seriously.** It is the only idea
   found that attacks the x86-64 problem, because a byte stream is
   independent of cell width. Estimated 3x on i386 and 6x on x86-64,
   at a literature-measured cost near 9%.
7. **Try tail-call dispatch**, separately, as a speed lever that could
   fund the rest.

Items 5, 6 and 7 are each larger than anything currently in
`attic/docs/DENSITY-PLAN.md`, and none of them was reachable by measuring this
image. That is the argument for having read the field, and for doing
it earlier next time.
