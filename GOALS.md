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

- **Watch for development-process wins, and raise them.** Alongside
  feature work, actively look for ways the *process* of working on
  this project could be faster or more reliable, and discuss them
  rather than just absorbing the friction. Measure before proposing:
  the point is to find real costs, not plausible-sounding ones.
  Iteration 40 is the model - `relfsh` had been recompiling
  `shell.4` from source on every single invocation, ~253ms of every
  ~254ms, which made the shell test suite take a minute and hid a
  hard blocker in the acceptance criterion. A prebuilt image cut the
  suite from 59.3s to 1.2s. That had been true and unnoticed since
  Iteration 5. Slow feedback loops compound: they discourage running
  the full suite, which is exactly when regressions slip through.
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

## Named locals (`locals.4`) — available since Iteration 38

Not a goal in itself; infrastructure the rest of the project can use.
Load with `S" locals.4" INCLUDED`.

`shell.4` carries 181 global `VARIABLE`s, most of which are not global
state at all but per-word scratch cells faked with a naming convention
(`GM-*`, `NORM-*`, `SAEK-*`, …), because this kernel has no locals
wordset. That is the *root cause* of the nesting limitations recorded
under phase 8 below: a word whose scratch state lives in fixed globals
cannot be re-entered. `while`/`for` don't nest because their body lives
in one fixed buffer set; `if` does nest, because its state is a single
scalar saved across `>R`/`R>`.

**A local is an ordinary `VARIABLE`, saved on entry to the declaring
word and restored on every exit.** That design is what keeps the
implementation to ~65 lines and, crucially, means a converted word's
*body is unchanged* — `CA-SRC @` and `CA-N !` keep working, because a
local still is a variable. Converting existing code is adding one
declaration line and deleting the argument-popping stores.

    : COPY-ARGV ( src-argv src-argc --- )  {: CA-SRC CA-N :}

    : GLOB-MATCH ( pat plen text tlen --- f )
      {: GM-PATTERN GM-PLEN GM-TEXT GM-TLEN | GM-P GM-S :}

Names before an optional `|` are initialized from the data stack, left
to right = deepest to top. Names after `|` are scratch: saved and
restored the same way, but zeroed. `EXIT` and `;` are wrapped so the
restore happens on every exit path including early `IF EXIT THEN`, and
both compile nothing at all in a definition that declares no locals.

The kernel, `cross.4` and `kernel.img` are **untouched** — `locals.4`
uses only what the kernel already exposes. That was a deliberate
constraint given this file's own warning about `cross.4`'s hand-embedded
primitive-dispatch token numbers.

**In use since Iteration 39**: `relfsh` loads `locals.4` ahead of
`shell.4`, and 31 words are converted. The dynamic-scoping property
earned its keep immediately - words like `GLOB-MATCH` share their
scratch with helper words (`BRACKET-END`, `GLOB-CHAR-MATCHES?`), and
the six `SPLIT-*`/`PARSE-REDIRECTIONS` words share the `PR-I` cursor
with the `AT-*?` predicates; because a local *is* the variable, every
one of those helpers kept working untouched, where a conventional
locals frame would have forced rewriting them all to take parameters.
Locals also made two real deduplications comfortable: four
near-identical prefix/suffix searchers became one six-argument
`FIND-TRIM-LEN`, and `SPLIT-AT-KEYWORD` collapsed into a two-line
wrapper over `SPLIT-AT-EITHER-KEYWORD`.

**What locals cannot fix, and what comes next.** A local saves and
restores one *cell*. `while`/`for` bodies live in `WHILE-BODY-BUF`, a
fixed 4096-byte *buffer*, which is why they still don't nest. The
route to nesting is to make those buffers pointers into an arena so
the pointer is what locals save - a real design change to how loop
bodies are stored, and the natural next step. The same applies to
`CASE-WORD-BUF`, `FUNC-BODIES` and `ARITH-BUF`.

Documented scope limits: a local must already be a defined `VARIABLE`
(so converting `shell.4` makes its globals re-entrant without reducing
their count); one physical line per declaration; 16 locals per
definition; 256 cells of live save stack; `ABORT` inside a
locals-using word leaks its saved cells. See `PROGRESS.md`'s Iteration
38 entry, including a real bug worth remembering: **a Forth file that
is `INCLUDED` into an unknown session must not inherit the caller's
`BASE`** — `tester.fr` leaves it at 16, which turned `locals.4`'s own
`32 WORD` into `0x32 WORD`, delimiting names on the character `2`.

## Tracked numbers

Three figures are reported on every full test run and are expected to
move honestly, the same way the mrsh count is:

- `tests/run_tests.sh`: core-suite OK markers and shell-suite
  assertions, on both cell widths.
- `tests/mrsh-suite/run.sh`: the acceptance criterion for goal 8.
- **Size**: stripped engine + prebuilt shell image, both cell widths.

Baseline at Iteration 41:

| | engine | image | total |
|---|---|---|---|
| **i386 (4-byte cells)** | 17,808 | 72,528 | **90,336** |
| x86-64 (8-byte cells) | 22,744 | 131,784 | 154,528 |

For context, on the same machine: `dash` is 121,520; `mrsh` is 183,312
plus a 15,432-byte shared library. Both are far more complete shells
than `shell.4` is today, so the comparison currently flatters this
project — the point of tracking is the trajectory as phases E/F fill
the functionality gap, not the snapshot.

**The 8-byte build is ~1.8x the 4-byte one, and that is structural.**
Measured zero-rate by byte position within each cell: byte 0 is 14.8%
zero, bytes 1-7 are 56-64% zero, and only 13.8% of cells are entirely
zero. So the image is mostly small values — dispatch tokens, relative
offsets, small literals — padded out in wide cells, not wasted buffer
space. RelF dereferences a cell directly as a real host pointer (see
the load-bearing architectural note above), so cell width must equal
pointer width and a 64-bit host pays double. No amount of tuning
reaches that; the genuinely small build is the i386 one.

