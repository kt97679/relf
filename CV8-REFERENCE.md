# CV8-REFERENCE.md — the CV8 format and engine, in detail

This is the reference: what a CV8 image contains, byte by byte, and what
the engine does with it. `CV8.md` argues *why* this design; `VM-SURVEY.md`
covers the specialised opcodes and where they were borrowed from;
`XARCH.md` covers other architectures. This file assumes you want to
implement or debug it.

Everything here describes the working lab implementation:
`tools/lab/vm-lab.c` (`ENC=3`), `tools/sod16.py` and
`tools/sod16-layout.py`. Byte values quoted below are from a real image
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

## 2. The byte stream

### 2.1 The fundamental test

```
b = ip[0]
b < 0x80  ->  opcode b, one byte, ip += 1
b >= 0x80 ->  call: v = ((b & 0x7F) << 8) | ip[1], ip += 2
             target = base + (v << SCALE)
```

`SCALE` is 3 on a 64-bit build and 2 on a 32-bit build. This is the
whole decoder. There is no length table and no prefix.

The engine loads the byte **sign-extended**, so "is this an opcode?" is a
branch on sign with no comparison (`SIGNTEST`, on by default except on
32-bit ARM; see `XARCH.md` §3).

### 2.2 Opcode map

| range | meaning |
|---|---|
| `0x00`–`0x43` | the 68 primitives of `kernel.4`, in `PRIMITIVE` order |
| `0x44` | `LIT32` — 4-byte signed operand |
| `0x45` | `DOVAR` — data body prologue |
| `0x46` | `DODOES` — `DOES>` body prologue |
| `0x47` | `LIT8` — 1-byte unsigned operand |
| `0x48` | `LIT8;EXIT` |
| `0x49`–`0x5F` | folded `primitive;EXIT`, in `--fold-set` order (23 used) |
| `0x60`–`0x7B` | specialised opcodes (§6) |
| `0x7C`–`0x7F` | **free** (4 slots; one is reserved for `FARCALL`) |
| `0x80`–`0xFF` | first byte of a two-byte call |

The primitive numbering is not a CV8 invention: it is the order words
appear as `PRIMITIVE` lines in `kernel.4`, the same numbering the cell
engine uses. `LIT` is primitive 2 and keeps a 2-byte operand.

### 2.3 Operands

| form | operand |
|---|---|
| `LIT8` | 1 byte, unsigned 0–255 |
| `LIT` | 2 bytes, unsigned little-endian |
| `LIT32` | 4 bytes, signed little-endian, sign-extended to a cell |
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

### 2.4 Calls, and the reach limit

A call names a **byte offset from the image base, divided by 2^SCALE**.
It does not name a word number, so there is no word table, no load-time
chain walk and no xt-to-index map. This is HotSpot's compressed-oops
decode (`base + (narrow << shift)`) and, before it, 8086 Forth's
segment threading.

Consequences:

- **Every call target must be 2^SCALE aligned.** Word bodies already are,
  because the name field is padded to a cell.
- **Reach is 32,767 × 2^SCALE**: 256 KB on 64-bit, 128 KB on 32-bit.
  Today's shell images are 66 KB and 53 KB.
- **The limit is bytes, not words.** At today's average of ~60 bytes per
  entry that is roughly 4,300 words (64-bit) or 2,700 (32-bit).
- `COMPILE,` becomes arithmetic: `xt START @ - SCALE RSHIFT 0x8000 OR`.

When the image outgrows the window, in order: raise 32-bit `SCALE` to 3
(costs ~2 KB of padding, doubles reach), then add a `FARCALL` opcode with
a 3-byte operand in one of the free slots.

---

## 3. Worked examples

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

## 4. Image layout

