# PROGRESS.md — RelF self-hosting project log

Append-only. Newest entries at the bottom. This log exists so future work
(including future Claude sessions, which have no memory of prior ones)
doesn't silently retry a path already found to be wrong.

## 2026-08-31 — Iteration 1: scaffolding

### Context / where this project came from

This repository continues work that started as an unrelated investigation
(comparing SOD32 and RelF VM designs for a "busybox on Forth" project) in a
prior chat session, not committed to git at the time. Relevant findings
from that session, carried forward here because they'll matter for later
phases of this repo specifically:

- **RelF's real-pointer addressing model is why it needs a genuine 32-bit
  process, not just a 4-byte `UNS32` type.** `CELL(reg)` dereferences `reg`
  directly as a host pointer (`*(UNS32*)(reg)`), unlike SOD32's
  array-indexed model (`mem[reg & MEMMASK]`). This means the *process's*
  pointer width must match the declared cell width, not just the C type.
  Hit this twice already in this repo alone (see below) — worth being
  explicit about since it's an easy trap to re-fall into.
- **RelF's asm engine (`vm_tos.asm`, TOS-in-register) beats SOD32's own
  hand-tuned asm engine by 30-50% on call/primitive/memory-heavy
  benchmarks**, even after crediting SOD32 with maximally dense opcode
  packing. Working hypothesis (not confirmed by disassembly/profiling):
  native x86 `push`/`pop` for the data stack gets near-free pointer
  tracking from the CPU's dedicated stack engine; SOD32's manual
  array-indexed `sp`/`rp` arithmetic pays a real ALU cost SOD32's opcode
  packing doesn't fully offset.
- **A hybrid (SOD32-style packed dispatch + RelF-style native-stack
  primitive bodies + relative addressing) was built and benchmarked.** It
  beat plain SOD32 by ~20% but did not close the gap to RelF (RelF still
  27-39% faster). Not part of this repo's plan — noted so it isn't
  reinvented. RelF's primitive bodies are self-contained (assume only
  "TOS in one register, rest on the stack"), unlike SOD32/hybrid's, which
  are coupled to shared packed-dispatch state (`PREPARE`/`NEXTINSTR`
  macros) — this reusability is part of why RelF, not the hybrid, was
  chosen as the basis for this project. See "Why RelF, not the hybrid or
  SOD32" below.
- **Relative addressing costs nothing (possibly slightly negative,
  i.e. free-or-better) vs. absolute** — measured directly, not assumed.
