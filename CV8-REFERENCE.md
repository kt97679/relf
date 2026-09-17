# CV8-REFERENCE.md — the CV8 format and engine, in detail

This is the reference: what a CV8 image contains, byte by byte, and what
the engine does with it. `CV8.md` argues *why* this design; `VM-SURVEY.md`
covers the specialised opcodes and where they were borrowed from;
`XARCH.md` covers other architectures. This file assumes you want to
implement or debug it.

Everything here describes the working lab implementation:
`tools/lab/vm-lab.c` (`ENC=3`), `tools/sod16.py` and
`tools/layout.py`. Byte values quoted below are from a real image
built by `tools/lab/build-cv8.sh`.

---

## 1. The idea in one paragraph

RelF's traditional image stores **one cell per operation**: eight bytes
on a 64-bit host, holding either a relative offset to the word being
called or a small primitive number. CV8 stores **one byte per
operation** instead, and calls become **two bytes** holding a scaled
offset from the image base. A byte whose top bit is clear is an opcode;
a byte whose top bit is set begins a call. Nothing is a pointer, so the
image is position independent and identical on every machine of the same
cell width. The result is 0.32x the size of the cell image, and, with the
specialised opcodes, about a fifth of its execution time.

---

## 2. Where CV8 comes from

### The name

**CV8** is short for **C**ompressed-pointer, **V**ariable-length, **8**-bit
units: calls are compressed pointers (§3.4), operations are
variable-length, and the unit is a byte rather than a cell or a 16-bit
token. It is also the image's magic string — `CV8` followed by the
scale digit, so an image reads `CV80` (`CV83` for a 64-bit image before Iteration 244).

The name was coined in Iteration 189 of this project, when the encoding
was first built and measured. It is not a name from the Forth
literature, and nothing outside this repository uses it. If it ever
ships, a less cryptic name would be an improvement.

### The lineage

CV8 is the fifth encoding in a line, and each step was a response to a
measured problem with the one before:

**SOD32** (L.C. Benschop) is where the family starts. Its idea, stated
in this project's own README, is a **separated engine and
machine-independent image**: the Forth system is a binary blob that any
host's engine can load. That property is the reason this project exists,
and CV8 keeps it exactly. SOD32 packed several 5-bit operations into a
32-bit cell. Iteration 157 measured that packing directly
(`tools/pack-bench.c`): it costs 1.06–1.19x in dispatch on x86-64 and
1.67x on i386, for about 9% of image size. CV8 takes the separated-image
idea and rejects the packing.

**RelF** (Kirill Timofeev) is SOD32 sped up, and it is what this project
refactors. Its key change, and its name, is that *a reference to a
high-level definition holds a relative offset rather than an address* —
so the image is position independent. CV8's calls are the same idea
carried further: still an offset, but scaled and squeezed into 15 bits.
RelF's cell image is the baseline every measurement here is against.

**SOD16** (Iterations 156–167, branch `token16`) replaced one cell per
operation with one 16-bit token, and got the image to 0.41x. Tokens
0–255 were primitives; 256 and above were **word numbers**, indexes into
a table of addresses built at load time. It was measured 1.25x slower
than the cell engine, which is what prompted the brief in
`INNER-INTERPRETER.md`.

**CPT16** (Iteration 189) came from re-examining that slowdown. Most of
it turned out not to be the table at all — it was VM registers living in
statics and executed alignment padding (`CV8.md` §1). But the table was
worth removing anyway: if call targets are aligned, the map from index
to address is a *linear function*, so scaling replaces indexing and the
table disappears. That is compressed-pointer threading, still 16-bit
units.

**CV8** (Iteration 189) is CPT16 with the unit narrowed from 16 bits to
8. Once calls no longer need to be a whole unit wide, most operations
fit in one byte, and the image drops another 13–16% at no measured cost
on x86-64 — and a small gain on i386. The specialised opcodes
(`VM-SURVEY.md`, §7 here) were added in Iteration 190, and are what took
it from "denser" to "several times faster".

### The ideas it borrows

None of the mechanisms are new; the contribution is the combination and
the measurement.

