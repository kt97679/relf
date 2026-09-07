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

- **`FORTH-STYLE.md` is the coding-practice reference.** Read it
  before writing Forth here. Every rule in it is paired with the
  incident that produced it, and most of the recurring defect classes
  in this project are covered: stack-parameter limits, position
  independence, sentinel values, keeping flags with their data,
  reentrancy of globals, this kernel's specific hazards
  (`DO`/`LOOP` at `start = limit`, multi-line `( )` comments,
  inherited `BASE`), the three testing layers, and when a small
  facility is worth building versus a language layer.

- **Read `PROGRESS.md` through its Index, never end to end.** It is
  119 entries and roughly 114k tokens — over half a context window,
  and reading it whole is not a thorough start, it is most of the
  budget spent before any work begins. The Index at the top lists
  every entry in one screen (~2k tokens); find the one you need and
  read that entry (~700). A citation elsewhere in this repository
  always gives an iteration number, which is what to search for.

- **These two documents are the ones that can go stale.**
  `PROGRESS.md` only makes claims about the past and cannot rot;
  `GOALS.md` and `PARSE-EXPAND-PLAN.md` make claims about the present
  tense, and they rot silently and in the worst direction — describing
  finished work as unfinished, in the file a new session is told to
  trust first. Iteration 122 found five such claims, some eighty
  iterations old, each of which could have sent a session to rebuild
  something that already worked. **When an iteration finishes an item
  named here, update this file in the same commit**, and audit the
  open items whenever the shape of the work changes rather than
  waiting to notice.

- **Periodically audit for duplication and refactor.** Not only when
  adding a feature: look over the codebase for repeated shapes and
  collapse them, keeping it simple, minimal and orthogonal. This has
  repeatedly turned out to *fix bugs*, not just shorten files —
  merging the four prefix/suffix searchers (Iteration 39) and the two
  group splitters (Iteration 50) each removed a latent defect that
  existed in one copy and not the other. A duplicated shape is a place
  where two copies can disagree.
- **Mine the bash maintainers' experience.** Ramey's chapter (see the
  bash-architecture section below) has already named three bugs this
  project actually had, before they were found here. When a design
  question comes up, check what bash does and why, rather than
  deriving it from scratch — and record the finding.
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

  **GPLv2-only, and it cannot be changed here.** The headers in
  `relf.c`, `kernel.4` and `cross.4` say "released under the GNU
  General Public License version 2" with no "or any later version",
  and GPLv2-only is incompatible with GPLv3. Relicensing would need
  the copyright holders' permission — Kirill Timofeev for the RelF
  sources and L.C. Benschop for SOD32, which `relf.c` derives from —
  and would work against the push-back-to-upstream target above,
  since a GPLv3 fork could not be merged back.

  Practical consequence, and the reason this came up: **bash's own
  test files cannot be vendored** (bash is GPLv3). That is no loss.
  Its tests encode bash behaviour including extensions this shell
  deliberately does not have, so they would import failures that are
  not bugs. Using bash as a *live oracle* instead — `tests/diff/` —
  has the same authority, no licence entanglement, and no bash-isms.

## Build environment: what a fresh machine needs

Everything here is checked into the repository except the toolchain.
There is no `configure`, no `Makefile`, and no package manifest, so
this is the list.

**Required.**

- **A C compiler reachable as `cc`.** `tests/run_tests.sh` invokes
  `cc -O2 -Wall` directly. GCC and Clang both work.
- **32-bit support for that compiler**, because the suite builds
  `relf32` with `cc -m32` and *every commit must pass on both cell
  widths* (see Repository conventions). On Debian/Ubuntu:

      apt-get update && apt-get install -y gcc-multilib

  Without it `cc -m32` fails with `cannot find Scrt1.o` and
  `run_tests.sh` prints `SKIP:` and carries on — so the 4-byte-cell
  half is silently not tested. **Install it before trusting a green
  run.** A container image with only the 64-bit libraries looks
  entirely healthy while checking half of what it claims to.
