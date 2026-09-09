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

Verified size, word bodies (Iteration 172, both widths re-measured on
a machine with the 32-bit toolchain present):

    i386     92,616 B -> 52,698 B   0.569x
    x86-64  182,456 B -> 59,764 B   0.328x

The round trip gives 541 exact, 0 differ, 3 ambiguous **on both cell
widths**, and the structural check - inline strings adjacent to their
call, `(LOOP)` operands cell-aligned - gives 194 and 17 with zero
violations at 4 bytes and at 8. Sabotaging either offset conversion
breaks the same 277 and 15 words at both widths, so the width-dependent
alignment arithmetic is genuinely under test and not merely exercised.

Field widths checked rather than assumed: highest word number used is
**1,044** against a 65,279 ceiling, and **zero** branch offsets need
more than 16 signed bits.

## The layout pass, and the whole-image number

`tools/sod16-layout.py` (Iteration 173) lays the entire image out again
with token bodies, recomputes every reference the new spacing
invalidates, and checks the result. Run it on a dump from either
engine. It reports, and exits nonzero if any of it fails:

    x86-64   205,336 B -> 83,920 B   0.409x
    i386     109,256 B -> 69,748 B   0.638x

**Quote this, not the body-only ratio.** Bodies shrink to 0.284x and
0.539x, but headers, names and data bodies do not shrink at all, and
they are 35,688 bytes of the x86-64 image. The body figure is the
interesting one about the encoding; this is the one about the artifact.

Checked rather than asserted, at both cell widths: the header
adjacency holds on all 1,081 consecutive pairs, the recomputed link
chain re-walks to the same 1,082 words in the same order, all 12
`DEFER` xts convert to word numbers with none unresolved, and all 81
`BUFFER:` links remap with none unresolved.

**`BUFFER:` parameter fields are a relocation category this list did
not have** (Iteration 174). `pool.4` lays them out `[+0 ptr][+1 size]
[+2 link]`. The ptr is a live `malloc`'d address in a dump and
`RESET-BUFFERS` zeroes it before a save, so it is written as 0, the
state `ALLOC-BUFFERS` expects. The link is a `START`-relative offset to
the previous buffer's **parameter field** - one cell past its body
start, because `BUF-BODY` is `HERE` at the moment `CREATE` has laid the
header and the leading call cell - and bodies move, so it is remapped.
Aiming that remap at the body start instead of the parameter field
fails on 80 of 81 and passes on the one whose link is 0, which is
exactly the shape of a bug that a less complete check would have
called success.

A data body is the SAME SIZE in both images, which is not a
coincidence: its leading call cell becomes NOOP padding plus a 2-byte
call token, and that is exactly one cell at either width.

## The blocker in front of emitting an image

**`(POSTPONE)` is an eighth inline-operand word, and it is the one that
does not carry across unchanged.** Its own comment in `kernel.4` says
"has inline argument"; the body is
`R> DUP DUP @ + SWAP CELL+ >R`, which reads a CELL holding a RELATIVE
ADDRESS and skips it.

The other seven inline-operand words survive because their arithmetic
is about *positions*, and the rule "only the opcode stream becomes
tokens" keeps positions cell-granular. This one is about *identity*:
it turns its operand into an address and then `EXECUTE`s or
`COMPILE,`s it, and under SOD16 an xt is a word NUMBER (Iteration
165). So `(POSTPONE)` needs a source change - to fetch a word number
rather than compute an address - and that decision is not made here.

Until it is, `(POSTPONE)` is **refused** rather than mis-decoded. The
cost is the 13 words that compile through it - `CREATE`, `WHILE`,
`DO`, `?DO`, `LEAVE`, `LOOP`, `+LOOP`, `."`, `S"`, `ABORT"`,
`POSTPONE`, `DOES>`, `L-EMIT` - plus `DO-ULIMIT` and `DO-UNALIAS`,
which fail for a reason not yet diagnosed. `tools/sod16-layout.py`
names all 15 and **exits nonzero**, because the failure mode to avoid
is emitting an image in which fifteen code bodies were quietly copied
as data.

That list is why no image is emitted yet. It is not a long list, and
none of it is mysterious except the last two.

## What is next

**A `DOES>` word's body calls a mid-word address, and SOD16 cannot
encode that.** Found in Iteration 170. It is the blocker in front of a
bootable image. Iteration 173 measured it and took route 3 below: there
are exactly **two** such targets, so they get word numbers past the end
of the chain and the image carries a two-entry side table of (word
number, byte offset) so the loader can finish deriving the word table
after walking the chain. The table itself stays derived and unsaved.
The translator and layout pass do this; the ENGINE does not read that
side table yet.

`(;CODE)` stores into the created word's first cell a relative offset
to the address just past the `DOES>` in the *defining* word:

    : (;CODE)  LAST @ NAME> R> OVER - CELLBYTES-TOK - SWAP ! ;

