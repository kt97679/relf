# VM-SURVEY.md — what other VMs do, and what this shell borrowed

Iteration 190, branch `cv8`. Iteration 189's `CV8.md` settled the
*encoding*. This file asks a different question: which ideas from other
virtual machines make a Forth VM denser or faster, and which of them
pay off **for this shell's actual code**.

The answer came from measuring, not from the literature. A per-address
execution profile (`vm-lab.c -DPROFILE`, joined to the translator's op
list by `tools/lab/patterns.py`) ranked every candidate by static sites
and dynamic executions. Each idea was then built as a translator
rewrite plus engine opcodes, and ablated on one engine binary over four
code layouts (`CV8.md` §2.2).

---

## 0. The result

Speed is measured on x86-64, as the time of CV8 + idea relative to CV8
on the same engine binary. The range covers the four layouts, `loop`
workload. Size is the whole image.

| idea | borrowed from | x86-64 | i386 | speed |
|---|---|---|---|---|
| **locals as frame-slot opcodes** | JVM `iload`/`istore`, CPython `LOAD_FAST`, Smalltalk push-temp | −3,680 | −3,704 | **0.43–0.50** |
| **tiny colon words as primitives** | Gforth primitive selection, Proebsting superoperators | −1,136 | −1,164 | **0.75–0.82** |
| fused variable access (`VAR@` `VAR!`) | JVM `getstatic`/`putstatic`, CPython `LOAD_GLOBAL` | +64 | +56 | 0.90–0.97 |
| small-int opcodes (`0` `1` `-1`) | JVM `iconst_*`, YARV operand unification | −1,464 | −1,500 | not separately timed |
| immediate `ADDI`/`EQI` | Lua 5.4 `OP_ADDI`/`OP_EQI` | −400 | −432 | noise (0.94–1.06) |
| **all five together** | | **−6,544 (−9.0%)** | **−6,520 (−11.0%)** | **0.33–0.34** (str 0.28–0.33) |
| shared call path in the engine | CPython tail-call analysis, Ertl on replication | engine −5.7 KB `.text` | −3.7 KB | 0.89–0.97 vs 0.92–1.02: no loss |

Against **today's committed engine**, in one run including `dash`:

| | loop | fn | str | arith | start |
|---|---|---|---|---|---|
| `relf` (committed) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `relf`, registers as locals (Iteration 189a) | 0.84 | 0.80 | 0.79 | 0.82 | 0.90 |
| CV8 (Iteration 189) | 0.54–0.57 | 0.53–0.56 | 0.53–0.57 | 0.56–0.58 | 0.79 |
| **CV8 + all five** | **0.18–0.20** | **0.20–0.23** | **0.16** | **0.19–0.21** | **0.70–0.81** |
| `dash` | 0.004 | 0.004 | 0.004 | 0.004 | 0.36 |

i386 is the same shape. CV8 + all five runs at 0.17–0.19 on `loop`,
0.20–0.24 on `fn`, 0.15–0.17 on `str` and 0.18–0.20 on `arith`.

Stripped engine plus image:

| | today | CV8 | **CV8 + borrowed** |
|---|---|---|---|
| x86-64 | 229,160 | 99,488 | **97,080** (0.42x) |
| i386 | 127,684 | 77,196 | **74,792** (0.59x) |

Stripped sizes move in 4 KB pages, so the image saving is partly hidden
by one extra engine page. The opcodes cost about 1.7 KB of `.text` on
64-bit and 3.7 KB on i386 over plain CV8 with the shared call path.

**Correctness.**
- The final configuration (all five plus the shared call path, both
  widths) passes `tests/diff` 20/20.
- It passes every `tests/shell` file except `run-forth`'s
  colon-definition assertion. That is the same known phase-3 gap as
  CV8.
- The locals fallback path is tested separately (§1.1).

**`dash` is still about 40x faster on loops.** That gap is this shell
re-parsing every line (`PARSE-EXPAND-PLAN.md`), not the VM. No VM idea
closes it.

---

## 1. The ideas that paid, and why they fit this shell

### 1.1 Locals: specialise the frame, keep the semantics