- **`bash` and `dash`.** `tests/diff/` uses bash as a live oracle;
  the mrsh suite compares against `sh`, which is dash on Debian and
  Ubuntu; `tests/bench` reports both. They are test dependencies, not
  runtime ones - the shell itself needs nothing but libc.
- **`timeout`** (coreutils), used throughout the test scripts.

**Strongly recommended: more reference shells.** `tests/posix/` scores
a case only when every reference shell present agrees, so each one
added makes that suite stricter about what it scores and more
trustworthy about what it does. With only dash and bash it degrades to
`tests/diff/` and says so in its output. On Debian/Ubuntu:

    apt-get install -y mksh yash posh ksh busybox-static

That gives seven independent readings - dash, bash, mksh (MirBSD ksh),
ksh93, yash, posh and busybox ash - which is what the numbers in
`PROGRESS.md`'s Iteration 127 entry were measured against.

**`zsh` is deliberately not a reference.** Invoked as `zsh script.sh`
it runs in its native mode rather than sh emulation and differs from
POSIX on word splitting and much else, so it would generate
INCONCLUSIVE verdicts about zsh rather than about the specification.
A fine shell, the wrong oracle. `POSIX_REF_SHELLS` can add it back for
anyone who wants to see what it says.

**Not required.** `qemu-user` only for the ARM64 cross-check recorded
in Phase 5; nothing in the normal loop needs it.

**Rebuilding `kernel.img`.** It is a committed build artifact and does
*not* rebuild itself. Adding an engine primitive means editing the
dispatch table in `relf.c` and the `PRIMITIVE` list in `kernel.4` -
which are positional, so append at the end of both - and then
cross-compiling:

    ./relf kernel.img
    S" extend.4" INCLUDED
    S" cross.4" INCLUDED

which overwrites `kernel.img` in place. Do not delete it first: the
cross-compiler runs *on* the existing image. Recovering from that is
`git checkout kernel.img` (Iteration 120 did exactly this wrong).
Delete `kernel-shell.img` afterwards so `relfsh` rebuilds the shell
image against the new kernel.

**The whole check** is `bash tests/run_tests.sh` (core suite on both
cell widths, shell suite, differential suite) plus
`bash tests/mrsh-suite/run.sh` and `tests/posix/run.sh`. `tests/bench` is deliberately not run
by either; run it when performance is the point.

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

**The four layers, and what each is for.** `FORTH-STYLE.md` §13 covers
how to test; this is what exists:

1. **`tests/` core suite** - `tester.fr` and the Forth-level tests, run
   on both cell widths. Counted in OK markers.
2. **`tests/shell/run-*`** - hand-written shell assertions, one file
   per feature, run by `tests/shell/run-all`. Use these for things bash
   is the *wrong* oracle for: diagnostics this shell emits, forms bash
   accepts that this shell deliberately rejects, and its own scope
   limits. `run-unterminated` is the model.
3. **`tests/diff/cases/*.sh`** - the differential suite. Each case is a
   plain script run under both this shell and bash, with the outputs
   compared and **no hand-written expectations at all**. This is the
   strongest layer and the one to reach for first: it has caught bugs
   no hand-written test would have, precisely because nobody had to
   think of the failing case. Add cases *before* changing behaviour.
   Note the scripts must avoid forms bash and this shell legitimately
   disagree on, or the case fails for the wrong reason.
4. **`tests/mrsh-suite/`** - vendored third-party acceptance tests, the
   criterion for goal 8. Not editable; they are the outside view.
   **Fully passed as of Iteration 125.**
5. **`tests/posix/`** - conformance cases derived from POSIX.1 XCU
   itself, scored against the *consensus* of every reference shell
   present rather than against one. A case only counts when the
   references agree; where they disagree it is reported
   INCONCLUSIVE and scored neither way, which keeps one shell's
   extensions from becoming the standard. This is the successor to
   layer 4 now that layer 4 is passed, and the layer that will grow.
   See its own `README.md`.

A `run-*` file must be executable and is picked up by `run-all`
automatically. Run them through `run-all` rather than directly:
`lib.sh` defaults `THIS_SH` to `../../relfsh`, so a file run from the
repository root silently tests a shell that does not exist and reports
every assertion as a failure.

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
  Met at Iteration 125.