```
+-------------------------+
| header (§4.1)           |
+-------------------------+
| prologue, 40 bytes      |  the boot call; entry point of the image
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

### 4.1 Header

| offset | size | contents |
|---|---|---|
| 0 | 4 | magic `CV8` + `'0'+SCALE` — e.g. `CV83` |
| 4 | 1 | cell width in bytes (8 or 4) |
| 5 | 1 | `'L'` if specialised opcodes are used, else 0 |
| 6 | 2 | zero |
| 8 | cell | offset of the newest word's name field (the dictionary head) |
| +cell | cell | number of `DOES>` tail entries, *N* |
| … | 2·*N*·cell | the tail entries: (word number, byte offset) pairs |
| … | 5·cell | **SPEC only**: the locals header (§6.3) |

The engine rejects an image whose magic does not match its build exactly,
including the cell width and the `SCALE`, so a 32-bit image cannot be
loaded by a 64-bit engine.

A `SPEC` image **always** carries the five locals cells, zero-filled when
the dictionary had no `locals.4`. That keeps the format independent of
what was loaded; a bare kernel image and a shell image differ only in
content.

### 4.2 Loading

Loading is: read the header, read the rest of the file into memory at
`base`, done. There is **no relocation pass**. Every call, branch and
slot operand is an offset, so the image works wherever it lands.

The `wordtab` walk still present in `vm-lab.c` exists only for the
`ENC=1` (SOD16 table) configuration. A CV8-only engine can delete it,
along with the `DOES>` tail entries in the header, since `DODOES` carries
its target inline.

---

## 5. The engine

### 5.1 VM registers

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

### 5.2 Dispatch

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

### 5.3 A handler

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

### 5.4 Folded `primitive;EXIT`

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

### 5.5 Stack limits

The data and return stacks have floors checked on push. Both live inside
the same memory block as the image; `dsp_limit` and `rp_limit` are
copied into locals on entry, and `stack_fault()` is marked
`noreturn, cold` so the checks stay off the hot path.

---

## 6. The specialised opcodes

These are the difference between "2x faster" and "5x faster" on shell
code. Each was chosen from a per-address execution profile
(`tools/lab/patterns.py`), not from intuition.

### 6.1 Small integers and immediates

```
0x60 push 0      0x61 push 1      0x62 push -1
0x78 ADDI n      0x79 ADDI n;EXIT
0x7A EQI n       0x7B EQI n;EXIT
```

`LIT 0` alone is 556 static sites. `-1` had been a 5-byte `LIT32`,
because `LIT8` is unsigned. `ADDI`/`EQI` are Lua 5.4's `OP_ADDI`/`OP_EQI`
and are honestly marginal — measured within noise, kept only because they
are two handlers and save 400 bytes.

### 6.2 Variable access

```
0x63 VAR@ slot16      0x64 VAR! slot16
```

`slot16` is scaled exactly like a call, so the address is
`base + (v << SCALE)` — here pointing at the **parameter field**, not the
body. This replaces call/`DOVAR`/`@` with one dispatch. This is the JVM's
`getstatic`/`putstatic`.

### 6.3 Locals

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
Forth-visible save stack**. The engine finds it through the five header
cells:

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
of a Forth data structure. §8 says what to do about it.

### 6.4 Tiny kernel words

```
0x69..0x77  0=  -  <>  0<  >  2DUP  2DROP  CHAR+  1+
            CELL+  CELLS  1-  INVERT  COUNT  ALIGNED
```

These are colon words in `kernel.4`, two or three operations long, that
together took 6.4% of all dispatches as calls. As opcodes they cost one
byte instead of a two-byte call plus a body plus a return.

The translator substitutes one **only where the compiled body is exactly
the definition the engine implements**, checked per address, so a
redefinition of the same name is left alone. In a real phase-3 system
this check disappears: you simply declare them `PRIMITIVE` in `kernel.4`
and delete the Forth definitions.

---

## 7. Building an image today

Images are currently **translated** from a cell image, because the Forth
compiler still emits cells. That is the one large piece of work left.

```
relf kernel.img
  + tools/dict-dump-addr.4      -> a text dump of the dictionary
  |
  v
tools/sod16-layout.py           -> decodes every word body, re-lays it
  --v8 --cpt S --dataprims          out in CV8, fixes up every offset
  --fold --fold-set ...             and writes the image
  --spec loc,var,tiny,small,imm
```

`tools/lab/build-cv8.sh` runs the whole matrix and smoke-tests each
engine/image pair against `dash`.

The translator is also the **specification of the compiler's rules**:
`fold_exit()` for folding, `specialise()` for the opcode rewrites,
`layout()` for padding and branch conversion. When phase 3 emits CV8
directly, those three functions are what it must reproduce.

---

## 8. What a production CV8 engine should do differently

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

## 9. Things that will bite you

- **Branch offsets are from the operand, not past it** (§2.3).
- **Never execute alignment padding.** SOD16 lost 17% of dispatches to
  `NOOP`s before data bodies.
- **`(LOOP)` operands are still cell-aligned**, so NOOP padding before
  them *is* executed, once per loop iteration. The shell barely uses
  `DO` loops; a kernel that did should make `(LOOP)` read an `ALIGNED`
  operand.
- **`LIT8` is unsigned.** `-1` needs `LIT32` unless the `0x62` opcode is
  enabled.
- **A folded `EXIT` must not be a branch target** (§5.4).
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
