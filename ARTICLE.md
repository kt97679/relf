# ARTICLE.md — notes for the write-up on the VM evolution

Working notes for an article about how this project's virtual machine
got to where it is. Nothing here is a design document; `CV8.md`,
`CV8-REFERENCE.md`, `attic/docs/VM-SURVEY.md` and `XARCH.md` are. This file exists
so that the *story* — especially the parts where a measurement
overturned the previous conclusion — is not lost as the code moves on.

**Rule for future iterations: when a change invalidates a number or a
claim quoted below, correct it HERE as well as in PROGRESS.md.** The
corrections are the most valuable part of the material and the easiest
to lose.

---

## 1. The chain, in order, with what was actually built

A first draft of the chain was "SOD32 → RelF → nibble packing → byte
packing → SOD16 → CV8". That is the right spine but it drops five
links, and it blurs a distinction the article must keep.

| # | design | what it is | status |
|---|---|---|---|
| 1 | **SOD32** (L.C. Benschop) | 5-bit fields packed into a 32-bit cell; separated engine and machine-independent image | pre-existing system |
| 2 | **RelF** (Kirill Timofeev) | one relative offset or token per cell; assembly engines `vm.asm`, `vm_tos.asm` | pre-existing system |
| 3 | **the hybrid** | SOD32's opcode packing on RelF's stack mechanism | **built and benchmarked in prior exploratory work, then dropped** |
| 4 | **portable C engine** | `relf.c`, computed-goto dispatch, asm engines deleted (phase 2) | built, is the mainline today |
| 5 | **the tagged family** | tag-in-low-bits (iters 132, 133); payload-above-index (134); SOD32 5-bit; SOD32+inline literals; tagged nibble 4-bit×7; tagged byte 8-bit; tagged byte + hot-call | **modelled and micro-benchmarked only** |
| 6 | **variable-length tokens** | varint forms (iter 158, `tools/varint-bench.c`) | modelled only |
| 7 | **SOD16** | uniform 16-bit tokens; ≥256 is a WORD NUMBER indexing a table built at load | **built**, branch `token16` |
| 8 | **CPT16** | same tokens, table DELETED: a call is `base + (v << S)` | **built** |
| 9 | **CV8** | CPT16 with the unit narrowed to one byte; calls 2–3 bytes | **built**, branch `cv8` |
| 10 | **the specialisations** | locals as opcodes, tiny kernel words as opcodes, `prim;EXIT` folding, `VAR@`, small ints | **built**; worth more than the encoding change |

**The distinction to keep:** rows 5 and 6 were *costed*, not built —
size-modelled from a real dictionary census and dispatch-microbenchmarked
in isolation (`tools/pack-bench.c`, `tools/varint-bench.c`,
`tools/dispatch-bench.c`). Only rows 1, 2, 3, 4, 7, 8, 9, 10 ever ran
real code. Presenting the whole table as implemented VMs would
overclaim.

### Links the first draft dropped

- **the hybrid (3)** — it is *why* RelF was chosen; without it the
  choice looks arbitrary;
- **the move to a portable C engine (4)** — it changes what every
  later comparison means (see §3);
- **the tagged family is six schemes, not two** — "nibble packing" and
  "byte packing" are two rows of it;
- **CPT16 (8)** — the pivot: deleting the table is what makes a byte
  stream possible;
- **the specialisations (10)** — a separate stage, and the larger win.

---

## 2. The corrections — the most useful material

An article that presents this as a clean march to a good design would
be both boring and false. Four times a measurement overturned the
previous conclusion, and three of those were this project correcting
itself.

**(a) Iteration 158 corrects 157 — the cache artifact.** 157 reported
token threading at 0.985, i.e. *faster* than cell dispatch, and
concluded it "costs nothing". The benchmark's cell stream was 32 MB
against the byte stream's 6.8 MB on a machine with 2 MB of L2: it was
measuring memory traffic and being read as a decode result. Varying the
working set gave 1.063 (16 KB), 1.064 (128 KB), 1.059 (1 MB), 1.002
(32 MB). Token threading costs **~6% in decode**, repaid only when the
working set is large.

**(b) Iteration 191 corrects `CV8.md` §3.3 — the same mistake again, by
me.** I attributed CV8's speed over the cell engine to L1d misses, on
cachegrind *counts* (243K vs 9K). Weighed against instruction counts the
rates are 0.06% vs 0.012% — worth roughly 1–3% of run time, not the
explanation. The real causes were EXIT folding and TOS caching.

**(c) Iteration 189 overturns the design brief.** `attic/docs/INNER-INTERPRETER.md`
attributed SOD16's 1.25x slowdown to the word table's dependent load.
It was mostly two other things: VM registers living in file-scope
statics (~20%, because a cell store may alias them, so GCC reloaded `ip`
around every dispatch) and NOOP padding that was actually *executed*
(17.3% of all dispatches). The table's own cost was below noise.

**(d) The asm-engine prediction.** I predicted hand-written assembly
would be a wash. Measured: **20% faster** and 7% *larger* than GCC's
code for the same 63 handlers. Wrong about the direction of both.