`locals.4`'s `{: ... :}` locals are **shallow-bound global
`VARIABLE`s**, like Lisp special variables.
- On entry, `LSAVE` pushes each variable's value onto a save stack.
- On exit, `LRESTORE` pops it back.
- A call site is `LIT32 offset` plus a call: 7 bytes in CV8.
- `LSAVE` itself is 23 operations and nine calls, including an
  `ABORT"` check that runs `COUNT` and `ALIGNED` even when it does not
  abort.

The profile showed:
- The hottest call target in the whole shell was the `LSAVE-SP`
  variable, at 45M calls.
- `COUNT`, `ALIGNED` and `(ABORT")` were at 11–12M each.
- All of it came from those two words.

JVM `iload n`, CPython `LOAD_FAST` and Smalltalk-80's one-byte
push-temp forms all make local access one instruction on a small
operand. The shallow-binding *semantics* must stay: shell code may read
a caller's local through its variable. So what this borrows is the
instruction, not the frame:
- `LSAVE`, `LRESTORE`, `L!` and `LZERO` each become an opcode with a
  2-byte compressed slot pointer: 3 bytes, one dispatch.
- They work on **the same Forth-visible save stack**, `LSAVE-SP` and
  `LSAVE-STACK`, located through the image header.

**Deoptimisation.** Whenever the Forth version would take its `ABORT"`
path (overflow, underflow, or no buffer), the opcode pushes the
`START`-relative offset exactly as `LIT` did and calls the original
Forth word. That is PEP 659's recipe: specialise single instructions,
so that de-optimisation can never happen mid-region and stays trivial.

Tested by forcing `LSAVE-SP` to both limits through the `forth`
builtin. The Forth underflow message and the resulting state are
identical to the cell engine's, at both widths.

**In the real compiler this is a one-line change.** `L-EMIT` is,
in its own words, "the one place any code is generated" for locals.

### 1.2 Tiny colon words: choose the primitive set by frequency

`0=`, `-`, `CELLS`, `1+`, `1-`, `>`, `<>`, `0<`, `2DUP`, `2DROP`,
`CHAR+`, `CELL+`, `INVERT`, `COUNT` and `ALIGNED` are colon words in
`kernel.4`, two or three primitives long. Together they took 6.4% of
all dispatches as calls, each followed by its body and a return.

Gforth's primitive-centric design and Proebsting's superoperators both
say: pick the VM's instruction set by frequency, not by minimality. In
a byte stream there are free opcodes to do it with, and each becomes 1
byte instead of a 2-byte call.

The translator substitutes an opcode **only where the compiled body is
exactly** the definition the engine implements. It checks this per
address, so a later redefinition of the same name is left alone. All
15 matched at both widths.

### 1.3 Fused global access

A variable read was three dispatches: call, DOVAR, `@`. `VAR@ slot`
does it in one, at the same 3 bytes. This is JVM
`getstatic`/`putstatic` and CPython's specialised `LOAD_GLOBAL`. PEP
659 names global variables, with attribute lookup and calls, among the
largest contributors to its speedup. Here the gain is real but modest:
DOVAR was already a primitive.

### 1.4 Small integers and immediates

**Operand specialisation** is the idea behind JVM `iconst_m1..5`,
YARV's operand unification and CPython's small-int loads.
- `LIT 0` (556 sites), `LIT -1` (222) and `LIT 1` (147) become 1-byte
  opcodes.
- `-1` had been a 5-byte `LIT32`, because `LIT8` is unsigned.

**Immediate arithmetic** came with a warning from Lua. Lua 5.4's
development added immediate-operand opcodes for every arithmetic
operator, then removed all but `OP_ADDI`. The commit message says the
performance difference did not justify the extra opcodes. Following
that lesson, only `ADDI` and `EQI` were built, the two hottest
`LIT n <op>` pairs. **Measured: within noise.** Lua's judgement holds
here too. They are kept only because they are tiny and save 400
bytes; dropping them would lose nothing.

### 1.5 A shared call path (engine size)