| mechanism | where it comes from |
|---|---|
| separated engine and portable image | SOD32 |
| relative (position-independent) references | RelF |
| a byte-granular instruction stream | the JVM; Open Firmware's FCode |
| `base + (value << shift)` as a pointer | HotSpot's compressed oops; 8086 Forth's **segment threading**, which aligned words to 16-byte paragraphs and used the segment number as the token |
| one-byte forms for the commonest constants | JVM `iconst_*`; YARV's operand unification |
| locals as one-instruction slot access | JVM `iload`/`istore`; CPython `LOAD_FAST`; Smalltalk-80's push-temp |
| specialise the common case, deoptimise the rest | CPython 3.11's adaptive interpreter (PEP 659) |
| choosing the primitive set by frequency | Gforth; Proebsting's superoperators |
| small immediate operands | Lua 5.4's `OP_ADDI`/`OP_EQI` |
| interpreting the compact form in place, rather than rewriting it at load | Titzer's in-place WebAssembly interpreter — as against OCaml and YARV, which translate to threaded code when loading |

The last row is the one design choice worth restating, because it is
where CV8 differs from most bytecode systems: **the dense form is
executed directly.** OCaml and Ruby's YARV both expand their compact
on-disk code into pointer-wide threaded code at load time, trading
memory for speed. CV8 does not, because the metric here is disk *and*
memory, and because a load-time expansion pass would be charged to every
shell start. The measurements agree: the cell image misses L1d about
five times more often than the token image (`XARCH.md` §5).

---

## 3. The byte stream

### 3.1 The fundamental test

```
b = ip[0]
b < 0x80    ->  opcode b, one byte, ip += 1
b = 10xxxxxx -> call, 2 bytes: v = ((b & 0x3F) << 8)  | ip[1]
b = 11xxxxxx -> call, 3 bytes: v = ((b & 0x3F) << 16) | (ip[1] << 8) | ip[2]
                target = base + (v << SCALE)
```

`SCALE` is 0 at both widths since Iteration 244, when headers became
byte-granular and bodies stopped being aligned; it was 3 on a 64-bit
build and 2 on a 32-bit one before that. This is the
whole decoder. There is no length table and no prefix.

The two call widths (`VARCALL`) exist so the format is not capped at a
single window. The near form reaches 16384 << SCALE and the far form
4M << SCALE, and the compiler picks per call site by distance, exactly
as it picks `LIT8`/`LIT`/`LIT32`. Measured cost of the extra test: under
1% of instructions, and no measurable time - it runs only on calls
(~22% of dispatches) and predicts nearly perfectly, since almost every
call is near. Building with `-DVARCALL=0` restores a fixed 15-bit call
if you ever want it.

Slot operands (`VAR@`, `VAR!`, the locals opcodes) use the same trick
(`VARSLOT`): one leading bit selects a 15-bit or 23-bit payload - SIGNED,
and counted from the operand itself since Iteration 259 (see §7.2). Without
it slots were a fixed 16 bits, so **variables had to live in the first
512 KB while code could span 32 MB** - an asymmetry that would have
failed silently in a larger system.

The engine loads the byte **sign-extended**, so "is this an opcode?" is a
branch on sign with no comparison (`SIGNTEST`, on by default except on
32-bit ARM; see `XARCH.md` §3).

### 3.2 Opcode map

Nothing in this table is a constant in the source. Every boundary is
derived from the number of `PRIMITIVE` lines in `kernel.4` - by
`cross.4` and `kernel.4`'s compiler, and by `cv8.c` from its `NPRIM`
and `NESC`, which must be raised by hand. Until Iteration 214 the
numbers were written out, and adding one primitive then made the image
encode an opcode the engine decoded as something else, with no build
error. Until Iteration 245 the engine's folded table was still written
as `[72 + k]`, which is right for 67 primitives only.

With 35 direct and 38 escaped primitives (Iteration 264):

| range | meaning |
|---|---|
| `0x00`–`0x22` | the 35 **direct** primitives, in `PRIMITIVE` order |
| `0x23` | `LIT32` — 4-byte signed operand |
| `0x24` | `DOVAR` — data body prologue |
| `0x25` | `DODOES` — `DOES>` body prologue |
| `0x26` | `LIT8` — 1-byte unsigned operand |
| `0x27` | `LIT8;EXIT` |
| `0x28`–`0x3E` | folded `primitive;EXIT`, in the fold-list order (23) |
| `0x3F` | `BRANCH8` — 1-byte signed offset (Iteration 258) |
| `0x40` | `?BRANCH8` — likewise |
| `0x41`–`0x60` | **free** — 32 opcodes |
| `0x61`–`0x7C` | specialised opcodes (§7) — 28 of them |
| `0x7D` | `LIT64` — a full cell, little-endian |
| `0x7E` | `ESC` + a selector byte: 38 OS/libc primitives of 256 selectors |
| `0x7F` | free |
| `0x80`–`0xFF` | first byte of a two- or three-byte call |

