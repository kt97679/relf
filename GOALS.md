# GOALS.md — RelF self-hosting project

Stable reference document. Changes rarely, and only when the project's
actual direction changes — not a log. For "what happened and when," see
`PROGRESS.md` instead. Read this file first when starting a new session;
it's meant to make that possible without re-reading full chat history.

## What this is

A refactor of RelF (Kirill Timofeev's SOD32-derived Forth VM,
https://github.com/kt97679/relf) working toward:

1. **Full self-hosting** — eliminating every external dependency until
   the system compiles itself, including its own engine, not just its
   own Forth-level dictionary/image (which it already does, via
   `cross.4th`/`extend.4`).
2. **Eventually, JIT/AOT native-code generation** for speed, built as a
   natural extension of the same self-hosted compiler machinery, not a
   separate C-based subsystem.
3. **Minimalism and simplicity as the top priority** — above raw
   performance, when the two trade off against each other.

## Why RelF specifically, not SOD32 or a hybrid design

This was decided after directly benchmarking multiple VM designs (SOD32,
RelF, and a hand-built hybrid combining SOD32's opcode-packing with
RelF's stack mechanism) in prior exploratory work. Three reasons, in
order of how directly they matter to *this* project's actual goal:

1. **RelF is the fastest of the designs measured**, at both 32-bit and
   64-bit, including after crediting SOD32 with maximally dense opcode
   packing (SOD32 still 27-51% slower across benchmarks). Working
   hypothesis for why (not confirmed by disassembly/profiling): RelF's
   primitive bodies use the real x86 `push`/`pop` stack directly, which
   gets near-free pointer tracking from the CPU's own stack engine;
   SOD32's manual array-indexed `sp`/`rp` arithmetic pays a real,
   measurable ALU cost that its opcode-packing advantage doesn't fully
   offset.
2. **RelF's primitive bodies are individually reusable as JIT code
   templates with no rewriting** — each one only assumes "TOS in one
   register, everything else on the real stack," no shared dispatch
   state. SOD32/hybrid's primitive bodies are coupled to shared
   packed-dispatch machinery (`PREPARE`/`NEXTINSTR`-style macros in the
   asm engine) and would need a *second*, separate set of bodies just
   for JIT purposes. This matters a lot for goal 2 above.
3. **RelF's bytecode format is simpler for a Forth-hosted metacompiler
   to emit** — one token or one relative offset per cell, versus SOD32's
   packed 5-bit-fields-per-cell format, which needs cell-boundary and
   ret-flag bookkeeping the metacompiler has to get right. Matters for
   goal 1.

## A load-bearing architectural fact about RelF (know this before
touching the engine)

RelF's `CELL(reg)` macro dereferences `reg` **directly as a real host
pointer**, not as an index into an isolated array (unlike SOD32, which
does `mem[reg & MEMMASK]`). This means the *process's own pointer width*
must match the VM's declared cell width — not just the C type width.
This has caused real, confirmed bugs already (see `PROGRESS.md`,
2026-08-31 and 2026-09-01 entries). As of phase 2 (2026-09-01), this is
resolved for good: the engine is a genuine x86-64 process with 8-byte
cells, so process pointer width and cell width match natively, with no
`-m32` special-casing required. It is a deliberate design property of
RelF (it's what gives RelF its relative/relocatable addressing), not a
bug to "fix away."

A second, less obvious load-bearing fact, discovered while migrating to
8-byte cells (see `PROGRESS.md`, 2026-09-01): **the *host* used to
cross-compile a new `kernel.img` must itself have cells at least as wide
as the *target* cell width being compiled**, because `cross.4`'s
literal-parsing and `@-T`/`!-T` plumbing does host-cell arithmetic on
values that end up in target cells. `cross.4`/`kernel.4` also hand-embed
a handful of raw primitive-dispatch token numbers (for `LIT`, `EXIT`,
`BRANCH`, `0BRANCH`, `R>`) that must be updated by hand whenever the
primitive-token stride changes (it's tied to `sizeof(host function
pointer)` — 8 on x86-64). Both of these are silent, non-obviously-broken
failure modes if missed: the first quietly truncates/corrupts large or
negative literals; the second segfaults the *next* engine at whatever
primitive happens to land on the stale token value. See `PROGRESS.md` for
the full account and the fixes applied.

## End state (what "done" looks like)

- **No libraries.** The engine talks to the OS via raw syscalls only —
  no libc. **Done as of phase 2** (`relf.c`, built `-nostdlib -static`,
  hand-written syscall wrappers, custom `_start`). This applies to the
  *engine's runtime*, not to build-time bootstrap tooling: `gcc`/`as`/`ld`
  remain fine to use for building the engine until phase 3 below (a
  self-hosted assembler) replaces them.
- **Fully self-hosted.** Forth already compiles the Forth image
  (`cross.4` → `kernel.img`), now with 8-byte target cells matching the
  engine's own pointer width. The remaining piece is Forth compiling the
  *engine itself* (currently `relf.c`, built by `gcc`) — a Forth-hosted
  native-code assembler, in the tradition of the classic Forth
  `ASSEMBLER` wordset / `CODE ... END-CODE` facility.
- **Eventually, JIT/AOT.** Once the self-hosted assembler exists, extend
  it to compile hot colon-word bodies to native code, including
  unwinding (inlining) non-recursive calls. Prior exploratory
  benchmarking found dispatch removal alone gives ~4-4.75x, with a
  further ~2-2.2x from inlining non-recursive calls on top of that — this
  is the single biggest performance lever identified across everything
  tried, larger than any interpreter-level tuning.

## Repository conventions

- **Single branch: `master`.** Linear history, no feature branches.
- **Code must always build and run, with all tests passing, at every
  commit** — not just at the end of a session.
- **Git bundle handed off at the end of each iteration.** Always bundle
  with both `HEAD` and `master` (`git bundle create f.bundle HEAD
  master`) so a plain `git pull f.bundle` works on the receiving end
  without needing the branch name specified.
- **Bundle filename convention**: `relf-claude-iterN-YYYYMMDD-HHMMSS.bundle`
  (UTC). `N` is the iteration number (increments each handoff, not each
  commit). Example: `relf-claude-iter1-20260831-085821.bundle`.
- **Target: push back to upstream** `https://github.com/kt97679/relf`
  eventually.
- **License: GPLv2**, matching both upstream `relf.c` and SOD32 (which
  RelF is derived from).

## Test suite strategy

- Full `forth2012-test-suite` (ANS/Forth-2012) compliance is a long-term
  target, **not** a near-term requirement — RelF's word set is far
  smaller than the full standard.
- For now: pull in directly-applicable individual test cases, translated
  into RelF's own `{ -> }` syntax (see `tester.fr`), rather than porting
  the modern suite's `T{ -> }T` harness wholesale — that harness needs
  infrastructure RelF doesn't have yet.
- The bundled `tester.fr` (a working port of John Hayes's 1993 CORE word
  test suite, already using RelF's `{ -> }` convention) is the primary
  regression suite. It existed in the repo but wasn't wired into any
  automated runner before this project — now is, via `tests/run_tests.sh`.

## Phases

1. **Scaffolding** — repo structure, test runner, process log. **Done**
   (iteration 1).
2. **No-libc, syscalls-only x86-64 engine**, replacing `relf.c`/
   `vm.asm`/`vm_tos.asm` in place (not preserved alongside — the goal is
   a leaner successor, not a fork-with-extras). **Done** (iteration 2).
   `relf.c` is now the only engine: built `-nostdlib -static`, raw
   syscalls, 8-byte cells, no `relfgcc.c`/`vm.asm`/`vm_tos.asm`. Also
   fixed Bug 3 (EOF hang) as part of this work, since it was directly a
   syscall-level concern. See `PROGRESS.md`, 2026-09-01, for the full
   account, including the cross-compiler-side work this dragged in
   (migrating `cross.4`/`kernel.4` to 8-byte target cells, which turned
   out to be most of the actual effort).
3. **Forth-hosted assembler** — a `CODE`/`END-CODE`-style facility so
   the engine itself can eventually be assembled by the running Forth
   system, not `gcc`/`as`. Not started.
4. **JIT/AOT** — extend the phase-3 assembler to compile hot colon-word
   bodies to native code, including non-recursive call inlining. Not
   started.
5. **Portability + performance without JIT** — libc-based multi-
   architecture support (all architectures `bash` runs on), native-
   endianness images, computed-goto dispatch, call-flattening, ARM64 as
   first proof target. Planned, not started — see the phase 5 section
   below for the full agreed plan (a byte-granular opcode encoding was
   also considered for this phase and rejected — see below).

## Non-goals (at least for now — revisit if this changes)

- Full ANS/Forth-2012 compliance (see test suite strategy above).
- Preserving support for the old 32-bit-only build path — single
  supported target as of phase 2 (**done**: no `-m32`, no BIG_ENDIAN
  switch, no `relfgcc.c`/`vm.asm`/`vm_tos.asm`). Superseded by the
  multi-architecture direction below — "single supported target" no
  longer applies going forward, kept here only as the historical record
  of what phase 2 itself did.
- gforth (or any other non-RelF Forth) as an alternative cross-compile
  host. `cross.4`/`extend.4`/`kernel.4` rely on RelF-kernel-specific
  search-order words (`CONTEXT`, `#ORDER`, `CURRENT`) that gforth
  doesn't provide — confirmed by trying, see `PROGRESS.md`, 2026-09-01.
  The README's older claim that gforth works is no longer accurate for
  the current kernel source and hasn't been re-verified; don't assume
  it without testing.
- Big-endian hosts. Images are planned to move to native host
  endianness (see phase 5 below) rather than SOD32's portable-on-disk
  big-endian format, since there's no current need for one image to run
  unmodified on hosts of differing endianness. Little-endian only,
  documented as such, not configurable.

## Phase 5 (planned, not started): portability + performance, without JIT

Agreed direction as of 2026-09-01 (see `PROGRESS.md` for the full
discussion this came out of): run on every architecture `bash` runs on,
prioritizing simplicity/minimalism per goal 3 above, while getting as
much speed as possible *without* per-architecture native codegen (that
remains phase 3/4, deliberately kept separate and optional):

- **libc as the portability layer.** Phase 2's no-libc x86-64-only
  syscall layer doesn't scale to "every architecture bash supports" —
  most of those don't have a well-trodden raw-syscall path the way
  x86-64 Linux does. Rather than write per-architecture syscall shims
  for a long tail of targets, use libc (just the handful of functions
  already in use: `read`/`write`/`open`/`close`/`lseek`/`unlink`/
  `fork`/`execve`/`wait`/`exit`) as the common denominator everywhere.
  This is a deliberate reversal of phase 2's "no libc" stance, made for
  portability rather than performance reasons — no-libc bought nothing
  measurable for speed, only architecture lock-in.
- **Native host endianness for `kernel.img`**, replacing SOD32's
  portable-on-disk big-endian format. Removes `swap_mem()` from the
  engine and the explicit byte-assembly in `cross.4`'s `@-T`/`!-T`
  entirely — a real simplification, not just a policy change. Add a
  small magic/version marker at the start of the image recording cell
  width + endianness, so a mismatched image fails clearly at load
  rather than silently misbehaving. Architectures that agree on cell
  width and endianness (e.g. x86-64 and ARM64, both LE, both 8-byte
  pointers) can still share a single image, since nothing in it is
  architecture-specific below this tier.
- **Computed-goto threaded dispatch** (GCC/Clang "labels as values"),
  replacing the current function-pointer-table indirect call per
  primitive with a direct `goto` to the next primitive's code. Fully
  portable across every architecture GCC/Clang target. Prior
  exploratory benchmarking (see `GOALS.md`'s JIT paragraph above) put
  dispatch-overhead removal alone at ~4-4.75x, though that predates
  this codebase's current shape (see caveat in `PROGRESS.md`) and
  should be re-measured here rather than assumed.
- **Call-flattening at cross-compile time**: `cross.4` inlines a
  non-recursive colon-word's body directly into its caller instead of
  emitting a threaded call, when there's no recursion. Build-time only,
  doesn't touch the engine. Prior benchmarking put this at a further
  ~2-2.2x on top of the above, same re-measurement caveat.
- ARM64 Linux as the first concrete non-x86-64 target to prove the
  whole thing out end-to-end, tested via QEMU user-mode emulation if
  physical hardware isn't available.
- **Byte-granular opcode encoding: considered, rejected.** (Primitives
  as single bytes instead of full cells, with `CALL`/`BRANCH`/
  `0BRANCH`/`LIT` still using cell-width relative values but stored at
  aligned addresses reached via an explicit marker byte.) Motivation
  was up to 8x denser encoding for primitive-heavy straight-line code.
  Rejected because plain `CALL` (a colon-word invocation, which has no
  opcode overhead at all in the current format — the offset cell *is*
  the whole instruction) needs an explicit marker byte plus alignment
  padding under this scheme, and the padding is structurally biased
  toward its 7-byte worst case: any aligned instruction leaves the
  following position aligned again, which is exactly the worst-case
  starting position for the *next* one, so back-to-back calls (common
  in idiomatically-factored, glue-heavy Forth code) hit close to worst
  case every time, not occasionally. A corrected simulation against the
  actual `kernel.img` (see `PROGRESS.md`, 2026-09-01 second entry) found
  this plausibly makes the *total image larger*, not smaller, and the
  same extra marker-fetch + realignment + second-fetch overhead lands
  on `CALL`/`BRANCH`/`0BRANCH`/`LIT` dispatch specifically — exactly the
  instructions that dominate real code's *dynamic* execution trace, not
  just its static size. Computed-goto dispatch already captures the
  well-understood dispatch-overhead win without this risk or the
  two-level-dispatch complexity, so there's no case for pursuing this
  further without a fundamentally different encoding for `CALL` (e.g.
  variable-length short/near/far forms, which drags in assembler
  relaxation — real complexity, against goal 3). Not pursuing this.

## External references (potentially reusable ideas, not yet mined)

Not read/evaluated in depth yet — listed here so a future session knows
where to look before reinventing something, rather than as an endorsement
of any specific approach. Update this list with findings (useful or not)
in `PROGRESS.md` once actually looked at.

- https://github.com/certik/bcompiler — incremental compiler/bootstrap
  ideas. Possibly relevant to phase 3 (self-hosted assembler) and the
  general bootstrapping-a-compiler-from-nothing problem this project
  keeps running into (see the cross-compile-host discussion above).
- https://github.com/gerryjackson/forth2012-test-suite — Forth semantic
  tests. Already the source of `tests/core-extra.fth`'s cases (see test
  suite strategy above); may have more directly-applicable cases to pull
  in the same way.
- https://github.com/larsbrinkhoff/lbForth — self-hosting/metacompiled
  Forth. Relevant to phases 3-4 (self-hosted assembler, JIT/AOT) as a
  reference for how another project structured metacompilation.
- https://github.com/rufig/spf — mature Forth implementation reference.
  Appears (unconfirmed) to be the same `spf` benchmarked in `README.md`'s
  historical numbers.
- https://github.com/lennart-benschop/sod32 — minimal Forth/kernel
  ideas. The SOD32 this project is derived from/compared against (see
  "Why RelF specifically" above) — this may be the canonical upstream
  rather than the mirror originally benchmarked against.
- https://github.com/kragen/stoneknifeforth — small/self-hosting Forth
  reference. Relevant to the "full self-hosting" end-state goal and
  phase 3 in particular: a from-nothing bootstrap is exactly the kind of
  problem this repository is working toward.
- https://github.com/tehologist/forthkit — eForth-derived Forth in a
  single ~440-line C file (`forth.c`), stdio.h only, outer and inner
  interpreter both in that one file. Relevant to goal 3 (minimalism) as
  a comparison point on kernel-construction philosophy: forthkit builds
  its ~24-word primitive kernel by calling a C-level `int_create()`
  directly for each word, rather than through a separate Forth-level
  cross-compiler script the way `cross.4`/`kernel.4` do — a notably
  different (smaller engine, less flexible/self-hosting for the kernel
  build step itself) tradeoff worth being aware of. Its own opcode
  dispatch is a plain `switch` over a full-cell (2-byte, in its case)
  opcode read from memory via offset arithmetic (SOD32-style indexed
  addressing, not RelF's direct-pointer addressing) — not itself prior
  art for the byte-granular-opcode idea in phase 5 above, but relevant
  to phases 1/3 (self-hosting, minimal bootstrap).