GCC copies the whole of `NEXT` into every handler: opcode dispatch,
call decode, `RPUSH` and the stack-limit check.
- Adding 32 handlers grew `.text` by 7.4 KB.
- Keeping the per-handler *opcode* dispatch, which the branch predictor
  wants, while sending calls to one shared `do_call` label cut the
  engine by 5.7 KB (x86-64) and 3.7 KB (i386).
- Speed was unchanged across four layouts.

This is the part of the dispatch-replication literature that matters
for size. Ertl found that replicating dispatch helps prediction.
CPython's 3.14 tail-call analysis found that the *merging* compilers
do can hurt. Neither argues for replicating the cold path.

---

## 2. The survey: what each VM family does

For each family: the design, then what was borrowed and what was not.
Claims about other systems come from their documentation and papers,
with sources at the end. Only the RelF numbers are measured here.

### Forth

**Indirect threading** puts a code field in every word.

**Direct threading** stores code addresses in the thread. RelF's cell
image is this, with relative offsets.

**Subroutine threading** compiles native calls. It is phase 4.

**Token threading** uses indices into a table. That was SOD16.

**Segment threading** (8086) aligned words to 16-byte paragraphs and
used the segment number as the token. It is the precedent for CV8's
compressed-pointer calls.

**Gforth** went primitive-centric so that superinstructions and stack
caching could apply everywhere. It uses stack caching (Ertl, PLDI 1995)
and dynamic superinstructions with replication, which copy native code.

**Open Firmware's FCode** is a byte-token format with 1-byte common
tokens and 2-byte others, detokenized at load.

**SOD32** packed 5-bit subinstructions into a cell. This project
measured that packing costs 21–68% in dispatch (Iteration 157).

- **Borrowed:** primitive selection by frequency (§1.2); stack caching
  (TOS, `CV8.md` §3.3); the segment-threading call.
- **Not borrowed:** dynamic superinstructions and code copying, which
  need native code (phase 4).

### CPython

- 16-bit code units: opcode plus an 8-bit argument, with `EXTENDED_ARG`
  to widen.
- Computed-goto dispatch.
- Since 3.11, the specialising adaptive interpreter (PEP 659):
  instructions rewrite themselves to type-specialised forms and
  deoptimise cheaply.
- Since 3.14, an optional tail-calling interpreter. Its early 10% claim
  was corrected to 3–5% after an LLVM 19 bug was found inflating it.

- **Borrowed:** the specialise-and-deoptimise *shape* (§1.1). It is
  done statically, because Forth has no dynamic types to discover at
  run time. Also local and global access as dedicated instructions.
- **Not borrowed:**
  - inline caches, since there is no dynamic dispatch to cache;
  - the tail-call interpreter, which is single-digit and depends on
    the compiler.

### Ruby (YARV)

- A stack VM whose instruction sequences are translated to
  **direct-threaded** code: every opcode is replaced by its handler's
  address. That is one pointer-sized slot per instruction, like
  today's RelF cell image.
- Operand and instruction unification (specialised and fused
  instructions).
- YJIT, a lazy basic-block-versioning JIT.

- **Borrowed:** operand unification (§1.4).
- **Not borrowed:** direct threading. `CV8.md` §3.3 shows that at this
  shell's size the wide form is slower, because it misses L1d.

### JVM

- Byte-granular variable-length bytecode.
- Short forms for the commonest operands: `iconst_m1..5`, `iload_0..3`,
  `aload_0`.
- `getstatic`/`putstatic` as single instructions.
- In early VMs, "quick" bytecodes rewritten after first resolution.
- HotSpot's compressed oops: `base + (narrow << shift)`.

- **Borrowed:** all of the short-form and fused-access ideas (§1.3,
  §1.4), and compressed oops as CV8's call.
- **Not borrowed:** constant-pool indirection, which is a table load,
  and the template interpreter, which is native code.

### Dalvik / ART

- 16-bit code units in a register VM, chosen for density.

- **Not borrowed:** register VMs are closed for this project (Shi et
  al.: about 46% fewer instructions for about 26% more code).

### Lua

- A register VM since 5.0, with fixed 32-bit instructions.
- 5.4's immediate-operand experiment, kept only for `ADDI` and
  comparisons.

- **Borrowed:** the discipline — few, ubiquitous specialisations
  (§1.4). Measured here, and it held.