**Escaped primitives cost no opcode.** The 38 OS/libc primitives —
`BYE`, the file and process words, `READ`, `WRITE`, `POLL`,
`RAW-MODE`, and since Iteration 260 `MOVE`, `FILL`, `COMPARE`, `SCAN`
and `CSTRLEN` (memmove, memset, memcmp, memchr, strlen), and since 264
`ISATTY` — are
declared after `ESCAPED` in `kernel.4`, contiguous at the end of the
list, and selector *t* is the *t*-th of them. Adding one appends a
`PRIMITIVE` line, a handler to `cv8.c`'s `escaped_prims[]` and one to
`NESC`, and moves nothing: there are 256 selectors, and a selector the
engine does not have is reported rather than jumped through.

**The synthetic opcodes start at `NDIRECT`** — `LIT32` through the end
of the folded band are `NDIRECT + k`. So only a new DIRECT primitive
moves the map, by one; the free band is its headroom, and both
`cross.4` (`MAP-FITS?`) and `cv8.c` (a static assertion) refuse a map
whose folded band reaches `0x61`.

Until Iteration 247 the synthetic opcodes were numbered from the TOTAL
primitive count. That left the 31 opcodes after the direct band unused
- they were labelled "vacated" in this table - and made every escaped
primitive push the map up by one, so the headroom looked like three
opcodes when it was thirty-four. The byte meanings changed with the
fix, which is why the format version went to 3.

The primitive numbering is not a CV8 invention: it is the order words
appear as `PRIMITIVE` lines in `kernel.4`, the same numbering the cell
engine uses. `LIT` is primitive 2 and keeps a 2-byte operand.

### 3.3 Operands

| form | operand |
|---|---|
| `LIT8` | 1 byte, unsigned 0–255 |
| `LIT` | 2 bytes, unsigned little-endian |
| `LIT32` | 4 bytes, signed little-endian, sign-extended to a cell |
| `LIT64` | `CELL_BYTES` bytes, little-endian — for values outside int32 |
| `BRANCH`, `?BRANCH` | 2 bytes, **signed byte offset from the operand itself** |
| `BRANCH8`, `?BRANCH8` | 1 byte, signed, from the operand; backward branches that reach |
| `ADDI`, `EQI` | 1 byte, signed −128..127 |
| specialised slot ops | 2 or 3 bytes, a signed offset from the operand (§7.2) |
| `(LOOP)`, `(+LOOP)` | none: the call is followed by a branch back to the loop's start |
| `(?DO)` | none: followed by a 16-bit branch to the loop's exit |
| `(POSTPONE)` | 3 bytes, big-endian, the xt as an offset from START |
| inline strings | a count byte and the text, unpadded |

Two conventions matter when writing a compiler:

- **A backward branch takes `BRANCH8`/`?BRANCH8` when its offset fits
  -128..127** (`BACK,`), since its distance is known when it is compiled;
  forward branches are always 16-bit, patched by `>RESOLVE`. Measured in
  Iteration 258 on the 64-bit shell image: every forward branch is
  within 875 bytes, and 97% would fit a byte - reachable only by a pass
  that shrinks a finished definition.
- **Loops decide by where they return.** `(LOOP)` and `(+LOOP)` return
  INTO the branch after them to go round again, and past it (two bytes
  or three, by its opcode) when done; `(?DO)` returns into its forward
  branch for an empty loop. `LEAVE` is `UNLOOP` and a forward branch;
  until the loop ends, the operands of its `?DO` and `LEAVE`s chain
  through `'LEAVE`, each holding the distance back to the previous.
- **Branch offsets are measured from the operand's own position**, not
  from the byte after it. `ip += (int16_t)LD16(ip)`. Getting this wrong
  produces an image that runs and then jumps two bytes off; it cost me a
  debugging round.
- **Multi-byte operands are unaligned.** The engine reads them by
  composing bytes, which GCC merges into one load on x86, ARMv7 and
  AArch64, and leaves as byte loads on RISC-V. Do not use `memcpy` here:
  on RISC-V it compiled to a stack round trip and a stack-protector
  check.

### 3.4 Calls, and the reach limit

A call names a **byte offset from the image base, divided by 2^SCALE**
(with SCALE 0, simply the byte offset).
It does not name a word number, so there is no word table, no load-time
chain walk and no xt-to-index map. This is HotSpot's compressed-oops
decode (`base + (narrow << shift)`) and, before it, 8086 Forth's
segment threading.

Consequences:

- **Every call target must be 2^SCALE aligned** - which, at SCALE 0, is
  every byte. Before Iteration 244 it meant padding every name and body
  to a cell. The cost of SCALE 0 is reach: the near form covers 16 KB,
  so calls to the upper part of a shell image take the three-byte form.
- **The limit is bytes, not words.** At today's average of ~60 bytes per
  entry, the far form is roughly 500,000 words.
- `COMPILE,` becomes arithmetic on the target's distance.

### 3.5 Every ceiling in the format

Audited in Iteration 194, after the question "will these limits stop a
bigger project?". They are listed here because the answer depended on
limits I had not been tracking - the binding one was not the call reach.

| limit | 64-bit | 32-bit | kind |
|---|---|---|---|
| VM memory (`MEMSIZE`) | 16 MB | 16 MB | build parameter, **not** format |
| call reach, near form | 16 KB | 16 KB | format |
| call reach, far form | **4 MB** | 4 MB | format |
| slot reach, near form | ±16 KB of the operand | ±16 KB | format |
| slot reach, far form | **±4 MB** of the operand | ±4 MB | format |
| literal width | full cell | full cell | format |
| branch, within one word | ±32 KB | ±32 KB | format |
| opcode space | 128 + a reserved second bank | same | format |
| `DOES>` tails (`MAX_TAILS`) | 16 | 16 | build parameter |

The reach figures are for SCALE 0 (Iteration 244); at the old scales
they were 8x (64-bit) and 4x (32-bit) larger. **The far call reach, 4
MB, is now below `MEMSIZE`**, so a dictionary that grew past 4 MB could
not call its own oldest words' neighbours from its newest - the first
ceiling a growing system meets. At today's 60 KB it is 70x away. The
remedy is a fourth call width, not a return to aligned bodies.

(Until Iteration 258 a second, tighter limit came from the kernel's
`OPERAND-ALIGN`, which assumed the loop runtimes sat in the first 16 KB.
Nothing is aligned in code now.)

`MEMSIZE` covers the image, all runtime dictionary growth and the
stacks. It is a plain parameter: every reference in an image is
relative, so raising it breaks nothing.

---

## 4. Worked examples

Real bytes from `spec-64.img`, an image from before Iteration 244:
the bodies there are cell-aligned and the calls scaled, which today's
are not. Word bodies are cell-aligned, so the
trailing zeros are padding, not code.

**`: 2DUP OVER OVER ;`** at offset 1344:

```
09 57 00 00 00 00 00 00
^^ OVER (primitive 9)
   ^^ folded OVER;EXIT (0x49 + index of OVER in the fold set)
```

Two bytes for a word that costs 24 bytes in the cell image (`OVER`,
`OVER`, `EXIT` at 8 bytes each). The `EXIT` disappears into the second
`OVER`.

**`: COUNT DUP 1+ SWAP C@ ;`** at offset 1792:

```
06 78 01 07 4f 00 00 00
^^ DUP (primitive 6)
   ^^ ^^ ADDI +1   (the compiler folded `LIT 1` `+` into one opcode)
         ^^ SWAP (primitive 7)
            ^^ folded C@;EXIT
```

Four operations, five bytes, one `EXIT` elided.

**`32 CONSTANT BL`** at offset 1936:

```
48 20 00 00 00 00 00 00
^^ LIT8;EXIT
   ^^ the value 32
```

A constant is two bytes of code. In the cell image it is a call to
`DOCON` plus a cell of value.

**A data word** (`VARIABLE`, `CREATE`) has this body:

```
45 00 00 00 00 00 00 00   <- DOVAR, then padding to the cell
<parameter field, cell-aligned>
```

`DOVAR` pushes the aligned address just past itself and returns. The
padding is **never executed**: calls to the word land on the `DOVAR`
byte, and `DOVAR` itself computes `align(ip)` rather than stepping
through. In SOD16 this padding *was* executed, and it cost 17% of all
dispatches (`CV8.md` §1.2).

A `DOES>` word instead begins:

```
46 <call-hi> <call-lo> 00 00 00 00 00
^^ DODOES    ^^^^^^^^^^^ the DOES> tail
<parameter field>
```

`DODOES` pushes the aligned parameter-field address onto the **return**
stack — which is where the tail's leading `R>` expects it — and jumps to
the tail.

---

## 5. Image layout

```
+-------------------------+
| header (§5.1)           |
+-------------------------+
| prologue, 8 + 5 cells   |  offset 0: call COLD - the entry point
|                         |  offset 3: call WARM
|                         |  offset 8: the five locals cells (7.3)
+-------------------------+
| word 0: link, name, body|  the OLDEST word first
| word 1: ...             |
| ...                     |
+-------------------------+
```

