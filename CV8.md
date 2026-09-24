# CV8.md — the engine and its image format

A RelF image is a byte stream, and `cv8.c` is the engine that runs it.
This file is both halves of that story:

- **Part I, the reference**: what every byte means, how an image is
  laid out, and what the engine does with it. Every fact in it was
  checked against the sources, and the examples are real bytes, dumped
  from `kernel.img` at Iteration 491.
- **Part II, the reasons**: the decisions behind the format, what each
  was measured to buy, and how they hold on other architectures.

The sources of truth are `cv8.c` (the engine), `kernel.4` (the primitive
list, the fold list, the specialised opcodes and the run-time compiler)
and `cross.4` (the cross-compiler). Where this file and they disagree,
they are right and this file has a bug. How each part came to be is in
`PROGRESS.md`, cited here by iteration number.

---

# Part I — Reference

## 1. The idea

An image holds **one byte per operation**. A call is two or three bytes
holding the target's **byte offset from the image base**. Nothing in an
image is a pointer, so an image is position-independent, and the same
image runs on every machine of its cell width: `kernel.img` on 64-bit
hosts, `kernel32.img` on 32-bit ones. The engine executes the byte
stream **in place**; nothing is translated or relocated when an image
loads.

## 2. The byte stream

### 2.1 Decoding

```
b = ip[0]
b <  0x80        opcode b, one byte
b =  10xxxxxx    call, two bytes:   v = (b & 0x3F) << 8  | ip[1]
b =  11xxxxxx    call, three bytes: v = (b & 0x3F) << 16 | ip[1] << 8 | ip[2]
                 the target is image base + v
```

That is the whole decoder: no length table, no prefix. The engine does
not test the top bit. It dispatches every byte through a 256-entry
table whose upper half all points at one shared call path:

```c
#define NEXT() do { t = BYTE(ip); ip += 1; goto *dtab256[t]; } while (0)

do_call:    /* ip is already past the first byte */
    if (t & 0x40) { t = ((t & 0x3F) << 16) | ((UNS64)BYTE(ip) << 8) | BYTE(ip + 1);
                    ip += 2; }
    else          { t = ((t & 0x3F) << 8) | BYTE(ip); ip += 1; }
    RPUSH(ip); ip = cbase + (t << SCALE);
    NEXT();
```

(Profiling hooks, compiled out, are left out here.) `SCALE` is 0 at
both cell widths since Iteration 244, so offsets are plain bytes.

### 2.2 The opcode map

| range | meaning |
|---|---|
| `0x00`–`0x22` | the 35 **direct** primitives, in `kernel.4`'s `PRIMITIVE` order: `NOOP EXIT LIT BRANCH ?BRANCH DROP DUP SWAP ROT OVER C@ @ C! ! AND OR XOR R> >R R@ = U< < + NEGATE LSHIFT RSHIFT UM* UM/MOD D+ TYPE SP@ SP! RP@ RP!` |
| `0x23` | `LIT32`: a 4-byte signed operand |
| `0x24` | `DOVAR`: a data word's body |
| `0x25` | `DODOES`: a `DOES>` word's body |
| `0x26` | `LIT8`: a 1-byte unsigned operand |
| `0x27` | `LIT8;EXIT` |
| `0x28`–`0x3E` | 23 **folded** `primitive;EXIT` opcodes, in the fold list's order: `+ = ! @ LSHIFT RSHIFT C@ C! AND OR XOR LIT < U< OVER DROP DUP SWAP ROT >R R> R@ NEGATE` |
| `0x3F` | `BRANCH8`: a 1-byte signed offset |
| `0x40` | `?BRANCH8`: likewise |
| `0x41`–`0x60` | free: 32 opcodes |
| `0x61`–`0x7C` | 28 **specialised** opcodes (§6) |
| `0x7D` | `LIT64`: a full cell, little-endian |
| `0x7E` | `ESC` and a selector byte: the 62 **escaped** primitives |
| `0x7F` | free |
| `0x80`–`0xBF` | the first byte of a two-byte call |
| `0xC0`–`0xFF` | the first byte of a three-byte call |

