# GOALS.md history - sections that stopped describing the present

Moved out of `GOALS.md` in Iteration 425, content unchanged, when that
file was split into the present (`GOALS.md`) and the past (this file,
and `PROGRESS.md`). Their open items were carried into GOALS.md's single
"Open now" list; nothing here is a to-do any more.

## The widening cross-compile - FIXED (Iteration 415)

An 8-byte image cross-compiled on a 32-bit host is byte-identical to
the committed one now, and so are the other three host/target
combinations. The cause, and why the notes that stood here were wrong,
is in PROGRESS.md under Iteration 415. tests/run_tests.sh checks the
widening direction on every run that has an i386 engine, and
tests/verify records it as `image:widening`.

## Where things stand (Iteration 368)

The shell is the work now; the engine has been stable since Iteration
243. Current counts, all green: differential 86 cases, matrix 420,
POSIX 46, mrsh 21, interactive 22 with one listed divergence, every
file in `tests/shell`, no dead words, both cell widths. busybox's ash
suite, run from outside the tree by `tools/busybox-suite.sh`, is at 203
of 357 against dash's 211 - near parity on a suite written for another
shell.

The standing worklist is no longer in this file. It is
`tests/from-others/CATALOGUE.md`: behaviours learned from other
projects' test suites, written in this project's own words, each either
implemented and covered by a case here or marked open with what is in
the way. `DOCS.md` says what every document is for.

Performance: three iterations of profiling (365-367) took a
system-shaped script from 25.1M dispatches to 21.6M, 14% fewer, and
about 11% off the wall clock. `PERFORMANCE.md` has the method and the
current profile; `tools/profile.py` reproduces it.

## Where things stood (Iteration 253)

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

    64-bit   kernel.img     8,882    kernel-shell.img     77,384
    32-bit   kernel32.img   8,370    kernel32-shell.img   71,452

**Eighty-two primitives**: 35 direct, with one-byte opcodes, and 47
OS/libc ones behind ESC + a selector, declared after `ESCAPED` in
`kernel.4`. The synthetic opcodes are numbered from the direct count,
so an escaped primitive costs no opcode (Iteration 247); 32 opcodes
are free. `CV8-REFERENCE.md` 3.2 has the map.

**Descriptor I/O is three primitives**: `READ` and `WRITE` (Iteration
245), one read(2) or write(2) each, returning a count or a negative
errno, and `POLL` (246), one poll(2); `RAW-MODE` (254) sets a terminal
to a byte at a time. `FD-POLL` wraps it for one
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

## Next (Iteration 412)

1. DONE (413): `[ "" -eq 0 ]` is an error, and the guide agrees 58/58.
2. DONE (413): the rest of the guide classified - nothing fixable here.
3. DONE (417): `\t \T \@ \A \d`, `\!` and `\#`, and `\$` from the real
   effective uid. Still missing: `\D{format}`, `\j`, `\l`, `\v`, `\V`.

## The interactive editor's two missing features (Iteration 407)

Raised by a user of the shell, and the honest answer is that they are
the most visible gaps left: everything else in the standing queue is
conformance detail, and these are what a person notices in the first
minute at the prompt.

**Tab completion - filenames DONE (411), command names and a sorted
listing DONE (414), escaped characters in the word DONE (418).** Still
open: a word inside quotes (`"my n<TAB>`). Functions and aliases
complete as commands since Iteration 419. The original note follows.
Nothing was bound to TAB. What exists to build on:
`OPEN-DIR` and `READ-DIR` are engine primitives (kernel.4), pathname
expansion already matches a pattern against a directory's names
(`GLOB-FIELDS` in shell.4), and the editor has the line buffer, the
cursor and a redraw. The work: find the word under the cursor, decide
whether it is in command position (complete from PATH and the builtin
table) or an operand (complete as a path), collect the matches, insert
the longest common prefix, and on a second TAB print the candidates and
redraw the prompt. Quoting matters: a completed name containing a space
must come back quoted, or the completion breaks the line it completed.