Each word is three fields with nothing padded (Iteration 244):

```
[ link: 1-3 bytes, the distance back to the previous name field in
        the same thread, tag byte LAST                             ]
[ name: count byte (bit 7 set, bit 6 immediate, bit 5 inline)
        + characters                                               ]
[ body: CV8 bytes                                                  ]
```

The link is read backward from the name field, so the tag is the
first byte read:

| tag at nfa-1 | length | distance |
|---|---|---|
| `0xxxxxxx` | 1 | the tag, 0-127 |
| `10xxxxxx` | 2 | `(tag & 0x3F) << 8 \| [nfa-2]` |
| `11xxxxxx` | 3 | `(tag & 0x3F) << 16 \| [nfa-2] << 8 \| [nfa-3]` |

A distance of 0 ends the thread. `kernel.4`'s `PREV-NFA` decodes it,
`HEADER` and `cross.4`'s `"HEADER` lay it down, and nothing in the
engine reads it. `>NAME` still scans back from the body for the count
byte, which names being 7-bit makes unambiguous.

**A data body is the one thing aligned**: `[DOVAR or DODOES][three
bytes][pad][parameter field]`, with the parameter field at
`align(xt + 4)`. That is what `>BODY`, `CREATE`, the engine's `DOVAR`
and `DODOES`, and both compilers' `VAR@`/`VAR!` peepholes compute, and
all of them must agree. Code that lays down cells after a colon
definition must `ALIGN` first, since `HERE` is not aligned there
(`BUILTIN` in `shell.4` and `WORDLIST` in `extend.4` do).

Measured when this layout replaced padded headers: the 64-bit kernel
from 11,638 to 8,094 bytes and the shell image from 69,518 to 58,657;
at 32-bit, 8,674 to 7,486 and 55,382 to 53,461. The gain is mostly a
64-bit one, since a padded cell there is 8 bytes. The layout was
first built as `attic/cv8b.4` for translated images.

### 5.1 Header

| offset | size | contents |
|---|---|---|
| 0 | 4 | magic `CV8` + `'0'+SCALE` — `CV80` today |
| 4 | 1 | cell width in bytes (8 or 4) |
| 5 | 1 | `'L'` if specialised opcodes are used, else 0 |
| 6 | 1 | **format version** (5); the engine runs only its own |
| 7 | 1 | **feature bitmap**: 1 varcall, 2 varslot, 4 spec, 8 lit64 |
| 8 | cell | thread **count** *T* (32 — the hashed word list) |
| +cell | *T*·cell | the thread heads, `START`-relative |
| … | cell | number of `DOES>` tail entries, *N* |
| … | 2·*N*·cell | the tail entries: (word number, byte offset) pairs — **skipped**, see below; both compilers write *N* = 0 |

The engine checks the first five bytes exactly - name, scale and cell
width - so a 32-bit image cannot be loaded by a 64-bit engine. Then it
checks that the image's **version is not newer** than its own and that
its **required features are a subset** of what the engine implements.

That is the point of the bitmap: a feature added later sets a bit rather
than breaking the format, older images keep working on newer engines,
and an older engine refuses a newer image with a clear message instead
of misreading it. Before Iteration 194 the magic was compared byte for
byte, so any change to the format invalidated every image.

**Version 5** (Iteration 259) made slot operands relative to themselves.

**Version 4** (Iteration 258) added `BRANCH8`/`?BRANCH8` after the folded
band and changed the loop, `(POSTPONE)` and string operand forms.

**Version 3** (Iteration 247) renumbered the synthetic opcodes (§3.2).
The same byte means different things in versions 2 and 3, and each
engine ran the other's image and crashed; since 247 an engine refuses
any version but its own, where before it refused only newer ones.

**Version 2** (Iteration 243) moved the five locals cells out of the
header and into the image, at offset 8. In version 1 the engine read
them once at load, so a word using locals could only run in an image
that had been saved and reloaded - which was never a problem while the
shell was compiled on the cell engine and translated, and broke the
first native build at the first `BUILTIN` registration. Now `kernel.4`
reserves the cells, `shadow.4` fills them in when it loads, and they
are saved like any other part of the image. A version-1 engine refuses
a version-2 image.

The byte-header bit (16) is gone: since Iteration 244 byte-granular
headers are the only layout, and the engine never reads a link, so
there is nothing for it to refuse. Scale 0 is recorded in the magic,
which is what makes an older engine refuse these images.