Only two numbers in the map are fixed: the specialised band starts at
`0x61`, and `LIT64` and `ESC` sit at `0x7D` and `0x7E`. Everything else
is derived from the count of direct primitives, `NDIRECT`: the
synthetic opcodes (`LIT32` through the folded band and the two short
branches) start at `NSYN = NDIRECT`. So only a new **direct** primitive
moves the map, by one, into the free band; `cv8.c` has a static
assertion and `cross.4` a check (`MAP-FITS?`) that refuse a map whose
branches reach `0x61`.

**The escaped primitives cost no opcode.** They are the OS and libc
interface - files, processes, signals, the terminal, memory
(`MOVE FILL COMPARE SCAN CSTRLEN`) - declared after `ESCAPED` in
`kernel.4`, and selector *n* is the *n*-th of them. There are 256
selectors, and one the engine does not have is reported, not jumped
through. The list, in selector order:

> `BYE OPEN-FILE CLOSE-FILE SYSTEM REPOSITION-FILE FILE-POSITION
> DELETE-FILE FILE-SIZE FORK EXECVE WAITPID PIPE DUP2 GETENV SETENV
> SYS-EXIT CHDIR GETCWD SYS-ARGC SYS-ARG GETPID UNSETENV ALLOCATE FREE
> RESIZE GETPWHOME GETFSIZE SETFSIZE READ WRITE POLL RAW-MODE MOVE FILL
> COMPARE SCAN CSTRLEN ISATTY OPEN-DIR READ-DIR CLOSE-DIR ACCESS KILL
> UMASK CPU-TIMES SIGNAL-ACTION SIGNALS-PENDING TERM-RAW TERM-RESTORE
> FILE-KIND GETRLIMIT SETRLIMIT WAIT-NOHANG GETPPID ENV-AT SETPGID
> TCSETPGRP TCGETPGRP WAIT-JOB FILE-MODE LOCAL-TIME DUP-FROM`

**Four places must agree on these numbers**, and a mismatch is silent -
the image encodes one operation and the engine decodes another:
`cv8.c`'s `direct_prims[]`, `escaped_prims[]`, `NDIRECT` and `NESC`;
`kernel.4`'s `PRIMITIVE` and `OPCODE` order and the fixed numbers in its
compiler; `cross.4`'s PART 4 constants; and `shadow.4`'s locals
opcodes. `cv8.c` checks its two counts against its tables when it is
compiled.

**Adding a primitive.** An OS or libc one is escaped: append its
`PRIMITIVE` line at the end of `kernel.4`'s list, append its handler to
`escaped_prims[]` and raise `NESC`. Nothing moves. Then rebuild the
kernels deliberately - `make images IMAGES_FORCE=1` - and check that
they reproduce themselves with `make check-images` (Iteration 486 did
exactly this for `DUP-FROM`). A hot primitive is direct: add it before
`ESCAPED` in `kernel.4` and at the same position in `direct_prims[]`,
and raise `NDIRECT`; that moves the synthetic opcodes up by one.

### 2.3 Operands

| form | operand |
|---|---|
| `LIT8` | 1 byte, unsigned 0–255 |
| `LIT` | 2 bytes, unsigned, little-endian |
| `LIT32` | 4 bytes, signed, little-endian, sign-extended to a cell |
| `LIT64` | a cell's bytes, little-endian: values outside 32 bits |
| `BRANCH`, `?BRANCH` | 2 bytes, signed, little-endian, **from the operand itself** |
| `BRANCH8`, `?BRANCH8` | 1 byte, signed, from the operand |
| `ADDI`, `EQI` | 1 byte, signed −128..127 |
| slot operands (§6) | 2 or 3 bytes, big-endian, signed, from the operand |
| `(LOOP)`, `(+LOOP)` | none: the call is followed by a branch back to the loop's start |
| `(?DO)` | none: the call is followed by a 16-bit branch to the loop's exit |
| `(POSTPONE)` | 3 bytes, big-endian: the xt as an offset from `START` |
| inline strings | a count byte and the text, unpadded |

Rules a compiler must keep:

- **A branch offset counts from the operand's own position**, not from
  the byte after it: `ip += (int16_t)LD16(ip)`. Getting this wrong makes
  an image that runs, then jumps two bytes off.
