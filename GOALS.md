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

## How this file is kept

This file is the PRESENT: what the project is for, what is open now,
what was decided and why, and what has been tried and rejected. How it
is built is `README.md`; how it is checked, `CHECKING.md`. The past is
`PROGRESS.md`, one entry per iteration, append-only. When a section here
stops describing the present - a snapshot of where things stood, a
"next" list that is done - it is deleted, not kept: the history is
`PROGRESS.md` and git. (Such sections used to move to
`attic/docs/GOALS-HISTORY.md`; the attic went at Iteration 489, and 493
removed the last of them from here, two-thirds of the file.) How the log
and the register below are used, and why, is
`prompts/12-progress-log.md`.

## Open now

The one current queue. Worked in order of severity
(`prompts/13-severity-first.md`): crashes and hangs, then wrong results
ordinary scripts hit, then edge cases and wording.

1. **No known crashes.** The fuzzer's last findings - `printf` and
   `kill` with no arguments, and the job table past 64 jobs - were fixed
   in Iteration 426. Run `tools/crashfuzz.py` after any change to the
   parser, the expander or the job code.
1c. **The order of a simple command's expansions**: stages 1 and 2 done
   (480, 482) - both yash cases pass. For a special builtin, a function
   and an external command this shell still expands assignments before
   redirections, as bash does and dash does not; the measurement and the
   costs are in EXPANSION-ORDER.md. Worth doing only if something asks.

   (Resolved and removed in 469: line continuation in yash's torture
   cases - 456, 457, 460; `export NAME` with no value - 469; `${#a}`
   split by IFS - 450. PROGRESS.md has each.)
5. **`a=b exec 1>&1` exports `a`**, as bash does and dash does not
   (424). Behaves like bash; low priority.
5b. **`return` outside a function, in a loop, repeats its error forever**
   (found by the fuzzer, 426). POSIX leaves it unspecified; bash reports
   and carries on, as this shell does, and dash leaves the script. Only
   worth changing if dash's reading is adopted as policy.
   (5c, a script descriptor in the shell's spare range overwritten, is
   fixed in 486 with the DUP-FROM primitive: F_DUPFD_CLOEXEC.)

6. **Prompt escapes**: `\D{format}` and `\j` came in 476. `\v` and
   `\V` stay as written on purpose - they are bash's version - and so
   does `\l`, which would need a readlink primitive in the engine.
6b. **`$-` shows no `i` in an interactive shell**, nor `s` when the
   script is standard input; dash shows `si` for `echo 'echo $-' | dash
   -i` (found at 493). `-i` itself works. Small; a script testing
   `case $- in *i*)` to detect interactivity is what it would break.
7. **Speed on busybox's many_ifs**: 12 s against dash's 7.5 (423),
   profiled in 451 and FLAT - `(LOOP)` 5.6%, EXPAND-WORDS 4.8%, nothing
   else above 2.6%. No cheap win; it is the interpreter, which is
   PERFORMANCE.md's standing question. Do not re-profile this workload
   expecting a hot spot. But see the next paragraph.
   **In-process work has drifted about 1.8x slower** since Iteration 268:
   an empty loop iteration is 61 µs where it was 34.5, on a machine
   where dash still measures 1.4 (DASH.md §1, found at 492). Bisected at
   495 (PERFORMANCE.md): steps between 268 and 360, flat since; the
   largest, 341's scan of literal words for pattern marks, is cheaper
   now, and there is no single cause left to remove - that much is the
   price of those iterations' correctness, as with many_ifs.
   **Two levers were never tried** (found at 496, in PERFORMANCE.md's
   list from 292): `I`, `(LOOP)`, `(+LOOP)` and `(?DO)` are colon
   definitions, 7.6% of an empty loop iteration's dispatches, and could
   be engine opcodes like the tiny words of CV8.md 6.4; the tree's field
   reads `X@`/`XF@`, 4.1%, could be primitives. Price each first
   (`prompts/10-price-before-refactor.md`): a direct opcode moves the
   map by one (CV8.md 2.2).
8. **`intr-at-prompt` loses a race under full-suite load** (406, again
   in 423): passes alone, fails about one verify in five on one CPU.
   (8b, the intermittent `wait-job-status-345.sh`, is resolved in 470:
   the varying shell was BASH, which drops a finished job and answers
   127 when it reaps before `wait %%` runs. The case's named jobs sleep
   a moment now; the finished-job reading is asserted on its own.)

## What comes next: the user's list (recorded at Iteration 499)

The user's notes for the project's next phase, in their order, each
with what is already known and what is still to be settled. Nothing
here is started; an item's open questions are answered before its
work begins.

