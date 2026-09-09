# SOD16

The engine encoding chosen in Iterations 156-167, being built on branch
`token16`. This file is the brief: what it is, what is decided and why,
what is built, what is next, and what will bite.

Read this before `TOKEN-THREADING.md` or `DENSITY-PLAN.md`, both of
which describe designs that were measured and set aside.

---

## The encoding

One 16-bit token per operation.

    0 .. 255        primitive index
    256 .. 65535    word number (token - 256)

Operands follow their token as further 16-bit units:

    LIT      one operand, or two via LIT32 when it does not fit
    BRANCH   one signed operand, offset in TOKEN units
    ?BRANCH  same
    (S")     inline counted string, byte-packed, padded to a token

Decode is **one 16-bit read, one compare against 256, one branch**:

    t = TOK(ip); ip += 2;
    if (t < 256) goto *dispatch[t];
    RPUSH(ip); ip = wordtab[t - 256];

There is no tag, no varint, no packing, and no branch on token width.

## Why this and not the others

Measured, not argued. `tools/encoding-census.py` regenerates the sizes,
`tools/pack-bench.c` and `tools/varint-bench.c` the dispatch costs.

| scheme | x86-64 size | dispatch |
|---|---|---|
| RelF today | 1.00x | 1.00 |
| SOD32 packed (5-bit x6) | 0.75x | 1.21 |
| tagged nibble / tagged byte | 0.76x | 1.60-1.65 |
| **SOD16** | **0.34x** | **~1.00** |
| variable-width byte stream | 0.19x | ~1.06 + table cost |

**Packing is closed.** Every packed form costs 21-68% in dispatch to
buy density a plain 16-bit token gets more of anyway, and the penalty
holds at every working-set size from 9KB to 18MB, so it is decode cost
rather than a cache artifact.

**Variable-width byte tokens are denser and were still rejected.** They
need a prefix budget to ration, a varint decode loop costing ~15% per
additional byte, and a ceiling: 1,024 targets against 1,082 dictionary
entries, since a variable reference compiles as a call. SOD16 holds
65,280 word numbers with no escape hatch.

**The decisive argument is goal 3.** `sod16.c` differs from `relf.c` by
**eight executable lines**, because only 4 of 68 primitives touch `ip`.
It is not a new engine; it is the same engine with a different code
representation.

## Decisions, and why they are forced

**An xt is a word number, not an address.** `SET-BOOT` and 17 `DEFER`
cells store xts *in the image*, which is saved and reloaded at a
different base. An address there is the absolute-address-in-a-saved-
image fault `SS-SCRUB` exists to catch. `EXECUTE` therefore needs a
bounds check - marked in `sod16.c`, not yet written.

**Word numbers run oldest-first, i.e. definition order.** The dump
walks the link chain newest-first, and numbering in that order was a
bug: defining one word would renumber everything and invalidate every
compiled token. Oldest-first means a new definition takes the next
unused number and nothing that exists moves. A load rebuilds this by
walking the chain to its end, then assigning coming back.

**The word table lives outside the image.** It is derived data: rebuilt
at startup from the link chain, never saved, so nothing for `SS-SCRUB`
to clean and no image growth. Because it is rebuilt after load it holds
**absolute** addresses, making dispatch one load with no base add and
no shift. It grows by `realloc`, so it never collides with `HERE` and a
runtime-defined word just appends. 1,082 entries is 8,656 bytes, and
the size figures correctly never counted it.

## What is built

Six commits on `token16`, `master` untouched, `tests/verify` green at
every one.

- **`tools/sod16.py`** - translator, and it **proves itself**: it
  decodes its own output and asserts equality per word. 528 words
  round-trip exactly, 0 differ, 3 ambiguous by construction. `--emit`
  writes a loadable text form. The figure was 531 before Iteration 169
  corrected two decoder faults; the size result is unchanged.
- **`tools/sod16-engine.c`** - dispatch core and table rebuild, running
  real translated bodies. Primitives are stubs, so its throughput
  figure is a decode rate and **not** a comparison against `relf`.
- **`sod16.c`** - the real engine, `relf.c` with eight lines changed.
  Compiles clean. Cannot boot yet, see below.
- **`tools/dict-dump-addr.4`** - the addressed dictionary dump the
  tools consume.

Verified size, word bodies:

    i386     92,616 B -> 54,084 B   0.584x
    x86-64  182,456 B -> 62,626 B   0.343x

Field widths checked rather than assumed: highest word number used is
**1,044** against a 65,279 ceiling, and **zero** branch offsets need
more than 16 signed bits.

## What is next

**The layout pass.** `sod16.c` still loads a cell image. A token
image's bodies are a different size, so offsets must be recomputed.
Iteration 167 established this is a list, not a search, because the
image is already position-independent - `cross.4`'s link fields are
relative "so it survives relocation", calls are relative, and
`SS-SCRUB` guarantees no absolute address survives a save. Of 23,154
cells only 13 hold values in the image's address range, and those come
from a live-process dump, not a saved image.

To recompute:

1. **link fields** - spacing between headers changes as bodies shrink;
2. **call offsets** - become word numbers, so the category vanishes;
3. **branch offsets** - converted to token units in Iteration 169, and
   verified to fit: the widest is 559 against a 32,767 ceiling. This
   line previously read "already in token units", and that was wrong -
   see the traps below;
4. **xts in `DEFER` and `SET-BOOT`** - word numbers, which do not move.

Then: emit a loadable image, boot it, and run `tests/bench` against
`freeze/iter156-encoding-baseline`. That is the like-for-like number
this line of work has been circling since Iteration 133, and
`tests/bench` can now resolve about +/-4% on a ratio.

After that, `cross.4` emitting tokens directly, for self-hosting. That
is the one that decides whether SOD16 *replaces* the current encoding
or only sits beside it, and it is where `cross.4`'s hand-embedded
dispatch numbers finally have to be touched.

## Traps

**Verify the tools, not just the code.** Three analysis tools in this
line of work had silent bugs producing plausible wrong numbers:

- call targets resolved as `addr + value` instead of
  `addr + CELL + value`, matching 24 of 6,548 calls;
- an inline counted string's length read as a CELL when `(S")` uses
  `COUNT`, so it is a **byte** - every word containing a string was
  truncated and the operation count was low by 21.5%, for four
  iterations, in numbers that had already been published;
- word numbering in the wrong direction.

The first two were caught by round-tripping. **The third could not
be** - a round trip re-encodes and decodes with the same numbering and
agrees with itself either way. It was caught by asking what an xt has
to be. Some faults need a design question, not a test.

Iteration 169 found two more of the same family, in the same tool, and
neither was visible to the round trip for the same reason:

- **Branch offsets were never converted to token units.** `to_tokens`
  copied the cell image's *byte* offset straight into the token, with
  a comment promising it was "re-derived below"; nothing re-derived it.
  1,308 of 1,310 branches carried a wrong number, and the round trip
  agreed with itself because it decoded with the same convention. The
  fix converts in both directions through an explicit cell-offset /
  token-index layout map, which is what makes the round trip evidence
  about branches instead of a tautology. Sabotaging the conversion now
  breaks 272 words; before, it broke none.
- **A `PRIMITIVE` stub is not threaded code.** `cross.4` emits
  `"HEADER DUP , ,-T EXIT-TOKEN ,-T`, so a stub body is exactly
  `[prim-token, EXIT]`. Read as code, `LIT`, `BRANCH` and `?BRANCH`
  each swallowed the trailing `EXIT` as their operand: the word `LIT`
  translated to "push 9". It round-tripped clean and was counted among
  the successes. Detect stubs **by shape, not by name** - `locals.4`
  redefines `EXIT`, so a name test picks the wrong word.

The rule those two sharpen: **a round trip only tests a
transformation the two directions actually disagree about.** Where
encode and decode share an assumption, it proves the assumption is
applied consistently, not that it is right. Check by breaking the
transformation on purpose and confirming the harness notices.

**Three words are ambiguous by construction**, and the report now says
so rather than passing them. The stub for `LIT`, `BRANCH` or `?BRANCH`
encodes to `[prim, EXIT]`, which cannot be told from "prim, with EXIT
as its operand" - by the same positional-operand rule the encoding
relies on everywhere else. The cell image has the identical ambiguity;
either engine executing one of those three would consume the `EXIT`
and run on past the word. The bodies exist so the *name* resolves, not
to be executed, so this is inherited, not introduced.

**Operands are positional.** Only the operation that emitted an operand
knows it is there. `(LOOP)`'s bare operand token was read back as a
call because the decoder did not know to consume it. Signed operands
need sign extension - `-24` came back as `65512`.

**Anything after `END-CROSS` in `kernel.4` is not cross-compiled.** It
compiles into the host, not the target, and changes nothing about the
image. A probe appended there will silently do nothing.

**Script lines over 256 characters have their tail executed as a
separate command** (`LINE-MAX`, still unfixed - see the backlog in
`PROGRESS.md` Iteration 154). Easy to hit when writing long one-liner
probes, and it looks like an engine bug.

## Reproducing everything

Every figure in this file comes from these four commands. The dump is
the input to both Python tools and is not committed, because it is
derived; regenerate it rather than looking for it.

    # the addressed dictionary dump, 4-byte cells (relf32) and 8-byte
    printf 'S" pool.4" INCLUDED\nS" locals.4" INCLUDED\nS" shell.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n' \
      | ./relf32 kernel32.img | tr -d '\r' > /tmp/dump3.txt
    printf 'S" pool.4" INCLUDED\nS" locals.4" INCLUDED\nS" shell.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n' \
      | ./relf  kernel.img   | tr -d '\r' > /tmp/dump64.txt

    # translator + round-trip proof, and a loadable token file
    python3 tools/sod16.py /tmp/dump3.txt  4 --emit /tmp/shell.tk
    python3 tools/sod16.py /tmp/dump64.txt 8

    # every size in ENCODING-COMPARISON.md
    python3 tools/encoding-census.py

    # the dispatch core, on real translated bodies
    cc -O2 -o /tmp/s16 tools/sod16-engine.c && /tmp/s16 /tmp/shell.tk 50

`sod16.py` exits nonzero if the round trip fails, so it can be wired
into `tests/verify` once the layout pass lands.

Note the `tr -d '\r'`: the engine emits CRLF and the parsers do not
strip it. Without it every regex silently fails to match and the tools
report zero words.

## Where the numbers live

- `ENCODING-COMPARISON.md` - the full comparison, regenerated in
  Iteration 161 after the census bug. Do not quote the Iteration 156
  figures.
- `PROGRESS.md` Iterations 156-167 - the reasoning, including the
  corrections and two retracted claims.
- `tools/encoding-census.py` - regenerates every size figure.
- `tools/pack-bench.c`, `tools/varint-bench.c` - dispatch costs. Their
  `cell` baselines **disagree with each other** and the disagreement is
  unresolved; trust within-tool comparisons only.