- **Backward branches take `BRANCH8`/`?BRANCH8` when the offset fits**,
  since the distance is known when they are compiled. Forward branches
  are always 16-bit, patched when resolved.
- **Loops decide by where they return.** `(LOOP)` and `(+LOOP)` return
  into the branch after them to go round again, and past it when done;
  `(?DO)` returns into its forward branch for an empty loop. `LEAVE` is
  `UNLOOP` and a forward branch.
- **Nothing in code is aligned** (Iteration 258). Multi-byte operands
  are read by composing bytes, which GCC merges into one load on x86,
  ARMv7 and AArch64 (§10). Do not use `memcpy` for them.
- Calls and slots are big-endian because their first byte carries the
  form bits; everything else is little-endian.

### 2.4 Calls, and how far they reach

A call names a **byte offset from the image base** - not a word number,
so there is no word table, no load-time walk and no xt-to-number map;
`COMPILE,` is arithmetic on the distance. This is HotSpot's
compressed-oops decode, `base + (narrow << shift)`, with a shift of 0.
The compiler picks the two- or three-byte form by distance, as it picks
`LIT8`, `LIT` or `LIT32` by value.

| limit | value | kind |
|---|---|---|
| VM memory (`MEMSIZE`) | 16 MB | engine parameter, not format |
| call reach, two-byte form | 16 KB | format |
| call reach, three-byte form | **4 MB** | format |
| slot reach, two-byte form | ±16 KB of the operand | format |
| slot reach, three-byte form | ±4 MB of the operand | format |
| branch, within one word | ±32 KB | format |
| literal width | a full cell | format |
| opcodes | 128, with 256 escaped selectors | format |

**The three-byte call's reach, 4 MB, is below `MEMSIZE`**, so a
dictionary grown past 4 MB could not reach its oldest words from its
newest. It is the first ceiling a growing system would meet; today's
shell image is about 120 KB, 35 times short of it. The remedy would be
a fourth call width, not aligned bodies again.

## 3. Worked examples

Real bytes, compiled at the prompt of the 64-bit `kernel.img` at
Iteration 491. Opcode values are hexadecimal.

| source | bytes | reading |
|---|---|---|
| `32 CONSTANT BL` | `27 20` | `LIT8;EXIT` 32: a constant is two bytes |
| `: X OVER OVER ;` | `09 36` | `OVER`, then `OVER;EXIT` (`0x28` + 14): the `EXIT` disappears |
| `: X DUP + ;` | `06 28` | `DUP`, then `+;EXIT` |
| `: X 1 + ;` | `7A 01` | `ADDI;EXIT` 1: `LIT 1 +` became one opcode, and folded |
| `: X 5 = ;` | `7C 05` | `EQI;EXIT` 5 |
| `: X -1 ;` | `63 01` | push −1 in one byte, then `EXIT` |
| `: X $123456789 ;` | `7D 89 67 45 23 01 00 00 00 01` | `LIT64`, eight bytes little-endian, `EXIT` |
| `VARIABLE VV` | `24 00 00 00 …` | `DOVAR`; the parameter field is at `align(xt + 4)` |
| `: X VV @ ;` | `64 7F F0 01` | `VAR@`, slot `0x7FF0` = −16 from the operand: `VV`'s parameter field; then `EXIT` |
| `: X IF 1 ELSE 2 THEN ;` | `04 06 00 62 03 04 00 26 02 01` | `?BRANCH` +6 to the `ELSE` part; push 1; `BRANCH` +4 past it; `LIT8 2`; `EXIT` |

The last line shows the folding rule at work: `LIT8 2` is **not** folded
into `LIT8;EXIT`, because `THEN` makes the `EXIT` a branch target.

`: X 0 ?DO I DROP LOOP ;` shows a loop: `61` (push 0), `85 A7` (a
two-byte call to `(?DO)`), `03 09 00` (its forward branch to the exit),
`85 BB` (`I`), `05` (`DROP`), `85 E4` (`(LOOP)`), then `3F`, a one-byte
branch back.

## 4. The image file

### 4.1 Header

