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
values that end up in target cells.

A third, since Iteration 243: **opcode numbers live in four places
that must agree** - `cv8.c`'s `direct_prims[]`, `escaped_prims[]`,
`NDIRECT` and `NESC`; `kernel.4`'s `PRIMITIVE`/`OPCODE` order and the
fixed numbers in its compiler (97-126); `cross.4`'s PART 4 constants;
and `shadow.4`'s four locals opcodes. The synthetic opcodes are derived
from the DIRECT primitive count by both compilers (Iteration 247); the
specialised band at 0x61-0x7E is written out, because it does not
move. `cv8.c` checks its two counts against its tables at build time. A mismatch is
silent: the image encodes one operation and the engine decodes
another. `CV8-REFERENCE.md` 3.2 has the map.

## End state (what "done" looks like)

- **No libraries.** The engine talks to the OS via raw syscalls only —
  no libc. **Done in phase 2 and deliberately undone in phase 5**,
  which traded it for portability: the engine uses libc, and the
  primitives are thin wrappers over it (`READ`, `WRITE`, `POLL`, ...).
  The goal stands; phase 5 explains why it waits. This applies to the
  *engine's runtime*, not to build-time bootstrap tooling: `gcc`/`as`/`ld`
  remain fine to use for building the engine until phase 3 below (a
  self-hosted assembler) replaces them.
- **Fully self-hosted.** Forth already compiles the Forth image:
  `cross.4`, running on the CV8 engine, compiles `kernel.4` into the
  CV8 `kernel.img` it runs on, byte for byte (Iteration 243). The remaining piece is Forth compiling the
  *engine itself* (currently `cv8.c`, built by `gcc`) — a Forth-hosted
  native-code assembler, in the tradition of the classic Forth
  `ASSEMBLER` wordset / `CODE ... END-CODE` facility.
- **Eventually, JIT/AOT.** Once the self-hosted assembler exists, extend
  it to compile hot colon-word bodies to native code, including
  unwinding (inlining) non-recursive calls. Prior exploratory
  benchmarking found dispatch removal alone gives ~4-4.75x, with a
  further ~2-2.2x from inlining non-recursive calls on top of that — this
  is the single biggest performance lever identified across everything
  tried, larger than any interpreter-level tuning.

## Where things stand (Iteration 248)

The state a reader needs before anything else in this file, because
several sections below describe a system with more parts than it now
has.

**One engine, and it hosts itself.** `cv8.c` runs CV8: a byte stream
of 1-byte opcodes with 2- or 3-byte compressed-pointer calls. `cross.4`
runs on the committed CV8 `kernel.img` and compiles `kernel.4` into a
new one, byte-identical; `kernel.4`'s own compiler emits the same
encoding for everything loaded at run time, including the shell. No
other engine, translator or language is involved. `relf.c`, the cell
engine that bootstrapped every image until Iteration 243, is in
`attic/` with the translator and the encoding lab; the tag
`cell-engine-final` is the last commit they built.

**The compiler emits what the translator used to add.** The
specialised opcodes (`CV8-REFERENCE.md` 7) were the difference between
the cell product and CV8, and only `tools/layout.py` emitted them. They
are now peepholes in `kernel.4` and `cross.4`, `OPCODE` declarations
for the tiny kernel words, and opcodes emitted by `shadow.4`. Measured:
the natively compiled shell runs at 0.99-1.02 of the translated one's
time on every `tests/bench-vm` workload, and 3.3-4.4x faster than the
cell product it replaced.

**Headers are byte-granular** (Iteration 244): a 1-3 byte backward
link, an unpadded name, an unaligned body, and so a call scale of 0.
Only parameter fields are aligned. `CV8-REFERENCE.md` 5 has the layout
and the rule every consumer must share.

**Image sizes, the numbers to quote** (`tests/sizes` has the totals):

    64-bit   kernel.img     8,726    kernel-shell.img     61,273
    32-bit   kernel32.img   8,122    kernel32-shell.img   55,865

**Sixty-six primitives**: 35 direct, with one-byte opcodes, and 31
OS/libc ones behind ESC + a selector, declared after `ESCAPED` in
`kernel.4`. The synthetic opcodes are numbered from the direct count,
so an escaped primitive costs no opcode (Iteration 247); 34 opcodes
are free. `CV8-REFERENCE.md` 3.2 has the map.

**Descriptor I/O is three primitives**: `READ` and `WRITE` (Iteration
245), one read(2) or write(2) each, returning a count or a negative
errno, and `POLL` (246), one poll(2). `FD-POLL` wraps it for one
descriptor; `KEY?` and `MS` are built on it, and `KEY` uses it to wait. Everything else is Forth on top, in `kernel.4`: `KEY` (one
byte, retrying `EINTR`), `ACCEPT` on `KEY`, `READ-FILE` and
`WRITE-FILE` (looping over short counts), `WRITE-LINE`, and
`READ-LINE`. Nothing reads ahead: `READ-LINE` reads a block from a
descriptor that can seek and seeks back over what follows the
newline, and reads anything else a byte at a time, so a pipe or
terminal shared with a child never loses a byte. The one buffer left
is the engine's for `TYPE`, flushed by every primitive that reads,
writes, forks, execs or exits.