- **JIT/AOT compiling colon-word bodies to native code is a much bigger
  lever than any interpreter-level tuning** — 4-4.75x from removing
  dispatch overhead alone (keeping real `call`/`ret`), a further ~2-2.2x
  from inlining non-recursive calls on top of that. This is the long-term
  target this repo is working toward; the self-hosted *engine* assembler
  (this iteration's eventual goal) is a prerequisite building block for it,
  since the JIT's code-emission machinery is meant to reuse the same
  encoder.

None of the above numbers are re-derived in this repo yet — they're
carried over as motivation/direction, not verified here. Treat them as
"why we're doing this," not as facts about this specific codebase's state.

### Why RelF, not the hybrid or SOD32, as the basis for this project

Three reasons, in order of how directly they matter to *this* repo's goal
(self-hosting, eventually a JIT):

1. It's the fastest of the three designs actually measured, at every
   configuration tried.
2. Its primitive bodies are individually reusable as JIT code templates
   with no rewriting (self-contained register convention). SOD32/hybrid's
   are coupled to shared packed-dispatch state and would need a second,
   separate set of bodies just for JIT purposes.
3. Its bytecode format (one token or one relative offset per cell) is
   simpler for a Forth-hosted metacompiler to emit than SOD32's packed
   5-bit-fields-per-cell format, which needs cell-boundary and ret-flag
   bookkeeping the metacompiler has to get right.

### Repo direction (per owner's decisions this iteration)

- Old i386/libc-based files (`relf.c`, `vm.asm`, `vm_tos.asm`) will be
  replaced/refactored in place over time, not preserved in a side
  directory — the intent is a leaner successor, not a fork-with-extras.
  Not done yet this iteration (see "What this iteration did / didn't do").
- Single branch (`master`, matching upstream `kt97679/relf`), linear
  history, no feature branches.
- Test suite: `forth2012-test-suite` full ANS/Forth-2012 compliance is a
  future target, not now — RelF's primitive/word set is far smaller.
  Started by adding directly-applicable tests now, expanding later.
- Eventual target: push back to `kt97679/relf` upstream.
- Priority ordering: **simplicity and minimalism** above all else,
  including above raw performance where they trade off.
- End state: the engine relies on no libraries at all, talking to the OS
  via raw syscalls only. This applies to the *engine's runtime*
  (currently uses libc `fopen`/`printf`/`exit`/`getchar` etc. via
  `relf.c`) — it does **not** mean avoiding `gcc`/`as`/`ld` as build-time
  tools during bootstrap; those stay until the self-hosted assembler
  replaces them. Side benefit noted, not yet acted on: going fully
  static/no-libc means no PLT/GOT/dynamic-linker involvement at all,
  which will sidestep an entire class of `-no-pie`/PIE linking bugs hit
  repeatedly in the prior session's exploratory work.

### Bugs found and fixed this iteration

**Bug 1 — `UNS32`/`INT32` defined as `unsigned long`/`long`.** On the
i386 platform RelF targeted, `unsigned long` is 4 bytes; on this x86_64
host it's 8, silently breaking every 4-byte-cell memory access. This is
the exact issue upstream's own commit `25d3c0b` ("relf is not working on
the 64 bit platforms") documented in 2016 without fixing — it recommended
compiling 32-bit instead. Fixed here by changing the typedefs to
`unsigned int`/`int` (matching SOD32's own header, which avoids this trap
already). **This alone is not sufficient** — see Bug 2.

**Bug 2 (re-discovered from prior session, forgotten and re-hit once
already this iteration) — even with `UNS32` correctly sized, RelF still
needs a genuine 32-bit *process*.** `CELL(reg)` dereferences `reg`
directly as a real host pointer, not an array index. A 64-bit process's
real pointers don't fit in a 4-byte `UNS32`, so addresses truncate and
the engine segfaults or corrupts memory. Must build with `gcc -m32`.
**Do not attempt to "fix" this by widening `UNS32` to 8 bytes on a
64-bit build** — that changes the cell width and breaks the existing
`kernel.img`, which was compiled assuming 4-byte cells. The 32-bit build
is correct as-is for the current kernel image; a real 64-bit *cell*
version is a distinct, deliberate future project (also explored in the
prior session — see "Context" above), not a side effect of chasing this
bug.

**Bug 3 — engine hangs (does not exit) on EOF from stdin when no `BYE`
is reached.** Confirmed by running the bundled `tester.fr` suite: without
an appended `BYE`, the process runs all tests correctly (1841 `OK`,
zero errors) but then hangs indefinitely rather than exiting — `timeout`
killed it (exit 124) rather than it exiting on its own. With `BYE`
appended after the test file, exit code 0, same 1841 `OK`s, zero errors.
**Not fixed yet** — noted because it's directly relevant to the
syscall-based rewrite: a raw `read()` returning 0 at EOF should be
treated as "exit cleanly," and currently isn't. Test runner works around
this for now by always appending `BYE`.

### What this iteration did

- Applied Bug 1's fix to `relf.c` (`UNS32`/`INT32` → `unsigned int`/`int`).
- Confirmed the *existing, bundled* `tester.fr` — a working copy of John
  Hayes's 1993 CORE word test suite, already adapted to RelF's `{ -> }`
  test syntax (an earlier convention than the `T{ -> }T` used by the
  modern forth2012-test-suite) — passes cleanly end to end (1841 `OK`,
  0 errors) once both bugs above are worked around. This is a
  significantly better starting position than expected: a comprehensive,
  already-adapted regression suite already exists in the repo and was
  simply never being run in CI/automation.
- Added `tests/run_tests.sh`, a minimal test runner that builds `relf`,
  runs `tester.fr` (with `BYE` appended per Bug 3's workaround) through
  it, and fails loudly on any `ERROR`/non-zero exit/non-"OK" output.
  Verified end to end: full pass, 1892 `OK` markers, 0 errors.
- Note (not a bug, not fixed, not worth fixing): `gcc -m32` on `relf.c`
  produces many `-Wimplicit-int`/`-Wimplicit-function-declaration`
  warnings — expected from ~20-year-old pre-C99 K&R-style C compiled by
  a modern compiler default-strict about implicit declarations. Harmless,
  does not affect correctness (all tests pass), not addressed here since
  this file's C form is being replaced/refactored per the repo direction
  above, not incrementally modernized.
- Added a handful of small, directly-applicable tests adapted from
  `forth2012-test-suite`'s `src/core.fr` (arithmetic/stack/boolean ops),
  written in RelF's own `{ -> }` convention rather than porting the
  `T{ -> }T` framework wholesale — that framework needs infrastructure
  RelF doesn't have yet (see forth2012-test-suite scope decision above).
  Kept the suite's copyright notice attached per its terms ("MAY BE
  DISTRIBUTED FREELY AS LONG AS THIS COPYRIGHT NOTICE REMAINS").

### What this iteration deliberately did NOT do

Per the owner's explicit phase-1 scope ("scaffolding + test runner +
process log first, minimal engine changes") — these are next-iteration
work, not forgotten:

- Did not remove libc / move to raw syscalls yet.
- Did not touch `vm.asm`/`vm_tos.asm`/`relfgcc.c` at all.
- Did not restructure/replace old files in place yet (planned, per
  owner's decision above, but not started).
- Did not port the modern `T{ -> }T` forth2012-test-suite harness itself,
  only borrowed a few test values in RelF's existing convention.
- Did not investigate or fix Bug 3 (EOF hang) — logged, not fixed.
- Did not touch `relfgcc.c` (the labels-as-values GCC variant) — it has
  its own, different 64-bit trap (computed-goto target addresses stored
  in a `UNS32`-sized slot truncate on a 64-bit build for the same
  fundamental reason as Bug 2, but the fix isn't just `-m32` compatible
  in the same simple way since it was already observed in the prior
  session to need extra header-inclusion fixes even to compile at
  `-m32`). Low priority — `vm_tos.asm` is the actual performance-relevant
  target per "Why RelF" above, `relfgcc.c` was never the fast path.