| offset | size | contents |
|---|---|---|
| 0 | 4 | magic: `CV8` and `'0' + SCALE`, so `CV80` |
| 4 | 1 | the cell width in bytes, 8 or 4 |
| 5 | 1 | `'L'` when specialised opcodes are used |
| 6 | 1 | the **format version**, 5 |
| 7 | 1 | the **feature bitmap**: 1 variable-width calls, 2 variable-width slots, 4 specialised opcodes, 8 `LIT64` - 15 in every image today |
| 8 | cell | the number of threads in the hashed word list, 32 |
| … | 32 cells | the thread heads, relative to `START` |
| … | cell | the number of `DOES>` tail entries, always 0 |

`kernel.img`'s header is 280 bytes; `kernel32.img`'s, 144.

The engine compares the first five bytes exactly, so a 32-bit image is
refused by a 64-bit engine, and then **refuses any version but its
own** (since Iteration 247, when a renumbering made each version's
engine crash on the other's images). The feature bitmap lets a later
addition set a bit instead of breaking the format. The tail entries are
read and ignored: `DODOES` carries its target inline, and both
compilers write none.

Versions: 2 (243) moved the locals cells into the image; 3 (247)
renumbered the synthetic opcodes; 4 (258) added the short branches and
unaligned operands; 5 (259) made slot operands relative to themselves.

### 4.2 Layout

```
header (4.1)
offset 0   a three-byte call to COLD - the entry point
offset 3   a three-byte call to WARM
offset 6   two zero bytes
offset 8   the five locals cells (§6.3)
           word 0: link, name, body - the OLDEST word first
           word 1 ...
```

Each word is three fields, nothing padded (Iteration 244):

```
link   1-3 bytes: the distance back to the previous name in the same thread
name   a count byte (bit 7 set, bit 6 immediate, bit 5 inline) and the characters
body   CV8 bytes
```

The link is read **backward** from the name, so its tag is the first
byte read:

| tag at name − 1 | length | distance |
|---|---|---|
| `0xxxxxxx` | 1 | the tag, 0–127 |
| `10xxxxxx` | 2 | `(tag & 0x3F) << 8 \| [name−2]` |
| `11xxxxxx` | 3 | `(tag & 0x3F) << 16 \| [name−2] << 8 \| [name−3]` |

A distance of 0 ends the thread. The engine never reads a link: that is
the compilers' business (`PREV-NFA`, `HEADER`, `cross.4`'s `"HEADER`).

**A data body is the one aligned thing**: `[DOVAR or DODOES][three
bytes][padding][parameter field]`, with the parameter field at
`align(xt + 4)`. `>BODY`, `CREATE`, the engine's `DOVAR` and `DODOES`
and both compilers' `VAR@`/`VAR!` peepholes all compute that address,
and must agree. Code that lays down cells after a colon definition must
`ALIGN` first (`BUILTIN` in `shell.4` and `WORDLIST` in `extend.4` do).

**Loading** is: check the header, read the rest into memory at the
base, done. Every call, branch and slot is an offset, so there is no
relocation pass.

## 5. The engine

### 5.1 Registers

`ip`, `rp`, `dsp` and the scratch `t` are **locals of
`virtual_machine()`** (the `VMREGS` macro), and the top of the data
stack is cached in a local, `tos`. As statics they cost about a fifth
of every workload, because C's aliasing rules let any cell store hit
them, so the compiler reloaded them around every dispatch (§9).
`dsp` points at the second stack item while `tos` holds the first;
`SP@`, `DEPTH` and the OS primitives spill `tos` first, so Forth sees
the stack it always did. The i386 build is non-PIE, because PIE spends
`ebx` on the global offset table and the cached top of stack then costs
more than it saves.

### 5.2 Handlers

158 labelled handlers: the direct and escaped primitives, the synthetic
opcodes, the folded band and the specialised opcodes. Each ends in its
own `NEXT()`, so each has its own indirect branch for the predictor to
learn; only the call path is shared. A folded handler is the
primitive's body followed by a return:

```c
L_plus:  tos += NOS; dsp += CELL_BYTES; NEXT();
LX_plus: tos += NOS; dsp += CELL_BYTES; EXITNEXT();
```

### 5.3 Memory and stacks

