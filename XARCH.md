# XARCH.md — AArch64, ARMv7 and RISC-V, under qemu

Iteration 191, branch `cv8`. This file checks whether `CV8.md` and
`VM-SURVEY.md`, measured on one x86 machine, hold on the other ISAs
that matter to a small shell: 64-bit ARM, 32-bit ARM and RISC-V. The
tools are in `tools/lab/xarch/` (see its README), and the raw results
are the `results-*.txt` files there.

## 0. What qemu can and cannot say

**qemu-user wall time is not a performance measure.** On AArch64
`loop`, CV8 executes 8% fewer instructions than `relf-new`, yet runs
longer under qemu (5.9 s against 5.8 s). qemu's cost is dominated by
translating guest indirect branches, and a threaded interpreter does
one per dispatch.

The three things measured here are:

1. **Correctness** on the real instruction sets. Every engine/image
   pair matches `dash` on three architectures. The specialised engine
   passes `tests/diff` under qemu (§4).
2. **Exact guest instruction counts**, from qemu's `libinsn` plugin.
   qemu 8.2.2 was built from source, because Ubuntu's package has no
   plugin support. On in-order cores (Cortex-A7/A53/A55, most RISC-V
   boards) instruction count is a much better proxy for run time than
   on the out-of-order x86 where everything else was timed.
3. **A simulated L1**, from qemu's `contrib/plugins/cache.c`: 32 KB,
   4-way, 64-byte lines, roughly a Cortex-A53/A7 or SiFive U74. x86 is
   given the same model through cachegrind.

**Branch prediction is not modelled by anything here.** Any conclusion
that rests on it — EXIT folding's x86 gain, and TOS on ARM32 — still
needs real hardware.

**Images are portable.** The same cell-width image, built once on x86,
runs unchanged on every architecture. It was never tested before: 12
of 12 engine/image pairs run correctly.

## 1. Instructions, relative to today's engine

Whole runs, `relf-old` = the committed `token16` engine = 1.00. The
x86-64 row covers `fn` and `str` only, from cachegrind; the others are
qemu `libinsn`.

| | x86-64 | AArch64 | ARMv7 | RISC-V 64 |
|---|---|---|---|---|
| `relf-new` (registers as locals) | 0.75–0.76 | 0.67 | 0.71 | 0.69–0.70 |
| CV8 | 0.61–0.64 | 0.60–0.62 | 0.60–0.62 | 0.63–0.67 |
| **CV8 + specialisations** | **0.13–0.22** | **0.13–0.23** | **0.13–0.22** | **0.15–0.24** |

The same results relative to `relf-new`, which is the fairer baseline
now that the register fix is committed:

| CV8 + specialisations ÷ `relf-new` | loop | fn | str | arith |
|---|---|---|---|---|
| AArch64 | 0.24 | 0.34 | 0.20 | 0.24 |
| ARMv7 | 0.19 | 0.31 | 0.18 | 0.20 |
| RISC-V 64 | 0.25 | 0.34 | 0.22 | 0.25 |

**Startup** (`-c true`), in millions of instructions:

| | `relf-old` | `relf-new` | CV8 | CV8 + spec |
|---|---|---|---|---|
| AArch64 | 8.54 | 5.78 | 5.41 | 2.74 |
| ARMv7 | 16.06 | 11.58 | 10.16 | 5.38 |
| RISC-V 64 | 9.38 | 6.61 | 6.27 | 3.12 |

## 2. Instructions per dispatch

Dispatch counts come from `vm-lab.c -DPROFILE` on x86. They are
identical on every ISA for the same image. Startup is subtracted.

| | `relf-old` | `relf-new` | CV8 | CV8 + spec |
|---|---|---|---|---|
| x86-64 | 16.9–17.2 | 12.6–13.0 | 13.4–13.5 | 12.3–12.9 |
| AArch64 | 15.9–16.4 | 10.6–10.9 | 12.4–12.5 | 12.0–12.6 |
| ARMv7 | 18.1–18.7 | 12.9–13.3 | 14.2–14.3 | 14.0–14.6 |
| RISC-V 64 | 17.5–17.9 | 12.1–12.5 | 14.4–14.6 | 13.7–15.5 |

What this shows:

- **The register fix is worth more on RISC ISAs than on x86.** It
  removes a third of all AArch64 instructions, against a quarter on
  x86. Static `ip` and `rp` cost a load and a store per use on a
  load/store machine.
- **A CV8 dispatch costs 1–2 instructions more than a fixed-width
  cell dispatch** everywhere: the byte decode, the opcode/call test,
  and TOS bookkeeping. CV8 alone therefore removes only 7–15% of
  instructions against `relf-new` (dispatches −22%). On an in-order
  core, CV8 *by itself* should gain far less than the 0.68 it showed
  on x86.
