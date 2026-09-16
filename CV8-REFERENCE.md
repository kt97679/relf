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
scale digit, so a 64-bit image reads `CV83`.

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

`SCALE` is 3 on a 64-bit build and 2 on a 32-bit build. This is the
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
(`VARSLOT`): one leading bit selects a 15-bit or 23-bit payload. Without
it slots were a fixed 16 bits, so **variables had to live in the first
512 KB while code could span 32 MB** - an asymmetry that would have
failed silently in a larger system.

The engine loads the byte **sign-extended**, so "is this an opcode?" is a
branch on sign with no comparison (`SIGNTEST`, on by default except on
32-bit ARM; see `XARCH.md` §3).

### 3.2 Opcode map

Nothing in this table is a constant in the source. Every boundary is
derived from the number of `PRIMITIVE` lines in `kernel.4`, in five
places that must agree — `tools/sod16.py`, `tools/lab/gen-fold.py`,
`tools/lab/gen-tos.py`, `tools/layout.py` and `cv8.4`. They were
written out by hand until Iteration 214, and adding one primitive then
made the image encode an opcode the engine decoded as something else,
with no build error: a return stack overflow in one stage and a
corrupted heap in another.

With 67 primitives and the escaped band on, which is the default:

| range | meaning |
|---|---|
| `0x00`–`0x22` | the 35 **direct** primitives, in `PRIMITIVE` order |
| `0x23`–`0x42` | vacated — the 32 escaped primitives live behind `ESC` |
| `0x43` | `LIT32` — 4-byte signed operand |
| `0x44` | `DOVAR` — data body prologue |
| `0x45` | `DODOES` — `DOES>` body prologue |
| `0x46` | `LIT8` — 1-byte unsigned operand |
| `0x47` | `LIT8;EXIT` |
| `0x48`–`0x5E` | folded `primitive;EXIT`, in `--fold-set` order (23 used) |
| `0x5F`–`0x60` | free |
| `0x61`–`0x7C` | specialised opcodes (§7) — 28 of them |
| `0x7D` | `LIT64` — a full cell, little-endian |
| `0x7E` | `ESC` + a selector byte: one of the 32 OS/libc primitives |
| `0x7F` | free |
| `0x80`–`0xFF` | first byte of a two- or three-byte call |

Two things moved and are worth knowing about. The specialised band was
at `0x60`; a 69th primitive pushed the folded band onto it, so the last
folded opcode and `lit0` became the same byte, and the whole band moved
up one. `ESC` was `0x7D`.

Free: `0x5F`, `0x60`, `0x7F`, plus the 32 vacated at `0x23`–`0x42`.
The vacated ones are NOT usable by a new primitive — primitives are
numbered by position from 0, so a 68th would land at `0x23` and push
everything above it up. They are reachable only by something numbered
explicitly, which is why the folded band's headroom is the two at
`0x5F`–`0x60` and not thirty-four.

The numbers above are what `kernel.4` and `tools/sod16.py` produce
today, and they will move again the moment a primitive is added or
`--fold-set` changes. To print the current map rather than trust this
table, derive it the way the tools do: 35 direct primitives, then
`len(prims)+0..4`, then `len(prims)+5` for the folded band.

The escaped band is what keeps that from being tight. The 32 OS/libc
primitives — `BYE`, the file words, `FORK`, `EXECVE` and the rest — are
3.2% of static sites and 0.006% of dispatches, so putting them behind
`ESC` costs a byte each where it does not matter and frees 32 opcodes
where it does. They are **contiguous at the end** of `kernel.4`'s list,
which is what lets the engine compute the partition instead of carrying
a table: selector *t* is the primitive at `NDIRECT + t`.

`--no-escape` builds the unescaped numbering, where all 67 primitives
are direct at `0x00`–`0x42`; an engine built without the band refuses
such an image rather than misreading it.

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
| `ADDI`, `EQI` | 1 byte, signed −128..127 |
| specialised slot ops | 2 bytes, a scaled offset like a call |
| `(LOOP)`, `(POSTPONE)`, inline strings | **cell-sized and cell-aligned**, unchanged from the cell image |

Two conventions matter when writing a compiler:

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

A call names a **byte offset from the image base, divided by 2^SCALE**.
It does not name a word number, so there is no word table, no load-time
chain walk and no xt-to-index map. This is HotSpot's compressed-oops
decode (`base + (narrow << shift)`) and, before it, 8086 Forth's
segment threading.