1. **Folded `primitive;EXIT` opcodes behind the escape** - measure what
   it costs. Today they are 23 one-byte opcodes at `0x28`-`0x3E`, plus
   `LIT8;EXIT`, `ADDI;EXIT` and `EQI;EXIT` (CV8.md 2.2). Behind `ESC`
   each would cost one byte more and one more indirect jump - `L_esc`
   reads a selector and dispatches again - and folding is frequent:
   `EXIT` was 17% of all dispatches, 80% of them after a primitive
   (CV8.md 9). The measurement: image size, dispatches and time on
   `tests/bench-vm` and the shell suite, with both layouts. It is what
   item 2 would need.
2. **A two-bit selector**: `00` an opcode (64 of them), `01` a call
   with a 14-bit offset (6 bits and one byte), `10` 22 bits, `11` 30
   bits - a 1 GB code space, where today's three-byte call reaches 4 MB
   and one-byte opcodes number 128. 95 of those 128 are in use
   (CV8.md 2.2), so about 31 would move behind `ESC` - item 1 decides
   which. Slot operands (`VAR@`, `VAR!`, the locals) reach ±4 MB with
   the same trick and would want the same widening. An alternative to
   weigh: keep 128 opcodes and spend the free `0x7F` on a rare
   five-byte far call. Open: what the 1 GB is for (see the questions
   below).
3. **Profile the shell: what affects performance most.** A study across
   workloads rather than the one empty loop: `tests/bench-vm`, the
   corpora, real scripts; by subsystem - expansion, parsing, variable
   lookup, the tree walk, builtins, process creation. Starting points:
   `tools/profile.py` (working again since 495), PERFORMANCE.md, and the
   two untried levers in item 7 of "Open now" above.
4. **An alternative shell language** with better performance and
   shorter code, keeping the shell's features. Open: whether it replaces
   POSIX sh as the language users write, or is an internal form the
   shell compiles sh into (see the questions below).
   `prompts/02-escape-recall.md` applies before any candidate is named.
5. **An assembly engine on raw syscalls: no libc** - GOALS' first end
   state, deferred since phase 5 traded it for portability. `cv8.c`
   uses libc for `malloc` (`ALLOCATE`), stdio-free I/O wrappers, `fork`,
   `execve`, signals, `fcntl`, `localtime_r` and the terminal. Open:
   which architecture first.
6. **The assembly engine, self-hosted**: a Forth-hosted assembler
   (`CODE ... END-CODE`) that emits the engine itself, as `cross.4`
   emits the kernel - the second end state. Implies writing an
   executable (an ELF file) from Forth.
7. **`relfsh` not a shell script.** Today it is a POSIX `sh` wrapper:
   it costs about 2 ms of each start (DASH.md 1), and where `/bin/sh` is
   bash it loses `PS1` from the environment (CHECKING.md). The engine
   could recognise that it is the shell - by its name, or by an image
   it carries.
8. **`relfsh` as a single binary** - does it make sense? The shell image
   appended to the engine, found through `/proc/self/exe` or `argv[0]`,
   would make one file, drop the wrapper and its 2 ms, and remove the
   `PS1` problem. Costs: one binary per cell width, and the wrapper's
   rebuild-when-stale logic moves wholly into `make`. With item 5 the
   loader would be assembly too.
9. **A thorough audit of all the sources**: dead code (`tools/dead-words.py`
   says none, but it sees only unreachable words), duplicated logic
   (FORTH-STYLE.md 11), and performance on the way.
10. **A smaller image**: no buffers in the image - 142 are already
    `BUFFER:`s, allocated on first use, and 7 fixed ones remain, some of
    them tables that need their contents; no full-cell offsets where a
    narrower field would do - `BUFFER:` descriptors, deferred xts and
    the header's 32 thread heads are cells; and branches (see the
    questions below).
11. **A startup file.** This shell reads none today: not `$ENV` for an
    interactive shell and not `~/.profile` for a login shell, both
    checked at 499 - dash reads `.profile` as a login shell, and POSIX
    specifies both. The likely shape is dash's: a login shell (`-l`, or
    `argv[0]` beginning with `-`) reads `/etc/profile` and
    `$HOME/.profile`, an interactive shell then the file `$ENV` names.
12. **Examples of the `forth` builtin**: a network server,
    `PROMPT_COMMAND`, or others. A server needs socket primitives the
    engine does not have (`socket`, `bind`, `listen`, `accept`) -
    escaped, so they move nothing (CV8.md 2.2); a prompt hook needs a
    point in the prompt loop that calls a Forth word.