One static block of `MEMSIZE` (16 MB): the image at the bottom, the
dictionary growing up from it, and the stacks at the top - 256 KB of
data stack below 64 KB of return stack. Since Iteration 253 **each
stack has an unreadable guard page below it** instead of a compare on
every push (`GUARD`, on by default). A `SIGSEGV` handler reports which
guard was hit and exits with status 70:

```
$ echo ': R RECURSE ; R' | ./relf kernel.img
relf: return stack overflow                        (exit status 70)
```

The guard catches every push at the push itself, and the return stack's
guard sits two cells above the empty data stack, so an underflow of two
or more cells faults too. `-DGUARD=0` brings the compares back, for a
target without an MMU; they cost 3–6% at 64-bit and nothing measurable
at 32. The block is aligned to 64 KB so the guards fall on page
boundaries for pages up to that size.

### 5.4 Cells are host pointers

`CELL(a)` dereferences `a` as a **real host address**, not an index
into an isolated array as SOD32's `mem[a & MEMMASK]` does. So the
process's pointer width must equal the image's cell width: the 8-byte
image runs on a 64-bit engine, the 4-byte image on a 32-bit one
(`relf32`, or the native engine of a 32-bit host). It is a design
property - it is what makes addressing cheap - not a bug to fix away.

A second consequence, for cross-compiling: **the host that runs
`cross.4` must have cells at least as wide as the target's**, because
`cross.4`'s literal parsing and its `@-T`/`!-T` plumbing do host-cell
arithmetic on values that end up in target cells. An 8-byte host can
build a 4-byte kernel; a 4-byte host cannot build an 8-byte one.

## 6. The specialised opcodes

Chosen from per-address execution profiles, not intuition. They are the
difference between CV8 being denser and CV8 being several times faster
(§9).

### 6.1 The band

| opcode | operation | opcode | operation |
|---|---|---|---|
| `0x61` | push 0 | `0x6F` | `2DUP` |
| `0x62` | push 1 | `0x70` | `2DROP` |
| `0x63` | push −1 | `0x71` | `CHAR+` |
| `0x64` | `VAR@` slot | `0x72` | `1+` |
| `0x65` | `VAR!` slot | `0x73` | `CELL+` |
| `0x66` | `LSAVE` slot | `0x74` | `CELLS` |
| `0x67` | `LRESTORE` slot | `0x75` | `1-` |
| `0x68` | `L!` slot | `0x76` | `INVERT` |
| `0x69` | `LZERO` slot | `0x77` | `COUNT` |
| `0x6A` | `0=` | `0x78` | `ALIGNED` |
| `0x6B` | `-` | `0x79` | `ADDI` n |
| `0x6C` | `<>` | `0x7A` | `ADDI;EXIT` n |
| `0x6D` | `0<` | `0x7B` | `EQI` n |
| `0x6E` | `>` | `0x7C` | `EQI;EXIT` n |

### 6.2 Constants, immediates and variables

`LIT 0` alone had 556 static sites, and `-1` was a five-byte `LIT32`
because `LIT8` is unsigned. `ADDI` and `EQI` are Lua 5.4's `OP_ADDI`
and `OP_EQI`: honestly marginal in time, kept because they are four
handlers and save about 400 bytes.

`VAR@` and `VAR!` replace a call, `DOVAR` and `@` with one dispatch -
the JVM's `getstatic`. The slot is the variable's parameter field, as a
signed offset from the operand's own first byte: two bytes carry 15
bits (±16 KB), three with the top bit set carry 23 (±4 MB). Counting
from the operand rather than the base (Iteration 259) made nine slots in
ten the short form, where it had been half: code sits a few hundred
bytes after the variables it uses.

### 6.3 Locals

The largest single win - **0.41 to 0.54 of CV8's time on its own**,
about two-thirds of what all the specialisations buy. Forth locals in
`shadow.4` are shallow-bound: on entry each is saved to a save stack,
on exit restored. As Forth, `LSAVE` was 23 operations and nine calls,
and its save-stack pointer was the hottest call target in the whole
shell. The opcodes do the same in one dispatch, on **the same
Forth-visible save stack**, which the engine finds through the five
cells at image offset 8:

| cell | contents |
|---|---|
| 0 | offset of `LSAVE-SP`'s parameter field |
| 1 | offset of `LSAVE-STACK`'s parameter field |
| 2 | the value of `LSAVE-MAX` |
| 3 | offset of `LSAVE`'s body, the fallback |
| 4 | offset of `LRESTORE`'s body, the fallback |

`kernel.4` reserves the cells and `shadow.4` fills them as it loads.
**Deoptimisation**: whenever the Forth version would take its error
path - overflow, underflow, no buffer - the opcode pushes the slot as
`LIT` would and calls the Forth word, so the rare paths keep their
behaviour and messages. That is the shape of CPython's specialising
interpreter (PEP 659), and it is what makes specialising one
instruction safe. It is also the design's one real wart: the engine
knows the layout of a Forth data structure (§13).

### 6.4 The tiny words

`0x6A`–`0x78` are colon words of two or three operations that together
took 6.4% of all dispatches as calls. They are declared in `kernel.4`
with `OPCODE` and a number - `106 OPCODE 0=` - rather than defined in
Forth: the engine is the definition, and `COMPILE,` inlines the byte.

## 7. How images are built

Two Forth compilers emit CV8, and they are twins that must agree:

- **`cross.4`**, the cross-compiler, runs on `kernel.img` and compiles
  `kernel.4` into a new `kernel.img` - a fixpoint. `make images` does
  that in a temporary directory and installs the result only if it is
  byte-identical, or with `IMAGES_FORCE=1` when a change is intended;
  `make check-images` is the read-only half, and `tests/verify` runs it.
  The kernel images are committed because they are the bootstrap seed.
- **`kernel.4`'s own compiler** compiles everything loaded at run time.
  The shell image is `kernel.img` with `extend.4 pool.4 shadow.4
  save-system.4 shell.4 edit.4 tree.4` loaded and `SAVE-SYSTEM` run;
  `make` or `relfsh` itself builds it, and it is not committed.
  `tests/verify` checks that a rebuild is byte-identical, and records a
  checksum so that another machine's build is compared with this one's.

**Saving an image.** `save-system.4`'s `SAVE-SYSTEM` writes the
running system from `START` to `HERE` behind a header, subtracting
`START` back out of the two cells `COLD` relocates. `BOOT` holds the
offset of the word to run at startup - `MAIN`, in the shell image. Two
rules keep images reproducible and bootable anywhere:

- **Nothing in the dictionary may hold an absolute address**, a PID, a
  path, a time or a descriptor. An image loads at a different address
  every run; the first turnkey images segfaulted on exactly this. Store
  offsets from `START` (`!XT`, `@XT`), or add the cell to `SS-SCRUB`,
  which blanks such cells in the saved copy - `COLD`, `WARM` and `QUIT`
  set them again before anything reads them.
- **Compiling new code inside a reloaded image works** (since Iteration
  41), because the compile-time machinery holds offsets too. The
  `forth` builtin depends on it.

A prebuilt shell image starts about 128 times faster than compiling
`shell.4` from source (Iteration 40: 1.8 ms against 253 ms).

The specialised opcodes are emitted like this:

- push 0, 1 and −1 come straight from `LIT,`.
- `ADDI`, `EQI`, `VAR@` and `VAR!` are **peepholes**: `LIT,` and
  `CALL,` remember where they started, and when `COMPILE,` of `+`, `=`,
  `@` or `!` completes a pattern it rewinds over the first half.
- **Folding** is done by `EXIT,` at `;`: the last operation and the
  `EXIT` become one opcode.
- Both are stopped by `NO-PEEP`, which everything that makes `HERE` a
  branch target calls, so nothing can jump between the halves - the
  `ELSE 2 THEN ;` example in §3.
- The tiny words are inlined by `COMPILE,`; the locals opcodes are
  emitted by `shadow.4`'s `L-EMIT`.

---

# Part II — Why it is this way

## 8. Where CV8 comes from

**CV8** stands for Compressed-pointer, Variable-length, 8-bit units:
calls are compressed pointers, operations have variable length, and the
unit is a byte. The name was coined in this project at Iteration 189 and
is used nowhere else. It is the fifth encoding in a line, each a
response to a measured problem with the one before:

- **SOD32** (L.C. Benschop) separated the engine from a
  machine-independent image - the property this project exists to keep.
  It packed several 5-bit operations into a cell; measured at Iteration
  157, the packing cost 1.06–1.19x in dispatch on x86-64 and 1.67x on
  i386 for about 9% of size. CV8 keeps the separation and not the
  packing.
- **RelF** (Kirill Timofeev) is SOD32 sped up, and what this project
  refactors. Its idea - a reference to a word holds a **relative
  offset**, so the image is position-independent - is the one CV8's
  calls carry further.
- **SOD16** (Iterations 156–167) used 16-bit tokens: an image of 0.41x
  the cell image's size, but 1.25x slower. Tokens above 255 indexed a
  table of addresses built at load time.
- **CPT16** (189) found that most of SOD16's slowdown was not the table
  at all (§9), and removed the table anyway: when targets are aligned,
  index-to-address is a linear function, and scaling replaces indexing.
- **CV8** (189) narrowed the unit to a byte, and the image dropped a
  further 13–16%; the specialised opcodes (190) made it fast.

## 9. The decisions, and what each was measured to buy

Measured on x86-64 and i386 unless it says otherwise; §10 covers the
other architectures.

- **VM registers are locals, not statics** - 1.22x on its own, the
  largest single effect found in the whole investigation (189). A
  store through a cell pointer may alias a static cell, so GCC reloaded
  and re-stored `ip` around every dispatch. On load/store machines it is
  worth more still: a third of all AArch64 instructions.
- **No executed padding.** SOD16 padded data bodies with `NOOP`s that
  ran on every variable reference: 17.3% of all dispatches.
- **Data words are primitives** (`DOVAR`, `DODOES`): 12% fewer
  dispatches, no measurable time. Kept for structure - it is what lets a
  data body sit anywhere with its parameter field aligned.
- **`EXIT` folds into the operation before it** - about 20%. `EXIT` was
  17% of all dispatches, and 80% of them followed a primitive, because
  the kernel is full of two-operation colon words. It also gives every
  primitive's return its own predictable branch.
- **Calls are compressed pointers, not a table index.** Once the
  registers and the padding were fixed, the table's dependent load was
  below the noise end to end. The case against the table is structural:
  `COMPILE,` needed a reverse map, the table cost a cell of hot memory
  per word and a walk at every load, and it capped the system at a word
  count, which variables use up, instead of at image bytes.
- **The top of the stack is cached** - 5–8% on x86-64; on i386 only
  non-PIE, since with PIE the register it needs holds the GOT and the
  cache cost 3–18%. Ertl found the same: stack caching's value depends
  on the registers available.
- **The unit is a byte** - free on x86-64, a small gain on i386, and
  13–16% smaller than 16-bit tokens.
- **The specialised opcodes** take CV8 to 0.13–0.23 of the old cell
  engine's instructions (§10), the locals opcodes two-thirds of that.
- **A 256-entry dispatch table** instead of a test of the top bit
  (chosen at 243). Iteration 200 measured it 2–4% slower on x86, since
  the test it replaces predicts almost perfectly; 226–227 measured it
  1,600 bytes smaller. It is part of the configuration the engine was
  written out in, and minimalism is this project's first priority.
- **Guard pages instead of compares** (253): the compares cost 3–6% at
  64-bit.
- **Byte-granular headers** (244): the 64-bit kernel went from 11,638
  bytes to 8,094, and the shell image of the day from 69,518 to 58,657.

## 10. Other architectures

Iteration 191 checked the design on AArch64, ARMv7 and RISC-V 64 under
qemu. **qemu's wall time measures nothing here** - it is dominated by
translating the guest's indirect branches, one per dispatch - so what
it gave was correctness, exact guest instruction counts (the `libinsn`
plugin; on in-order cores a much better proxy for time than on x86),
and a simulated 32 KB L1. Branch prediction is modelled by nothing.

- **Images are portable**: one image built on x86 ran on every
  architecture, 12 of 12 engine/image pairs.