- `tests/posix/run.sh`: passed / failed / **inconclusive**, plus which
  reference shells were present. All three move honestly; a rising
  inconclusive count means the references disagree more, not that the
  shell got worse.
- **Size**: `tests/sizes` — stripped engine + prebuilt shell image on
  both cell widths, and every other shell installed, on one table.
- **`tests/bench`**, when performance is the point. Not run by
  `run_tests.sh` - it takes minutes and is noisy. Iteration 116's
  measurement: loop 944ms, spawn ~155ms, startup ~235ms, against
  dash's 4/72/98. The loop figure is the one Stage 2 of
  `PARSE-EXPAND-PLAN.md` exists to move.

Baseline at Iteration 41, and where it stands at Iteration 137:

| | engine | image (41) | image (127) | image (137) | total (137) |
|---|---|---|---|---|---|
| **i386 (4-byte cells)** | 17,808 | 72,528 | 134,500 | 101,104 | **118,912** |
| x86-64 (8-byte cells) | 22,744 | 131,784 | 251,104 | 189,024 | 211,768 |

Iterations 136 and 137 took 33,396 bytes off the i386 image - every
`CREATE ... ALLOT` buffer moved out of the dictionary, and the locals
prologue/epilogue reduced from three cells per local per entry and
exit to one call each. **The i386 total is below a same-architecture
`dash`; the x86-64 total is 1.63x it.** See the per-architecture
tables below - Iteration 138 found the earlier comparison was mixing
word sizes.

**Against other shells, per architecture** (Iteration 138, run
`tests/sizes`). Architectures are never ranked against each other -
they were until 138, and the conclusion drawn from that table did not
survive fixing it.

*x86-64, the build that matters for a modern machine:*

| implementation | total |
|---|---|
| dash | 129,784 |
| posh | 149,352 |
| mksh | 310,312 |
| **shell.4** | **211,768** |
| yash | 653,680 (+libtinfo) |
| ksh93 | 1,432,848 |
| bash | 1,654,352 (+libtinfo) |

**shell.4 is 1.63x `dash` here**, between mksh and yash. That is the
honest headline: on the word size this machine actually runs, this is
not the smallest shell and is not close to `dash`.

*i386, where cell width suits the design:*

| implementation | total |
|---|---|
| **shell.4** | **118,912** |
| dash | 136,936 |
| posh | 163,308 |

**shell.4 is 0.87x `dash` here.** The comparators are built from
Debian source by `tools/build-shells-i386.sh`, and the same script
builds each for x86-64 from the same source and flags - a locally
built 32-bit binary against a distro-built 64-bit one would just swap
one unfair comparison for another. Its `dash` at 129,832 against the
distro's 129,784 is the check that the build is representative.

Worth knowing: **both comparison shells are LARGER at 32 bits than at
64** - dash 136,936 against 129,832, posh 163,308 against 149,336.
x86-64 code is not much bigger than i386 code and the extra registers
cut spills, while i386 position-independent code pays for GOT setup.
So the i386 result is not an artifact of comparing against a bloated
32-bit build; it holds against the fairest comparator available.

Read either table with the conformance number beside it or it means
nothing. It is **not** a claim to be a smaller bash: bash implements a
language several times larger, and the gaps under "Still open" are
real. The trajectory is the point, not the rank.

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

**Now measured, and planned: see `DENSITY-PLAN.md`** (Iterations 130,
131) **and `VM-RESEARCH.md`** (Iteration 139), which reviews the
published work and finds three larger options the plan did not have -
including token threading - designed in detail in
`TOKEN-THREADING.md`, the only idea found that attacks the
x86-64 size problem, and a measured 9% figure for the
variable-length encoding this file had rejected on reasoning alone. Two options, both of which should also make the image *faster*:
constant-pushing primitives over the range -1..63 (4,560 bytes on
i386) and superinstructions built from iterated pair fusion (11,708 at
K=128, less the engine growth they cost). Roughly 15KB together.