---

## 3. Claims that need re-verification before publishing

- **"SOD32 is 27–51% slower than RelF"** (`GOALS.md`). Measured against
  the *assembly* engines, which were deleted in phase 2. `GOALS.md`
  itself carries a caveat dated 2026-09-01: the portable C engine
  manages the data stack manually, which is architecturally closer to
  SOD32 than to what was benchmarked. **Do not quote this number
  without re-measuring or labelling it as historical.**
- **The Iteration 156 size census** used 1,059 words and an older
  dictionary; `attic/docs/ENCODING-COMPARISON.md` warns not to quote its 156
  numbers.
- All timings in this repo are from **one** machine: an Intel Xeon
  under KVM, one vCPU. ARM and RISC-V figures are qemu *instruction
  counts*, not timings.
- **Code layout moves an engine ±4–5%** with no semantic change; one
  engine got 8% faster by containing handlers it never ran. Any
  single-build comparison under ~8% in the history is suspect.

---

## 4. Numbers worth quoting (current, this branch)

Image size, whole shell image:

| | x86-64 | i386 |
|---|---|---|
| cell (today's `relf`) | 206,416 | 109,876 |
| SOD16 / CPT16 | 84,032 | 70,864 |
| CV8 + specialisations | 66,144 | 52,820 |

Speed, shell workloads, against the committed `token16` engine: CV8 +
specialisations is **~5x** (0.17–0.23). On *general* Forth code (a
kernel-only benchmark) it is **~2.0–2.4x** — the difference is that the
specialisations target what shell code does, and that distinction
belongs in the article.

Per stage, relative to the previous one: registers-as-locals 0.82;
CV8 over that ~0.68 (x86-64); specialisations 0.33 of CV8.

Cross-architecture (qemu instruction counts, vs `token16`): the
specialisations hold at 0.13–0.24 on x86-64, AArch64, ARMv7 and
RISC-V 64; registers-as-locals is *better* on RISC (0.67) than on x86
(0.75); CV8 alone is largely an x86 effect (a CV8 dispatch costs 1–2
more instructions everywhere).

---

## 4a. Measured tables the article will want

### The tiny kernel words (`attic/docs/VM-SURVEY.md` §7.4)

Two- and three-operation colon words in `kernel.4`, turned into opcodes.
Static call sites are from the shell image before substitution; dynamic
is executions of the word's body across the four bench workloads
(371.9M dispatches total).

| word | definition | static sites | dynamic |
|---|---|---|---|
| `0=` | `0 =` | 226 | **11.99M** |
| `1+` | `1 +` | **337** | 2.32M |
| `CHAR+` | `1 +` | 7 | 3.22M |
| `CELLS` | `n LSHIFT` | 116 | 1.53M |
| `-` | `NEGATE +` | 92 | 1.75M |
| `>` | `SWAP <` | 96 | 0.41M |
| `1-` | `-1 +` | 91 | 0.46M |
| `2DROP` | `DROP DROP` | 54 | 0.32M |
| `<>` | `= 0=` | 42 | 1.73M |
| `2DUP` | `OVER OVER` | 39 | 1.37M |
| `CELL+` | `CELL +` | 23 | 0.65M |
| `0<` | `0 <` | 13 | 0.23M |
| `COUNT` | `DUP 1+ SWAP C@` | 13 | 0.77M |
| `ALIGNED` | `CELL 1- + CELL NEGATE AND` | 8 | 0.77M |
| `INVERT` | `-1 XOR` | 1 | ~0 |

Total 1,158 static sites, 27.5M executions = **7.4% of all dispatches**.
Worth 0.75-0.82x on top of CV8. The distribution is heavily skewed:
`0=` alone is 44% of the dynamic total, and eight of the fifteen
capture ~90% of it. `INVERT` earns nothing and is in the set only
because it matched the pattern.

### The opcode budget

128 opcodes below the call band. Occupied: 68 primitives, 5 literal and
data forms, 23 folded `prim;EXIT`, 28 specialised, `LIT64`, `ESC`.

| configuration | free |
|---|---|
| as shipped (escape off) | **2** |
| with the escaped band | 34 |
| escaped band + tiny set trimmed to 8 | 41 |

Plus 256 reserved behind `ESC`, which is claimed but unimplemented.
This is the design's scarcest resource and the reason the escaped band
matters: it is what stands between "two spare" and "comfortable".

---

## 5. Ideas borrowed, and from where

For the "where the ideas came from" section the reviewer asked for.
Full table in `attic/docs/VM-SURVEY.md` §2; short form:

- separated engine + portable image — **SOD32**
- relative (position-independent) references — **RelF**
- byte-granular instruction stream — **JVM**, Open Firmware **FCode**
- `base + (value << shift)` as a pointer — **HotSpot compressed oops**;
  8086 Forth **segment threading**
- one-byte forms for common constants — **JVM** `iconst_*`, **YARV**
  operand unification
- locals as one-instruction slot access — **JVM** `iload`/`istore`,
  **CPython** `LOAD_FAST`, **Smalltalk-80** bytecodes 16–31
  ("push temporary variable 0–15")
- specialise the common case, deoptimise the rest — **CPython 3.11**,
  PEP 659
- choosing the primitive set by frequency — **Gforth**, Proebsting's
  superoperators
- small immediate operands — **Lua 5.4** `OP_ADDI`/`OP_EQI` (and Lua's
  own decision to keep only those, which we confirmed: ours measured
  within noise)
- interpreting the compact form in place rather than expanding at load
  — **Titzer's** in-place Wasm interpreter, *against* **OCaml** and
  **YARV**, which both expand to threaded code when loading

Before publishing, verify the FCode encoding details against IEEE 1275;
the general shape (byte tokens with an escape for two-byte codes) is
remembered, the exact ranges are not.

---

## 6. Threads the reviewer opened that the article should mention

These are open questions, not results, but they are the honest edge of
the work:

- **IP-relative calls** instead of base-relative: measured 99.8% of
  calls fit a signed 14-bit scaled field, and it would delete the
  window, the far-call plan and the module-base design. Needs the
  low bits of IP masked, since the difference is not aligned.
- **The kernel reachable as opcodes**, which removes the one argument
  against IP-relative (a distant word calling `DUP`).
- **ITC vs token threading**: with token threading a new behaviour type
  cannot be added from Forth — `DOES>` is the only extension point.
  This is the strongest architectural criticism the design has had.
- **Freezing a live image** and moving it between architectures: the
  dictionary is portable today, but stacks hold absolute addresses, so
  a snapshot needs a pointer map.
- **16-bit cells (MSP430)**: the format is already parameterised;
  the translator just does not know width 2 yet.

---

## 7. Where the material lives

- `PROGRESS.md` — the full iteration log, and the primary source.
- `GOALS.md` §"Why RelF specifically" — the prehistory and its caveat.
- `attic/docs/ENCODING-COMPARISON.md` — the size census and the dispatch costs.
- `CV8.md` — why CV8, with the method section on layout noise.
- `CV8-REFERENCE.md` — the format, with worked byte examples.
- `attic/docs/VM-SURVEY.md` — what other VMs do and what was borrowed.
- `XARCH.md` — ARM/RISC-V, and correction (b).
- `tools/pack-bench.c`, `varint-bench.c`, `dispatch-bench.c` — the
  microbenchmarks behind rows 5 and 6.
- `tools/lab/` — everything from Iteration 188 on.

---

## 8. Benchmarking for the article

**The shell workloads are not a fair VM benchmark** and the article
must not lead with them. They are dominated by locals and variable
access, which is exactly what the specialisations target - hence the
same build measures ~5x on shell code and ~2.0-2.4x on kernel code.
Quoting 5x as "the VM got 5x faster" would overstate it.

Suggested set, best first:

1. **Recompiling the kernel** - real self-hosting work, exercises the
   compiler and the dictionary rather than one idiom, and cannot be
   accused of being tuned to the encoding. `tests/verify` already does
   a reproducible build, so the harness exists.
2. **The ANS CORE suite run** (671 cases, `tools/lab/forth-tests.sh`) -
   compiles hundreds of definitions; compile-heavy rather than
   execution-heavy, so a useful second axis.
3. **`fib.4`** - narrow (calls and arithmetic), but readers expect it.
4. **One shell workload, clearly labelled** as "what the system is
   actually for", never as the headline.

Report kernel recompile as the headline with shell as a separate line,
and say plainly why they differ. Take all numbers from ONE build of the
committed branch: the figures in this repository accumulated across
many iterations and several were superseded (varcall became the
default, guard pages and the escaped band are opt-in and incomplete).

**Tooling gap to fix first if per-word dynamic data is wanted again:**
the CV8 path of `vm-lab.c -DPROFILE` records per-address counts but not
call targets (`PROFC` is only in the ENC=2 path), so `tools/lab/hot.py`
returns nothing for CV8 images. The tables above were produced by
mapping the per-address `I` records onto `--symbols` output instead.

---

---

## 9. For the honesty section

The article's most useful material is where the work was wrong, and
the log has more than the four corrections in §2:

- **72 empty files committed** (Iteration 204, removed in 208). Piping
  `tester.fr` into an image that boots into the SHELL makes the shell
  read `->` and `>` as redirections, creating one file per token; then
  `git add -A` committed them. The harness now refuses an image that
  does not boot into the interpreter.
- **A test that could not fail.** For several iterations the only
  suites being run were the shell ones, which never compile anything -
  so they passed long before the Forth compiler was correct. The ANS
  CORE suite, run for the first time in Iteration 204, both validated
  the compiler (671/671) and immediately found a fault the shell suites
  could not see.
- **A fixed point is not cleanliness.** Two generations of a saved
  image being byte-identical proves the save is self-consistent, not
  that the saved state is clean: state that is stale but *stable* looks
  identical in both. Diffing against a different, working build found
  22 more variables that generation-diffing could not.
