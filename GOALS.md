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
   offset. **Caveat added 2026-09-01**: this specific advantage was
   measured against the old assembly engines (`vm.asm`/`vm_tos.asm`,
   removed in phase 2), which used the real CPU stack directly for the
   data stack. The current portable C engine (phase 2 onward) manages
   the data stack manually via a `dsp` variable instead - architecturally
   closer to SOD32's approach than to what was actually benchmarked
   here. The other two reasons below (JIT-template reusability,
   metacompiler simplicity) still hold for the portable engine; this
   specific speed reason may not, and hasn't been re-measured since the
   asm engines were removed. Phase 5's own computed-goto measurement
   (~1.30x, see below) came in well under an earlier ~4-4.75x estimate
   for dispatch-overhead removal alone - consistent with, though not
   proof of, this gap actually mattering.
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
   endianness images, computed-goto dispatch. **Mostly done** (this
   iteration): libc port, native-endianness images with a magic header,
   and computed-goto dispatch are all done and verified on x86-64 and
   ARM64 (same `kernel.img` on both, confirming the shared-image design).
   Call-flattening is **not done** — deliberately deferred, see the
   phase 5 section below for why. See `PROGRESS.md` for the full
   account, including several real bugs found and fixed along the way.
6. **32-bit-cell targets (i386)** — cell width parameterized at compile
   time (engine) and via `TARGET-CELL-BYTES` (cross-compiler/kernel).
   **Done**, verified on i386. See the phase 6 section below.
7. **Userland: a POSIX-flavored shell on RelF** — process-control
   primitives (`FORK`/`EXECVE`/`WAITPID`/`PIPE`/`DUP2`/`GETENV`/
   `SETENV`/`SYS-EXIT`/`CHDIR`/`GETCWD`/`SYS-ARGC`/`SYS-ARG`) plus
   `shell.4`, a shell built on top of them, plus `relfsh` (a
   single-executable wrapper) and a real, scoped test suite in
   `tests/shell/`. **v0.1 done**: external command execution via PATH
   search, `cd`/`pwd`/`export`/`exit` builtins, and a `-c` invocation
   mode (`relfsh -c 'command'`, matching `sh -c '...'`) — all verified
   end-to-end on x86-64 and i386, with an automated test suite
   (structurally inspired by bash's own `tests/`) now checking this on
   every run. See `PROGRESS.md`'s Iteration 5 and 6 entries for the
   full account, including several real bugs found getting there — one
   caught directly by the new test suite on its first run. Pipes,
   redirection, quoting, variable expansion, and control structures are
   explicitly **not yet done** — see those entries' "what this
   iteration deliberately did NOT do". This phase is the first concrete
   step toward the "busybox-on-RelF" direction discussed under
   "Non-goals" and in `PROGRESS.md`'s architectural notes; whether
   it's worth pushing toward a fuller coreutils/shell replacement, versus
   stopping at "useful enough to drive the system interactively", is an
   open question to revisit once v0.1's rough edges (pipes/redirection
   in particular) are smoothed out.

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
- Big-endian hosts. Images are native host endianness as of phase 5
  (**done**) rather than SOD32's portable-on-disk big-endian format,
  since there's no current need for one image to run unmodified on
  hosts of differing endianness. Little-endian only, documented as
  such, not configurable - a mismatched image's magic header will at
  least fail cleanly rather than silently misbehave, but there's no
  attempt to actually support big-endian hosts.
- ~~32-bit-cell hosts (ARM32, i386, etc.), for now.~~ **Done as of
  phase 6** (i386 specifically - see below and `PROGRESS.md`'s
  2026-09-03 entry). ARM32 not yet tried; see phase 6's own notes.

## Phase 5: portability + performance, without JIT

Agreed direction as of 2026-09-01 (see `PROGRESS.md` for the full
discussion this came out of, and the later 2026-09-02 entry for the
implementation and the bugs it surfaced): run on every architecture
`bash` runs on, prioritizing simplicity/minimalism per goal 3 above,
while getting as much speed as possible *without* per-architecture
native codegen (that remains phase 3/4, deliberately kept separate and
optional).

- **libc as the portability layer. Done.** Phase 2's no-libc
  x86-64-only syscall layer doesn't scale to "every architecture bash
  supports" — most of those don't have a well-trodden raw-syscall path
  the way x86-64 Linux does. `relf.c` now uses plain libc calls (`read`/
  `write`/`open`/`close`/`lseek`/`unlink`/`fork`/`execve`/`waitpid`/
  `exit`) and builds with a plain `cc -O2 -Wall -o relf relf.c` — no
  special flags, no custom `_start`, no inline assembly for syscalls.
  This is a deliberate reversal of phase 2's "no libc" stance, made for
  portability rather than performance reasons — no-libc bought nothing
  measurable for speed, only architecture lock-in.