**Headerless words are withdrawn, not deferred.** Extending the shell
in Forth requires `FIND`, `FIND` requires headers, and the 16,400
bytes below are what that costs. Lever 1 is kept here as the record of
a decision rather than a plan.

1. **Headerless words — rejected (Iteration 131).** `cross.4` carries a commented-out
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
  The body arena (Iteration 44) is the worked example: it starts at
  4KB and doubles via `RESIZE`, with no maximum.
- **Hold offsets, not pointers, into anything growable.** `RESIZE` is
  allowed to relocate a block and measurably does — 7 moves in 15
  calls on this machine. That is *safe* as long as nothing outside
  holds a raw pointer in. Offsets are already the rule everywhere else
  here (`START`-relative xts, `BOOT`, locals' slots, the `BUFFER:`
  chain); this is the same rule, and it is what makes growable
  allocation work without a chunked-arena scheme.
- **A full fixed table must never fail silently.** Several still do,
  and each produces wrong output rather than an error: `MAX-SHVARS`
  (32 shell variables — found in Iteration 44, `SET-SHVAR` just does
  nothing when full), `MAX-FUNCS` (16), `MAX-POS-PARAM-DEPTH` (32),
  `MAX-ARGS` (64). Making them growable is the goal; diagnosing
  overflow is the minimum.

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

**Status only.** How each phase was done, and every bug found getting
there, is in `PROGRESS.md` — find the entry through its Index rather
than reading the log. This section went stale twice by trying to be
both, so it no longer carries accounts.

1. **Scaffolding** — repo structure, test runner, process log.
   **Done** (Iteration 1).
2. **No-libc, syscalls-only x86-64 engine.** **Done** (2), and
   **deliberately superseded by phase 5**, which traded no-libc back
   for portability. `relf.c` is the only engine; `relfgcc.c`,
   `vm.asm` and `vm_tos.asm` are gone and are not coming back.
3. **Forth-hosted assembler** — a `CODE`/`END-CODE` facility so the
   engine itself can be assembled by the running Forth system rather
   than by `gcc`/`as`. **Not started.** This is the last piece of
   goal 1 and the only phase never begun.
4. **JIT/AOT** — extend the phase-3 assembler to compile hot
   colon-word bodies to native code, including non-recursive call
   inlining. **Not started**; needs phase 3 first.
5. **Portability + performance without JIT.** **Done except
   call-flattening** (3). libc as the portability layer,
   native-endianness images with a magic header, computed-goto
   dispatch measured at ~1.30x. Verified on x86-64 and ARM64 running
   the identical `kernel.img`. Call-flattening and the rejected
   byte-granular opcode encoding are covered in the phase 5 section
   below.
6. **32-bit-cell targets.** **Done**, verified on i386 (4). Cell
   width is a compile-time parameter of the engine and a
   `TARGET-CELL-BYTES` parameter of the cross-compiler. ARM32 should
   work by the same mechanism but has not been attempted. Details in
   the phase 6 section below.
7. **Userland: a POSIX-flavored shell on RelF.** **Done and
   continuing.** Fourteen process-control primitives in the engine
   plus `shell.4`, `relfsh`, and the test suites. For the
   user-facing feature set, read `README.md` §4 — it is the
   description of what the shell does today, and this file does not
   duplicate it. Iterations 5-13 built v0.1 through v0.8; everything
   since has been driven by phase 8.
8. **Goal: pass the whole mrsh test suite.** **Done** (Iteration
   125): 20 of 21, and the one failure is a test upstream itself does
   not run. See below.

## Phase 8: the mrsh suite, and what is left