**Single branch `master`.**

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

- **The build is reproducible, and that is checked.** A rebuilt image
  must equal the committed one byte for byte. It did not until
  Iteration 148: `SS-SCRUB` did not know about `shadow.4`'s scratch
  variables (added in 137) or about `#TIB`, so the image recorded
  leftover addresses and the length of the builder's last command
  line. Every test run dirtied the working tree, which meant no diff
  of a tracked artifact could be trusted. If a rebuild stops
  reproducing, something is saving transient state - look at
  `SS-SCRUB` first.

- **Read `PROGRESS.md` through its Index, never end to end.** It is
  about 222 entries and roughly 183k tokens (Iteration 243) — most of a
  context window, and reading it whole is not a thorough start, it is most of the
  budget spent before any work begins. The Index at the top lists
  every entry in one screen (~2k tokens); find the one you need and
  read that entry (~700). A citation elsewhere in this repository
  always gives an iteration number, which is what to search for.

- `INNER-INTERPRETER.md` is a design brief, not a record: it collects
  the measured constraints on `NEXT` and the alternatives to it, for a
  discussion that has not happened yet. It will be stale the moment
  that discussion reaches a conclusion.

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

  This held for 160 iterations, lapsed for about 70, and is restored.
  The engine work ran on `cv8` from Iteration 162, with `token16`
  branched off it; by 217 `master` was 72 commits behind and nothing
  was merging back. `cv8` fast-forwarded into `master` cleanly - there
  was never any divergence, only neglect - and both `cv8` and
  `token16` are gone. If a branch appears again, merge it back or
  delete it; do not let it run for seventy iterations.

  Some of the work also lives in a SEPARATE repository,
  `kt97679/forth-vm-evolution`, which is the article's working code.
  It is a fork of this system's engine and Forth sources, and
  improvements have flowed back from it - see "Integrated from the
  article repository" below. When the two disagree about a shared
  file, this tree is not automatically right.
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
  `cv8.c` (from `relf.c`), `kernel.4` and `cross.4` say "released under the GNU
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
dispatch table in `cv8.c` and the `PRIMITIVE` list in `kernel.4` -
which are positional, so append at the end of both - raising `NPRIM`
in `cv8.c`, and then cross-compiling. `cv8.c`'s header comment has the
details, including the escaped band. The kernel is the host of its own
rebuild, so an image that cannot run `cross.4` cannot be repaired from
the tree: rebuild from `git checkout kernel.img` or, failing that,
from the tag `cell-engine-final`. The rebuild is:

    ./relf kernel.img
    S" extend.4" INCLUDED
    S" cross.4" INCLUDED

which overwrites `kernel.img` in place. Do not delete it first: the
cross-compiler runs *on* the existing image. Recovering from that is
`git checkout kernel.img` (Iteration 120 did exactly this wrong).
Delete `kernel-shell.img` afterwards so `relfsh` rebuilds the shell
image against the new kernel.

**The whole check is `tests/verify`** (Iteration 148). It runs every
suite, checks that a rebuilt `kernel-shell.img` and
`kernel32-shell.img` reproduce the committed ones byte for byte, and
compares every number in `tests/BASELINE` with this run. Any difference -
better or worse - is reported and fails the run. When a change is
intended, commit the fix and `tests/verify --update` together, so
`BASELINE` always records what the tree actually does.

The individual suites still run on their own: `bash
tests/run_tests.sh` (core on both cell widths, shell suite,
differential suite), `bash tests/mrsh-suite/run.sh` and
`tests/posix/run.sh`. `tests/bench` is deliberately not run
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

**The layers, and what each is for.** `FORTH-STYLE.md` §13 covers
how to test; this is what exists:

1. **`tests/` core suite** - `tester.fr` and the Forth-level tests, run
   on both cell widths. Counted in OK markers. `tests/ext/` holds the
   CORE EXT, Memory-Allocation and File-Access suites, which need
   `extend.4` and run one file per engine invocation. `tests/io/run`
   checks how the kernel reads its terminal - `KEY` on a non-blocking
   pipe, `KEY?`, `MS`, `FD-POLL`, end of input and read errors - with a
   small C helper, `tests/io/nonblock.c`, to set `O_NONBLOCK`.
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

## Named locals (`shadow.4`) — available since Iteration 38

Not a goal in itself; infrastructure the rest of the project can use.
Load with `S" shadow.4" INCLUDED`. Spelled `SHADOW{ ... }` since
Iteration 236; it was `{: ... :}`, the standard's spelling for a
different thing.

`shell.4` carries 356 global `VARIABLE`s, most of which are not global
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

    : COPY-ARGV ( src-argv src-argc --- )  SHADOW{ CA-SRC CA-N }

    : GLOB-MATCH ( pat plen text tlen --- f )
      SHADOW{ GM-PATTERN GM-PLEN GM-TEXT GM-TLEN | GM-P GM-S }