**History search - DONE (Iteration 409).** `^R` with readline's
prompt and rules; see edit.4 and tests/interactive/search-probe.py.
The original note follows. `HIST-BUF` holds 32 lines and the arrows
walk them, so the storage is there. What is missing is incremental reverse search:
^R enters a search mode with its own prompt (`(reverse-i-search)`),
each keystroke extends the pattern and shows the most recent match,
^R again steps to the next older one, RETURN accepts the line, ^G or
^C restores what was being typed. The editor's redraw already handles a
line that is shorter than the previous one, which is the fiddly part.

Both are in `edit.4`, both are testable through the pty harness in
`tests/interactive`, and neither touches the shell's semantics - which
is why they can be done in any order relative to the conformance work.
Order suggested: history search first (smaller, self-contained, no
quoting questions), then completion.

## What to do next, in order (as of Iteration 368)

1. **The open catalogue entries**, in
   `tests/from-others/CATALOGUE.md`: each names a behaviour, what this
   shell does instead, and what was measured about it.
2. **The per-word bookkeeping**, `EXPAND-WORDS` at 6.7% and `ARGV-ADD`
   at 3.7% of a realistic script. Five parallel byte arrays that could
   be one record, seven flag clears that could be one fill; a
   restructuring rather than a substitution, with `tools/profile.py` in
   the loop.
3. **The remaining busybox gap**, eight tests behind dash. Several are
   deliberate divergences already recorded; the rest are listed by
   `tools/busybox-suite.sh`.
4. The older queue below, which is still accurate about the engine.

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

3. ~~**`GUARD`.**~~ **On by default since Iteration 253.** One
   unreadable page below each stack replaces the compare on every push:
   3-6% faster at 64-bit (every workload's interval excludes 1.0),
   neutral at 32. The `tests/diff` regression that kept it off since 206
   was a real bug the guard exposed - `PASSWD-HOME` dropped one cell too
   many from its caller's stack on every `~user` - and it is fixed. The
   guard above the empty data stack makes an underflow of two cells or
   more a fault; `-DGUARD=0` brings back the compares for a target
   without an MMU.

4. ~~**`KEY?` plus a termios/fcntl primitive.**~~ **`KEY?` done**
   (Iteration 246), on `POLL` rather than `fcntl`: poll(2) waits
   without changing the descriptor's flags, which every process sharing
   it would see. The non-blocking `KEY` hazard is fixed with it.
   **Terminal raw mode done too** (Iteration 254): `RAW-MODE ( fd flag
   --- ior )`, escaped, hides `struct termios`. A byte at a time without
   echo, Ctrl-C still working; the engine puts the terminal back on
   every way out, and only in the process that changed it.
   `tests/io/pty.c` runs the tests on a pseudo-terminal.

4a. **Image encoding** (Iteration 258's audit, `tools/image-audit.py`).
   ~~Variable slots relative to the instruction~~ **done in Iteration
   259**: 3,843 of 4,380 slots are short where 2,171 were, 1.6 KB off
   the 64-bit shell image. Still open: a pass that shrinks a finished
   definition's forward branches to `BRANCH8` would save about 1.36 KB
   (97% fit). Calls are best left base-relative: pc-relative is worse,
   and allowing either saves only 3%.

4b. **`I`, `(LOOP)` and `(+LOOP)` as engine opcodes.** Colon
   definitions today, and 8% of the shell's loop benchmark dispatches
   (Iteration 266's profile); every Forth `DO` loop pays them. A format
   change (direct opcodes), so with a version bump.

5. **The rest of the growable-buffer work.** Iteration 249 did the
   line buffers, 250 the word arrays and positional parameters, 251
   expansion output, command substitution, `for` lists and
   here-documents, 252 variable values and the variable table. What is
   left is the alias table and name lengths, all reported rather than
   silent; worth doing only if a real script meets them. Each by the same rule: grow before any
   pointer into the table is taken, retire rather than free, and
   diagnose whatever stays fixed.

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