mrsh (https://github.com/emersion/mrsh) is a minimal but far more
complete POSIX shell. Its test suite, vendored unmodified into
`tests/mrsh-suite/vendor/` at commit
`4c81598721bc5eeb28f9faa818b3102d0471b7f6`, is adopted here as a
concrete external target rather than one this project invents its own
criteria for. `tests/mrsh-suite/run.sh` is the acceptance criterion;
re-run it after each iteration and let the count move honestly.

**Current: 20 passed, 1 failed, 3 skipped**, measured against `sh` —
and the single failure is `2.2.3-alias-expansion.fail.sh`, which is
**commented out of upstream's own conformance `meson.build`** against
a TODO citing mrsh issue #145. mrsh does not run it either.

**So against the set mrsh itself runs, this suite is fully passed:
20 of 20**, as of Iteration 125. `run.sh` keeps scoring the disabled
file rather than quietly dropping it, so the headline number stays
20 of 21.

The reference shell is `${REF_SH:-sh}`, matching upstream's own
`meson_options.txt` default. This harness used bash until Iteration
124, and that choice was costing a genuine pass and buying a hollow
one — see below. `REF_SH=bash tests/mrsh-suite/run.sh` still works and
is worth a periodic second opinion, but `sh` is what the number means.

The 3 skips are `*.undefined.sh` conformance cases, which POSIX does
not specify a result for. Upstream runs them behind a
`test-undefined-behavior` option; this harness reports them unscored.
They are not outstanding work and never will be.

**What this does and does not mean.** It means `shell.4` handles
everything mrsh's own acceptance tests exercise. It does not mean the
shell is POSIX-complete — the suite is 21 files, and the gaps listed
under "Still open" below are real and unmeasured by it. Goal 8 has
served its purpose as an external, honest yardstick; a broader
criterion derived from the POSIX specification itself is the natural
successor, and is the direction after this.

### The hollow pass, and how it resolved (122, 124, 125)

`ulimit.sh` used to pass while `ulimit` was not implemented at all.
The harness is differential and bash *also* failed that test on a
modern host — its last assertion greps `/proc/self/limits` for a
512-byte block count bash reports in 1024-byte blocks. Two shells
failing for unrelated reasons produced identical output.

Moving the reference shell to `sh` (124) turned it into an honest
failure, and 125 implemented the builtin. Kept here as the worked
example of the rule: **check *why* a test passes, and re-audit the
passes when the count moves**, not only when it stalls. Iteration 82
audited the then-17 passes for exactly this and found none; two landed
afterwards and one of them was hollow.

The same test surfaced `set -e`, which is **not implemented** in
either spelling. It is inert in this suite and inert in mrsh's own:
upstream's `test/harness.sh` passes the script as an argument exactly
as `run.sh` does, so `#!/bin/sh -e` is a comment on both sides.
Checked against upstream rather than assumed (Iteration 123). A
genuine POSIX gap, just not one this criterion measures.

### The criterion here is stricter than mrsh's own

`2.2.3-alias-expansion.fail.sh` is **commented out of upstream's
`test/conformance/meson.build`**, against a TODO pointing at
mrsh issue #145 — mrsh does not run it either. So the honest reading
of the current result is:

- **19 of 21** by `run.sh`'s own arithmetic, which scores every
  vendored file.
- **19 of 20** against the set mrsh itself actually runs.

Either way one genuine failure remains, `command.sh`, and it is the
alias divergence. The vendored file stays and `run.sh` keeps scoring
it — deleting a test to improve a number is exactly the move this
suite was adopted to prevent — but the denominator should not be
quoted without knowing this.

### Phases A-G: all complete

Each was a multi-iteration effort. Named here so a citation elsewhere
resolves; the accounts are in `PROGRESS.md`.

- **A — infrastructure to run the suite at all** (15-16, with a
  script-file correctness fix in 21). Crash-hardening — five sites
  where this kernel's `DO`/`LOOP` runs the entire unsigned range at
  `start = limit` — and real file-argument invocation, so `relfsh
  testcase` and `bash testcase` are symmetric.
- **B — foundational semantics** (17-22, 24-25). Shell-local
  assignment, `;`, `&&`/`||`, command grouping, `if` nesting,
  self-delimiting operators, same-line `if`.
- **C — control structures** (23, 27-30, 42-44, 63). `for`, `case`
  with full glob matching, functions, `return`, `break`/`continue`.
  Nesting to any depth arrived in 42-44 once replay became a real
  input source and body storage became per-invocation; nested
  function *definitions* in 63.
- **D — expansions** (31-36). Positional parameters, `${#VAR}` and
  the `:-`/`:=`/`:+` and `%`/`%%`/`#`/`##` modifiers, tilde,
  arithmetic, `IFS` field splitting — with `$IFS` genuinely
  controlling it since 67.
- **E — command substitution completeness** (73, 105). Finished by
  *deleting* `CMDSUB-TOKENIZE`: the substituted text is installed as
  a replay input source and read through the real tokenizer in the
  forked child, so nesting, pipes, redirection, compound commands and
  quoting inside `$(...)` work as a consequence rather than as
  features. Costs one extra fork per substitution, taken knowingly.
- **F — builtins** (37, 51, 54, 59, 61, 68, 69, 74). `test`/`[`, `:`,
  `shift`, `readonly`, `read`, `alias`/`unalias`, `getopts`,
  `command -v`, background jobs with `wait` and `$!`.
- **G — conformance edge cases** (60, 81). Unterminated quotes are a
  syntax error. The remaining `.fail.sh` case is the alias conflict
  above.

### Still open under this goal

Real gaps, each verified as of Iteration 122 rather than inherited
from an older revision of this file:

- **`NAME=value command args...`** — POSIX's temporary, per-command
  assignment prefix. Currently a failed command lookup, status 1.
  Ramey's temporary-scope design (see the bash-architecture section)
  is the shape to build.
- **Redirection does not apply to builtins - and the consequences are
  wider than that sentence suggests.** Iteration 146 found the same
  root behind `read -r l < file` reading nothing, `while read ...;
  done < file` producing nothing, and `{ ...; } > f 2>&1` writing
  nothing: any redirection whose target command is a builtin, or a
  compound containing one, is silently dropped. `pwd > file` writes to
  the terminal and creates nothing, because redirection is only
  applied in the forked child. Fixing it needs the **undo list** from
  Ramey's chapter: a redirection's effects must not outlive the
  command. Recorded in Iteration 55 as the next piece of redirection
  work.
- **Positional parameters stop at 9.** `set -- 1 2 3 4 5 6 7 8 9 10`
  leaves `$#` at 9; `${10}` cannot be reached. Found by
  `tests/posix/2.5.1-positional-parameters.sh` in Iteration 146.
- **`${#}`** - the count of positional parameters - yields 0.
  `${#var}` works; the bare form does not.
- **`for w; do ... done`**, the implicit `in "$@"` form, iterates over
  nothing.
- **`eval` is not implemented** (status 127). A POSIX special
  built-in.
- **`"$*"` joins with a space regardless of `IFS`.** POSIX says the
  first character of `IFS`, and nothing when `IFS` is null.
- **Non-whitespace `IFS` produces no empty fields.** With `IFS=:`,
  `a::b:` must split into three fields; it yields two.
- **Arithmetic division truncates the wrong way for negatives.**
  `$((-7 / 2))` is -4 here and -3 everywhere else; ISO C, which XCU
  2.6.4 defers to, truncates toward zero.
- **A reserved word cannot be a `for` list value.**
  `for x in do done; do ...; done` iterates over nothing.
- **Quoted and escaped patterns in `case` do not match.**
  `case 'a*b' in 'a*b')` selects no arm, and neither does `*)`.
- **An empty `case` word does not match an empty pattern.**
- **`set -e`**, per above.
- **`until` is recognised and then silently ignored.** It is in the
  reserved-word list (`shell.4` line 3155, so it is correctly refused
  as a command name) but the compound-command dispatcher tests only
  `while` and `for`, so `until ...; do ...; done` runs **nothing** and
  exits 0. A POSIX compound command that is a silent no-op, unrecorded
  here until Iteration 144 audited for it.
- **`{ ... }` spanning lines drops every line but the last**, silently.
  `SPLIT-GROUP` handles a group contained in one line only.
- **`&` is treated as a line terminator, not a list terminator.**
  `true & echo after` passes `&` and `echo` and `after` as arguments
  to `true`. A command may follow `&` on the same line.
- **`$( (list) )` is read as arithmetic.** POSIX requires the space to
  disambiguate a command substitution whose first token is a subshell
  from `$((` arithmetic expansion; this shell ignores it, so
  `x=$( (echo n) )` yields the empty string. `$((echo n))` likewise
  yields 0 where other shells diagnose it. `NORMALIZE-OPERATORS`'
  comment predicted exactly this when it left `(` and `)` out of
  operator spacing.
- **`case` cannot be written on one line**, and therefore cannot
  appear in a one-line function body. `case x in x) echo M ;; esac` is
  a syntax error.
- **Content after a nested `fi` on the same line is dropped**,
  silently. The un-nested form works.

  The last four are one fault with four faces: the line is the unit of
  both input and body storage, so each construct needs its own
  same-line adapter and the ones that never got one are broken. See
  Iterations 143 and 144, and `PARSE-EXPAND-PLAN.md` Stage 2, which
  fixes the class rather than the instances.
- **`trap`, `exec`, `hash`, `type`**, none of which anything has
  needed yet. `ulimit` landed in Iteration 125 — POSIX specifies only
  the file-size limit, so `ulimit [-f] [blocks|unlimited]` is the
  whole of it; other resource options are diagnosed, not ignored.
- **Fixed tables with hard limits.** No longer *silent* — Iteration
  90 gave `SET-SHVAR`, `SET-FUNC` and the positional-parameter save
  stack real diagnostics, and the 33rd variable now says so. They are
  still fixed. Growable is the goal; see the memory policy above.
- **A shell variable longer than 256 characters truncates** to the
  first line-buffer's worth. Found in Iteration 108, predates it,
  same family as the fixed tables.

## Non-goals (at least for now — revisit if this changes)

- **Non-POSIX shell extensions**, including here-strings (`<<<`),
  `[[ ]]`, arrays, and process substitution. The mrsh suite is the
  acceptance criterion for goal 8 and uses none of them (checked:
  zero occurrences of `<<<` in the vendored tests). They are cheap to
  add on top of what exists — `<<<` in particular is one more
  redirection op reusing the here-document's pipe — but they are
  additions to make deliberately once POSIX conformance is reached,
  not while it is still the goal.

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

## Where bash and POSIX disagree, and this shell follows POSIX

Deliberate divergences from the differential oracle. Each was checked
against a second reference (`dash`) before being recorded, because
"bash does X" and "X is correct" are not the same claim.

- **Aliases are not expanded by bash in non-interactive shells.** POSIX
  says alias substitution applies; this shell applies it, and so does
  `dash`. Cost two mrsh tests while bash was the reference shell;
  costs none since Iteration 124 moved the harness to `sh`, upstream's
  own default. bash is the outlier here, which is why the reference
  shell mattered more than it looked.
- **Tilde after `=` in a non-assignment word.** `echo other=~/y`:
  bash expands the tilde, dash does not, and neither do we. POSIX
  applies tilde-after-`=` to assignment *words*; an argument to `echo`
  is not one. bash is being permissive with any `name=value`-shaped
  word. (Iteration 98.)

## Known shortcuts to revisit

Deliberate compromises that work today and are wrong in general. Each
is implemented, tested and *incorrect in a way that will not show up
locally* — which is exactly why they need to be written down rather
than remembered.

- *(This section is currently empty. `~user` reading `/etc/passwd`
  directly was the last entry; Iteration 120 replaced it with a
  `GETPWHOME` primitive calling `getpwnam(3)`, which goes through NSS.
  Entries here are things that are implemented, tested and incorrect
  in a way that will not show up locally - keep adding them.)*

## Next architectural work: `PARSE-EXPAND-PLAN.md`

**Stage 1 is done** (Iterations 108, 112, 113, 114). Expansion writes
into its own buffer, so the in-place-growth bug class no longer
exists; word boundaries come from `NORMALIZE-OPERATORS`, the pass that
already knew them; and `EXPAND-WORDS` runs when a command runs rather
than when its line is read, which took the mrsh suite to 19 of 21. Stages 3 and 4 are done as well — nested `$(...)` in
Iteration 105, and the limitation notes retired in 115.

**Stage 2 is the only one left**: caching tokenized body lines, where
the pure-loop gap measured in `tests/bench` (236x dash, Iteration 116)
is addressed, and the only stage whose justification is speed rather
than correctness. Read that
file before starting; each stage must leave the full suite green and
be committed separately.

## Shell architecture: what bash does differently (read, Iteration 48)

From Chet Ramey's chapter on bash in *The Architecture of Open Source
Applications*, vol. 1 (https://aosabook.org/en/v1/bash.html). Read in
full; these are the parts that bear directly on `shell.4`, several of
which name bugs this project has actually had.

**On hand-written parsers.** Ramey, after twenty-odd years maintaining
bash's yacc/bison grammar: he has considered rewriting the parser as
straight recursive descent several times, and *"were I starting bash
from scratch, I probably would have written a parser by hand"*. Not to
be read as endorsing what `shell.4` does today — his target is
recursive descent building a **command tree**, and `shell.4` has a
sequence of split passes over one flat token array. The note says the
destination is right, not that we have arrived.

**Applicable now, in rough order of value:**

1. **Attach flags to the word, not to a parallel array.** Bash's
   `WORD_DESC` is `{ char *word; int flags; }`, and a word list is a
   list of those. `shell.4` keeps `ARGV` with `ARGV-QUOTED` and
   `ARGV-NAME-QUOTED` beside it — and *every* stale-flag bug this
   project has had (Iteration 28's vanishing `&&`, Iteration 47's
   literal `;`) is `COPY-ARGV` moving words without their flags.
   Bash's shape makes that class impossible.

   Half-addressed in Iteration 109: the bare `COPY-ARGV` was deleted
   rather than audited, so a word that moves words without their flags
   no longer exists to be called. The parallel arrays themselves
   remain, and Iteration 114 hit the same shape from a different
   direction — a global "is this list expanded" flag that did not
   travel with a copied segment. Still worth doing.
2. **Parse first, expand after. Done** (Iterations 108-114). Bash
   parses to a command structure, *then* expands words. `shell.4` used
   to expand during tokenization, in place, once per raw line — the
   single root of `FOO=bar; echo $FOO`
   not seeing the value (Iteration 18), `set a b c; echo $#` reporting
   0 (Iteration 45), and the whole `ENSURE-ROOM` smear class
   (Iterations 26, 46, 99, 103). Expansion is now `EXPAND-WORDS`, run
   when a command runs and writing into its own buffer: all three are
   fixed, and the smear class cannot recur because there is no shared
   buffer to overrun.

   Still short of Ramey's shape: he expands words hanging off a
   command *tree*, and this is still a flat token array with splitting
   passes over it. The destination is right; this is one step closer
   to it, not at it.

3. **Command substitution should reuse the real parser. Done**
   (Iteration 105), though not by this route: the substituted text
   became a replay input source read through the real tokenizer in the
   forked child, which already has its own copy of every buffer, so
   there was no state to save. `CMDSUB-TOKENIZE` is deleted, which was
   the point: Ramey regrets that bash's `parse_comsub` *"knows an
   uncomfortable amount of shell syntax and duplicates rather more of
   the token-reading code than is optimal"*, and that word was
   precisely it. The route sketched here — `)` flagged as EOF in that
   context, parser state saved and restored around a recursive parse —
   turned out not to be needed once the work happened in the child.

4. **Redirections need an undo list.** Their effects must not persist
   beyond the command, however the command is implemented. `shell.4`
   sidesteps this by only applying redirection in the forked child,
   which is why `pwd > file` does not redirect a builtin. When that is
   fixed, this is the mechanism.
5. **Aliases are purely lexical**, handled in the analyzer, with the
   parser telling it when alias expansion is permitted. That is the
   design for the pending `alias` item.
6. **Variable scoping**: bash uses hash tables plus linked lists of
   them, including *temporary scopes* for assignments preceding a
   command. That covers both the silently-full 32-entry `MAX-SHVARS`
   table and the unimplemented `NAME=value command` prefix.
7. `for for in for; do for=for; done` prints `for` — a good
   conformance test for reserved-word context handling.

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