Names before an optional `|` are initialized from the data stack, left
to right = deepest to top. Names after `|` are scratch: saved and
restored the same way, but zeroed. `EXIT` and `;` are wrapped so the
restore happens on every exit path including early `IF EXIT THEN`, and
both compile nothing at all in a definition that declares no locals.

The kernel, `cross.4` and `kernel.img` are **untouched** — `shadow.4`
uses only what the kernel already exposes. That was a deliberate
constraint given this file's own warning about `cross.4`'s hand-embedded
primitive-dispatch token numbers.

**In use since Iteration 39**: `relfsh` loads `shadow.4` ahead of
`shell.4`, and 71 of its 300 words are converted. The dynamic-scoping
property earned its keep immediately - words like `GLOB-MATCH` share their
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
`BASE`** — `tester.fr` leaves it at 16, which turned `shadow.4`'s own
`32 WORD` into `0x32 WORD`, delimiting names on the character `2`.

## Tracked numbers

Every figure below is recorded in `tests/BASELINE` and checked by
`tests/verify`, which fails on ANY change, better or worse - so each is
expected to move honestly, and only together with an `--update` in the
same commit. The size and speed tables further down are historical:
they were measured on the cell engine, which Iteration 243 retired, and
are kept for their reasoning. The current sizes are under "Where things
stand".

- `tests/run_tests.sh`: core-suite OK markers, the extension and I/O
  suites, and shell-suite assertions, on both cell widths.
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

- **Every engine ratio in this repository comes from a single build,
  and that is worth about ±5%.** The article repository measured the
  variation properly and it is dominated by per-BUILD bias, not by
  run-to-run noise: three consecutive runs of the SAME binaries agree
  to 1-2%, but rebuild the tree and a stage moves five or ten percent,
  because where the compiler places code is worth that much and is
  fixed for a given binary. Taking the minimum over more repetitions
  measures that bias more precisely instead of removing it; only
  building several ways and averaging removes it.

  The sting is in which stage moved most. The widest spread of any,
  **12.6%, belongs to the cell engine** - the baseline that divides
  every ratio in every table here. So a figure quoted from one build
  should be read as ±5% on most stages and ±13% on the baseline, and
  differences smaller than that were never resolved. `CV8.md` section
  2.2 already knew the mechanism (±4-5% from alignment alone, which is
  what `tools/lab/layout-variants.sh` builds for); what was missing
  was that the baseline is the worst offender.

Baseline at Iteration 41, and where it stands at Iteration 137:

| | engine | image (41) | image (127) | image (137) | total (137) |
|---|---|---|---|---|---|
| **i386 (4-byte cells)** | 17,808 | 72,528 | 134,500 | 109,600 | **127,408** |
| x86-64 (8-byte cells) | 22,744 | 131,784 | 251,104 | 206,024 | 228,768 |

Iteration 136 took 24,900 bytes off the i386 image by moving every
`CREATE ... ALLOT` buffer out of the dictionary. Iteration 137 took a
further 8,472 by rewriting the locals prologue and epilogue, and
**Iteration 149 reverted it**: it cost 42% of the loop benchmark, and
a clean baseline matters more before engine work than 8KB does. **The i386 total is below a same-architecture
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
| **shell.4** | **228,768** |
| yash | 653,680 (+libtinfo) |
| ksh93 | 1,432,848 |
| bash | 1,654,352 (+libtinfo) |

**shell.4 is 1.76x `dash` here**, between mksh and yash. That is the
honest headline: on the word size this machine actually runs, this is
not the smallest shell and is not close to `dash`.

*i386, where cell width suits the design:*

| implementation | total |
|---|---|
| **shell.4** | **127,408** |
| dash | 136,936 |
| posh | 163,308 |

**shell.4 is 0.93x `dash` here.** The comparators are built from
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
   is real. **The way to shrink it is the code encoding, not the
   content** - see `SOD16.md`. The 0.34x this line used to quote was a
   DECODE microbenchmark; the whole-image figure, measured on a booting
   token image in Iteration 185, is **0.40x**, and engine + image goes
   from 229,160 to **106,240** - smaller than `dash`. The same
   measurement cost 1.25x on interpretation speed; see
   `INNER-INTERPRETER.md`.
4. **Headerless words came up again in Iteration 158** and were
   rejected again, this time with a number: the 314 words that
   profitably become `M:` macros carry 4,456 bytes of headers, 26.9%
   of the image's header bytes. Still not worth losing `FIND`.
