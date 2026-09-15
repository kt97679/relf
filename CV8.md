# CV8.md — the inner interpreter, measured end to end

> **Iteration 194 widened the format** after an audit of its ceilings:
> variable-width calls and slots (32 MB / 64 MB reach), `LIT64` (a
> 64-bit literal was silently truncated), a reserved opcode bank, a
> 16 MB `MEMSIZE`, and a version + feature bitmap in the header so
> future widening is not a format break. See `CV8-REFERENCE.md` §3.5.
>
> **`CV8-REFERENCE.md`** is the format-and-engine reference: opcode
> map, image layout, worked byte examples, and the rules a compiler
> must follow. **Iteration 191 adds `XARCH.md`** (ARM/RISC-V under qemu; corrects
> 3.3's cache attribution). **Iteration 190 adds `VM-SURVEY.md`**: five specialisations borrowed
> from the JVM, CPython, Lua and Gforth - locals as frame-slot opcodes
> above all - take CV8 to ~0.33x its own time (0.16-0.23x of today's
> engine) and 9-11% smaller. Read it after this file.

Iteration 189, branch `cv8` (from `token16`). This answers
`INNER-INTERPRETER.md`. Read that first; this file does not repeat its
constraints, it measures against them.

**Everything below is measured unless it says otherwise.** Every
number comes from `tools/lab/`. `tools/lab/build-cv8.sh` rebuilds every
engine and image quoted here, at both cell widths, from a clean
checkout, and smoke-tests each pair against `dash`.

---

## 0. The answer, first

**One encoding for both cell widths: a byte stream in which a call is a
two-byte compressed pointer.**

```c
t = ip[0];
if (t < 0x80) { ip += 1; goto *dispatch[t]; }          /* opcode    */
t = ((t & 0x7F) << 8) | ip[1]; ip += 2;                 /* 15 bits   */
RPUSH(ip); ip = base + (t << S);                        /* no table  */
```

It comes with four other decisions. Each is measured separately below.

1. **VM registers are locals, not statics.** This is now done in
   `relf.c`. It is worth about 1.22x on its own and changes nothing
   else.
2. **Data words get primitives.** `DOVAR` and `DODOES` become
   primitives instead of calls to Forth runtimes. No alignment padding
   is ever executed.
3. **`EXIT` folds into the preceding primitive.** For a hot set of 23
   primitives, "`+` then `EXIT`" becomes one opcode. This is worth
   about 20%.
4. **Top of stack is cached in a register on 64-bit.** On 32-bit only
   if the build is non-PIE. This is the one place where 32 and 64 bit
   should differ.

**Size.** Stripped engine plus image, counted the way `tests/sizes`
does:

| | x86-64 | i386 |
|---|---|---|
| today (`relf` + cell image) | 229,160 | 127,684 |
| CV8 | **99,488** (0.43x) | **81,224** (0.64x) |
| `dash` | 129,784 | — |

**Speed.** Compared with the committed engine, CV8 is roughly
**1.6–1.7x faster** on the shell workloads, at both widths. This is a
product of separately measured ratios; see §3 for the pieces.

**Correctness.**
- At both widths, and for both the PIE and non-PIE i386 builds, the
  CV8 images pass `tests/diff` 20/20.
- They pass every `tests/shell` file except one assertion in
  `run-forth`, which compiles a new colon definition. The Forth
  compiler still emits cells, and that is phase 3.
- `tests/verify` on this branch matches the unmodified tree exactly.

---

## 1. What the brief had wrong, and why it matters

`INNER-INTERPRETER.md` §3.3 attributed SOD16's 1.25x to the word-table
dependent load. That mechanism is real in `tools/thread-chase`.
End to end it is not what cost the time.

### 1.1 The VM registers lived in memory

`ip`, `rp`, `dsp` and `t` were file-scope statics.
- Every primitive stores through `CELL()`.
- That is a `UNS64` store, and C's aliasing rules allow it to hit a
  `UNS64` static.
- So GCC reloaded and re-stored `ip` around every `NEXT`. The
  disassembly shows `mov 0x...(%rip),%rdx` / `mov %rdx,0x...(%rip)` on
  every dispatch.
- Making them locals of `virtual_machine()` puts them in registers.

On the same images, `bench-vm.py` gives these ratios against the old
engine:

| | loop | fn | str | arith | start |
|---|---|---|---|---|---|
| x86-64 | 0.82 | 0.79 | 0.80 | 0.82 | 0.91 |
| i386   | 0.80 | 0.77 | 0.81 | 0.81 | 0.91 |

This is larger than any encoding effect in this file. It is also
invisible to a microbenchmark that keeps its own registers, which is
why `thread-chase` never saw it.

### 1.2 SOD16 executed its padding

SOD16 lays out a data body as `[NOOP pad][call DOVAR][PFA]`. The pad
keeps the parameter field cell-aligned, and it is *executed* on every
variable reference: three NOOPs on 64-bit.
- An instrumented engine (`vm-lab.c -DPROFILE=1`) shows **NOOP at 17.3%
  of all dispatches** on `loop`: 579.7M against 479.3M with the pad
  skipped.
- Variables are 29% of all call targets. `DOVAR` alone is 25% of calls.

### 1.3 With both fixed, the dependent load is invisible end to end

Here is SOD16 against CPT16 with register locals and no executed
padding. CPT16 is SOD16 with the table replaced by `base + (t << S)`.
Each design was built with four compiler-flag layouts (§2.2):

| | loop | str |
|---|---|---|
| SOD16 (table) | 0.89 – 0.98 | 0.87 – 0.94 |
| CPT16 (no table) | 0.95 – 0.97 | 0.92 – 0.94 |

**These ranges are indistinguishable.** A single-layout run had shown
CPT16 5% ahead, and that did not survive randomisation.

The table's end-to-end cost on this core is below the noise. The case
against it is **structural**:
- **`COMPILE,`.** It needs an xt-to-word-number reverse map. With a
  compressed pointer it is `START - S RSHIFT` arithmetic.
- **Memory.** The table costs 8 bytes per word of hot memory.
- **Loading.** It needs a load-time chain walk and a DOES> side table.
- **Ceiling.** It caps the system at word count, which variables
  exhaust. A compressed pointer caps it at image bytes instead.

So open question 1 has an answer. The dependent load is avoidable at
any token width narrower than a pointer, by **scaling instead of
indexing**. When call targets are aligned, the table maps
`i → base + i·align`, and a linear function needs no table. HotSpot's
compressed oops decode by exactly this formula: `base + (narrow <<
shift)` (`compressedOops.inline.hpp`). 8086 Forths did the same thing
with 16-byte segments ("segment threading").

---

## 2. Method

### 2.1 The instrument

`tools/lab/bench-vm.py ROUNDS CFG` works as follows.
- It runs every (engine, image) pair on every workload once per round,
  in shuffled order, with round 0 discarded as warmup.
- It records **child CPU time** (user+sys via `wait4`) rather than wall
  clock.
- It forms ratios **per round** against the first configuration, so the
  ratios are paired.
- It reports the median ratio and a bootstrap 95% interval of that
  median.

The workloads are in `tests/bench-vm/`:
- `loop` is `tests/bench`'s loop.
- `fn` is function calls.
- `str` is `${x##*/}`, `${x%/*}` and `case`.
- `arith` is Fibonacci mod p.
- `start` is 20 × `-c true`.

Profiles and cachegrind showed all four script workloads have
near-identical dispatch mixes, so `loop` and `str` stand for the rest in
the layout runs.

### 2.2 The noise that is not in the error bars

**Code layout moves an engine by ±4–5% with no semantic change.**
- The CV8 fold engine, built with `""`, `-falign-labels=16`,
  `-falign-labels=32`, `-falign-jumps=32 -falign-labels=8`,
  `-fno-reorder-blocks-and-partition` and `-O3`, spans 0.737–0.803 of
  the same baseline.
- Adding 41 never-executed folded handlers to an engine once made it
  **8% faster**. The image and the dispatch count were identical,
  checked with the profiler.

This is Mytkowicz et al.'s "producing wrong data without doing anything
obviously wrong" (ASPLOS 2009), and it has bitten this project before.
Iteration 140 also found GCC merging dispatch sites. **The rule used
here: any engine comparison under about 8% is built with four flag
sets (`tools/lab/layout-variants.sh`), and the ranges are compared,
not the points.**

### 2.3 The caveats

- One machine: an Intel Xeon (family 6, model 207) under KVM with one
  vCPU.
- i386 is measured by running 32-bit builds on that same x86-64 core.
  No ARM numbers.
- Cachegrind's branch model is simplistic, so use it for direction
  only.

---

## 3. The measurements, stage by stage

### 3.1 Size

Whole image, header included, from `build-cv8.sh`. The 32-bit-unit row
is estimated by `tools/size-estimate.py`, whose 16-bit estimate
reproduces the real image to the byte.

| scheme | x86-64 | i386 |
|---|---|---|
| cell (today) | 206,416 | 109,876 |
| 32-bit units (estimated) | ~122,000 | ~108,900 |
| SOD16 / CPT16 | 84,032 | 70,864 |
| CPT16 + data prims + fold | 83,392 | 70,096 |
| **CV8** + data prims + fold | **72,648** | **59,320** |

**32-bit units are dominated.** They save nothing on i386 and are 1.47x
the 16-bit size on 64-bit. That closes option D of the brief.

**EXIT folding barely changes size**, saving 640–780 bytes. Most
folded `EXIT`s were at a body's end, where cell alignment re-pads.

Engine `.text` in bytes:

| | x86-64 | i386 |
|---|---|---|
| `relf` | 5,518 | 5,428 |
| CV8 + fold | 8,638 | 7,988 |
| CV8 + fold + TOS | 9,758 | 7,940 |

About 1.5 KB of that is the 23 folded handlers. **Folding all 64
primitives costs about 10 KB of `.text`** against 700 bytes of image.
Do not.

### 3.2 Speed

Each stage is measured against its predecessor, and ranges are over
four layouts.

**x86-64**, relative to one cell + reg build:

| design | loop | str |
|---|---|---|
| cell + reg (4 layouts) | 0.96 – 1.04 | 0.93 – 1.02 |
| CPT16, pad skipped | 0.95 – 0.97 | 0.92 – 0.94 |
| CPT16 + data prims + fold | 0.75 – 0.80 | 0.71 – 0.79 |
| CV8 + data prims + fold | 0.75 – 0.79 | 0.73 – 0.77 |
| **CV8 + fold + TOS** | **0.69 – 0.77** | **0.69 – 0.77** |

**i386**, relative to one cell + reg build:

| design | loop | str |
|---|---|---|
| cell + reg (4 layouts) | 0.97 – 1.00 | 0.98 – 1.00 |
| CPT16 + data prims + fold | 0.79 – 0.82 | 0.77 – 0.81 |
| **CV8 + data prims + fold** | **0.70 – 0.76** | **0.68 – 0.75** |
| CV8 + fold + TOS, PIE | 0.78 – 0.86 | 0.78 – 0.85 |
| CV8 + fold, non-PIE | 0.75 | 0.74 |
| **CV8 + fold + TOS, non-PIE** | **0.72** | **0.71** |

### 3.3 What each stage buys, and why

**Token vs cell** is about 5% on 64-bit and nothing on i386.

> **Corrected in Iteration 191 (`XARCH.md` §5).** The miss *counts*
> below are right, but weighed they are ~0.06% of instructions (cell)
> against ~0.012% (token): roughly 1-3% of time, not the explanation
> of CV8's x86 lead over `relf-new`. That comes mainly from EXIT
> folding and TOS caching. The original reasoning is kept below.

The reason was taken to be the data cache, not dispatch. Cachegrind on a 300-iteration
loop shows **243K L1d misses for the cell image against 9K for every
token image**. 156 KB of cell code does not fit a 48 KB L1d, and 50 KB
of tokens nearly does.

**Data primitives** cut dispatches by 12% (479M to 423M) and cut
instructions by 8% in cachegrind, but bought **no measurable time**.
They are kept for structure:
- Data bodies become aligned call targets with no executed padding.
- That is what allows S > 1.
- It is size-neutral. `[DOVAR][pad][PFA]` and
  `[DODOES][tail][pad][PFA]` fit in the space the pad already took.

**EXIT folding** is the largest encoding-level win.
- `EXIT` was 17% of dispatches. About 80% of `EXIT`s follow a
  primitive: `+` 12%, `=` 9%, `!` 7%, `@` 6.5%, `LSHIFT` 5%.
- Those are the kernel's tiny colon words: `: - NEGATE + ;`,
  `: 0= 0 = ;`, `CELLS`.
- Folding cut dispatches by a further 11% and modelled mispredictions
  by 26%. The single shared `EXIT` dispatch is a poorly predicted
  indirect branch, and folding gives every primitive its own.
- **Calls almost never precede `EXIT` dynamically.** So tail-call
  conversion, with its return-stack semantics risk, is not worth doing
  here.

**The byte stream is free on 64-bit and faster on i386.** It won in
every one of four layout pairings on i386. The likely cause is register
pressure: CV8 needs no `-256` bias, so `cbase` is the image base
itself.

**TOS caching depends on register count.**
- On x86-64, with 16 GPRs, it is 5–8% faster in three of four layouts.
- On i386 PIE, `ebx` holds the GOT, `rp` already spills, and `tos`
  pushes `cbase` to the stack too. It is 3–18% slower.
- A non-PIE i386 build frees `ebx`, and TOS becomes a win.

This is exactly Ertl's finding that stack caching's value depends on
the registers available (Ertl, *Stack Caching for Interpreters*, PLDI
1995). ARM32 has 13 usable registers and is untested.

---

## 4. The CV8 encoding, precisely

```
0x00-0x43   primitive, index = byte (kernel.4's 68, in PRIMITIVE order)
0x43        LIT32   4-byte little-endian signed operand
0x44        DOVAR   [DOVAR][pad to CELL][PFA]: push PFA, return
0x45        DODOES  [DODOES][call form][pad][PFA]:
                    RPUSH(PFA), jump to the DOES> tail
0x46        LIT8    1-byte operand
0x47        LIT8;EXIT
0x48-0x5E   folded "primitive then EXIT", in the order of --fold-set
            (LIT here means LIT16;EXIT)
0x61-0x7C   specialised opcodes
0x7D        LIT64
0x7E        ESC + selector: one of the 32 escaped OS/libc primitives
0x80-0xFF   call: target = base + ((b & 0x7F) << 8 | next) << S
```

**These numbers move.** Every boundary is derived from the number of
`PRIMITIVE` lines in `kernel.4`; the map above is 67 primitives with
the escaped band on, which is the default. `CV8-REFERENCE.md` §3.2 has
the full table and the derivation. The specialised band sat at `0x60`
until a 69th primitive pushed the folded band onto it.

**Operands.**
- `LIT` is 2 bytes. `BRANCH` and `?BRANCH` take a 2-byte signed *byte*
  offset from the operand, and all measured branches fit.
- Inline strings and `(LOOP)`/`(POSTPONE)` operands keep **cell
  granularity and alignment**, the SOD16 rule. `(S")`, `(LOOP)`,
  `(POSTPONE)` and the rest need no kernel change.

**Alignment.**
- Every call target must be `1 << S` aligned.
- Word bodies already are, because the name field is cell-aligned.
- Data bodies are aligned because the primitives made them so.
- The two DOES> tails get NOOP padding *before* them. That padding is
  dead code after an `EXIT` and is never executed.

**Reach, which is the design's limit.**
- 15 bits × 2^S: **256 KB on 64-bit (S=3), 128 KB on 32-bit (S=2)**.
- Today's images are 72 KB and 59 KB: 3.5x and 2.2x headroom.
- The low window always contains the kernel, and so the hottest
  targets.

Beyond that there are two unbuilt remedies, in order:
1. S=3 on 32-bit too, with bodies aligned to 8, at about 2 KB.
2. A `FARCALL` opcode with a 3-byte operand for 16 MB × 2^S.

SOD16's word-number ceiling of 65,280 words would have lasted longer
at busybox scale. That is the one axis on which it wins.

**Unaligned operands.** 16- and 32-bit operands are read with
`memcpy`. That is one load on x86, ARMv7+ and ARM64, and byte loads
where the ISA requires them.

---

## 5. The design space, as the field has explored it

What other VMs do, and what of it applies.

**Forth threading.** Direct threading puts a code address per cell,
which is what RelF has. Indirect threading adds a code field.
Subroutine threading uses native calls. Token threading uses indices
into a table, which is SOD16's table.

*Segment threading* on the 8086 is the precedent for CPT/CV8. Words
were aligned to 16-byte paragraphs and the token was the segment
number: an address = base + token × 16, no table.

Open Firmware's FCode is a byte-token format, 1 byte for the common
set and 2 for the rest, detokenized at load. Gforth went
primitive-centric in order to use superinstructions and stack caching.
Ertl reported that the switch grew threaded code more than
superinstructions recovered. RelF was always primitive-centric, so it
has already paid that cost.

**CPython.** It uses 16-bit code units: opcode plus 8-bit argument,
with `EXTENDED_ARG` to widen. Dispatch is computed goto, and 3.14 adds
a tail-calling interpreter. The first claims of about 10% were later
corrected. A compiler bug in LLVM 19 had inflated them, and the
corrected numbers are closer to a 3–5% geometric mean. Independent
measurement on Raptor Lake found about 1–2% over computed goto when
the compiler does not regress.

Lesson for RelF: dispatch mechanics are a single-digit lever, and
compiler layout effects are the same size as the effect. §2.2 finds
the same.

**Lua.** A register VM since 5.0, with fixed 32-bit instructions. Shi
et al. measured register VMs at about 46% fewer instructions for about
26% larger code (TACO 2008). That is the wrong direction for
`GOALS.md` goal 3, and nothing here reopens it.

**Ruby YARV.** A stack VM that translates its instruction sequence to
**direct-threaded code**: each opcode is replaced by its handler
address (`iseq_translate_direct_threaded_code`). That costs a
pointer-sized slot per instruction. It is today's RelF cell image,
chosen for speed. §3.3 shows that at this project's scale, the cell
form is not even the faster one once the working set exceeds L1d.

**JVM.** Byte-granular variable-length bytecode, interpreted in place.
HotSpot's compressed oops are the CPT decode: a 32-bit value shifted
by the object alignment, plus a heap base, reaching 32 GB with 8-byte
alignment.

**Dalvik.** 16-bit code units in a register VM, chosen for density on
phones.

**OCaml.** Bytecode on disk, translated to threaded code at load. It is
the "dense at rest, fast in memory" point.

That option was considered here and rejected:
- The metric is disk *and* memory.
- Load-time relocation of the whole image in C is exactly what
  `layout.py` is, and it would have to be in the engine.
- The `start` workload would pay it every time.

**WebAssembly.** Titzer's in-place interpreter executes the compact
binary directly, with a side table for control flow, instead of
rewriting to an internal format. It performs **on par with interpreting
a custom-designed internal format** (OOPSLA 2022). That is the same
result as §3.3: once dispatch is sane, a compact encoding interpreted
directly costs nothing against a wide one, and the smaller working set
pays for its decoding.

---

## 6. Answers to `INNER-INTERPRETER.md` §5

1. **Is the dependent load avoidable with a narrow token?** Yes, by
   scaling instead of indexing (§1.3). It also turned out not to be the
   cost.
2. **Decide on `loop` or `spawn`?** Moot. The recommended design is
   faster than today on every workload, and `spawn` is fork/exec-bound
   anyway.
3. **Does the representation constrain phase 3 and phase 4?**
   - A compressed pointer makes phase 3 *easier*. `COMPILE,` becomes
     `DUP PRIMITIVE? IF emit-byte ELSE START @ - S RSHIFT emit-call
     THEN`, with no table and no reverse map.
   - Runtime-defined words need nothing, because the target address is
     the token.
   - For phase 4, a call token decodes to an address with arithmetic
     alone, so a JIT or AOT can resolve it statically.
4. **Smaller than A with no dependent load?** Yes: CV8 is 0.35x (64)
   and 0.54x (32) of the cell image, with no second load.
5. **What else was measuring the wrong thing?**
   - `thread-chase` measured the call chain in isolation. It could not
     see the register statics (§1.1) or the executed padding (§1.2),
     which together cost about 35%.
   - Single-layout engine comparisons are ±5% noise (§2.2).
   - VM-RESEARCH.md's 10% for CPython's tail-call interpreter was the
     pre-correction figure.

---

## 7. What is not done, and what could go wrong

- **The compiler.** `,`, `COMPILE,`, `LITERAL`, `IF`/`THEN`, `DOES>`
  and `(;CODE)` all still emit cells. Every image here is translated
  from a cell image, so `run-forth` fails. This is phase 3, and it is
  the next real work.
  - Branch resolution must write 2-byte byte offsets.
  - `CREATE` must lay down `[DOVAR][pad]`.
  - The compiler must choose LIT8/16/32 by value.
  - It must emit folded opcodes only where no branch targets the
    `EXIT`. The translator's rule (`fold_exit`) is the specification.
- **`save-system.4`** has not been adapted. The images carry 16
  variables with live-session absolute addresses from the dump
  (`START`, `S0`, `LAST`, `CONTEXT`, …). `COLD` resets them, so every
  image boots. But **token images are not byte-reproducible across
  dumps**, and this was equally true of SOD16's. `SS-SCRUB` is the
  real answer.
- **`(LOOP)`/`(+LOOP)` padding is still executed.** Its NOOPs sit
  before the call so that the operand lands aligned. The shell barely
  uses `DO` loops. A kernel that did would want `(LOOP)` to read an
  `ALIGNED` operand instead.
- **Far calls are not built**; see §4.
- **The folded-opcode set is fixed in two places**: `--fold-set` and
  the engine's generated table. A real build should derive both from
  one list in `kernel.4`.
- **`(?DO)` and `(LEAVE)`** still store absolute addresses. This is
  latent, as the brief says.
- **The engine is generated.** `gen-fold.py` and `gen-tos.py` rewrite
  `vm-lab.c` textually. That is right for a lab. A committed engine
  should have the folded and TOS bodies written out, or produced by
  one small, reviewed generator.

---

## 8. Recommended order of work

1. **Keep the `relf.c` change**: VM registers as locals. It is done and
   verified.
2. **Phase 3 against CV8**: a Forth-hosted compiler that emits the §4
   encoding, with `run-forth` as its first test. Make the images
   through `save-system.4`, not the translator.
3. **Engine**: `cv8.c` written out from `vm-lab.c`'s `ENC=3` path. TOS
   on when `CELL_BYTES == 8`. The fold set is generated from
   `kernel.4`.
4. **`FARCALL`** before the image passes about 200 KB (64-bit) or about
   100 KB (32-bit).
5. **Re-measure on real ARM hardware.** It is the one platform class
   where the byte stream's unaligned 16-bit reads and the register
   budget could change §3's conclusions.

---

## 9. Reproduction

```sh
sudo apt-get install gcc-multilib valgrind          # -m32, cachegrind
bash tools/lab/build-cv8.sh /tmp/cv8-build          # all images+engines
cd /tmp/cv8-build && cat > cfg <<EOF
cell|$OLDPWD|/tmp/cv8-build/relf64 kernel-shell.img {w}
cv8t|$OLDPWD|/tmp/cv8-build/cv8t-64 /tmp/cv8-build/cv8-64.img {w}
EOF
python3 $OLDPWD/tools/lab/bench-vm.py 5 cfg        # paired CPU-time ratios
```

**Profiling.** `cc -DPROFILE=1` on `vm-lab.c`, then
`VMPROF=/tmp/p.txt <engine> <image> script.sh`. `tools/lab/prof.py`
summarises the dispatch mix. `tools/lab/hot.py` maps call targets to
words, using `layout.py --symbols`.

**Translator options** (all in `tools/layout.py`). With no
options, the output is byte-identical to `token16`'s tool; this was
checked at both widths.

    --cpt S          call token = scaled image offset (S = shift)
    --skip-pad       calls land past a data body's NOOP pad
    --dataprims      DOVAR/DODOES primitives in data bodies
    --fold           fold prim;EXIT (--fold-set NAMES restricts it)
    --v8             the CV8 byte stream (with --cpt S)
    --symbols FILE   body offset, size, kind, name per word

**Sources**

- Ertl, *Stack Caching for Interpreters*, PLDI 1995.
- Ertl, *Threaded Code Variations and Optimizations*, EuroForth 2001.
- Shi, Casey, Ertl, Gregg, *Virtual Machine Showdown: Stack Versus
  Registers*, TACO 2008.
- Ierusalimschy, de Figueiredo, Celes, *The Implementation of Lua 5.0*,
  J.UCS 11(7), 2005.
- Titzer, *A Fast In-Place Interpreter for WebAssembly*, OOPSLA 2022,
  doi:10.1145/3563311.
- CPython tail-calling interpreter: python/cpython#128563 (and its
  correction notice); nelhage/cpython-interp-perf.
- HotSpot `compressedOops.inline.hpp`: `decode_raw`.
- Mytkowicz, Diwan, Hauswirth, Sweeney, *Producing Wrong Data Without
  Doing Anything Obviously Wrong!*, ASPLOS 2009.