So the target is inside another word's body, not at a word start. A
SOD16 call token is a word *number*, and a word number can only name a
word start, so these calls have no representation at all. Measured on
this image: **93 words**, 81 through `pool.4`'s `BUFFER:` (target
`+176` inside its body) and 12 through `kernel.4`'s `DEFER` (`+40`).
The 12 include the `DEFER` cells `SOD16.md` already discusses under
"an xt is a word number" - the xt *stored* in a `DEFER` was settled;
the call *to* the `DEFER` runtime was not.

Three routes, none measured:

1. **Give each `DOES>` tail its own word number** by making it a real
   word, so a call to it is an ordinary call. Cleanest against "an xt
   is a word number", and a `cross.4`/`kernel.4` change.
2. **A second call form carrying an offset.** Buys generality and
   spends the simplicity that won the encoding comparison in the first
   place - see the table above before proposing it.
3. **Let the word table carry the tails.** It is derived and rebuilt
   at load anyway, so it could append an entry per `DOES>` word. The
   cost is that a word number stops meaning "the Nth word in the
   chain", and the loader must reproduce the translator's numbering
   exactly - which is the property Iteration 165 went to some trouble
   to establish.

**Do not classify code and data by whether the body decodes.** 26
`CONSTANT`s decode cleanly as code and *are* code - `CONSTANT` compiles
`LIT-TOK , , EXIT-TOK ,` - while 404 `DOVAR` words and 93 `DOES>` words
are data with a call in front. The structural handle is the first cell:
a call to `DOVAR`, or to a `DOES>` tail, means the rest of the body is
data and must be copied as cells.

**Then the layout pass.** `sod16.c` still loads a cell image. A token
image's bodies are a different size, so offsets must be recomputed.
Iteration 167 established this is a list, not a search, because the
image is already position-independent - `cross.4`'s link fields are
relative "so it survives relocation", calls are relative, and
`SS-SCRUB` guarantees no absolute address survives a save. Of 23,154
cells only 13 hold values in the image's address range, and those come
from a live-process dump, not a saved image.

The image structure is confirmed (Iteration 170) and is a strict
sequence, ascending: a 48-byte prologue - two calls at `+0` and `+8`,
which is where `ip = base` starts executing, then three filler cells -
then, per word, `[link cell][name field, aligned][body]`, ending at
`HERE`. The older word's body ends exactly where the newer word's link
cell begins: checked on all **1,081** consecutive pairs, 0 disagree.

To recompute:

1. **link fields** - spacing between headers changes as bodies shrink;
2. **call offsets** - become word numbers, so the category vanishes,
   *except* for the mid-word `DOES>` targets above;
3. **branch offsets** - converted to token units in Iteration 169, and
   verified to fit: the widest is 559 against a 32,767 ceiling. This
   line previously read "already in token units", and that was wrong -
   see the traps below;
4. **`(LOOP)` operands** - a byte offset in a cell, recomputed for the
   new spacing rather than reinterpreted (Iteration 170);
5. **xts in `DEFER` and `SET-BOOT`** - word numbers, which do not move.

Then: emit a loadable image, boot it, and run `tests/bench` against
`freeze/iter156-encoding-baseline`. That is the like-for-like number
this line of work has been circling since Iteration 133, and
`tests/bench` can now resolve about +/-4% on a ratio.

After that, `cross.4` emitting tokens directly, for self-hosting. That
is the one that decides whether SOD16 *replaces* the current encoding
or only sits beside it, and it is where `cross.4`'s hand-embedded
dispatch numbers finally have to be touched.

**Only the opcode stream becomes tokens.** Inline operands and inline
strings keep cell granularity and cell alignment, so the seven words
that read inline data off the return stack in Forth - `(S")`, `(.")`,
`(ABORT")`, `(LOOP)`, `(+LOOP)`, `(?DO)`, `(LEAVE)` - need no change.
`(LOOP)` gets NOOP padding *before* its call token, since padding after
it is what `DUP @` would read. Verified structurally: 194 inline
strings adjacent to their call with correct `ALIGNED` resume points,
all 17 `(LOOP)` operands cell-aligned, zero violations.

**`(?DO)` and `(LEAVE)` compile an absolute address.**
`RESOLVE-LEAVE` stores a bare `HERE`. That is a latent fault in the
*cell* image too, since an absolute address does not survive the
relocation performed on every load, and it is invisible only because
both words have **zero call sites** in this image. Anything that adds
a `?DO` or a `LEAVE` to `shell.4` breaks saved images before it ever
reaches SOD16. The translator refuses both rather than mis-decoding.

**Still unwritten in `sod16.c`:** the `EXECUTE` bounds check
(Iteration 165), and a dispatch entry for `LIT32`. The latter is now
token index 68, appended past the 68 real primitives, because the
dispatch table has exactly that many entries and the earlier choice of
255 would have read past the end of it.

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