5. **Macro inlining (`M:`) is worth ~5-6%, and the naive form is a
   size REGRESSION.** Inlining every eligible word made the image
   bigger, 17,481 -> 18,763 cells; it only pays when selected by call
   count. `VM-RESEARCH.md` explains why the ceiling is low - this
   source is already factored by hand, so there is little left for
   either factoring or inlining to find.

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
  and is not bounded by `cv8.c`'s `MEMSIZE`. `pool.4`'s `BUFFER:`
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
- **A full fixed table must never fail silently.** When this was
  agreed, several did: `MAX-SHVARS` (32 shell variables - `SET-SHVAR`
  just did nothing when full), `MAX-FUNCS` (16),
  `MAX-POS-PARAM-DEPTH` (32), `MAX-ARGS` (64). Iteration 90 gave them
  diagnostics, so none is silent now; they are still fixed. Making them
  growable is the goal. The line length limit (`LINE-MAX`, 256) was the
  same kind of table: silent until Iteration 248, growable since 249 -
  pool.4's `BUF-ENSURE`, which RETIRES the old block rather than
  freeing it, because code holds addresses into these buffers; the
  top-level loop frees retired blocks between commands. That is the
  pattern for the tables still to convert.

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
to reimplement on `mmap`/`brk` - three primitives in `cv8.c` and
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

`relfsh` runs a prebuilt image rather than compiling `shadow.4` +
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
  temporary name then `mv`. The image IS committed, and `tests/verify`
  rebuilds it and checks the rebuild is byte-identical, from this
  directory and from a long path; the line that follows is from before
  that check existed —
  a committed binary derived from `shell.4` is a second source of truth
  that goes stale silently.

**Position-independence is now load-bearing, and was not before.** An
image reloads at a different address every run, so any absolute address
compiled into a word's body is stale the moment it boots. Two places
had them, both found by the turnkey image segfaulting: `shell.4`'s six
deferred-word xts (now stored as `START`-relative offsets via
`!XT`/`@XT`), and the slot addresses `shadow.4` compiles into every
locals-using word (now offsets, with the runtime words adding `START`
themselves). **Anything added in future that stores or compiles an
address must do the same.**

Compiling new code inside a reloaded image **works** as of Iteration
41. It did not in Iteration 40, because `shadow.4`'s compile-time
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
   for portability. `relfgcc.c`, `vm.asm` and `vm_tos.asm` are gone
   and are not coming back; `relf.c` followed them to `attic/` in
   Iteration 243, replaced by `cv8.c`.
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
of the current result (re-run in Iteration 248) is:

- **20 of 21** by `run.sh`'s own arithmetic, which scores every
  vendored file.
- **20 of 20** against the set mrsh itself actually runs.

The one failure is that file, and it is the alias divergence recorded
under "Where bash and POSIX disagree". The vendored file stays and
`run.sh` keeps scoring it — deleting a test to improve a number is
exactly the move this suite was adopted to prevent — but the
denominator should not be quoted without knowing this. (This
subsection said 19 of 21, with `command.sh` failing, from before
Iteration 125 until 248.)

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

Real gaps, each checked against the running shell in Iteration 248
(first verified in 122) rather than inherited from an older revision
of this file:

- **`NAME=value command args...`** — POSIX's temporary, per-command
  assignment prefix. Currently a failed command lookup, status 1.
  Ramey's temporary-scope design (see the bash-architecture section)
  is the shape to build.
- **Redirection does not apply to builtins - and the consequences are
  wider than that sentence suggests.** Iteration 146 found the same
  root behind `read -r l < file` reading nothing, `while read ...;
  done < file` producing nothing - or, since the redirection is
  dropped, reading the shell's own stdin, which with a terminal or an
  open pipe means waiting for ever - and `{ ...; } > f 2>&1` writing
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
  `a::b:` must split into three fields; it yields two. Whitespace
  splitting is correct - Iteration 146 implied otherwise and 147
  corrected it.
- **Arithmetic division truncates the wrong way for negatives.**
  `$((-7 / 2))` is -4 here and -3 everywhere else; ISO C, which XCU
  2.6.4 defers to, truncates toward zero.
- **A reserved word cannot be a `for` list value.**
  `for x in do done; do ...; done` iterates over nothing.
- **Quoted and escaped patterns in `case` do not match.**
  `case 'a*b' in 'a*b')` selects no arm, and neither does `*)`.
- **An empty `case` word does not match an empty pattern.**
- **`set -e`**, per above.
- ~~**A script line over `LINE-MAX` (256) has its TAIL EXECUTED as a
  separate command.**~~ Made an error in Iteration 248, and **lifted in
  249**: lines of any length run, through scripts, stdin, `-c`,
  continued lines, open quotes, bodies, here-documents and `read`
  (`tests/shell/run-long-line`, and `tests/diff/cases/long-lines.sh`
  against bash). A line past 1 MB (`LINE-HARD-MAX`) is reported and
  discarded, so a binary file costs a message, not the memory.
- **Fixed limits that a long line now reaches first**, each REPORTED
  rather than silent unless noted: a variable's value, 255 characters
  ("value too long", status 2, the value empty - until 249 it kept the
  PREVIOUS value); 64 words on a line (`MAX-ARGS`, about thirty
  parallel arrays - the next stage); a here-document body, 8 KB
  (`HEREDOC-MAX`, excess dropped SILENTLY); positional parameters and
  alias values, 256. And one that is not this shell's: Linux refuses a
  single exec argument over 128 KB, which a long `echo` meets because
  `echo` here is `/bin/echo`.