### OCaml

- Bytecode on disk, translated to threaded code at load: dense at rest,
  fast in memory.

- **Not borrowed:** load-time translation moves the whole relocation
  pass into the engine and charges it to every start. `start` is a
  measured workload.

### WebAssembly interpreters

- **Titzer's in-place interpreter** runs the compact binary directly,
  with a side table for control flow. It performs on par with engines
  that first rewrite to an internal format.
- **wasm3** uses tail-call "operations".
- **WAMR's fast interpreter** rewrites to a register-like internal
  code.

- **Borrowed:** the conclusion. Interpret the dense form in place and
  let the smaller working set pay for decoding. That is CV8.

---

## 3. What was not borrowed, and why

- **Register VMs.** Closed by measurement elsewhere; the wrong
  direction for size.
- **Inline caching and type specialisation.** Forth cells are untyped
  and calls are static, so there is nothing to cache.
- **Mined superinstructions beyond the specific fusions.** EXIT
  folding, `VAR@`, the tiny-word primitives and the locals opcodes are
  the fusions the profile justified. After them, the hottest remaining
  bigrams (`LIT +` 3.3%, `+ SWAP` 2.5%) are small, and Lua's
  experience and §1.4's result both say the tail is not worth opcodes.
- **Tail-call conversion.** Calls almost never precede `EXIT`
  dynamically (`CV8.md` §3.3), and it risks return-stack semantics.
- **JIT tiers.** These are phase 4. The best fit found is CPython
  3.13's copy-and-patch approach: stencils compiled from C by the
  normal toolchain, patched at run time. It keeps "C compiler as the
  portability layer" and could reuse primitive bodies directly, which
  `GOALS.md` reason 2 already values. Not measured here.

---

## 4. The next density lever is not in the VM

Headers and names are **23 KB of the 66 KB x86-64 image (35%)**.
- Each word pays a cell-wide link.
- Its name is padded to a cell.
- Its body is padded to a cell at the end.

A compact header — 16-bit relative link, count byte, name, padding
only to the call-target alignment — is **estimated** (not built) to
save:
- 8.1 KB (12.3%) on x86-64;
- 2.9 KB (5.5%) on i386.

It needs kernel changes. `FIND`/`SEARCH-WORDLIST` compare names cell
by cell, and the link walk, `>NAME` and `save-system.4` all know the
layout. That is larger than anything left in the VM, and it is a
kernel question.

---

## 5. Reproduce

```sh
bash tools/lab/build-cv8.sh /tmp/cv8-build     # now includes spec-64/-32
# profile + pattern ranking:
cc -O2 -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=3 -DPROFILE=1 ...  # see build-cv8.sh
VMPROF=/tmp/p.txt <engine> <image> tests/bench-vm/loop.sh
python3 tools/lab/patterns.py /tmp/cv8-build/d64.txt 8 /tmp/p.txt
```

Translator: `--spec LIST` with any of `loc`, `var`, `tiny`, `small` and
`imm` (CV8 only). The engine needs `-DSPEC=1`, and preferably
`-DSHAREDCALL=1`.

## Sources

- PEP 659, *Specializing Adaptive Interpreter* (Shannon, 2021).
- CPython tail-calling interpreter: python/cpython#128563 and its
  correction notice; nelhage/cpython-interp-perf.
- Lua `lopcodes.c` history, commit "Removed arithmetic opcodes with
  immediate operand" (2019-09-10).
- Ierusalimschy, de Figueiredo, Celes, *The Implementation of Lua 5.0*,
  J.UCS 11(7), 2005.
- Ertl, *Stack Caching for Interpreters*, PLDI 1995.
- Ertl, *Threaded Code Variations and Optimizations*, EuroForth 2001.
- Proebsting, *Optimizing an ANSI C Interpreter with Superoperators*,
  POPL 1995.
- Shi, Casey, Ertl, Gregg, *Virtual Machine Showdown*, TACO 2008.
- Titzer, *A Fast In-Place Interpreter for WebAssembly*, OOPSLA 2022.
- HotSpot `compressedOops.inline.hpp`; YARV `compile.c`
  (`iseq_translate_direct_threaded_code`).