- **The specialisations remove work on every ISA.** They cut
  dispatches to a fifth of the cell engine's, and instructions follow
  within a few percent. That is why they transfer and CV8 alone may
  not.
- **RISC-V is the most expensive decoder.** It has no scaled-index
  load (without Zba), no compare-immediate-and-branch, and GCC
  rematerialised `li 127` on every dispatch. §3's sign test removes
  the last of these.

## 3. Two engine changes found here

**Byte-composed operand loads.** CV8's 16- and 32-bit operands are
unaligned. `LD16`/`LD32` used `memcpy`, which on RISC-V compiled, in a
standalone test, to byte loads, a stack round trip and a
stack-protector check. Composing from bytes compiles to one
`ldrh`/`movzwl` on ARMv7, AArch64 and x86, and four instructions on
RISC-V.

Inside the real engine GCC had already avoided most of the round trip:
RISC-V `virtual_machine` went from 1,779 to 1,775 instructions. It is
kept because it is never worse, and because it makes operand byte
order explicit rather than the host's.

**Sign-tested dispatch** (`SIGNTEST`). The byte is loaded
sign-extended, so "opcode" is `t >= 0`: one branch-on-sign with no
constant and no compare. Guest instructions on `fn` with the
specialised engine:

| | off | on | |
|---|---|---|---|
| AArch64 | 1,149.8M | 1,108.7M | −3.6% |
| RISC-V 64 | 1,315.9M | 1,260.4M | −4.2% |
| x86-64 | 1,175.7M | 1,173.5M | −0.2% |
| i386 | 1,020.6M | 1,017.7M | −0.3% |
| ARMv7 | 1,220.0M | 1,256.8M | **+3.0%** |

It is on by default except on 32-bit ARM. These are instruction
counts, not timings.

## 4. Correctness under qemu

- All 12 engine/image pairs match `dash` on the `fn`, `str` and
  `arith` workloads.
- The specialised engine, in its final per-arch build (SIGNTEST on
  AArch64/RISC-V, off on ARMv7), was run through `tests/diff` under
  qemu. The results are recorded in `PROGRESS.md`, Iteration 191.
- `tests/shell` was not run under qemu; it is roughly 25 minutes per
  architecture there.

## 5. The cache, and a correction to `CV8.md`

Simulated L1d data misses on scaled workloads, 32 KB 4-way. The x86
rows are cachegrind on the full workloads with the same model.

| misses | `relf-old` | `relf-new` | CV8 | CV8 + spec |
|---|---|---|---|---|
| AArch64 fn60 / str40 | 202K / 202K | 195K / 198K | 39K / 31K | 28K / 24K |
| ARMv7 fn60 / str40 | 73K / 67K | 72K / 67K | 20K / 15K | 18K / 15K |
| RISC-V fn60 / str40 | 178K / 183K | 176K / 181K | 40K / 29K | 36K / 31K |
| x86-64 fn / str | 1.69M / 1.71M | 1.69M / 1.71M | 332K / 279K | 234K / 175K |

**Token code misses about 5x less** on every ISA. The 32-bit cell
image is half the size of the 64-bit one, and misses correspondingly
less.

**But the rates are tiny, and `CV8.md` §3.3 overstated their weight.**
- `relf-new` on AArch64 misses 195K times in 342M instructions:
  0.06%. CV8 is at 0.012%.
- At the 15–60 cycles an L1 miss costs, that is roughly 1–3% of run
  time. It cannot account for CV8's x86 speedup over `relf-new`
  (about 0.68).
- `CV8.md` attributed "token vs cell" to L1d misses from cachegrind's
  *counts* without weighing them. The counts were right; the
  attribution was not.
- CV8's x86 gain must come mainly from EXIT folding (fewer and
  better-predicted dispatches; −26% mispredictions in cachegrind's
  model) and from TOS caching (fewer data accesses: 1.11G against
  1.26G on `fn`). Both depend on the microarchitecture. That is one
  more reason the in-order-core question needs real hardware.

## 6. What this changes

- **Nothing in the recommendation.** The specialisations are
  ISA-independent wins: 0.19–0.34 of `relf-new`'s instructions on all
  three ISAs. The register fix is a bigger win on RISC than on x86.
  CV8's density holds everywhere, because it is a property of the
  image.
- **CV8's speed claim is x86-specific.** On in-order cores, expect
  CV8 without the specialisations to be roughly level with
  `relf-new`: 7–15% fewer instructions, but more expensive
  dispatches. Its case there rests on density, and on being the
  encoding the specialisations are built in.
- **Still unknown without hardware:** TOS caching on ARM32 (register
  pressure; i386 showed it can hurt), and whether folding's
  prediction gain appears on cores with simpler predictors.