- **`shell.4`'s older diagnostics go to STDOUT.** "cd: no such
  directory", "shell: syntax error: ...", "alias: too many aliases"
  all still use `."`. Iteration 153 moved the prompt and 154 added
  `ERR-TYPE`/`ERR-CSTR`/`ERR-NL` on fd 2, but the older messages were
  left alone - a separate change with its own test churn.
- **Nine dead variables in `shell.4`**, one occurrence each:
  `IN-ASSIGN-CONTEXT?`, `PW-FID`, `WT-PID`, `FDL-I`, `WHILE-BODY-I`,
  `WHILE-BODY-CUR`, `CASE-PATLAST-LEN`, `FD-ADDR`, `FD-LEN`.
- **The duplication pass is two blocks deep.** Iteration 152 found the
  largest duplicated block had drifted and was causing a real
  status-127 bug. A full pass over 7,091 lines has not been done and
  is likely to find more of the same class - it should be its own
  iteration, not folded into a fix.
- **`until` is recognised and then silently ignored.** It is in the
  reserved-word list (`shell.4` line 3155, so it is correctly refused
  as a command name) but the compound-command dispatcher tests only
  `while` and `for`, so `until ...; do ...; done` runs **nothing** and
  exits **127**, not 0 as this entry claimed until Iteration 151 -
  the body never executes and `until` falls through to the "command
  not found" path. A POSIX compound command that is a near-silent
  no-op, unrecorded here until Iteration 144 audited for it.
- ~~**A multi-line `{ ... }` after `&&` returns 127**~~ — fixed in
  Iteration 152. The cause was one duplicated block, `shell.4` 4248
  against 6936, where only the second copy carried the `ARGC @ 1 =`
  multi-line arm; the two are now a single `DISPATCH-GROUP`. Covered
  by `tests/diff/cases/multiline-group-segment.sh`.
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

## What to do next, in order (as of Iteration 248)

The first two items were ordered around the `relf.c` retirement:
kernel semantics before it, while the cell engine was the simplest
thing to debug against, and engine work after it, so it would be done
once. Both are done; the rest keep their order.

1. ~~**`+LOOP` boundary conformance.**~~ **Done** (Iteration 243), and
   smaller than planned: no biased index was needed. The overflow test
   the bias enables can be computed from the unbiased `index - limit`,
   so only `(+LOOP)` changed - `(DO)`, `I`, `J`, `UNLOOP` and `LEAVE` did
   not, and `I` stayed cheap. `tests/coreplus-loop.fth` carries the
   standard's four `+LOOP` sections.

2. ~~**Adapt `cv8.4` for cross-compilation**, then retire `relf.c`.~~
   **Done** (Iteration 243). `cv8.4` was merged into `kernel.4` and
   `cross.4` emits CV8, so the class of load-time obstacles the entry
   below describes never had to be solved one by one: nothing is
   translated any more. The measurement that made it safe - the
   specialised opcodes - is under "Where things stand".

3. **`GUARD`.** A measured 5-6% win, disabled since Iteration 206 for a
   `tests/diff` regression that predates most of the engine work since.
   Worth re-measuring, and cheaper with one engine than two. The
   guard-page code was specialised out of `cv8.c`; it is in
   `attic/tools/lab/vm-lab.c`.

4. ~~**`KEY?` plus a termios/fcntl primitive.**~~ **`KEY?` done**
   (Iteration 246), on `POLL` rather than `fcntl`: poll(2) waits
   without changing the descriptor's flags, which every process sharing
   it would see. The non-blocking `KEY` hazard is fixed with it.
   **Still open: terminal raw mode**, without which `KEY?` on a
   terminal sees nothing until Enter. It wants its own primitive that
   hides `struct termios`, whose layout differs by platform - say
   `RAW-MODE ( fd flag --- ior )` - escaped, so it costs no opcode.

5. **The rest of the growable-buffer work** (Iteration 249 did the
   line buffers). Stage 3: the `MAX-ARGS` arrays grow with the number
   of words, the largest audit - `ARGV` and about thirty copies of it.
   Stage 4: variable values, here-documents, positional parameters and
   alias values. Each by the same rule: grow before any pointer into
   the table is taken, retire rather than free, and diagnose whatever
   stays fixed.

6. **A cooperative multitasker**, the other thing `POLL` was chosen
   for: `PAUSE` switches tasks, and when every task is waiting on a
   descriptor the scheduler makes one poll(2) over all of them. Two
   things to settle first. The engine checks both stacks against the
   MAIN stacks' limits, so task stacks must lie inside the VM's memory
   or the limits need a way to change. And poll(2) sees descriptors,
   not child processes, so waiting on a background job needs a
   SIGCHLD self-pipe or pidfd_open. `FD-POLL` is already reentrant -
   it keeps its struct on the data stack - for this reason.

A SMALLER THING, left so it is not re-proposed:

- **`forth.img` is NOT worth building.** SOD32 builds one - kernel.img
  plus extend.4th, saved - and cross-compiles from it. Measured here:
  cross-compile 19ms total, bare boot 2ms, boot + extend.4 3ms. So
  extend.4 costs about 1ms of 19, and a `forth.img` buys 5% in
  exchange for another tracked binary to keep in sync and scrub. Left
  here so it is not re-proposed.

## Known shortcuts to revisit

Deliberate compromises that work today and are wrong in general. Each
is implemented, tested and *incorrect in a way that will not show up
locally* — which is exactly why they need to be written down rather
than remembered.

- **The Locals word set is not provided.** This is CONFORMANT: Locals
  is optional and CORE stands at 133 of 133 without it. Recorded
  because the system HAS a facility that looks like it and is not -
  `SHADOW{ ... }`, which is dynamic scoping over existing VARIABLEs
  (see `shadow.4`). Iteration 236 renamed it off the standard's `{: :}`
  spelling so that standard code fails loudly rather than computing
  address arithmetic. If real locals are ever wanted, `{: :}` is free
  and the two can coexist.

  The COST of converting `SHADOW{` itself to value semantics, measured
  at Iteration 235 so it does not have to be guessed at again: 71 words
  in `shell.4` declare them, 192 distinct names, appearing as **784
  `NAME @`**, **279 `NAME !`**, and **456 other occurrences** that each
  need reading rather than rewriting. Plus the dictionary machinery -
  standard locals are new names bound by splicing temporary headers,
  which `shadow.4` deliberately avoids. That is a decision about
  `shell.4`, not a fix to `shadow.4`.

- **`relf.c` was retired in Iteration 243**, and what it took is in
  `PROGRESS.md`. Two things from the plan that was here are worth
  keeping. The dead ends on getting `cv8.4` into the cross-compiled
  kernel (Iterations 239-242) were real, and they stopped mattering
  once `cross.4` emitted CV8 itself rather than cells for a translator.
  And the plan missed the obstacle that mattered most: the shell image
  was only fast because the translator added opcodes the compiler did
  not emit, so retiring the translator without teaching the compiler
  would have cost 2.4x.

- ~~**`KEY` exits the shell if descriptor 0 is non-blocking and
  idle.**~~ **Fixed in Iteration 246.** A failed read now waits once,
  with `FD-WAIT`, for descriptor 0 to become readable and tries again;
  a second failure exits. That handles `EAGAIN` without knowing its
  value (11 on Linux, 35 on the BSDs), and a real error - stdin a
  directory, a terminal gone - leaves the descriptor readable, so the
  retry fails at once and `KEY` exits instead of spinning.
  `tests/io/run` covers it with a non-blocking pipe; the engine before
  246 fails that case. One corner is accepted: if another process
  sharing descriptor 0 takes the byte between the poll and the retry,
  `KEY` exits. Reading a shared terminal concurrently is a race in any
  case.

## Integrated from the article repository

`kt97679/forth-vm-evolution` is the article's working code: this
system's engine and Forth sources, taken sideways to build a ladder of
encodings and measure them honestly. While the article was being
written the shared parts improved, and those improvements are now
here. What follows is what changed and what it is worth, because the
largest of them **invalidates comparisons made before it**.

### The hashed word list, and why it resets the numbers

RelF was derived from SOD32 and dropped SOD32's hashed `FORTH-WORDLIST`
- a thread count and 32 chain heads - for a single cell. Nothing
replaced it. Every dictionary lookup was therefore a linear scan of the
whole dictionary, twice, because the default search order holds
`FORTH-WORDLIST` in two slots. It is worst for NUMBERS, which are never
found and so cost a complete traversal before the system gives up and
converts them.

Measured here with `tools/find-depth.sh`, entries examined on 4000
lines of interpreted arithmetic:

    single chain     8,052,327
    32 threads         288,009      28.0x fewer

and in time, interleaved min of 5:

    parse workload   8-byte   400ms -> 84ms    4.76x
    CORE corpus      8-byte    58ms -> 19ms    3.05x
    shell image build         482ms -> 86ms    5.60x

**Read that against the encoding work.** CV8 and the whole ladder
behind it - SOD16, CPT16, folding, the specialisations, TOS caching,
every one of iterations 156-208 - are worth between 0.72x and 0.81x.
One omission, restored, is worth more than all of it. That is not an
argument against the encoding work; it is an argument about where this
project was looking. Every benchmark it used compared the system
against ITSELF, and a defect present from the first commit is
invisible to that. The article repository found it by comparing
against the ANCESTOR.

Two consequences for anything quoted from before this landed:

- Any whole-system timing taken before the hash was measuring a
  system spending ~81% of its operations in dictionary search. Ratios
  between encodings are still meaningful - the constant was identical
  for all of them - but absolute figures and any comparison against
  SOD32 or dash are not.