Size optimization is **deliberately deferred** until POSIX
functionality is in place and the mrsh suite passes: the code's shape
will change as phases E/F land and as loop bodies move to an arena, so
tuning now would be tuning something about to be rewritten. The levers
that will still be there afterwards, in rough order of value:

1. **Headerless words.** `cross.4` already carries a commented-out
   alternative `"HEADER` "in case the target system is just an
   application without headers". Names and headers for ~180 shell
   words are a real fraction of the image. The cost is that `FIND`
   stops working for them, which rules out the `forth` builtin and
   interactive use — a genuine trade, not free.
2. The ~11K of small hot buffers still declared with `CREATE`, once
   it is measured whether `BUFFER:`'s extra indirection matters on the
   tokenizer's hot path.
3. Nothing else looks large: the compiled code is ~88K and most of it
   is real.

## Memory policy — agreed in Iteration 41

Standing requirements for how this project uses memory, and the
reasoning behind them:

- **Don't hardcode limits, and don't preallocate.** Reserve space when
  it is actually needed, not at compile time against a guessed worst
  case. `CREATE name n ALLOT` does the opposite: it takes dictionary
  at compile time, so the space lands in every saved image whether or
  not it is ever used. Measured on the first prebuilt shell image:
  135,576 of its 253,528 bytes were such buffers and 77.3% of the file
  was zeros, with a single unused 73,728-byte buffer accounting for
  29% of it.