### 5.2 Loading

Loading is: read the header, read the rest of the file into memory at
`base`, done. There is **no relocation pass**. Every call, branch and
slot operand is an offset, so the image works wherever it lands.

The `wordtab` walk still present in `vm-lab.c` exists only for the
`ENC=1` (SOD16 table) configuration. A CV8-only engine can delete it,
along with the `DOES>` tail entries in the header, since `DODOES` carries
its target inline.

---

## 6. The engine

### 6.1 VM registers

```c
UNS64 ip;     /* instruction pointer, into the image        */
UNS64 rp;     /* return stack pointer, grows down           */
UNS64 dsp;    /* data stack pointer, grows down             */
UNS64 tos;    /* top of data stack, cached (64-bit builds)  */
UNS64 cbase;  /* image base; call targets are cbase + v<<S  */
UNS64 t;      /* scratch                                    */
```

**These must be locals of the interpreter function, not statics.** As
statics they cost about 20% of every workload, because a store through a
cell pointer may alias them under C's rules, so the compiler reloads `ip`
and `rp` around every dispatch. This was the single largest speed finding
of the whole investigation and applies equally to the cell engine, where
it is now fixed (`relf.c`, Iteration 189a).

`dsp` points at the **second** stack item when TOS caching is on; the top
is in `tos`. `SP@`, `DEPTH` and the syscall primitives therefore spill
`tos` first, so Forth code sees the same stack it always did.

### 6.2 Dispatch

```c
#define NEXT() do {                                            \
    t = (UNS64)(INT64)(int8_t)BYTE(ip);   /* sign-extended */  \
    if ((INT64)t >= 0) { ip += 1; goto *dispatch[t]; }         \
    goto do_call;                                              \
} while (0)
```

`NEXT()` is written at the end of **every handler**, not once at the top
of a loop. That is standard threaded-code practice: each handler gets its
own indirect branch, so the branch predictor can learn per-opcode
patterns rather than aliasing everything onto one site. It requires GCC's
computed-goto extension (`&&label`), which `GOALS.md` already accepts.

The call path is the one thing **not** replicated:

```c
do_call:
    t = ((t & 0x7F) << 8) | BYTE(ip + 1); ip += 2;
    RPUSH(ip);                       /* return address       */
    ip = cbase + (t << SCALE);
    NEXT();
```

Sharing it saves 5.7 KB of engine code on x86-64 and 3.7 KB on i386, at
no measured speed cost — the call's own dispatch is not the part
prediction cares about.

### 6.3 A handler

Handlers are what you would write by hand:

```c
L_plus:  tos += NOS; dsp += CELL_BYTES; NEXT();
L_exit:  ip = RS; rp += CELL_BYTES; NEXT();
L_lit8:  PUSHT(BYTE(ip)); ip += 1; NEXT();
L_dovar: PUSHT((ip + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1));
         ip = RS; rp += CELL_BYTES; NEXT();
```

There are 124 of them in the full `SPEC` build. Each compiles to a median
of 50 bytes, most of which is its copy of `NEXT()`.

### 6.4 Folded `primitive;EXIT`

A folded opcode is the primitive's body followed by a return:

```c
LX_plus: tos += NOS; dsp += CELL_BYTES;
         ip = RS; rp += CELL_BYTES; NEXT();
```

These are generated mechanically from the ordinary bodies
(`tools/lab/gen-fold.py`), so there is no second implementation to keep
in step. **The compiler must not fold when anything can branch to the
`EXIT`** — a loop or `IF` whose target is the final `EXIT`. The
translator's `fold_exit()` is the specification: it collects every branch
target first and refuses to fold across one.

Folding is worth about 20%. `EXIT` was 17% of all dispatches, and about
80% of `EXIT`s followed a primitive, because the kernel is full of
two-operation colon words.

### 6.5 Stack limits

Both stacks live at the top of the same memory block as the image, and
since Iteration 253 each has an unreadable GUARD page below it instead
of a compare on every push (`GUARD`, on by default):

```
[rfloor, top)            return stack
[rfloor - page, rfloor)  guard: "return stack overflow"
[... , rfloor - page)    data stack; the empty stack is two cells
                         below the return stack's guard
[dfloor, dfloor + page)  guard: "data stack overflow", and the
                         dictionary growing up into the stacks
```

A `SIGSEGV` handler reports which guard was hit and exits with status
70, as the compares did. Two consequences worth knowing. Every push is
caught at the push itself, including `SPILL()`, which the compares left
to the next checked push. And the return stack's guard sits two cells
above the empty data stack, so reading two or more cells past empty -
an underflow - faults too; the first thing it found was a word in
`shell.4` that took one cell too many from its caller's stack.