- The same applies to the syscall constant fixed alongside it. `KEY`,
  `EMIT` and `READ-LINE` did one syscall per CHARACTER; the CORE
  corpus made 32,357 against SOD32's 59. Being identical for every
  stage, it compressed every ratio toward 1.0 - so pre-existing
  encoding comparisons are, if anything, understated.

### What else came across

- **Buffered terminal and file I/O** in `relf.c` and `vm-lab.c`.
  `NOINLINE_IO` on those paths is load-bearing: upstream measured an
  85% loss from letting a cold I/O path with loops and static state
  inline into the dispatch function and wreck register allocation.
  Same class as Iteration 189a, from the other side.
- **`tools/layout.py`** (was `sod16-layout.py`), reworked for 32
  threads: it reads the thread count out of the image rather than
  assuming one, rebuilds every chain, and walks them all back to prove
  the union is exactly the dictionary.
- **`LIT64` in `tools/sod16.py`** - literals were masked to 32 bits
  and silently truncated above that, the same fault CV8 had until
  Iteration 194.
- **A far `DOES>` call in `cv8.4`.** The two-byte near form has a
  14-bit field of SCALED units: 131 KB of reach at scale 3, but only
  16 KB at scale 0, so a `DOES>` word above 16 KB had its target
  truncated and jumped into the data stack.
- **`cv8b.4` and `cpt16.4`**, new overlays - byte-granular dictionary
  headers, and CPT16.

### What this tree had to solve that upstream did not

Upstream builds kernel images from committed seed images and emits
them with `layout.py`. This tree cross-compiles in place and saves
images with `SAVE-SYSTEM`, so two things had no upstream equivalent:

- **The bootstrap.** `extend.4`'s new `WORDLIST` reads
  `FORTH-WORDLIST @` as a thread count, but on the pre-hash host that
  cell is a POINTER - it allotted a garbage-sized block and
  segfaulted. Done as a two-stage transition: old `extend.4` with new
  `cross.4`/`kernel.4` to build the first hashed image, then new
  `extend.4` to reach the fixed point. Both stages came out
  byte-identical to upstream's seed images, which is the evidence the
  port is faithful and not merely working. The transition is spent;
  every host from here is hashed.
- **`SAVE-SYSTEM`.** It unrelocated ONE cell of `FORTH-WORDLIST` where
  there are now 33, so a saved image booted with 32 stale absolute
  addresses and segfaulted in `FIND`. `SS-UNRELOCATE-WORDLIST` in
  `save-system.4` fixes it, and `cv8-save.4` writes the header's new
  count-then-heads form. **Two traps there are silent**: cell 0 is the
  thread COUNT and must not be touched, and an empty thread is 0 and
  must STAY 0, or `COLD`'s own `?DUP` guard relocates it into a
  pointer to the image base.

Anything that walks the dictionary must now walk 32 chains and sort by
address: a single chain reaches about a thirty-second of the words and
does not visit them in address order, which matters because
`tools/dict-report.4` and `tools/dict-dump-addr.4` both derive a body's
extent from its address neighbour.

### Known, and not introduced by any of this

Calling `SAVE-SYSTEM` from a RUNNING shell writes a correct image and
then segfaults: `RESET-BUFFERS` releases pool buffers the shell goes on
using. `relfsh` always follows `SAVE-SYSTEM` with `BYE`, so nothing
hits it in normal use. Confirmed against the pre-hash tree rather than
assumed - it does the same thing, the same way.

## The shell queue (written at Iteration 149, audited at 248)

The engine queue is "What to do next" above; this one is the shell's.
It was written at the Iteration 149 freeze and not audited again until
Iteration 248, when every item below was checked against the running
shell and `tests/posix` (25 passed, 21 failed, 2 inconclusive). Item 4
is finished and kept for its reasoning; the rest are still open.

Run `tests/verify` first - if it does not say VERIFIED, fix that
before anything else, because every number here is relative to it.

### Settled, so nobody re-proposes them

- **Headerless words: rejected.** 16,400 bytes, and extending the
  shell in Forth needs `FIND`, which needs headers. A decision, not a
  deferral (Iteration 131).
- **Register VMs: closed.** Measured elsewhere at 26% larger bytecode
  for 46% fewer executed instructions - the wrong direction for goal 3
  (Shi et al., TACO 2008; `VM-RESEARCH.md`).
- **Replicating the dispatch site: measured, gains nothing here.** GCC
  had merged 68 `NEXT()` sites into 5; forcing 66 apart changed the
  benchmark by nothing on this hardware. That also devalues a
  tail-call interpreter, whose reported gain rests on the same
  mechanism (Iteration 140).
- **Byte-granular *offsets*: still rejected.** Byte-granular
  *indices* are not - see token threading below. The objection was
  always about the width an offset needs.
- **Variable-length branch offsets: rejected**, twice. They need
  assembler relaxation.
- **Iteration 137's locals rewrite: reverted** in 149. If it is ever
  re-applied, `SS-SCRUB` must scrub `LE-A`, `LE-N`, `LE-ARGS`, `LE-P`,
  `LE-Q` and `LX-N`, or the image stops reproducing.