- **The specialisations transfer**: guest instructions against the
  cell engine of the day, whole runs:

  | | x86-64 | AArch64 | ARMv7 | RISC-V 64 |
  |---|---|---|---|---|
  | registers as locals | 0.75–0.76 | 0.67 | 0.71 | 0.69–0.70 |
  | CV8 | 0.61–0.64 | 0.60–0.62 | 0.60–0.62 | 0.63–0.67 |
  | CV8 and the specialised opcodes | 0.13–0.22 | 0.13–0.23 | 0.13–0.22 | 0.15–0.24 |

- **A CV8 dispatch costs one or two instructions more** than a
  fixed-width cell dispatch everywhere, so CV8 alone gains less on an
  in-order core than on x86; the specialisations remove dispatches
  outright, which is why they transfer and CV8 alone may not.
- **Operand loads are composed from bytes.** `memcpy` compiled, on
  RISC-V, to byte loads, a stack round trip and a stack-protector
  check; composing compiles to one load on ARMv7, AArch64 and x86.
- A sign-tested dispatch saved 3.6–4.2% of instructions on AArch64 and
  RISC-V and cost 3.0% on ARMv7. It has been moot since 243: the
  256-entry table has no test at all.

Since then the design has run on real ARMv7 hardware - an NVIDIA Tegra,
32-bit, running the 4-byte image - where `make verify` has passed
repeatedly, including after the engine gained `DUP-FROM` at 486.

## 11. What was borrowed

None of the mechanisms is new; the contribution is the combination and
the measurements.

| mechanism | from |
|---|---|
| a separated engine and a portable image | SOD32 |
| relative, position-independent references | RelF |
| a byte-granular instruction stream | the JVM; Open Firmware's FCode |
| `base + (value << shift)` as a pointer | HotSpot's compressed oops; 8086 Forth's segment threading |
| one-byte forms for the commonest constants | the JVM's `iconst_*`; YARV's operand unification |
| locals as single-instruction slot access | the JVM's `iload`; CPython's `LOAD_FAST` |
| specialise the common case, fall back for the rest | CPython 3.11's specialising interpreter (PEP 659) |
| the primitive set chosen by frequency | Gforth; Proebsting's superoperators |
| small immediate operands | Lua 5.4's `OP_ADDI`, `OP_EQI` |
| interpreting the compact form in place | Titzer's in-place WebAssembly interpreter |

The last row is where CV8 differs from most bytecode systems. OCaml and
Ruby's YARV expand compact code into pointer-wide threaded code when it
loads; CV8 executes the dense form directly, because size on disk *and*
in memory both count here, and a load-time expansion would be charged to
every shell start. Simulated, the cell image missed the L1 data cache
about five times as often as the byte image.

## 12. Things that will bite you

- **Branch offsets count from the operand**, not past it (§2.3).
- **Never fold an `EXIT` that anything branches to** (§3, §7).
- **Never execute padding**: nothing in code is aligned, and data
  bodies are entered at `DOVAR`/`DODOES`, never stepped into.
- **Compute a parameter field one way everywhere**: `align(xt + 4)`.
  Four defects in the byte-header work were two places computing the
  same address differently (Iterations 213, 244).
- **`LIT8` is unsigned**, and a value outside 32 bits needs `LIT64`:
  until Iteration 194 such values were silently cut to 32 bits.
- **The four places that number opcodes must agree** (§2.2), and
  nothing but the build-time checks will say so.
- **A new direct primitive moves the map**; an escaped one moves
  nothing. Prefer escaped unless the primitive is hot.
- **Rebuild the kernels deliberately**: `make images IMAGES_FORCE=1`
  and `make check-images`, never a copy from elsewhere.

## 13. Open questions

- **One source for the numbering.** Four hand-maintained places (§2.2)
  are the real risk in this design, more than any opcode. `kernel.4`
  could emit the engine's tables as well as the compiler's.
- **The locals opcodes know a Forth data structure** (§6.3). Making
  `LSAVE` and `LRESTORE` real primitives, with the Forth versions
  deleted, would remove the five cells and the fallback.
- **The three-byte call's 4 MB reach** is below `MEMSIZE` (§2.4).
- **The self-hosted assembler and native code** that `GOALS.md` names as
  the end state: dispatch removal was measured at 4–4.75x, and inlining
  at a further 2–2.2x - larger than anything the interpreter can do.