`-DGUARD=0` restores the compares, for a target without an MMU:
`dsp_limit` and `rp_limit` copied into locals on entry, and
`stack_fault()` marked `noreturn, cold` so they stay off the hot path.
Measured: the compares cost 3-6% at 64-bit, nothing measurable at 32.

---

## 7. The specialised opcodes

These are the difference between "2x faster" and "5x faster" on shell
code. Each was chosen from a per-address execution profile
(`tools/lab/patterns.py`), not from intuition.

### 7.1 Small integers and immediates

```
0x60 push 0      0x61 push 1      0x62 push -1
0x78 ADDI n      0x79 ADDI n;EXIT
0x7A EQI n       0x7B EQI n;EXIT
```

`LIT 0` alone is 556 static sites. `-1` had been a 5-byte `LIT32`,
because `LIT8` is unsigned. `ADDI`/`EQI` are Lua 5.4's `OP_ADDI`/`OP_EQI`
and are honestly marginal — measured within noise, kept only because they
are two handlers and save 400 bytes.

### 7.2 Variable access

```
0x63 VAR@ slot16      0x64 VAR! slot16
```

The slot is the address of the variable's **parameter field**, not its
body, given as a signed offset from the operand's own first byte:
`operand + v`. Two bytes carry 15 bits (±16 KB), three with the top bit
set carry 23 (±4 MB); `SLOT,` refuses anything further. This replaces
call/`DOVAR`/`@` with one dispatch - the JVM's `getstatic`/`putstatic`.

Until Iteration 259 the offset was from the image base, like a call's.
Code usually follows the variables it uses by a few hundred bytes, but
half of a 66 KB shell image lies past the 32 KB the short form reached
from the base, so 2,209 of 4,380 slots were three bytes. Counted from the
operand, 3,843 are two bytes; the 536 left are mostly kernel variables
used from the shell. Calls stay base-relative: measured, that is better
for them (§ "Things that will bite you" and PROGRESS.md 258).

### 7.3 Locals

```
0x65 LSAVE slot   0x66 LRESTORE slot   0x67 L! slot   0x68 LZERO slot
```

This is the largest single win: **0.41–0.54 of CV8's time on its own**,
about two-thirds of everything the specialisations buy.

Forth locals in `locals.4` are shallow-bound global `VARIABLE`s: on
entry each is saved to a save stack, on exit restored. The Forth
`LSAVE` is 23 operations and nine calls, and the profile showed the
`LSAVE-SP` variable was the hottest call target in the entire shell, at
45M calls.

The opcodes do the same thing in one dispatch, on **the same
Forth-visible save stack**. The engine finds it through the five cells at
image offset 8 (header cells before format version 2):

| cell | contents |
|---|---|
| 0 | offset of `LSAVE-SP`'s parameter field |
| 1 | offset of `LSAVE-STACK`'s parameter field |
| 2 | the value of `LSAVE-MAX` |
| 3 | offset of `LSAVE`'s body (fallback) |
| 4 | offset of `LRESTORE`'s body (fallback) |

**Deoptimisation.** Whenever the Forth version would take its `ABORT"`
path — save-stack overflow, underflow, or no buffer allocated — the
opcode pushes the slot's `START`-relative offset exactly as `LIT` did,
and calls the Forth word. So the rare and error paths keep their original
behaviour and messages, and only the common case is specialised. That is
PEP 659's shape, and it is why specialising a single instruction is safe:
de-optimisation can never land in the middle of a region.

This is also the design's one genuine wart: the engine knows the layout
of a Forth data structure. §9 says what to do about it.

### 7.4 Tiny kernel words

```
0x69..0x77  0=  -  <>  0<  >  2DUP  2DROP  CHAR+  1+
            CELL+  CELLS  1-  INVERT  COUNT  ALIGNED
```

These are colon words in `kernel.4`, two or three operations long, that
together took 6.4% of all dispatches as calls. As opcodes they cost one
byte instead of a two-byte call plus a body plus a return.

They are declared in `kernel.4` with `OPCODE` rather than defined in
Forth, exactly as the translator's notes suggested a phase-3 system
would: the engine is the definition, and `COMPILE,` inlines the byte.
The translator used to substitute one only where a compiled body
matched the engine's implementation.

---

## 8. Building an image today

Since Iteration 243 nothing is translated. Two Forth compilers emit
CV8 directly, and they are twins that must agree:

- **`cross.4`**, the cross-compiler, runs on the committed `kernel.img`
  and compiles `kernel.4` into a new one. Its PART 4 emits against the
  target space (`C,-T`, `THERE`).
- **`kernel.4`'s own compiler** (`LIT,`, `CALL,`, `COMPILE,`,
  `EXIT,`, `NO-PEEP` and the rest) compiles everything loaded at run
  time: `extend.4`, `pool.4`, `shadow.4`, `save-system.4`, `shell.4`.

```
relf kernel.img  + extend.4 + cross.4   -> kernel.img       (a fixpoint)
relf kernel.img  + extend.4 + pool.4 + shadow.4 + save-system.4
                 + shell.4, SAVE-SYSTEM -> kernel-shell.img
```

The specialised opcodes of section 7 are emitted as follows:

- **Constants** `0`, `1` and `-1` come straight from `LIT,`.
- **`ADDI`, `EQI`, `VAR@` and `VAR!`** are peepholes. `LIT,` and
  `CALL,` remember where they started. When `COMPILE,` of `+`, `=`,
  `@` or `!` completes a pattern, it rewinds `HERE` over the first
  half. `NO-PEEP` is called by everything that makes `HERE` a branch
  target, so nothing can jump between the halves.
- **Folding** is done by `EXIT,` at `;`. It folds the last operation
  and the `EXIT` into one opcode, under the same rule.
- **The fifteen tiny words** are declared in `kernel.4` with
  `OPCODE`, like primitives. `COMPILE,` inlines them, and the engine
  defines what they do.
- **The locals opcodes** are emitted by `shadow.4`'s `L-EMIT`.

The translator (`attic/tools/layout.py`) was the specification these
were written from, and the measurement that retired it is in
`PROGRESS.md`: the natively compiled shell runs at 0.99-1.02 of the
translated one's time on every workload in `tests/bench-vm`.

---

## 9. What a production CV8 engine should do differently

The lab engine carries four encodings at once and is generated in
places. A committed engine should:

1. **Keep one encoding.** Delete `ENC=1`/`ENC=2`, the `wordtab` walk and
   the `DOES>` tail header entries.
2. **Generate the opcode list from one place.** `kernel.4` should be the
   single source of truth for primitive numbering, the fold set and the
   specialised set, emitting both the engine's dispatch table and the
   compiler's emitter. Two hand-maintained lists drifting apart is the
   real risk in this design, more than any individual opcode.
3. **Make the locals opcodes real primitives.** Define `LSAVE` and
   `LRESTORE` as primitives in `kernel.4` and delete the Forth versions.
   Then there is no dual implementation, no fallback, and no locals
   header — the engine stops knowing about `locals.4`'s internals, and
   `locals.4` gets shorter. The retrofit above only exists because I was
   translating an existing image.
4. **Reserve the escape opcode now.** Only four slots are free.
5. **Compile with `-O2 -fcf-protection=none`**, not `-Os`. `-Os` merges
   the dispatch tails and made a test core 88% slower.

---

## 10. Things that will bite you

- **Branch offsets are from the operand, not past it** (§3.3).
- **Never execute alignment padding.** SOD16 lost 17% of dispatches to
  `NOOP`s before data bodies.
- **Nothing in code is aligned** since Iteration 258: not loop operands
  (which used to be cells, padded with NOOPs that executed once per
  loop), not `(POSTPONE)`'s xt, not strings. Data bodies still are.
- **`LIT8` is unsigned.** `-1` needs `LIT32` unless the `0x62` opcode is
  enabled. Values outside int32 need `LIT64`: until Iteration 194 they
  were silently masked to 32 bits, so `$123456789ABC` evaluated
  differently under CV8 than under the cell engine. The translator now
  emits `LIT64`; anything that generates CV8 code must do the same.
- **A folded `EXIT` must not be a branch target** (§6.4).
- **Parameter fields must be computed one way everywhere**:
  `align(xt + 4)`. Four defects in the byte-header work were two places
  computing the same address differently (PROGRESS.md 213, 244).
- **The image is not byte-reproducible across dumps.** It carries 16
  variables holding live-session absolute addresses (`START`, `S0`,
  `LAST`, …). `COLD` resets them, so every image boots, but two dumps of
  the same system differ. SOD16's images had this too; `SS-SCRUB` in
  `save-system.4` is the real fix.
- **`tests/shell/run-forth` fails on every translated image**, because it
  compiles a new colon definition at run time. That is the phase-3 gap,
  not a bug in the encoding.