**Decisions** (the user's answers, recorded at 500):

- **Item 2 - measure, don't adopt.** 16 MB is plenty for this project
  and many others, but a large project could hit 4 MB easily, and this
  Forth's speed is not yet what JIT or AOT could make it. So: an
  experiment estimating the performance loss of two-bit tagging with
  six-bit opcodes. Method, as agreed: count each opcode's executions on
  the shell's workloads and its occurrences in the images (the
  profiler's `PROF` hook); keep the 64 most executed as one-byte
  opcodes; measure time with a variant engine that sends the other
  ~31 through a second dispatch, as `ESC` would - real code, no format
  change - and size from the static counts, a byte each. Calls under
  4 MB keep their size in either scheme, so those two numbers are the
  price of the 1 GB. A synthetic loop of nothing but moved opcodes
  bounds the worst case. **Done at 501** (CV8.md 13): real workloads
  0-0.7% slower, the worst case 18%, the image 255 bytes larger - and
  with every operation ranked together, fewer second dispatches than
  today. The 1 GB costs nothing measurable; whether to take it is now a
  format decision only.
- **Item 4 - analysis first, then a language of our own.** First: which
  shell features cause the most parsing and implementation complexity;
  if dropping some would halve the shell's source, that is a finding in
  itself. Then a shell language designed from scratch - "completely
  different from what is used so far", convenient and expressive, more
  testable, simpler to implement, better formalized - the user asked
  for imagination here, not a variation on sh, csh or any other known
  pattern. It is a design with examples before it is code. **Analysis done at
  502** (SHELL-LANGUAGE.md, Part 1): no set of features halves the
  source - the largest is the parser at 12.6% - and the trouble is
  concentrated where POSIX re-reads text: quoting, field splitting,
  redirections, command substitution. **Designed at 503**: Rill
  (SHELL-LANGUAGE.md, Part 2) - text never re-read, commands as values
  until used, the world as an interface a test can replace, failure that
  stops, and a grammar context-free at the token level. A design; its
  "about half the source" is a guess to be measured by building it.
- **Item 10 - no two-pass compiler**: the complexity is not worth the
  gain. The task is to find what else still stores a full cell where a
  compact offset would do.
- **Items 5 and 6 - x86-64 first.** The debugging loop has to run where
  the code is written; on x86-64 it runs here, without relaying every
  attempt through the user's machines.
- **Item 12 - yes**: add whatever primitives the examples need, sockets
  included (escaped, so nothing moves), and put the examples in
  `forth-shell-examples/`.

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

## Deliberate divergences

From busybox's ash:

- **`echo` does not process escape sequences** (466). dash turns `\t`
  into a tab in `echo 'a\tb'`; bash prints it as written and takes
  `-e` to do otherwise. This shell is bash's. Several busybox tests
  expect dash's answer, ash-heredoc/heredoc_backslash1's last line
  among them; they stay failing.
- **A here-document line that joins to exactly the delimiter** (464):
  busybox ends the document on it, dash does not, and this follows
  dash (ash-heredoc/heredoc_bkslash_newline2).
- **`a=b exec 1>&1` exports a**, which is bash's behaviour and was
  chosen deliberately (ash-vars/var_leaks).

### Where bash and POSIX disagree, and this shell follows POSIX

Deliberate divergences from the differential oracle. Each was checked
against a second reference (`dash`) before being recorded, because
"bash does X" and "X is correct" are not the same claim.

- **Aliases are not expanded by bash in non-interactive shells.** POSIX
  says alias substitution applies; this shell applies it, and so does
  `dash`. Cost two mrsh tests while bash was the reference shell;
  costs none since Iteration 124 moved the harness to `sh`, upstream's
  own default. bash is the outlier here, which is why the reference
  shell mattered more than it looked.
- **OPTARG is unset after an option without an argument** (Iteration
  432) - here dash is the outlier: POSIX says unset, bash unsets it, and
  yash's suite tests for it (getopts-p.tst:66), while dash leaves it
  empty. The one place in this list where the second reference, not the
  first, disagrees with POSIX.
- **An arithmetic error ends a non-interactive shell** (Iteration 427).
  `echo $((1/0)); echo after`: bash reports it and carries on; POSIX
  makes an expansion error fatal in a non-interactive shell (XCU 2.8.1),
  dash exits with status 2, and so does this shell. Iteration 257 had
  chosen bash's behaviour while fixing a crash - its entry says so and
  names dash's - and 427 reversed it on new evidence: the POSIX table,
  this list's own rule, and a fuzzer case where carrying on led into an
  infinite loop. The checks moved from the bash-differential cases to
  `tests/shell/run-special-error`.
- **Tilde after `=` in a non-assignment word.** `echo other=~/y`:
  bash expands the tilde, dash does not, and neither do we. POSIX
  applies tilde-after-`=` to assignment *words*; an argument to `echo`
  is not one. bash is being permissive with any `name=value`-shaped
  word. (Iteration 98.)

## Tools for finding the next bug

- `tools/crashfuzz.py` (421) mutates existing scripts and reports only
  crashes and hangs.
- `tools/difffuzz.py` (471) generates well-formed scripts and reports a
  difference from dash AND bash where they agree with each other. Run it
  after any change to expansion, splitting, quoting or the parser:
  `python3 tools/difffuzz.py --seconds 300`. Its first hour found three
  bugs behind 365 scripts; a clean run of a few minutes is the bar.

### Crashes: how they are looked for here (Iteration 421)

The method is `prompts/13-severity-first.md`. This project's tools for
it: `tools/crashfuzz.py [--seconds N]` (mutated snippets, both widths,
crash and hang only, shrunk); `make busybox` and `make yash` print
CRASH / HANG / wrong per failure, `YASH_KEEP=DIR` keeping yash's result
files; and gdb with `tools/image-where.py` for a Forth-level backtrace
(`FORTH-STYLE.md` section 13). Reproducers live in `tests/crashers/`.

## Tried and rejected - do not retry without new evidence

One line each: what, the number that decided it, and where the evidence
is. Add to this list whenever an attempt is reverted or priced out; read
it before starting anything it could cover.

- **Headerless words** - 16,400 bytes saved, but extending the shell in
  Forth needs `FIND`, which needs headers. A decision (131).
- **A register VM** - 26% larger bytecode for 46% fewer instructions
  elsewhere, the wrong trade for size (research, Iteration 189; the survey
  is in git: `git show 9513df0:attic/docs/VM-RESEARCH.md`).
- **Replicating the dispatch site** - GCC merged 68 sites into 5;
  forcing 66 apart changed the benchmark by nothing here (140). Devalues
  a tail-call interpreter for the same reason.
- **Byte-granular offsets; variable-length branch offsets** - the width
  an offset needs; relaxation. Rejected twice (GOALS history, 131-149).
- **Iteration 137's locals rewrite** - reverted in 149. If re-applied,
  `SS-SCRUB` must scrub `LE-A LE-N LE-ARGS LE-P LE-Q LX-N` or images
  stop reproducing.
- **Compiling `$((...))` once** - the whole arithmetic evaluator is 10% of
  the arithmetic benchmark and compiling removes only the reading half
  (284).
- **A variable-lookup cache** - built: 4.9% fewer dispatches, 0.75% less
  time; reverted (373). The profile that suggests it never changes.
- **Refactoring per-word expansion bookkeeping** - priced at ~1% by doing
  the work twice, not done (374; the method is
  `prompts/10-price-before-refactor.md`).
- **A field-level quoting flag for an empty quoted field** - changed
  nothing, reverted; the case is still open (359).
- **Splitting a braced word's literal text as a region, alone** - fixes
  field order but breaks two quoted-empty cases (430). Done in 431 with
  the two changes it needed - see PROGRESS.md - so this line records why
  the first attempt alone was not enough.

## Method, and the evidence for it

**Prompt overrides** (as `prompts/USAGE.md` asks a project to record
them): `04-expert-review` and `05-reader-review` wait for the article
about the Forth shell (End state); until it is written, nothing is
published from this repository. `01-problem-framing`,
`02-escape-recall` and `06-handling-review` apply as written: `01` to
any benchmark, `02` to any design choice, and `06` to review feedback of
any kind, the user's included.

Each rule is stated once, in `prompts/`; this project's instances stay
here as the evidence for it.

- Measure before proposing, and measure the HARNESS -
  `prompts/03-audit-tooling.md`. Here: three wrong conclusions came
  from a broken oracle - the mrsh reference shell (124), the token
  decoder (135, 141), two flattering benchmarks (140, 141).
- Compare against something that is not this system -
  `prompts/02-escape-recall.md`. Here: a 4x regression in the outer
  interpreter survived 200 iterations of RelF-against-RelF measurement
  and was found in an afternoon by running SOD32 on the same input.
- Check why a test passes, not just that it does -
  `prompts/03-audit-tooling.md`. Here: `ulimit.sh` passed while `ulimit`
  did not exist (122).
- One feature per test case. Here: a case exercising two attributes
  the fault to whichever one you were thinking about (147).
- A fix and `tests/verify --update` go in the same commit, and a changed
  line is explained before it is recorded -
  `prompts/09-baseline-discipline.md`.

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


- **Then, an article about the Forth shell**, written when the project
  is judged complete (the user's plan, recorded at 497). Its material is
  already here: `PROGRESS.md`, the log of every attempt with its
  deciding number; the measurements in `CV8.md`, `DASH.md` and
  `PERFORMANCE.md`; and the corpus results. Keep them honest with that
  reader in mind - an article can only be as true as its sources.
  Prompts `04` and `05` apply to it. (The earlier article, about the
  VM's evolution, lives in its own repository; `ARTICLE.md`, its working
  notes, left this one at 489.)
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
   and are not coming back; `relf.c` was retired in Iteration 243,
   replaced by `cv8.c`.
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

## Known limits of the 4-byte-cell build (Iteration 397)

A limit, a file size or an arithmetic value that does not fit a CELL
cannot be represented in the 4-byte build. `ulimit -l` on a machine with
3.4 GB of lockable memory reads back wrapped, where dash - which keeps
limits in a 64-bit `rlim_t` whatever the pointer width - reads them
exactly. The fix, if it is ever wanted, is for the engine to return such
values as a double cell rather than one; the test suite compares only
where the value fits, and says so.

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

- **Every document but `PROGRESS.md` can go stale.** `PROGRESS.md`
  only makes claims about the past and cannot rot; every other document
  makes claims about the present tense, and they rot silently and in
  the worst direction — describing
  finished work as unfinished, in the file a new session is told to
  trust first. Iteration 122 found five such claims, some eighty
  iterations old, each of which could have sent a session to rebuild
  something that already worked, and the cleanup of 489-493 found more:
  the engine reference listed the specialised opcodes one position low,
  and the comparison with dash listed as missing five features present
  for a hundred iterations. **When an iteration finishes an item
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
- **Mine the bash maintainers' experience.** Chet Ramey's chapter on
  bash in *The Architecture of Open Source Applications*
  (https://aosabook.org/en/v1/bash.html) has already named three bugs this
  project actually had, before they were found here. When a design
  question comes up, check what bash does and why, rather than
  deriving it from scratch — and record the finding.
- **`prompts/` is a library that outlives this project.** The user
  extends it and uses it in other projects, so nothing in it is removed
  here - not even a prompt this project does not cite (recorded at 497,
  after 496 audited it). When a failure here teaches something a prompt
  would have prevented, add to the library, as `prompts/USAGE.md`'s
  "Growing the library" says.
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
  `token16` were to go. They did not, upstream: the Iteration 243
  handover still carried `origin/cv8` (as the default branch) and
  `origin/token16`. Checked at Iteration 258: both, and the old
  `origin/master`, are ancestors of `master`, so `master`
  fast-forwards over them and both branches can be deleted with
  nothing lost. The bundles carry `master` only. If a branch appears
  again, merge it back or delete it; do not let it run for seventy
  iterations.

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

## External references (potentially reusable ideas, not yet mined)

**Read in Iteration 280: pForth** (https://github.com/philburk/pforth),
reached by way of gitlab.com/mschwartz/mykesforth and its sibling
nixforth ("Phil Burk's pForth reimagined"), neither of which can be read
from here - GitLab renders its pages in the browser, and the container's
proxy does not allow gitlab.com. pForth is the closest published cousin
of this engine: portable C, a token dispatch, a saved dictionary image.
What it says about our choices, and the one thing worth taking:

- **A headerless image** - `ffSaveForth(file, entry, NameSize, CodeSize)`
  writes the names as their own chunk, and `NameSize` of 0 leaves them
  out entirely. Measured here: 21% of `kernel-shell.img` is headers
  (17.5 KB of 80.8 KB, 13.2 KB of it names). **Settled: not wanted.**
  It would cost the `forth` builtin and any runtime lookup, and that
  builtin - a Forth prompt inside the shell, on the shell's own
  dictionary - is a main reason this shell exists. 17 KB is not worth
  it. Left here so it is not re-proposed.
- **Code-relative tokens** (`LOCAL_CODEREL_TO_ABS`): pForth stores
  secondaries as offsets from the code base, as Iterations 258-259 made
  this engine do, and reaches absolute addresses the same way. Nothing
  to take; it does confirm the choice was not exotic.
- **A chunked image file** (P4DI/P4NM/P4CD: info, names, code). Ours is
  one block with a fixpoint check. Chunks would only buy the optional
  name space above.
- Not applicable: pForth refuses an image whose cell size differs from
  the running engine's; this project cross-builds a separate image per
  width, which is the same answer.

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