Consequences:

- **Every call target must be 2^SCALE aligned.** Word bodies already are,
  because the name field is padded to a cell.
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
| call reach, near form | 128 KB | 64 KB | format |
| call reach, far form | **32 MB** | 16 MB | format |
| slot reach, near form | 256 KB | 128 KB | format |
| slot reach, far form | **64 MB** | 32 MB | format |
| literal width | full cell | full cell | format |
| branch, within one word | ±32 KB | ±32 KB | format |
| opcode space | 128 + a reserved second bank | same | format |
| `DOES>` tails (`MAX_TAILS`) | 16 | 16 | build parameter |

`MEMSIZE` covers the image, all runtime dictionary growth and the
stacks, so it is the **first** ceiling a growing system meets. It was
1 MB until Iteration 194, which made the 32 MB call reach academic. It
is a plain parameter: every reference in an image is relative, so
raising it breaks nothing.

---

## 4. Worked examples

Real bytes from `spec-64.img`. Word bodies are cell-aligned, so the
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

Each word is laid out exactly as the cell image lays it out, and this is
deliberate: `FIND`, `>NAME`, the link walk and `save-system.4` are
unchanged.

```
[ link: one cell, relative offset to the previous word ]
[ name: count byte + characters, padded to a cell      ]
[ body: CV8 bytes, padded to a cell                    ]
```

**Headers and names are not compressed.** In the 64-bit shell image they
are 23 KB of 66 KB — 35%. That is now the largest single density lever
left, and it is a kernel question, not a VM one: `FIND` compares names
cell by cell.

### 5.1 Header

| offset | size | contents |
|---|---|---|
| 0 | 4 | magic `CV8` + `'0'+SCALE` — e.g. `CV83` |
| 4 | 1 | cell width in bytes (8 or 4) |
| 5 | 1 | `'L'` if specialised opcodes are used, else 0 |
| 6 | 1 | **format version** (2) |
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

**Version 2** (Iteration 243) moved the five locals cells out of the
header and into the image, at offset 8. In version 1 the engine read
them once at load, so a word using locals could only run in an image
that had been saved and reloaded - which was never a problem while the
shell was compiled on the cell engine and translated, and broke the
first native build at the first `BUILTIN` registration. Now `kernel.4`
reserves the cells, `shadow.4` fills them in when it loads, and they
are saved like any other part of the image. A version-1 engine refuses
a version-2 image.

The byte-header bit (16) is gone with the byte-header layout; see
`attic/README.md`.

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

The data and return stacks have floors checked on push. Both live inside
the same memory block as the image; `dsp_limit` and `rp_limit` are
copied into locals on entry, and `stack_fault()` is marked
`noreturn, cold` so the checks stay off the hot path.

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

`slot16` is scaled exactly like a call, so the address is
`base + (v << SCALE)` — here pointing at the **parameter field**, not the
body. This replaces call/`DOVAR`/`@` with one dispatch. This is the JVM's
`getstatic`/`putstatic`.

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
- **`(LOOP)` operands are still cell-aligned**, so NOOP padding before
  them *is* executed, once per loop iteration. The shell barely uses
  `DO` loops; a kernel that did should make `(LOOP)` read an `ALIGNED`
  operand.
- **`LIT8` is unsigned.** `-1` needs `LIT32` unless the `0x62` opcode is
  enabled. Values outside int32 need `LIT64`: until Iteration 194 they
  were silently masked to 32 bits, so `$123456789ABC` evaluated
  differently under CV8 than under the cell engine. The translator now
  emits `LIT64`; anything that generates CV8 code must do the same.
- **A folded `EXIT` must not be a branch target** (§6.4).
- **Call targets must be aligned** to 2^SCALE; data bodies only are
  because `DOVAR` made them so.
- **The image is not byte-reproducible across dumps.** It carries 16
  variables holding live-session absolute addresses (`START`, `S0`,
  `LAST`, …). `COLD` resets them, so every image boots, but two dumps of
  the same system differ. SOD16's images had this too; `SS-SCRUB` in
  `save-system.4` is the real fix.
- **`tests/shell/run-forth` fails on every translated image**, because it
  compiles a new colon definition at run time. That is the phase-3 gap,
  not a bug in the encoding.