### The queue

1. **The four absent POSIX items**: `until`, `eval`, `for w; do`, and
   the `NAME=value command` prefix - all four still absent at 248, each
   with its own `tests/posix` case. Small, independent, no
   architectural risk, and they would take `tests/posix` from 25/21 to
   about 29/17. Do these first for a reason beyond their size: **the corpus
   has only ever gone down, so it is unproven as a driver of work.**
2. **`PARSE-EXPAND-PLAN.md` Stage 2** - cache tokenized body lines.
   Two justifications, and the second was found later: it is the loop
   benchmark's fix *and* it removes the whole same-line fault class
   (Iterations 143, 144). Four POSIX failures go with it.
3. **Redirection's undo list** (Ramey's design, in the bash-
   architecture section below). Three more POSIX failures, including
   `while read ...; done < file` - the commonest file-reading idiom in
   shell scripting.
4. ~~**Engine: SOD16, on branch `token16`.**~~ **Done, superseded, and
   retired.** SOD16 won the Iteration 156-167 comparison, CV8 replaced
   it at 189, and Iteration 218 retired it along with every other
   encoding - the ladder had answered its question. `sod16.4`,
   `cpt16.4` and `sod16.c` are in `attic/`; `SOD16.md`,
   `TOKEN-THREADING.md`, `ENCODING-COMPARISON.md` and
   `INNER-INTERPRETER.md` are the historical record and should be read
   as such. `CV8.md` describes what actually runs.

   Two conclusions from that comparison were corrected by measuring
   the real thing, and both are worth carrying forward because they
   are about METHOD: an xt is an ADDRESS, not a word number, so
   `EXECUTE` is `>R ;` in Forth and was never a primitive; and the
   encoding won partly on a decode microbenchmark that measured the
   part SOD16 makes cheaper while omitting the dependent load it makes
   dearer.

5. ~~**Superinstructions**~~ - **closed by measurement (Iteration
   157).** Every packed encoding costs 21-68% in dispatch to buy
   density a plain 16-bit token gets more of anyway. That includes
   SOD32's own 5-bit x 6 format, the best of them, at 1.21x on x86-64
   and 1.68x on i386. `DENSITY-PLAN.md` option B should not be
   re-proposed without new evidence.
6. **A `FILL` primitive.** `FILL` is a per-byte threaded loop, which
   is most of what boot-time buffer zeroing costs (Iteration 136). A
   memset one-liner that helps everything.
7. **Phase 3, the Forth-hosted assembler.** Goal 1's last piece, never
   started in 149 iterations, and the prerequisite for phase 4.

The rest of the POSIX backlog - pattern matching, the tokenizer, and
the remaining parameter and expansion semantics - is grouped by root
cause in `PROGRESS.md`'s Iteration 147 entry. Six faults, not
twenty-one.

### Not yet audited at all

Whole XCU sections have no cases: signals and traps (2.11), the shell
execution environment (2.12), here-documents beyond the simplest form,
`getopts`, `exec`, `set -o`, `$0`, and what a subshell inherits. An
audit round *would* find more; Iteration 147's judgement was that
fixing what is known beats finding more of it, not that the well is
dry.

### Method that must survive contact with all of the above

- **Measure before proposing** - and measure the *harness* too. Three
  separate wrong conclusions this project reached came from a broken
  oracle, not broken code: the mrsh reference shell (124), the token
  decoder (135, 141), and two benchmarks that flattered the same
  answer (140, 141).
- **Compare against something that is not this system.** Every
  benchmark here compared RelF against RelF, which cannot see a defect
  that was present at the first commit. A 4x regression in the outer
  interpreter survived 200 iterations of careful measurement for
  exactly that reason, and was found in an afternoon by running SOD32
  on the same input. A ratio against your own previous build tells you
  whether you improved; it never tells you whether you are slow.
- **Check why a test passes**, not just that it does. `ulimit.sh`
  passed for two years' worth of iterations while `ulimit` did not
  exist (122).
- **One feature per test case.** A case exercising two attributes the
  fault to whichever one you were thinking about (147).
- **A fix and `tests/verify --update` go in the same commit**, so
  `tests/BASELINE` always records what the tree does.

## Next architectural work: `PARSE-EXPAND-PLAN.md`

**Stage 1 is done** (Iterations 108, 112, 113, 114). Expansion writes
into its own buffer, so the in-place-growth bug class no longer
exists; word boundaries come from `NORMALIZE-OPERATORS`, the pass that
already knew them; and `EXPAND-WORDS` runs when a command runs rather
than when its line is read, which took the mrsh suite to 19 of 21.
Stages 3 and 4 are done as well - nested `$(...)` in Iteration 105,
and the limitation notes retired in 115.

**Stage 2 is the only one left**: caching tokenized body lines, where
the pure-loop gap measured in `tests/bench` is addressed - and, found
later, the whole same-line fault class with it. Read that file before
starting; each stage must leave the full suite green and be committed
separately.

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