- **Prefer memory outside the image.** `ALLOCATE`/`FREE`/`RESIZE`
  (Forth-2012's own wordset, primitives since Iteration 41, backed by
  the host's `malloc`/`free`/`realloc`) give memory from the C heap.
  It costs no dictionary space, is not written out by `SAVE-SYSTEM`,
  and is not bounded by `relf.c`'s `MEMSIZE`. `pool.4`'s `BUFFER:`
  is the convenient front end: same call site as a `CREATE`d buffer,
  but three cells in the image and the space allocated on first use.
- **Growable rather than fixed, where the size genuinely varies.**
  `RESIZE` exists for this. Not yet used - see the concerns below for
  when it is and isn't safe.

Two concerns worth keeping in view, neither blocking:

1. **`RESIZE` can move a block, and this codebase stores interior
   pointers.** `ARGV` entries point into `LINE-BUF`; `REDIR-*-FILE`
   point into token storage. Growing a buffer that others point into
   would silently invalidate those pointers, and the failure would
   look like data corruption rather than an allocation error. So
   `RESIZE` is safe for a self-contained arena that nothing points
   into from outside, and unsafe for the shell's line and token
   buffers as they are written today. Worth checking per buffer
   rather than adopting wholesale.
2. **Heap memory can never be saved in an image.** Anything
   `ALLOCATE`d is process-local: an address is meaningless after a
   reload, which is exactly why `BUFFER:` pointers are reset before a
   save. That is the right default - it is what keeps images small and
   reproducible - but it does mean an image can carry *declarations*
   and never *contents*. Any future feature that wants state to
   survive into an image must put it in the dictionary deliberately.

A third point is a tension already present rather than one this
introduces: `malloc` deepens the dependence on libc, while this file's
end-state still says "no libraries, raw syscalls only". Phase 5
already traded that away for portability. If the no-libc goal is
revived, `ALLOCATE`/`FREE`/`RESIZE` are a small, well-isolated thing
to reimplement on `mmap`/`brk` - three primitives in `relf.c` and
nothing above them changes.

## Reproducible images

The same sources must produce a byte-identical image. Verified by
building twice and comparing. Without care they do not: the first
prebuilt image contained the build machine's path and the builder's
PID (left in the interpreter's include buffer) plus a dozen cells
holding absolute addresses that differ every run.

`SAVE-SYSTEM` assembles the image in a heap copy and scrubs it - see
`save-system.4`'s `SS-SCRUB` for the list, all of it re-initialized by
`COLD`/`WARM`/`QUIT` before anything reads it. **Anything added that
stores an absolute address, a PID, a timestamp or a file descriptor in
the dictionary breaks this**, and the fix is either to make the value
position-independent (preferred - see below) or to add it to
`SS-SCRUB`.

## Prebuilt shell image (`save-system.4`) — since Iteration 40

`relfsh` runs a prebuilt image rather than compiling `locals.4` +
`shell.4` from source on every invocation. Measured, 50 runs each:
source bootstrap 12.68s, prebuilt image 0.091s, bare `relf kernel.img`
0.061s. That is ~253ms against ~1.8ms, **~128x**, and it took the
shell test suite from 59.3s to 1.2s.

Three pieces:

- **`save-system.4`** — `SAVE-SYSTEM ( c-addr u -- )` writes the
  *running* system out as a bootable image: the magic header, then
  memory from `START` to `HERE`. RelF images are relocatable by design,
  so the only work is subtracting `START` back out of the two cells
  `COLD` relocates (`DP` and `FORTH-WORDLIST`) before writing. Needs no
  engine change; every word it uses already existed. Distinct from
  `cross.4`'s own `SAVE-IMAGE`, which is a host-side word writing the
  target image the cross-compiler is building.
- **`BOOT` in `kernel.4`** — 0 in a plain kernel image; when set it
  holds the xt of a word to run at startup, so the image boots straight
  into `shell.4`'s `MAIN` and never prints the banner or `OK`. Stored
  as an offset from `START`, never absolute.
- **`relfsh`** rebuilds the image whenever any input is newer, to a
  temporary name then `mv`. The image is **built, never committed** —
  a committed binary derived from `shell.4` is a second source of truth
  that goes stale silently.

**Position-independence is now load-bearing, and was not before.** An
image reloads at a different address every run, so any absolute address
compiled into a word's body is stale the moment it boots. Two places
had them, both found by the turnkey image segfaulting: `shell.4`'s six
deferred-word xts (now stored as `START`-relative offsets via
`!XT`/`@XT`), and the slot addresses `locals.4` compiles into every
locals-using word (now offsets, with the runtime words adding `START`
themselves). **Anything added in future that stores or compiles an
address must do the same.**

Compiling new code inside a reloaded image **works** as of Iteration
41. It did not in Iteration 40, because `locals.4`'s compile-time
machinery held absolute xts; those are now offsets like everything
else, which was needed for reproducible images anyway and removed the
limitation as a side effect. Verified by saving a non-turnkey image and
then defining a new locals-using word and a new `BUFFER:` inside it.
This was the blocker in front of the `forth` builtin.

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
   `SETENV`/`UNSETENV`/`SYS-EXIT`/`CHDIR`/`GETCWD`/`SYS-ARGC`/`SYS-ARG`/
   `GETPID`) plus `shell.4`, a shell built on top of them, plus
   `relfsh` (a single-executable wrapper) and a real, scoped test suite
   in `tests/shell/`. **v0.8 done**: external command execution via
   PATH search, `cd`/`pwd`/`export`/`unset`/`exit` builtins, a `-c`
   invocation mode (`relfsh -c 'command'`, matching `sh -c '...'`), a
   single pipe per line (`cmd1 | cmd2`), redirection (`<`/`>`/`>>`),
   quoting (single quotes, double quotes with minimal `\"`/`\\`
   escaping, and backslash-escaping outside quotes), `$VAR`/`${VAR}`/
   `$?`/`$$` expansion, `$(command)` command substitution (external
   commands only, no quoting/expansion/pipes within the substituted
   command's own text yet, no nesting — see `PROGRESS.md`'s Iteration
   13 entry for the design and for a real bug worth remembering: an
   absolute address silently compared against a plain offset, making a
   bounds check always pass), `if`/`then`/`else`/`fi`, and
   `while`/`do`/`done` (with the condition and body genuinely
   re-evaluated fresh each iteration — including fresh `$VAR`/`$?`/`$$`
   re-expansion, not frozen from the loop's first reading — see
   `PROGRESS.md`'s Iteration 11 entry for why that distinction was the
   whole design problem) — no nesting for either control structure
   yet, no `for`/`until`, see that same entry for exactly why those are
   harder — all with quote-awareness so a literal
   `'<'`/`'cd'`/`'if'`/`'while'` or an expansion result matching an
   operator isn't mistaken for the operator/builtin/keyword it happens
   to spell — all verified end-to-end on x86-64 and i386, with an
   automated test suite (structurally inspired by bash's own `tests/`,
   56 assertions as of this writing) checking all of it on every run.
   See `PROGRESS.md`'s Iteration 5 through 13 entries for the full
   account, including several real bugs found getting there — one
   caught directly by the test suite on its first run. Nesting,
   word-splitting of unquoted expansion results, parameter-expansion
   modifiers (`${VAR:-default}` etc.), and positional parameters are
   **not yet done**, and pipes and redirection still can't be combined
   on the same line — see
   those entries' "what this iteration deliberately did NOT do". This
   phase is the first concrete step toward the "busybox-on-RelF"
   direction discussed under "Non-goals" and in `PROGRESS.md`'s
   architectural notes; whether it's worth pushing toward a fuller
   coreutils/shell replacement, versus stopping at
   "useful enough to drive the system interactively", is an open
   question to revisit
   once quoting and variable expansion — the next natural gaps — are
   addressed.

8. **Goal: pass the whole mrsh test suite.** mrsh
   (https://github.com/emersion/mrsh) is a minimal but far more
   complete POSIX shell than `shell.4` currently is; its test suite
   (vendored unmodified into `tests/mrsh-suite/vendor/` at commit
   `4c81598721bc5eeb28f9faa818b3102d0471b7f6` — see that directory's
   own `README.md`) is adopted here as a concrete, external,
   trackable target rather than one this project invents its own
   criteria for. `tests/mrsh-suite/run.sh` runs it against `relfsh`
   and currently reports **2 passed, 19 failed, 3 skipped** - of which
   exactly **one is genuine**. `case.sh` passes on its merits: full
   `case`/`esac` with variable expansion, `*`, `?`, `[...]` and `|`
   patterns, quoted patterns, and an omitted final `;;`, all of which
   `shell.4` really implements (Iterations 27 and 33-36). It is the
   first vendored file ever carried across by actual shell features.
   `ulimit.sh` is hollow and should be read as such: `shell.4` has
   neither `ulimit` nor backquote substitution, both shells simply
   exit 1, and their stdout coincides only because of the one `grep`
   line that runs in both. It will stop being hollow when Phase F's
   `ulimit` and Phase E's backquotes land.

   **A structural blocker sat underneath that number, found in
   Iteration 39 and cleared in Iteration 40.** The 18 differential
   tests compare `relfsh`'s stdout against `bash`'s *byte for byte*,
   but `relfsh` used to emit `relf`'s own boot output first -
   `Welcome to Forth` and `OK` - so no differential test could pass
   however complete `shell.4` became. `relfsh` now runs a prebuilt
   image that boots straight into `MAIN` (see the prebuilt-image
   section below), so neither line is ever printed and stdout is
   exactly what the shell itself writes.

   That number has moved exactly three times, and never yet because a
   `shell.4` feature carried a vendored test file across the line:

   - Twice during Iterations 14 through 16, when an
     *invocation/measurement* bug was found and fixed each time (see
     those `PROGRESS.md` entries), settling at 1 passed, 20 failed, 3
     skipped.
   - Once at Iteration 36, **downward**, to the current 0 passed, 21
     failed, 3 skipped. This is not a regression. The single "pass"
     was `2.2.3-alias-expansion.fail.sh`, which this file had already
     flagged as hollow — `alias` isn't implemented at all, so the test
     passed by accident rather than because the shell handled its
     actual intent. Iteration 36's `TRY-ASSIGNMENT` fix made the
     script's own `var="$(myalias arg-two)"` assignment genuinely
     work, so it now exits 0 instead of being rejected outright, and
     the accidental pass evaporated. A `git stash` comparison
     confirmed the difference comes from the assignment now working,
     not from anything `alias`-related.

   Everything else — Iterations 17 through 35 and 37 — left the count
   untouched, which is expected: no single vendored file passes purely
   from variable assignment, `;`, `&&`/`||`, command-grouping, the
   if/while script-file fix, if-nesting, `for` loops, operator-fusion,
   same-line if/then/fi, the $VAR-expansion corruption fix,
   `case`/`esac`, functions, `return`, `break`/`continue`, any single
   Phase D expansion, or `test`/`[`/`:` alone. Each vendored file needs
   several still-missing features together. Known specific blockers:
   command-grouping doesn't apply to mrsh's tests at all yet given the
   whitespace-around-parens scope limit above; `while`/`for` (unlike
   `if`) still need `do` on their own separate line; `if.sh` also needs
   `$#` and `elif`; `case.sh` needs arithmetic and `$IFS` splitting in
   its later sections (both now implemented as of Iterations 35/36, so
   this file is worth re-checking specifically).

   **Phase A is done (Iterations 15–16).** It found and fixed two
   layers of problems before any real feature work could even be
   measured accurately:

   - **Four segfaults** (Iteration 15) — root cause: this kernel's
     `DO`/`LOOP` doesn't treat `start = limit` as zero iterations (the
     common, expected Forth behavior) but instead wraps around and
     runs the entire unsigned range, and five places in `shell.4` had
     a loop count that could legitimately be zero at runtime (most
     directly, `$(true)` or any command producing no output at all,
     inside `EXPAND-CMDSUB`'s splice loop). All five now guarded
     explicitly; no crashes remain anywhere in the suite.
   - **`relfsh` had no file-argument invocation** (Iteration 16) —
     `tests/mrsh-suite/run.sh` had been working around this since
     Iteration 14 by piping each script into `relfsh`'s stdin instead
     of passing it as an argument, which fed every script through the
     ordinary interactive loop rather than the more accurate
     `sh script.sh` semantics `SH-FILE` (new in Iteration 16) now
     provides. This surfaced something bigger than the missing
     feature itself: the old stdin-piped method's exit status was
     *always 0*, regardless of what the script's last command
     actually did — `relf`'s own top-level interpreter, not
     `shell.4`, is what notices EOF on stdin, and it always exits
     cleanly without ever touching `LAST-STATUS`/`SYS-EXIT`. So the
     Iteration 14/15 baselines' exit-status numbers for every
     differential test were themselves partly an artifact of the
     measurement method, not a genuine reflection of `shell.4`'s
     behavior (it didn't change any pass/fail *verdicts* for the 18
     differential tests, all of which were already failing on output
     grounds regardless — but it did flip the one conformance
     expected-failure test back to a genuine pass, this time via a
     correctly-propagated 127 rather than a piped-stdin artifact or a
     disguised crash).

   Along the way, a real, independent bug got fixed too: `exit` had
   always hardcoded status 0 regardless of any argument, and didn't
   default a bare `exit` to `$?` as POSIX requires — both fixed, since
   correct exit-status propagation is exactly what this whole
   suite depends on being measured accurately.

   Four of the original segfaults — `async.sh` (background jobs, `&`),
   `function.sh` (shell functions), `pipeline.sh` (subshells/brace
   groups inside a pipeline), and `read.sh` (the `read` builtin) —
   all now fail cleanly rather than crashing, though none of the
   underlying *features* exist yet, so they remain genuine failures
   for those reasons, which is exactly the honest state phase A was
   meant to produce.

   The full feature gap, roughly ordered by dependency (each phase
   below is expected to be its own multi-iteration effort, comparable
   in scope to phases 5 or 6 above — this is a large goal, not a
   quick one):

   - **Phase A — infrastructure to run the suite at all: done
     (Iterations 15–16).** Crash-hardening and script-file invocation
     both landed; `tests/mrsh-suite/run.sh` now invokes `relfsh` the
     same way it invokes `bash` (`relfsh testcase` /
     `bash testcase`), no more asymmetry. One correctness gap in
     script-file invocation itself surfaced later, while investigating
     phase B's if/while nesting item, and was fixed as its own
     iteration: `if`/`while` were completely broken when run via a
     script file (their own body-line reading always read from the
     real process stdin regardless of where the script's lines
     actually came from) — see `PROGRESS.md`'s Iteration 21 entry.
   - **Phase B — foundational semantics needed almost everywhere.**
     Shell-local (non-exported) variable assignment as a standalone
     statement: **done (Iteration 17)** — `VAR=value` (the whole
     line) sets a real shell-parameter table distinct from the OS
     environment, expanding via `$VAR`/`${VAR}` without being
     inherited by a child process; `export`/`unset` both updated to
     interact with it correctly (bare `export NAME` now exports an
     existing shell-local value; `unset` removes both copies). Still
     open: `NAME=value command args...` (POSIX's temporary,
     per-command assignment prefix — a real, acknowledged gap, not
     silently mishandled: it currently falls through to being looked
     up as a literal, failing command name, since `ARGC` isn't 1 in
     that shape).

     Multiple commands per line via `;`: **done (Iteration 18)** —
     `cmd1 ; cmd2 ; ...`, each run in sequence regardless of the
     previous one's own exit status, recursively handling any number
     of segments. Surfaced a real, pre-existing architectural
     limitation rather than introducing one: `FOO=bar ; echo $FOO`
     doesn't see the just-assigned value, because `$VAR` expansion
     happens once for the *entire* raw line during the initial
     tokenize pass, before any `;`-segment has actually run (the same
     assignment on its own, separate line works correctly) — a proper
     fix means tokenizing/expanding each `;`-separated piece
     independently in sequence rather than the whole line up front, a
     real architectural change left for its own future iteration; see
     `PROGRESS.md`'s Iteration 18 entry for the full account.

     `&&`/`||` (conditional chaining): **done (Iteration 19)** —
     left-associative, equal precedence for both, evaluated left to
     right, correctly carrying the "compound status so far" through a
     skipped segment (`a && b || c` runs `b` and skips `c` if `a`
     succeeds, but skips `b` and runs `c` if `a` fails) — tighter
     precedence than `;`, looser than `|`.

     Command grouping: **done (Iteration 20)** — `( list )` runs its
     body in a forked subshell (`cd`/variable/`export` changes inside
     it don't affect this shell); `{ list ; }` runs its body directly
     in this shell instead, so those changes do persist. Requires
     whitespace around `(`/`)`/`{`/`}` themselves, matching every
     other operator's convention here — a real, acknowledged gap
     against mrsh's own tests, which write `(cmd)` with no spaces (a
     trailing pipe or redirect after a group is also silently dropped
     rather than applied, for now); see `PROGRESS.md`'s Iteration 20
     entry.

     `if`/`then`/`else`/`fi` nesting: **done (Iteration 22)** — a body
     line that's itself another `if` works correctly at any nesting
     depth, regardless of whether the enclosing branch actually
     executes. A first attempt (saving/restoring `COND-TRUE?` alone)
     handled nesting correctly whenever the *enclosing* condition was
     true, but testing the opposite case directly surfaced a deeper
     gap: when the enclosing condition is false, body lines were never
     run through the recursive dispatch at all, so a nested if's own
     `then`/body/`fi` were never parsed as a nested construct, and its
     `fi` got mistaken for the enclosing if's own. Fixed by always
     recursing into every body line regardless of whether it should
     execute, gated instead by a separate `SUPPRESS-EXEC?` state
     checked at the two actual points that execute anything
     (`DO-ASSIGN`, `RUN-SIMPLE-OR-PIPELINE`) — see `PROGRESS.md`'s
     Iteration 22 entry for the full account, including three more
     file-ordering slips of the same kind Iterations 16/20/21 already
     hit.

     `while`/`do`/`done` nesting remains **not done** — its condition
     and body are buffered as raw text across dedicated, fixed-size
     buffers rather than a single scalar like `if`'s `COND-TRUE?`, so
     nesting it needs considerably more than what fixed `if` here;
     left as its own, separate, still-open problem. **Phase B is now
     complete** apart from that one item and the `NAME=value command`
     temporary-assignment-prefix form noted above.
   - **Foundational fix (Iteration 24, cuts across every phase):**
     operators no longer require surrounding whitespace — `;`, `|`,
     `&&`, `||`, `<`, `>`, `>>` are now self-delimiting (`"true;echo"`
     and `"a>file"` parse correctly), matching real POSIX shells,
     rather than needing whitespace on both sides as every earlier
     operator implementation had shortcut-taken. Implemented as a
     pre-pass over the raw line (`NORMALIZE-OPERATORS`, inserting
     synthetic spaces around unquoted operators before the existing
     tokenizer ever runs) rather than a `SCAN-TOKEN` rewrite, after
     identifying a real hazard in the more obvious approach (an
     unquoted word's own NUL-termination write lands exactly where a
     fused operator would sit, destroying it before it could be read).
     Deliberately still excludes `(`/`)`/`{`/`}` — blindly spacing
     those would break `$(...)` command substitution outright; left
     for its own future iteration. Surfaced a related, separate gap
     rather than fixing it outright: `if true; then` still didn't
     work at the time, since `DO-IF`/`DO-WHILE`/`DO-FOR` only looked
     for `then`/`do` by reading a *new* line, never by checking the
     remainder of the current line's already-correctly-tokenized
     `ARGV` — getting the tokenization right was necessary but not
     sufficient. **`if` specifically now supports this too (Iteration
     25)** — `if COND; then BODY; fi`/`else` all work on one line, at
     any nesting depth, via a new "pending remainder" mechanism
     (`SPLIT-AT-KEYWORD`/`SPLIT-AT-EITHER-KEYWORD`, tracking `if`/`fi`
     nesting depth so a *nested* if's own `else`/`fi` isn't mistaken
     for the outer one's — found to be necessary by testing directly,
     not by inspection). `while`/`for` still require `do` on its own
     separate line — extending this to them is separate, still-open
     future work. See `PROGRESS.md`'s Iteration 25 entry for the full
     account of the four real bugs found and fixed getting there,
     including one (operator normalization never having been wired
     into the *second* line-reading path control structures use
     internally) that had been silently present since Iteration 24
     itself. See `PROGRESS.md`'s Iteration 24 entry for the full
     account, including a real regression this surfaced in an
     *existing test* (not a shell bug — an unquoted `|` inside an
     assignment value was never actually valid in real shells either).
   - **Phase C — control structures.**
     `for`/`in`/`do`/`done`: **done (Iteration 23)** — iterates its
     body once per word, expanded once at the `for ... in ...` line
     itself (matching POSIX), reusing `while`'s own body-capture/
     replay machinery unmodified. Requires `do` on its own, separate
     line, same as `if`/`while` already do. Went smoothly — every test
     passed on the first attempt. Testing directly did surface a real,
     pre-existing, more general limitation (not introduced by this
     work — confirmed it already affects `while` too): a loop body
     cannot contain another multi-line construct at all (`if`, or a
     nested `while`/`for`) — the replay mechanism dispatches each
     stored body line independently, but `DO-IF`'s own search for
     `then`/`fi` reads from the real input stream, not the next stored
     line, so a nested `if` inside a loop body silently misbehaves
     (its own body lines run unconditionally, regardless of the
     condition). A real fix needs loop bodies to support genuine
     read-ahead into stored lines; left as its own, separate,
     substantial future item — see `PROGRESS.md`'s Iteration 23 entry.

     `case`/`in`/`esac`: **done (Iteration 27)** — `case WORD in
     PATTERN) <body> ;; ... esac` with full glob-pattern matching
     (`*`, `?`, `[...]` ranges and `[!...]`/`[^...]` negation, the
     classic iterative two-pointer backtrack algorithm, tested
     thoroughly in isolation, 22/22 cases before ever being wired in)
     and `|` alternation, matching the first arm whose pattern matches
     and never falling through to a later one, the way a C `switch`
     can. Requires each pattern arm on its own separate line, matching
     while/for's own "no same-line support" scope. A real bug was
     found and fixed by testing against a realistic, multi-arm script
     rather than one pattern type at a time: `CASE-MATCHED?` was being
     *set* once a match was found, but never actually *checked* — so
     every later arm, even a non-matching one, kept being tested and,
     if it happened to match too, ran its body as well. Also fixed
     along the way: `;;` was tokenizing as two separate `;` tokens
     rather than its own doubled-operator form (needed for `case`'s
     own arm terminator), by adding `;` to `NORM-DOUBLED-OP?` alongside
     `&`/`|`/`>`. See `PROGRESS.md`'s Iteration 27 entry for the full
     account.

     A significant, independent bug found and fixed along the way
     (Iteration 26, while testing `case` directly rather than
     something `case` itself caused):
     `TOKENIZE`'s in-place token compaction assumes the write cursor
     (`TOK-OUT`) never advances past the read cursor (`TOK-POS`) after
     an expansion — true for quote-stripping, false for `$VAR`/`$(...)`
     whenever the expanded value is *longer* than its own reference
     text. When that happens, the write destroys unread input before
     `SCAN-TOKEN` reads it, and `SCAN-TOKEN`'s own loop then re-reads
     and re-emits that corrupted byte, cascading into a self-
     propagating "smear" until the line ends — confirmed via `git
     stash` to already exist in the committed Iteration 25 state, not
     introduced by anything recent. `echo $x in` with `x=hello`
     printed `hellollo` instead of `hello in`. Fixed with a new
     `ENSURE-ROOM`, which shifts the remaining unread line rightward
     just enough to make room before writing a longer-than-source
     expansion value. The existing test suite never caught this
     because no existing test combined "value longer than its own
     `$NAME` reference" with "more text follows on the same line" — see
     `PROGRESS.md`'s Iteration 26 entry for the full account, including
     why five existing, seemingly-relevant tests each individually
     missed it.

     Shell functions (`name() { <body> }`): **done (Iteration 28)** —
     definition (persistent, named storage, unlike `while`/`for`'s own
     "replay once, discard" body), redefinition (a later definition
     with the same name simply replaces the earlier one), invocation
     (checked in `DISPATCH` ahead of external `PATH` search, existing
     builtins still take priority on a name collision), and genuine
     self-recursion (each invocation's own "which body line am I on"
     position nested via `>R`/`R>`, mirroring `if`'s own
     `COND-TRUE?`/`SUPPRESS-EXEC?` nesting from Iteration 22). Requires
     `{` either on the same line as `name()` (the common style) or its
     own line, but unlike `if`'s own same-line flexibility, each body
     line and the closing `}` must be on their own separate line — a
     deliberate, simpler initial scope cut. Shares the same
     multi-line-construct limitation noted above (a function body
     can't contain a nested `if`/`while`/`for`, for the identical
     reason). Recursion testing surfaced two real, independent bugs,
     neither specific to functions at all: (1) a standalone
     `NAME=value` assignment used as one segment of an `&&`/`||` chain
     was never recognized as an assignment, since that check had only
     ever lived in the non-chained fall-through path; and (2)
     `COPY-ARGV` never touched `ARGV-QUOTED`, so a stale "quoted" flag
     left behind by an earlier piece's own `$VAR` expansion could
     silently hide a real operator token from a later piece, if it
     happened to land at the same `ARGV` index after being copied in —
     found via a three-segment `&&` chain where the second `&&`
     vanished entirely. Both fixed; see `PROGRESS.md`'s Iteration 28
     entry for the full account, including why the fix restores
     quoted-flags at exactly two call sites rather than changing plain
     `COPY-ARGV` itself, and why that leaves the extent of the same
     hazard at other `COPY-ARGV` call sites (pipeline segments, group
     bodies) unverified rather than claimed safe.

     `return [n]`: **done (Iteration 29)** — exits the innermost
     currently-executing function immediately (`$?` becomes `n` if
     given, otherwise left as the last command's own status, per
     POSIX), correctly skipping everything else in that function's own
     body, including any remaining `;`/`&&`/`||`-chained segments on
     the same line `return` appeared on. A single `RETURN-PENDING?`
     flag, checked in exactly two places (`RUN-SIMPLE-OR-PIPELINE`,
     alongside the existing `SUPPRESS-EXEC?` check, since every
     individual command eventually funnels through there regardless of
     `;`/`&&`/`||` structure; and `RUN-FUNC-BODY`'s own replay-loop
     condition) — reset by `RUN-FUNC-BODY` itself before returning to
     its own caller, so an inner, recursive invocation's own return
     never leaks out to stop an outer, still-in-progress caller too. A
     top-level `return` (outside any function) is diagnosed rather
     than silently setting a flag nothing would ever consume. Went
     smoothly — every case passed on the first attempt. See
     `PROGRESS.md`'s Iteration 29 entry for the full design.

     `break`/`continue`: **done (Iteration 30)** — `break` exits the
     innermost enclosing `while`/`for` loop immediately; `continue`
     skips the rest of the current iteration and proceeds to the
     next as usual. Both recognized even from within a function
     called by a loop's own body — the trickiest case — via two flags:
     `LOOP-CONTROL-PENDING?` (set by either, checked by
     `RUN-SIMPLE-OR-PIPELINE` and both `RUN-FUNC-BODY`'s and
     `DO-WHILE-BODY`'s own replay loops, but reset only by
     `DO-WHILE-BODY`, so it keeps propagating outward through however
     many function-call frames separate the break/continue from the
     loop iteration it's actually meant for) and `LOOP-BREAK?` (set
     only by `break`, surviving past `DO-WHILE-BODY`'s own reset so
     the outer loop can check it and decide whether to stop entirely
     or proceed as normal). `LOOP-DEPTH` diagnoses break/continue
     outside any loop, mirroring `return`'s own `FUNC-DEPTH`. Went
     smoothly — every case passed on the first attempt, since the
     design was fully thought through before writing any code. See
     `PROGRESS.md`'s Iteration 30 entry for the full account.

     **Phase C is now complete, and so is nesting** (Iterations 42
     and 43). A loop or function body can contain any combination of
     `if`/`while`/`for`, at any depth — verified against `bash` on a
     three-deep `while` > `for` > `if` script. Two independent causes
     had to be fixed: replay had to become a real *input source* so a
     nested construct reads its continuation lines from the stored
     body (42), and the capture buffers had to become per-invocation
     arena allocations with a nesting-depth count in the capture loop,
     or the outer capture stopped at the inner loop's `done` (43).
     Still open: `BODY-ARENA-MAX` is a fixed 65,536 (growing it needs
     a chunked arena, since live pointers point into it — see the
     memory policy above); `WHILE-BODY-MAX` is still a fixed 4,096 per
     body; nested function *definitions* are not supported; and the
     unverified extent of the `COPY-ARGV`/`ARGV-QUOTED` hazard beyond
     the two call sites fixed in Iteration 28.
   - **Phase D — expansions.** Positional parameters (`$1`.., `$@`,
     `$*`, `$#`, `set`): **done (Iteration 31)** — a function's own
     call arguments, or a script's own command-line arguments at the
     top level, become `$1`-`$9` (single-digit access only, a
     documented scope limit) within its own scope; `set a b c`
     replaces whichever is currently active. Nested and recursive
     function calls each see only their own arguments — the caller's
     own positional parameters are saved (keyed by `FUNC-DEPTH`) and
     restored once the call returns. A real bug found by testing:
     `SAVE-POS-PARAMS`'s own `MOVE` call had source/destination
     backwards, silently corrupting the current parameters instead of
     preserving them — only surfaced once a nested (non-recursive)
     call test re-checked `$1` after the inner call returned. See
     `PROGRESS.md`'s Iteration 31 entry for the full design.

     `${#VAR}` (length), `${VAR:-word}`/`${VAR-word}` (default value),
     `${VAR:=word}`/`${VAR=word}` (assign default), `${VAR:+word}`/
     `${VAR+word}` (alternate value): **done (Iteration 32)** — the
     `:`-prefixed variants trigger on `VAR` being unset *or* empty;
     the plain variants trigger on unset only. Extracted into a
     dedicated `EXPAND-BRACED-VAR`, replacing the old inline `${NAME}`
     block, which just looked up everything between the braces as one
     literal name — workable for a plain name, but would have looked
     up (and failed to find) `${VAR:-word}` as a variable literally
     named `"VAR:-word"`. Went smoothly — every case passed on the
     first attempt. See `PROGRESS.md`'s Iteration 32 entry.

     `${VAR%word}`/`${VAR%%word}`/`${VAR#word}`/`${VAR##word}`
     (prefix/suffix removal): **done (Iteration 33)** — built on
     `GLOB-MATCH` (from `case`/`esac`), but needed new logic to find
     the shortest/longest *partial* prefix/suffix match rather than a
     whole-string match, by trying candidate lengths one at a time.
     While building this, found and fixed a significant kernel
     behavior: a `(...)` comment spanning multiple physical lines can
     silently corrupt parsing once enough code precedes it earlier in
     the file, surfacing as a cascade of unrelated "Undefined word"
     errors. Confirmed empirically (200 unrelated filler word
     definitions reproduced the identical failure in an otherwise
     pristine file) and fixed by collapsing the affected comment onto
     one line — no content change. **Future iterations should treat a
     sudden cascade of unrelated "Undefined word" errors as a signal
     to check for multi-line `(...)` comments first**, rather than
     assuming a logic bug in whatever was just edited; prefer `\` line
     comments (used pervasively already, never observed to have this
     problem) for anything spanning multiple lines. See `PROGRESS.md`'s
     Iteration 33 entry for the full investigation.

     Tilde expansion: **done (Iteration 34)** — a bare `~` at the very
     start of a word expands to `$HOME` (whole word, or followed by
     `/`); `~user`/`~+`/`~-` are out of scope. `TRY-TILDE-EXPAND`,
     called once at the start of `SCAN-TOKEN` before any other
     character is processed, since tilde expansion only ever applies
     right at a word's start. Reuses `$VAR` expansion's own
     `LOOKUP-VAR`/`TYPE0-TO-TOK`/`ENSURE-ROOM` mechanism. A real bug
     found immediately by testing: `S" HOME"` leaves `(addr len)` on
     the stack, not the single NUL-terminated address `LOOKUP-VAR`
     expects — corrupted the stack and crashed on the first real test;
     fixed by copying into the existing `ENVNAMBUF` scratch buffer
     first, the same pattern already used elsewhere in this file for
     this exact need. See `PROGRESS.md`'s Iteration 34 entry.

     Arithmetic expansion (`$((...))`): **done (Iteration 35)** — a
     real, precedence-climbing recursive-descent grammar (`||`, `&&`,
     `==`/`!=`, `<`/`>`/`<=`/`>=`, `+`/`-`, `*`/`/`/`%`, unary
     `-`/`+`/`!`, parentheses, decimal literals, variables — no
     bitwise, ternary, assignment forms, or octal/hex). Built and
     fully verified in an isolated diagnostic (22 cases) before
     touching `shell.4` at all, catching two bugs early (a missing
     `RECURSE` for self-reference within a still-compiling definition;
     a test helper consuming its own length argument before needing
     it again). A third, more significant bug surfaced only once
     wired in: `NORMALIZE-OPERATORS` had no awareness of `$((...))`
     regions, corrupting `2<=2` into `2 < =2` before the evaluator
     ever saw it — fixed the same way quoted regions are already
     protected, with new `NORM-IN-ARITH?`/`NORM-ARITH-DEPTH` tracking
     mirroring the existing quote-tracking shape exactly. See
     `PROGRESS.md`'s Iteration 35 entry for the full account.

     `IFS`-based field splitting of unquoted expansion results: **done
     (Iteration 36, completing Phase D)** — an unquoted `$VAR`/
     `${...}`/`$(...)`/`$((...))` result splits into separate `ARGV`
     entries wherever `IFS` whitespace (space/tab only, not yet a
     customizable `$IFS`, not newline) appears within it, composing
     correctly with literal text before/after the expansion in the
     same word. Built and verified in an isolated diagnostic before
     touching the real tokenizer. `EMIT-EXPANDED-CHAR`'s own split
     decision is deferred until the next non-`IFS` character actually
     needs writing — collapsing consecutive `IFS` runs into one split
     and avoiding spurious empty leading/trailing fields, both
     confirmed necessary and correct by direct testing. Two real bugs
     found: (1) the first attempt reused `TOK-WAS-QUOTED?` to decide
     whether to split, but that flag is set unconditionally by
     `EXPAND-VAR` for *every* expansion — fixed with a new, dedicated
     `IN-DQ-CONTEXT?` flag set only by `COPY-DOUBLE-QUOTED`; (2) a
     second, independent, *pre-existing* bug (confirmed via `git
     stash` to already exist in the prior commit) where
     `TRY-ASSIGNMENT` rejected any `x="value"`-style assignment
     because it checked the wrong "am I quoted" flag — fixed with a
     new, more precise `ARGV-NAME-QUOTED` array (true only if a
     token's own first character came from inside a quote), leaving
     the existing `ARGV-QUOTED` and its other uses untouched. See
     `PROGRESS.md`'s Iteration 36 entry for the full account.

     **Phase D is now complete.**
   - **Phase E — command substitution completeness.** Nested
     `$(...)`. Backquote `` `...` `` substitution. A `$(...)` body
     that supports the full command grammar (pipelines, quoting,
     expansion) rather than today's bare whitespace-split
     `CMDSUB-TOKENIZE` — likely requires the "save outer tokenizer
     state, run the inner command through the real `TOKENIZE`, restore
     outer state" approach considered and set aside as too complex
     during Iteration 13, now worth revisiting given the payoff.
   - **Phase F — builtins.**
     `[`/`test` and `:`: **done (Iteration 37)** — string tests (`-z`,
     `-n`, `=`, `!=`, bare non-empty check), numeric comparisons
     (`-eq`, `-ne`, `-lt`, `-le`, `-gt`, `-ge`), `!` negation (of a
     bare/1-arg test, or a full 3-arg `a op b`), and an approximate
     `-e`/`-f`/`-d` (existence only, via `OPEN-FILE` — no real
     stat/access primitive exists, so `-f`/`-d` can't distinguish file
     types). Installing `test` as a builtin shadows the external
     `/usr/bin/test` any script invokes bare, breaking
     `tests/shell/run-while` immediately (it uses bare `test -f`,
     which the initial implementation didn't recognize at all) — fixed
     by adding `-f`/`-d` as aliases for the same existence check `-e`
     uses. See `PROGRESS.md`'s Iteration 37 entry for the full design
     and documented scope limits (no `-r`/`-w`/`-x`/`-s`, no `-a`/`-o`,
     no `(` `)` grouping, no 3-arg negated unary tests).

     Still open: `read`. `readonly`.
     `shift`. `getopts`. `command`. Background jobs, `wait`, `$!`.
     `alias`/`unalias`. `ulimit`. Possibly `trap`, `exec`, `hash`,
     `type` if a test ends up needing them.
   - **Phase G — remaining conformance edge cases.** Both remaining
     `.fail.sh` cases are now genuine failures, each expecting
     `shell.4` to *reject* input it currently accepts with status 0:
     `2.2.2-nested-single-quotes.fail.sh` (should reject
     unterminated/invalid single-quote nesting) and
     `2.2.3-alias-expansion.fail.sh` (passed accidentally until
     Iteration 36 — see the count history above; a real pass here
     needs `alias` from Phase F first, and then the shell must reject
     the test's invalid alias usage rather than silently accepting
     it).

   `tests/mrsh-suite/run.sh` is the acceptance criterion for this
   goal — re-run it after each phase (or each iteration within a
   phase) and let the pass count go up honestly, the same way
   `tests/run_tests.sh` and `tests/shell/run-all` already track
   progress elsewhere in this project.

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