- **Native host endianness for `kernel.img`. Done.** Replaces SOD32's
  portable-on-disk big-endian format. Removed `swap_mem()` and the
  XOR-7 byte-addressing trick from the engine entirely, and simplified
  `cross.4`'s `@-T`/`!-T` correspondingly — a real simplification, not
  just a policy change (see `PROGRESS.md` for why byte-level access
  didn't even need the trick in the first place, once portability
  wasn't a goal). Images now start with an 8-byte magic header ("RELF"
  + cell width + reserved) so a mismatched image fails cleanly at load
  instead of silently misbehaving - confirmed working. Architectures
  that agree on cell width and endianness (x86-64 and ARM64, both LE,
  both 8-byte pointers) share a single image, confirmed by running the
  exact same `kernel.img` on both.
- **Computed-goto threaded dispatch. Done.** GCC/Clang "labels as
  values", replacing the function-pointer-table indirect call per
  primitive with a direct `goto` to the next primitive's code. Measured
  (not assumed) against an otherwise-identical function-pointer-table
  build on the same `fib.4` workload: **~1.30x**, consistent across
  repeated runs - a real, worthwhile win, but nowhere near the ~4-4.75x
  the JIT-section paragraph above cites from prior exploratory
  benchmarking. That number should now be treated as unverified for
  *this* codebase (it likely came from a different baseline or
  different hardware) rather than a forecast for phase 5's own
  numbers - see `PROGRESS.md` for the measurement.
- **Call-flattening at cross-compile time: deferred, not done.**
  (`cross.4` inlining a non-recursive colon-word's body directly into
  its caller instead of emitting a threaded call.) Given how much
  smaller computed-goto's actual win turned out to be versus the prior
  estimate, and how many non-obvious bugs phase 5's *other* changes
  surfaced in `cross.4` despite each seeming simple going in (see
  `PROGRESS.md`), call-flattening - a real change to the compiler's
  code-generation logic, not just its plumbing - deserves its own
  focused iteration with its own measurement, not a rushed add-on to an
  already large one. The ~2-2.2x prior estimate should be treated with
  the same skepticism as the dispatch number above until it's actually
  measured on this codebase.
- **ARM64 Linux as the first non-x86-64 target. Done.** Built with
  `aarch64-linux-gnu-gcc`, tested under `qemu-aarch64` user-mode
  emulation (no physical hardware used). Full test suite (1892 `OK`
  markers) and `fib.4` both pass, using the identical `kernel.img`
  produced on x86-64 - no ARM64-specific image rebuild needed,
  confirming the shared-image design above end-to-end.
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

## Phase 6: 32-bit-cell targets (i386)

Agreed direction as of 2026-09-03 (see `PROGRESS.md`'s 2026-09-03 entry
for the full account, including every bug found getting here): make
cell width a genuine parameter - of the engine *and* the cross-compiler
- rather than an 8-byte-only assumption, so a 32-bit target is a
build-time choice, not a fork.

- **`relf.c`: cell width from `UINTPTR_MAX`. Done.** 4 or 8 bytes,
  chosen at compile time to match the host's own pointer width, per
  RelF's real-pointer addressing model. Building with `gcc -m32`
  produces a working 4-byte-cell engine with no other source changes.
- **`cross.4`/`kernel.4`: `TARGET-CELL-BYTES` parameterization. Done.**
  Every cell-width-dependent computation (primitive token stride,
  `CELLS`/`CELL+`/`CELL-`, `2/`'s sign mask, `@-T`/`!-T`, alignment, the
  hand-numbered LIT/EXIT/BRANCH/0BRANCH/R> tokens) now derives from one
  `TARGET-CELL-BYTES` variable instead of being hardcoded for 8-byte
  cells. This surfaced a genuinely long chain of independent bugs along
  the way, the hardest being a pre-existing (not newly introduced)
  fragility in how `cross.4`'s target-shadow-word-defining `:`/`;`
  interacts with the base kernel's compile-state tracking - see
  `PROGRESS.md` for the full diagnosis and fix.
- **i386, verified working. Done.** Full CORE test suite (1892 `OK`
  markers, zero errors) passes on both the 8-byte-cell (default) and
  4-byte-cell (i386) builds, from the identical `cross.4`/`kernel.4`
  source - only `TARGET-CELL-BYTES` differs between the two
  cross-compiles. `fib.4` gives the identical correct result on both.
  `tests/run_tests.sh` builds and tests both automatically.
- **ARM32: not attempted.** Should work through the same
  `gcc`-target-picks-`UINTPTR_MAX` mechanism in principle - `relf.c`
  itself has no i386-specific code, only pointer-width-generic code -
  but hasn't actually been built or tested, given how many independent,
  non-obvious bugs turned up getting i386 working despite the design
  looking straightforward going in. Worth doing, not assumed to already
  work.
- **A clean "pre-set `TARGET-CELL-BYTES` before including `cross.4`"
  mechanism: attempted, reverted.** The natural way to make this
  convenient - `DEFINED?`-guard the variable's own creation so a person
  could set it themselves first - used `IF`/`THEN` at the top level
  (interpret mode), which turned out to silently corrupt the dictionary
  in this kernel rather than erroring (see `PROGRESS.md`). Reverted to
  a plain, unconditional default of 8; building for 32-bit means
  directly editing that one line in `cross.4` (documented in
  `README.md`). Less convenient, but with no equivalent silent-failure
  mode - the right tradeoff until/unless a real need for the
  pre-set-before-including convenience shows up.

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
