# PROGRESS.md — RelF self-hosting project log

Append-only. Newest entries at the bottom. This log exists so future work
(including future Claude sessions, which have no memory of prior ones)
doesn't silently retry a path already found to be wrong.

**For project context, priorities, and phase plan, read `GOALS.md`
first** — that's the stable reference. This file is only the log of what
was actually done, in order, and shouldn't repeat what's already stated
there.

The **Index** below is how to use this file: find the entry, read that
entry, don't read the log. It is long because it is 119 entries, not
because it is padded — and the oldest entries are the ones the other
documents cite most, so nothing here gets archived or trimmed by age.

## Index

Every entry, in order. Titles are the entries' own. `mrsh a->b`
marks the entries that moved the goal-8 acceptance count; **bold**
marks an entry cited by `GOALS.md`, `FORTH-STYLE.md`,
`PARSE-EXPAND-PLAN.md` or `README.md`, which is the closest thing to a
marker for "still load-bearing". Find an entry by searching for
`Iteration N:`.

### 1-4 — Engine: phases 1, 2, 5, 6

- 1 — scaffolding
- 2 — no-libc x86-64 engine, 8-byte cells
- 3 — phase 5 (libc, native endianness, computed-goto, ARM64)
- 4 — phase 6, i386/32-bit cell width (parameterized, verified working)

### 5-13 — Shell v0.1-v0.8 (phase 7)

- **5** — POSIX shell, v0.1 (process-control primitives + shell.4)
- 6 — shell `-c` mode + a real test suite for shell.4
- 7 — pipes and redirection
- 8 — quoting and escaping
- 9 — $VAR expansion
- 10 — if/then/else/fi
- **11** — while/do/done
- 12 — unset
- 13 — $(...) command substitution

### 14-16 — mrsh suite adopted; phase A

- **14** — adopt mrsh's test suite as goal 8, establish baseline
- **15** — phase A: crash-hardening
- **16** — phase A: script-file invocation (phase A done)

### 17-30 — Phases B and C: semantics and control structures

- **17** — phase B: shell-local variable assignment
- **18** — phase B: ';' (multiple commands per line)
- **19** — phase B: '&&'/'||' (conditional chaining)
- **20** — phase B: command grouping ('( )' and '{ ; }')
- **21** — fix if/while reading from the wrong input source in script-file mode
- **22** — phase B: if/then/else/fi nesting (phase B done)
- **23** — phase C: for/in/do/done loops
- **24** — operators no longer require surrounding whitespace
- **25** — same-line 'if COND; then BODY; fi' support
- **26** — fix a real, pre-existing token-corruption bug in $VAR/$(...) expansion
- **27** — phase C: case/in/esac (with glob-pattern matching)
- **28** — phase C: shell functions (`name() { ... }`)
- **29** — phase C: `return`
- **30** — phase C: `break`/`continue`

### 31-37 — Phases D and F: expansions and the first builtins

- **31** — phase D: positional parameters (`$1`-`$9`, `$#`, `$@`/`$*`, `set`)
- **32** — phase D: parameter-expansion modifiers (default/assign/alternate value, length)
- **33** — phase D: `${VAR%word}`/`${VAR%%word}`/ `${VAR#word}`/`${VAR##word}` (prefix/suffix removal), plus a significant kernel-behavior discovery
- **34** — phase D: tilde expansion
- **35** — phase D: arithmetic expansion (`$((...))`)
- **36** — phase D: `IFS`-based field splitting (Phase D complete)
- **37** — phase F: `:`, `test`/`[` (string, numeric, limited file-existence tests)

### 38-44 — Locals, the prebuilt image, and the arena

- **38** — `locals.4` - named, per-invocation locals
- **39** — converting `shell.4` to locals, and two real deduplications
- **40** — prebuilt shell image - ~128x faster startup, and the acceptance criterion unblocked
- **41** — pool allocator, memory outside the image, and reproducible images
- **42** — replay as an input source - nested constructs inside loop and function bodies
- 43 — per-invocation body storage - loops nest
- **44** — offset-based growable arena - two hardcoded limits gone

### 45-80 — Climbing the mrsh count

- **45** — `#` comments and same-line `; do` - mrsh 2 -> 4 passed  `mrsh 2->4`
- 46 — multi-stage pipelines, `!` negation, and a real pre-existing expansion bug
- **47** — `elif`, and closing a hazard open since Iteration 28
- **48** — `(` and `)` as self-delimiting operators
- **49** — groups as ordinary commands - mrsh 4 -> 6 passed  `mrsh 4->6`
- **50** — duplication audit - two merges, two latent bugs
- 51 — `shift`, `readonly`, `command -v`
- 52 — table-driven DISPATCH, and the `forth` builtin
- 53 — bitwise/shift operators and arithmetic assignment — mrsh 6 -> 7 passed  `mrsh 6->7`
- 54 — the `read` builtin
- 55 — file-descriptor redirection — mrsh 7 -> 8 passed  `mrsh 7->8`
- 56 — here-documents
- 57 — builtins as pipeline stages
- 58 — redirection on pipeline stages
- 59 — `alias` and `unalias`
- 60 — unterminated quotes are a syntax error — mrsh 8 -> 9  `mrsh 8->9`
- 61 — `getopts`, and `set --`
- 62 — subshell function bodies — mrsh 9 -> 10 passed  `mrsh 9->10`
- 63 — nested function definitions
- 64 — multi-line groups — mrsh 10 -> 11 passed  `mrsh 10->11`
- 65 — `return` inside a loop — mrsh 11 -> 12 passed  `mrsh 11->12`
- 66 — field splitting of command substitution, and the assignment exception
- 67 — `$IFS` actually controls field splitting — mrsh 12 -> 13  `mrsh 12->13`
- 68 — `readonly -p` — mrsh 13 -> 14 passed  `mrsh 13->14`
- 69 — `command -v` for reserved words and aliases, and LF-only output
- 70 — line continuation
- **71** — quoting inside `$(...)`
- 72 — braceless compound function bodies, and functions inside `$(...)` — mrsh 14 -> 15 passed  `mrsh 14->15`
- **73** — backquote command substitution
- 74 — background jobs — mrsh 15 -> 16 passed  `mrsh 15->16`
- 75 — same-line `case` arms
- 76 — compound commands as pipeline stages — attempted and reverted, with the design established
- **77** — `DEFER` / `IS`
- 78 — compound pipeline stages, second attempt — reverted
- **79** — third attempt — the isolated diagnostic paid off, and found the *next* obstacle
- 80 — compound pipeline stages — mrsh 16 -> 17 passed  `mrsh 16->17`

### 81-107 — The differential suite, and audits it made possible

- 81 — the alias conformance case is the same conflict
- 82 — auditing the 17 passes for hollowness
- 83 — a differential test suite, and two bugs it found immediately
- 84 — *(number not used)*
- 85 — performance baseline
- **86** — an unquoted empty expansion yields no field
- 87 — a written plan for parse-then-expand
- **88** — a segfault found by the plan's own first step
- 89 — auditing every `DO` — one more hang
- 90 — auditing the fixed tables — a silent failure, a crash, and two limits that pre-empted a diagnosis
- 91 — the recorded and-or reentrancy bug, demonstrated and fixed
- 92 — an operator after `fi`, and the status an untaken `if` leaves
- 93 — multi-line quoted strings
- 94 — is startup cost the reason the loop is slow? No — but the wrapper is 43% of startup
- 95 — positional parameters inside `${...}`, and what `word.sh` actually needs
- 96 — `~user` expansion
- 97 — recording that `~user` via `/etc/passwd` is a shortcut
- **98** — tilde in assignments
- 99 — `$*` lost characters after it
- 100 — `"$@"` as separate fields
- 101 — `done`/`esac` suffixes — diagnosed precisely, not implemented
- 102 — a trailing backslash run, counted by parity
- 103 — the fourth in-place-growth bug, where Iteration 99 predicted it
- 104 — the word in `${VAR:-word}` is word text
- **105** — `$(...)` gets the whole language, by deleting the parser that gave it a subset  `mrsh 17->18`
- 106 — the `done`/`esac` suffix, as specified in 101
- 107 — an unterminated compound command hangs

### 108-121 — Parse-then-expand (PARSE-EXPAND-PLAN.md Stage 1)

- **108** — expansion stops writing over its own input
- **109** — deleting the word rather than auditing its callers
- **110** — one word for normalize-then-tokenize, and the caller that was missing it
- 111 — tokenize the normalized line where it already is
- 112 — word boundaries recorded by the pass that finds them
- 113 — expansion becomes a word you can call later
- **114** — a word is expanded when its command runs  `mrsh 18->19`
- **115** — retire the limitation notes Stage 1 made false  *(written retrospectively in 122)*
- **116** — measuring what Stage 1 cost
- 117 — a loop written entirely on one line
- 118 — a function defined entirely on one line
- **119** — normalizing each line once instead of twice
- **120** — `~user` through NSS instead of /etc/passwd
- **121** — what a fresh machine needs, written down
- 122 — the documents that can rot
- 123 — correcting Iteration 122, from upstream's own harness
- 124 — the reference shell was the ceiling
- **125** — `ulimit`, and goal 8 is met  `mrsh 19->20`
- 126 — a conformance harness scored by consensus, not by bash
- 127 — seven reference shells, and the 32-bit half finally run
- **128** — the size axis of the comparison, as a script
- **129** — where the image bytes actually go, and why Forth being "compact" does not make this the smallest shell
- **130** — what the compiled code is actually made of (`DENSITY-PLAN.md`)
- **131** — correcting the density numbers; longer superinstructions are worth 1.3%
- **132** — two tag bits, and where `LIT` goes
- **133** — how the branch merge would work, and why not to do it
- **134** — keep the dispatch loop, put the payload above the index
- **135** — a review of `shell.4` for size: no duplicated logic, idioms instead
- **136** — every buffer out of the image (i386 total below `dash`)
- **137** — one `LENTER`/`LEXIT` instead of three cells per local (+42% loop, revertable alone)
- **138** — the size comparison was mixing word sizes
- **139** — reading the field: `VM-RESEARCH.md`
- **140** — token threading measured: 3.26x/6.51x smaller, no dispatch cost
- **141** — the prototype: size confirmed, speed 1.14-1.28x and 140's 0.98 was an artifact
- **142** — the token-threading design written out (`TOKEN-THREADING.md`)
- **143** — `ONE-LINE-LOOP?` is a symptom: two conformance bugs, one silent
- **144** — the audit: `until` silently does nothing, plus three more same-line faults
- **145** — why `(`/`)` are not reserved words; `$( (list) )` read as arithmetic
- **146** — a systematic POSIX corpus: 47 cases, eleven new gaps
- **147** — triage: the 21 failures are six faults; stop auditing, start fixing
- **148** — the freeze: reproducible build, `tests/verify`, `tests/BASELINE`
- **149** — revert 137; `GOALS.md` carries the whole plan
- **150** — the shell image did not build from a path over ~36 characters
- **151** — neither stack was bounded; overflow corrupted the dictionary
- **152** — one duplicated block had drifted; `true && {` left status 127
- **153** — the interactive prompt was on stdout, corrupting every piped script
- **154** — two silent failures given diagnostics; a third found (`LINE-MAX`)
- **155** — both images regenerated and checked; `tests/bench` made a measurement
- **156** — encoding comparison against SOD32; the freeze; the data-address finding
- **157** — the speed half: packing costs 20-66%; the threading figure was wrong
- **158** — variable-length tokens, and what the word table costs as it grows
- **159** — token width sweep; the uniform 16-bit token; the derived-table idea
- **160** — the 16-bit token prototype on real code, and a census bug that mattered
- **161** — `ENCODING-COMPARISON.md` regenerated from the fixed census
- **162** — branch `token16`: a translator that proves itself by round trip
- **163** — the dispatch core runs real translated words; the table is derived

### Not tied to an iteration

- 2026-09-01 — Design discussion: phase 5 direction, and a rejected byte-opcode idea
- Assessment: reusing mrsh's test suite

---

## 2026-08-31 — Iteration 1: scaffolding

### Context

This repository continues work that started as an unrelated investigation
(comparing SOD32 and RelF VM designs for a "busybox on Forth" project) in
a prior chat session, not committed to git at the time. The reasoning
behind choosing RelF as this project's basis, and a load-bearing fact
about RelF's addressing model, are now in `GOALS.md` rather than here —
put there because they're stable context, not iteration history.

### Bugs found and fixed

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
needs a genuine 32-bit *process*.** See `GOALS.md`'s note on RelF's
real-pointer addressing model for why. Must build with `gcc -m32`.
**Do not attempt to "fix" this by widening `UNS32` to 8 bytes on a
64-bit build** — that changes the cell width and breaks the existing
`kernel.img`, which was compiled assuming 4-byte cells. The 32-bit build
is correct as-is for the current kernel image; a real 64-bit *cell*
version is a distinct, deliberate future project (phase 2 in `GOALS.md`),
not a side effect of chasing this bug.

**Bug 3 — engine hangs (does not exit) on EOF from stdin when no `BYE`
is reached.** Confirmed by running the bundled `tester.fr` suite: without
an appended `BYE`, the process runs all tests correctly (1841 `OK`,
zero errors) but then hangs indefinitely rather than exiting — `timeout`
killed it (exit 124) rather than it exiting on its own. With `BYE`
appended after the test file, exit code 0, same 1841 `OK`s, zero errors.
**Not fixed yet** — noted because it's directly relevant to the
syscall-based rewrite (phase 2): a raw `read()` returning 0 at EOF
should be treated as "exit cleanly," and currently isn't. Test runner
works around this for now by always appending `BYE`.

### What this iteration did

- Applied Bug 1's fix to `relf.c` (`UNS32`/`INT32` → `unsigned int`/`int`).
- Confirmed the *existing, bundled* `tester.fr` — a working copy of John
  Hayes's 1993 CORE word test suite, already adapted to RelF's `{ -> }`
  test syntax — passes cleanly end to end (1841 `OK`, 0 errors) once
  both bugs above are worked around. This is a significantly better
  starting position than expected: a comprehensive, already-adapted
  regression suite already existed in the repo and was simply never
  being run in any automated way.
- Added `tests/run_tests.sh`, a minimal test runner that builds `relf`,
  runs `tester.fr` (with `BYE` appended per Bug 3's workaround) plus
  `tests/*.fth` through it, and fails loudly on any `ERROR`/non-zero
  exit/non-"OK" output. Verified end to end: full pass, 1892 `OK`
  markers, 0 errors.
- Added `tests/core-extra.fth`: a handful of small, directly-applicable
  tests adapted from `forth2012-test-suite`'s `src/core.fr`
  (arithmetic/stack/boolean ops), written in RelF's own `{ -> }`
  convention rather than porting the `T{ -> }T` framework wholesale (see
  `GOALS.md`'s test suite strategy). Kept the suite's copyright notice
  attached per its terms ("MAY BE DISTRIBUTED FREELY AS LONG AS THIS
  COPYRIGHT NOTICE REMAINS").
- Note (not a bug, not fixed, not worth fixing): `gcc -m32` on `relf.c`
  produces many `-Wimplicit-int`/`-Wimplicit-function-declaration`
  warnings — expected from ~20-year-old pre-C99 K&R-style C compiled by
  a modern compiler default-strict about implicit declarations. Harmless,
  does not affect correctness (all tests pass), not addressed here since
  this file's C form is being replaced/refactored per `GOALS.md`'s
  phase 2, not incrementally modernized.
- Added `GOALS.md` (this iteration, after the above): split the original
  single `PROGRESS.md` into stable context (`GOALS.md`) and pure
  iteration log (`PROGRESS.md`, this file), so a new session can read
  one short, rarely-changing file instead of a growing log to get
  oriented.

### What this iteration deliberately did NOT do

Per the owner's explicit phase-1 scope ("scaffolding + test runner +
process log first, minimal engine changes") — these are next-iteration
work, not forgotten:

- Did not remove libc / move to raw syscalls yet.
- Did not touch `vm.asm`/`vm_tos.asm`/`relfgcc.c` at all.
- Did not restructure/replace old files in place yet (planned per
  `GOALS.md`, but not started).
- Did not port the modern `T{ -> }T` forth2012-test-suite harness itself,
  only borrowed a few test values in RelF's existing convention.
- Did not investigate or fix Bug 3 (EOF hang) — logged, not fixed.
- Did not touch `relfgcc.c` (the labels-as-values GCC variant) — it has
  its own, different 64-bit trap (computed-goto target addresses stored
  in a `UNS32`-sized slot truncate on a 64-bit build for the same
  fundamental reason as Bug 2, but the fix isn't just `-m32`-compatible
  in the same simple way — was observed in prior exploratory work to
  need extra header-inclusion fixes even to compile at `-m32`). Low
  priority — `vm_tos.asm` is the actual performance-relevant target per
  `GOALS.md`'s "why RelF," `relfgcc.c` was never the fast path.

### Workflow notes (process, not project content — logged so future
iterations don't repeat the mistake)

- `git bundle create <file>.bundle master` alone is **not** enough for a
  plain `git pull <file>.bundle` to work on the receiving end — `git
  pull` without an explicit refspec looks for `HEAD` in the bundle, and
  a bundle created with only `master` named doesn't include a `HEAD`
  ref. Always bundle with `git bundle create <file>.bundle HEAD master`
  (or equivalent) so `git pull <file>.bundle` works standalone, without
  requiring `git pull <file>.bundle master`. Hit this exact issue on the
  very first handoff of this project — fixed by regenerating the bundle
  with both refs.

## 2026-09-01 — Iteration 2: no-libc x86-64 engine, 8-byte cells

### Summary

Phase 2 from `GOALS.md`, done in full: `relf.c` is now a genuine x86-64
process, built `-nostdlib -static`, talking to the OS via hand-written
raw syscall wrappers (`read`/`write`/`open`/`close`/`lseek`/`unlink`/
`fork`/`execve`/`wait4`/`exit_group`), no libc, no crt0, custom `_start`.
Cells are 8 bytes, matching the process's own pointer width (see
`GOALS.md`'s load-bearing fact). `vm.asm`, `vm_tos.asm`, and `relfgcc.c`
are removed, per the phase-2 plan ("replacing in place, not preserved
alongside") — `relfgcc.c`'s removal wasn't explicitly called out in
`GOALS.md`'s phase-2 line but follows the same reasoning (it was already
noted in iteration 1 as low-priority/never-the-fast-path, and keeping a
second stdio-based engine around contradicts "leaner successor, not a
fork-with-extras"). Bug 3 (EOF hang) is fixed as part of this, since it's
a syscall-level concern (`read()` returning 0 now exits cleanly instead
of spinning). Full test suite passes: 1892 `OK` markers, exact parity
with the pre-iteration 32-bit baseline. `fib.4` gives the correct
fib(34) = 9227465.

Most of the actual effort went into the cross-compiler side, not the
engine itself: moving from 4-byte to 8-byte target cells meant
`cross.4`/`kernel.4` needed real changes, not just a recompile, and this
surfaced several bugs latent in the original 4-byte-cell design (below).

### The 8-byte-cell target-image migration

`cross.4` and `kernel.4` hardcode cell width in many places
(`CELL+`/`CELLS`/`CELL-`/`ALIGNED`/`DEPTH`/`J`/name-comparison masks/
etc.) — all updated from 4-byte to 8-byte equivalents (e.g. `CELLS`'s
`2 LSHIFT` → `3 LSHIFT`, alignment masks `3`/`-4` → `7`/`-8`). This part
was mechanical. Two things were not:

**Bootstrapping needs a host with cells at least as wide as the new
target.** `cross.4`'s `@-T`/`!-T` (fetch/store a target cell) and
`NUMBER?`'s literal parsing do *host*-cell arithmetic on values that end
up in 8-byte target cells. The natural approach — bootstrap the new
8-byte image using the *existing* engine (still 4-byte cells at that
point) — runs into this directly: a 4-byte host cell cannot even
represent an 8-byte value, let alone do wide-shift arithmetic on it
safely (shifting a 32-bit C value by ≥32 is undefined behaviour, and
empirically did produce wrong results, not just theoretically). Tried
gforth (which has native 64-bit cells, matching the new target, and
which the old README claimed works as a cross-compile host) as a
workaround — it does not work with the current `cross.4`/`extend.4`/
`kernel.4`: they rely on RelF-kernel-specific search-order words
(`CONTEXT`, `#ORDER`, `CURRENT`) that gforth doesn't define, and this
isn't a small compatibility gap (confirmed by trying: `extend.4` fails
immediately on `#ORDER`). `GOALS.md`'s non-goals updated to record this.

The actual fix: rewrote `@-T`/`!-T` to only ever do host shifts ≤24 bits
(genuinely safe on a 32-bit host), and to rely on **sign-extension**
rather than truncation or wide-shift reconstruction — `!-T` fills the
high 4 (of 8) target bytes with `$00` or `$FF` based on the host value's
own sign bit, and `@-T` round-trips by reading back only the low 4 target
bytes. This correctly handles both small positive literals (all the
addresses/offsets cross.4 generates) and small negative ones (`-1`, used
as `TRUE` and in several other spots in `kernel.4`) without needing
double-precision host arithmetic anywhere. Two `kernel.4` literals that
didn't fit this pattern at all — masks with the top 3 bits of a 64-bit
word cleared, used in `2/` and in name-length comparison — were rewritten
to be *computed at target runtime* via small, host-safe literals (e.g.
`1 63 LSHIFT` instead of embedding `$8000000000000000` as a cross-compile
-time literal), sidestepping the host-width problem entirely rather than
solving it more generally.

Also found, while auditing `cross.4` for this: three places (`>BODY-T`,
`IF`, `ELSE`, `WHILE`) that used the *host's* `CELLS` where they meant
the *target's* `CELLS-T` — invisible before now because host cell width
(4 bytes, the old engine) accidentally equalled target cell width (also
4 bytes), so the wrong word happened to produce the right number. Fixed
to use `CELLS-T` explicitly; this also makes `cross.4` correctly
self-hosting once the new 8-byte engine exists (host = target = 8 bytes
again, but now because both are actually the same word, not by
coincidence).

**Primitive-dispatch tokens are hand-embedded in a few places and don't
auto-update.** `PRIMITIVE`'s numbering stride is tied to
`sizeof(host function pointer)` (4 on the old 32-bit engine, 8 on the
new x86-64 one) — this is inherent to how dispatch works (token value =
array-index-in-bytes + 1, see `README.md`), not something that could
have been left at 4. Updating the stride itself was one line. What
wasn't obvious: `cross.4` and `kernel.4` each hand-embed raw numeric
values for `LIT`/`EXIT`/`BRANCH`/`0BRANCH`/`R>`'s tokens in several
defining words (`;`, `CONSTANT`, `LITERAL`/`LITERAL-T`, `IF`/`ELSE`/
`THEN`/`WHILE`/`REPEAT`/`UNTIL`, `(;CODE)`) — these aren't derived from
`PRIMITIVE`'s own counter, so they silently kept their old-stride values
(`5`/`9`/`13`/`17`/`69`) after the stride changed. This didn't error
during cross-compilation (all the arithmetic is valid host arithmetic
either way) — it produced a `kernel.img` that built cleanly and then
segfaulted the *new* engine immediately, in primitive dispatch itself,
because e.g. `EXIT`'s compiled-in token was still `5` where the new
numbering needs `9`. Found via `gdb`, tracing the segfault back to an
invalid computed-call target. Fixed by hand-updating each occurrence to
the new stride's values (`EXIT`=9, `LIT`=17, `BRANCH`=25, `0BRANCH`=33,
`R>`=137 — `R>` is the 18th primitive, so `1 + 17*8`). Worth remembering
for any *future* primitive-set change: adding, removing, or reordering
entries in `kernel.4`'s `PRIMITIVE` list shifts every token after it,
and these hand-embedded values would all need re-deriving again.

### A pre-existing bug found and fixed along the way (unrelated to cell width)

**File-based `INCLUDED` mishandled CRLF line endings.** The old engine's
`vmreadline()` only stripped a trailing `\n`, not `\r` — harmless for
piped stdin (which goes through the kernel's own `ACCEPT`, which treats
both `\r` and `\n` as terminators) but broken for file-based `INCLUDED`
reading this repo's CRLF-checked-out `.4` files: the last token on every
line would get a stray `\r` appended, e.g. `CR` read as `CR\r`, an
"Undefined word" mismatch against the real 2-character `CR` in the
dictionary. Confirmed this is genuinely pre-existing (reproduces on an
unmodified `kernel.img`/`cross.4`, nothing to do with this iteration's
edits) and is why the documented bootstrap procedure (`S" cross.4"
INCLUDED`) didn't work out of the box on this checkout. Worked around
for the bootstrap itself by LF-normalizing temp copies of `extend.4`/
`cross.4`/`kernel.4`; fixed properly in the new engine's `vmreadline`
(strips a trailing `\r` too, so it tolerates either line-ending style
going forward); also normalized `cross.4`/`kernel.4` in the repo to LF,
matching most of the other source files.

### How the new `kernel.img` was actually produced

Bootstrapped using the *old* engine (still 4-byte cells, unmodified) plus
the *old* `kernel.img` as host, running the *new* (8-byte-cell-target)
`cross.4`/`kernel.4`/`extend.4` — this is exactly the self-hosting
cross-compilation path `README.md` describes, just exercised across a
cell-width change rather than a same-width rebuild. Once the resulting
`kernel.img` (8-byte cells) worked correctly under the new engine, the
old 4-byte engine's only remaining purpose (producing that one image) was
done; it isn't kept in the repo (per the phase-2 "replacing in place"
plan), but the bootstrap process itself — and why it has to go through
an existing engine at all rather than, say, gforth — is recorded above
in case a future cell-width or format change needs the same kind of
bootstrap again.

### What this iteration deliberately did NOT do

- Did not start phase 3 (Forth-hosted assembler) — phase 2 alone was
  substantial once the cross-compiler-side issues surfaced.
- Did not attempt to make `cross.4`/`kernel.4` cross-compile-host-agnostic
  beyond what was needed here (i.e., didn't try to make gforth work as an
  alternative host — see the non-goals update in `GOALS.md`).
- Did not increase `IMAGE_SIZE` (cross-compiler's target-image buffer,
  now 40000 bytes) or `MEMSIZE` (engine's VM memory, now 256KB) based on
  precise measurement — both were bumped generously (image roughly
  doubled in byte size going to 8-byte cells, actual new `kernel.img` is
  22472 bytes) rather than tightly sized; revisit if either becomes a
  real constraint.
- Did not re-verify the README's old benchmark numbers (they predate
  every engine variant this iteration removed) — left in place but
  flagged as historical/non-representative rather than re-run.

## 2026-09-01 — Design discussion: phase 5 direction, and a rejected byte-opcode idea

### Phase 5 agreed

Discussed and agreed the direction for phase 5 (see `GOALS.md`'s new
phase 5 section for the actual plan): libc as the portability layer for
"every architecture `bash` runs on" (phase 2's no-libc x86-64-only
syscalls don't scale to that), native host endianness for `kernel.img`
instead of SOD32's portable-on-disk format (no current need for one
image to run on hosts of differing endianness), computed-goto dispatch
and cross-compile-time call-flattening for portable, engine-format-
agnostic speed, and ARM64 Linux as the first non-x86-64 target. All of
this is planned, not yet implemented — this entry is the design
discussion that led to it, not an implementation log.

### Byte-granular opcode encoding: proposed, analyzed, rejected

Proposed idea: encode primitive opcodes as single bytes instead of full
cells (up to 8x denser for the common case of primitive-heavy
straight-line code), while keeping `CALL`/`BRANCH`/`0BRANCH`/`LIT` as
cell-width relative values stored at aligned addresses, reached via an
explicit marker byte (byte-granular positions can't reuse RelF's current
LSB-parity trick for distinguishing "primitive" from "offset", since
offsets between arbitrary byte positions don't have guaranteed parity
the way offsets between cell-aligned positions do).

First-pass analysis (mine) estimated a rough 25-30% image-size win by
counting the fraction of cells that are primitive-token-shaped (LSB=1)
in the current `kernel.img` — **this first pass had a real bug**: it
unpacked the image as little-endian to check the LSB, but `kernel.img`
is still in the old forced-big-endian on-disk format (see phase 2's
`swap_mem`/`@-T`/`!-T`) — so it was checking the parity of the wrong
byte entirely. Both the percentage split and the conclusion drawn from
it were wrong; corrected below.

The user then identified the actual structural problem directly, before
any corrected measurement: a plain `CALL` has **zero** opcode overhead
in the current format (the offset cell *is* the whole instruction, no
marker needed) but would need marker-byte-plus-alignment-padding under
the byte-opcode scheme — and that padding is structurally biased toward
its worst case (7 bytes), not averaged, because the position after any
aligned instruction is aligned again, which is exactly the worst-case
starting position for the next one. Back-to-back calls with no
primitives between them — common in idiomatically-factored, glue-heavy
Forth code — hit close to the 16-byte worst case (double the current
8-byte cost) essentially every time, not occasionally.

Redid the measurement correctly (big-endian unpack), and additionally
separated `LIT`/`BRANCH`/`0BRANCH` operand cells (identifiable exactly,
since their opcode tokens are fixed values 17/25/33 — see iteration 2)
from other LSB=0 cells (an upper bound on plain calls + header/link/name
data, not separable further without a full dictionary walk):

```
total cells: 2809
primitives (incl. LIT/BRANCH/0BRANCH opcodes): 1345 (47.9%)
LIT/BRANCH/0BRANCH operands: 292 (10.4%)
other LSB=0 (calls + header/link/name data): 1172 (41.7%)

current total:                                     22472 bytes
byte-format, best-case alignment throughout:       14521 bytes (~35% smaller)
byte-format, worst-case (steady-state back-to-back calls): 24769 bytes (~10% LARGER)
```

`LIT`/`BRANCH`/`0BRANCH` operands can only tie or improve under the new
scheme (they already pay for a full 8-byte opcode cell today). Plain
calls are the opposite — worse in the typical case, not just the worst
case — and are very likely the majority of that 41.7% "other" bucket in
real, call-heavy Forth code. So total image size plausibly *increases*,
not decreases. Separately, the same marker-fetch + realignment +
second-fetch overhead lands on `CALL`/`BRANCH`/`0BRANCH`/`LIT` dispatch
specifically, and those dominate real code's *dynamic* execution trace
(loops, conditionals, word calls), not just its static size — so a
performance regression is at least as plausible as a size regression.

**Decision: rejected, not pursuing further.** Computed-goto dispatch
already gets the well-understood, portable, low-risk dispatch-overhead
win without touching the image format at all, and call-flattening
directly reduces the number of `CALL`s in the first place — the exact
category this scheme handles worst. See `GOALS.md`'s phase 5 section for
the recorded reasoning (kept there so a future session doesn't re-derive
this from scratch). A different `CALL` encoding (variable-length
short/near/far forms, the way real ISAs handle this) could in principle
recover some of this, but needs assembler relaxation (multi-pass
encoding) — real, ongoing complexity that isn't justified without a much
stronger case than exists here, and cuts against goal 3.

## 2026-09-02 — Iteration 3: phase 5 (libc, native endianness, computed-goto, ARM64)

### Summary

Implemented most of phase 5 from `GOALS.md`: `relf.c` now builds with a
plain `cc -O2 -Wall -o relf relf.c` against libc (no special flags, no
custom `_start`, no inline asm for syscalls), `kernel.img` is native
host endianness with an 8-byte magic header, dispatch is computed-goto
threaded code, and the same binary + same `kernel.img` were verified
working on both x86-64 and ARM64 (the latter cross-compiled with
`aarch64-linux-gnu-gcc` and tested under `qemu-aarch64` user-mode
emulation — no physical ARM hardware used or available). Full test
suite (1892 `OK` markers) passes on both architectures, using the
*identical* `kernel.img`. `fib.4` gives the correct result on both.
Call-flattening (the other phase-5 item) is deliberately deferred — see
`GOALS.md`'s phase 5 section for why.

This iteration surfaced more real bugs than expected for what looked
like a fairly mechanical set of changes going in — three separate ones,
each documented below, each found by empirical testing after a plausible
-looking hand derivation turned out to be wrong or incomplete. Worth
internalizing for next time: this codebase's cross-compiler plumbing
(`cross.4`) is thin enough that small, seemingly-independent changes
(byte order, a flag stride, an open() mode table) interact in ways that
are easy to get wrong by reasoning alone and need to be checked against
running code, not just re-derived on paper.

### Bug found: wrong `open()` flags in the (now-removed) phase-2 engine

While bootstrapping the new image (which needs `SAVE-IMAGE`, i.e.
`CREATE-FILE`/`WRITE-FILE`, to actually run), `CREATE-FILE` failed with
`ENOENT` on a perfectly good path. `strace` showed the actual `open()`
call used `O_RDONLY|O_TRUNC` instead of `O_WRONLY|O_CREAT|O_TRUNC` — the
phase-2 engine's `open_flags` table had `0101000` (octal) where it
should have had `01101`: `O_WRONLY(01) | O_CREAT(0100) | O_TRUNC(01000)
= 577 decimal = 01101 octal`, not `0101000`. A plain arithmetic slip
when phase 2 was written, and it was never caught because no test in
this repo writes a file — everything runs via piped stdin. The
phase-2 engine (`relf.c` at that point) had never actually created a
file until this bootstrap tried to. Fixed in a scratch copy just to get
a working bootstrap host (the real fix is moot: `relf.c` is being
replaced by the phase-5 engine in the same commit, and the phase-5
version uses symbolic `O_WRONLY|O_CREAT|O_TRUNC` from `<fcntl.h>`
instead of a hand-computed octal literal, which is exactly the kind of
mistake that using named constants prevents). Worth remembering: a
clean test suite pass doesn't mean every code path has been exercised —
this one had zero coverage for over a full iteration.

### Bug found (by me, then corrected by more careful design): naive image-wide byte reversal corrupted string data

First attempt at native-endianness images: simplify `cross.4`'s
`@-T`/`!-T` to plain `@`/`!` (trivial, since this bootstrap's host and
target now agree on cell width — no 32-bit-host workaround needed this
time), and add a bulk `BSWAP-IMAGE` pass right before `SAVE-IMAGE`'s
`WRITE-FILE`, reasoning that the *existing* engine's `WRITE-FILE`
always reverses byte order on write (a leftover of the old portable
big-endian format), so a deliberate pre-reversal would cancel it out.

This worked correctly for cell-level data (verified by direct testing:
wrote known values, checked the resulting file bytes matched native-LE
expectations exactly) but broke string data — the boot banner came out
as `mocleW` (`Welcome` reversed) inside 8-byte groups. The bug: `BSWAP
-IMAGE` reversed the *whole* image uniformly, including name fields and
string literals written via `C!-T` (byte-level) — but byte-level data
was *already* coming out correct on disk without any help, because the
old engine's XOR-7 byte-addressing convention and its `WRITE-FILE`-time
`swap_mem()` cancel each other out for byte-level access (worked out by
hand-tracing what physical byte ends up where under each transform —
see the commit for the full derivation if this needs re-deriving).
Applying `BSWAP-IMAGE` on top double-reversed that data.

Fix: don't bulk-reverse anything. Instead, make `@-T`/`!-T` go through
the *same* byte-level path (`C@-T`/`C!-T`) that string data already
uses successfully, assembling/disassembling a little-endian value one
byte at a time. This gets the same automatic cancellation as string
data, for free, with no separate compensation pass needed. Verified
directly (round-tripped known values including `-1` through an actual
`SAVE-IMAGE`-style disk write, checked the raw file bytes with Python
matched native-LE expectations at the expected offsets) before
integrating it back into the real bootstrap.

### Bug found: `SEARCH-WORDLIST`'s name-comparison mask assumed the old byte order

With cell-level data now byte-assembled little-endian instead of the
old big-endian convention, `kernel.4`'s `SEARCH-WORDLIST` broke in a way
that took a moment to diagnose: `COLD`'s own compiled code ran fine
(banner printed correctly) but *every* interactively-typed word —
`CR`, `DUP`, `WORDS`, all of them — came back "Undefined word". Compiled
code doesn't need dictionary lookup (it's already resolved to direct
jumps at compile time); the interactive interpreter does, via `FIND`/
`SEARCH-WORDLIST`. That word has a fast-path optimization: compare a
candidate name's first cell against the search buffer's first cell in
one shot, masking off the 3 flag bits packed into the count byte first.
The mask (`1 61 LSHIFT 1 -`, clearing the top 3 bits of the cell) was
written for the old convention where the count/flag byte was the *most
significant* byte of the cell. Under native little-endian reads, the
count/flag byte is the *least significant* byte instead — masking bits
61-63 was clearing three bits that had nothing to do with the flags,
while leaving the real flag bits (now in the low byte) untouched, so
almost no candidate could ever match. Fixed by changing the mask to
clear the top 3 bits of the *low* byte instead (`-1 224 XOR AND`,
i.e. all-ones with the low byte's top 3 bits cleared - 224 = 0xE0).
`2/`'s own sign-bit mask (`1 63 LSHIFT`) didn't need a corresponding fix
— that one's about the numeric value of a cell as a whole, not about
which physical byte holds which character within a packed name, so it
was never sensitive to this distinction in the first place.

### Computed-goto: measured, not assumed

Built a throwaway function-pointer-table variant of the exact same
engine (same primitives, same everything else, dispatch loop swapped
back to the old `vmops[idx]()` indirect-call style) specifically to
isolate computed-goto's own contribution. `fib.4` at n=35, three runs
each: computed-goto averaged 0.666s, function-pointer averaged 0.866s —
a consistent **~1.30x**, not the ~4-4.75x the JIT section of `GOALS.md`
cites from prior exploratory work. See `GOALS.md`'s updated "Why RelF
specifically" section for a plausible explanation (that old number
likely came from measuring the removed asm engines, which used the real
CPU stack directly, not this portable C engine's manually-tracked
`dsp`). Recorded here so the old ~4-4.75x figure doesn't keep getting
cited as if it applies to this codebase - it doesn't, as measured.

### What this iteration deliberately did NOT do

- Call-flattening — see `GOALS.md`'s phase 5 section for the reasoning
  (given how each of the *other* phase-5 changes turned out to have a
  non-obvious bug despite looking simple going in, and how much smaller
  computed-goto's actual win was than expected, rushing a real
  code-generation change into the same iteration seemed like exactly
  the wrong lesson to take from the above).
- 32-bit-cell architectures (ARM32, i386, etc.) — see `GOALS.md`'s
  non-goals for why this is a separate, larger piece of work, not a
  small extension of what shipped here.
- Physical ARM64 hardware testing — QEMU user-mode emulation only, no
  physical device available. Worth spot-checking on real hardware if
  the opportunity comes up, though QEMU user-mode emulation of a
  syscall-level Linux binary is normally a reliable proxy for this kind
  of correctness testing (it's not emulating a different kernel, just
  translating the instruction stream).
- A general fix for the mask-computation *pattern* (i.e., auditing
  whether other bit-packed values elsewhere in `kernel.4` have similar
  byte-order sensitivity). Only `SEARCH-WORDLIST`'s mask actually turned
  out to be affected (see above); everything else that touches
  flag/count bytes already goes through `C@`/`C!` (byte-level, never
  sensitive to this) rather than treating multiple bytes as one packed
  cell. Worth keeping in mind as a category of bug if any *future* change
  introduces another whole-cell bit-packing trick.

## 2026-09-03 — Iteration 4: phase 6, i386/32-bit cell width (parameterized, verified working)

### Scope

Two fronts, both necessary: `relf.c` (the engine) parameterized for
cell width, and `cross.4`/`kernel.4` (the cross-compiler and kernel
source) also parameterized, since the cross-compiler itself computes
primitive dispatch tokens and packs/unpacks multi-byte target values -
it has to know the target's cell width, not just the engine. The engine
side was comparatively simple and verified early. The cross-compiler
side surfaced a long chain of real, independent bugs - documented below
roughly in the order found, since each one blocked visibility into the
next.

### relf.c: cell width from `UINTPTR_MAX`

Cell width (4 or 8 bytes) is now chosen at compile time from the host's
own `UINTPTR_MAX`, matching RelF's real-pointer addressing model (same
constraint as Bug 2, iteration 1). `umul`/`udiv` have separate paths:
`__int128`-based for 64-bit cells, plain `unsigned long long` for
32-bit (no extension needed there). `CELL_BYTES`/`CELL_SHIFT` macros
drive every stack-offset, dispatch-index, and alignment computation.
Building with `gcc -m32` therefore produces a working 4-byte-cell
engine with no other source changes. Verified: the 64-bit build regresses
nothing (full CORE suite still 1892 OK); the 32-bit build correctly
rejects a mismatched (8-byte) image at load via the magic header, and
correctly runs a genuine 4-byte-cell image once one exists (see below).

### cross.4/kernel.4: `TARGET-CELL-BYTES` and the hand-numbered tokens

Primitive tokens, `CELLS`/`CELL+`/`CELL-`, `2/`'s sign mask, alignment,
and the hand-embedded LIT/EXIT/BRANCH/0BRANCH/R> token numbers all
depend on cell width and were hardcoded for 8-byte cells throughout
`cross.4`/`kernel.4`. Introduced a single `TARGET-CELL-BYTES` variable
at the top of `cross.4` that everything else now derives from -
`CELLS-T`/`ALIGN-T`/`ALIGNED-T` (parameterized), `@-T`/`!-T` (rewritten
to loop over `TARGET-CELL-BYTES` instead of unrolled 8-byte access), and
a set of `-TOKEN` words (`EXIT-TOKEN`, `LIT-TOKEN`, `BRANCH-TOKEN`,
`0BRANCH-TOKEN`, `RFROM-TOKEN`, `CELLBYTES-TOKEN`, `CELLSHIFT-TOKEN`,
`SIGNSHIFT-TOKEN`) that compute the right value for whatever
`TARGET-CELL-BYTES` is currently set to, plus `TRANSIENT`-vocabulary
`-TOK` wrappers so `kernel.4`'s own source can reference them via
`CROSS-COMPILE`'s restricted `[TARGET, TRANSIENT]` search.

### Bug found — `DEFINED?`/`IF`/`THEN` at the top level silently corrupts the dictionary

First attempt at `TARGET-CELL-BYTES` used a `DEFINED?`-guarded
conditional (`VARIABLE` only if not already set, so a person could
pre-set it to 4 before including `cross.4`) at the *top level* -
outside any `:`...`;` definition. `IF`/`THEN` in this kernel are
compile-only words: their compiling machinery (`,`-based branch-offset
patching) only produces something coherent when a real definition is
being compiled around them. Used at the top level, they write into
whatever `HERE` happens to be at the time instead - which, depending on
what's defined nearby, either does nothing visible or corrupts an
unrelated word. Found via direct `DEPTH` tracing (a stray stack item
appeared at exactly that line) after this same top-level-`IF` mistake
had been mis-diagnosed several different ways first (see below). Fixed
by dropping the "avoid clobbering a pre-set value" cleverness entirely -
`TARGET-CELL-BYTES` is now a plain, unconditional `VARIABLE` set to 8,
and building for 32-bit means directly editing that one line to 4 (see
`README.md`) rather than something settable beforehand. Simpler, and -
per the immediately preceding paragraph - safer, since anything
IF/THEN-shaped at that scope is now known to be able to fail silently
rather than erroring.

### Bug found — the redefined `:` never sets the base kernel's `STATE`, breaking any word whose body isn't a self-contained `"HEADER`-based definition

The deepest and most time-consuming issue this iteration, eventually
diagnosed with certainty (gdb dictionary-chain walking, primitive-level
execution tracing via a temporary `TRACE-ON`/`TRACE-OFF`/`DBGDUMP`
instrumentation of the engine and a purpose-bootstrapped debug host -
see below) after several earlier, wrong theories.

`cross.4` redefines `:`/`;` (via `"HEADER`, a `>IN`-safe self-contained
name-parsing word) so that words like `PRIMITIVE`/`VARIABLE`/`CONSTANT`
can be defined as target-shadow words. This redefined `:` sets its own
`STATE-T` flag (so `NUMBER?` compiles numeric literals as target
literals) but never sets the base kernel's own `STATE` flag. Any
ordinary word compiled under it - one that isn't itself a
`"HEADER`/`DOES>`-based defining word with its own complete,
self-contained structure - therefore executes *immediately*, at
define-time, instead of being compiled to run later. This is a genuine,
pre-existing fragility in the original (pre-this-session) code, not
something introduced here: it silently "worked" there only by luck of
whatever garbage happened to be sitting on the stack at each such
point. Growing `cross.4` (adding the `TARGET-CELL-BYTES` machinery
earlier in the file) shifted that layout enough to turn several
previously-silent instances into visible crashes:

- `FORWARD` (uses plain `CREATE`, which has no `"HEADER`-style `>IN`
  safety): `CREATE`, executing immediately, consumed the literal text
  `-1` (the next source token) as its own name instead of as data,
  confirmed directly via `FIND`. The following `,` then had nothing
  reliable on the stack to store, and crashed. (An earlier session
  turn's belief that a bogus word literally named `-1` was somehow
  intentional/harmless turned out to be built on a broken `FIND` test -
  `FIND` was found to report "found" for *any* string this early in
  bootstrap, for reasons not further chased down since it wasn't the
  actual bug; a `Redefining:`-message-based check was used for
  everything after that instead, since it's a real signal, not
  inferred from a possibly-broken primitive.)
- `RESOLVE`/`T'`/`>BODY-T`: same root cause, same fix.
- `VARIABLE`/`CONSTANT`: these *do* use `"HEADER` (safe), but their own
  explicit `"HEADER`/`DOES>` - meant to run later, each time
  `VARIABLE X`/`CONSTANT X` is actually invoked from `kernel.4` - ran
  immediately instead, consuming the wrong token as a name and leaving
  the following store operation without a reliable value again (a
  clean, gdb-confirmed depth-check abort, not memory corruption - but
  still wrong).
- The control-structure words (`BEGIN`/`UNTIL`/`IF`/`THEN`/`ELSE`/
  `WHILE`/`REPEAT`) and `DO`/`LOOP`/`."`/`POSTPONE`/`ABORT"`: same root
  cause. Some of these (`BEGIN`/`IF`/`WHILE`) only *push* values and
  happened to survive running immediately; others (`UNTIL`/`REPEAT`)
  *consume* a value a real, deferred invocation would have had on the
  stack (from a matching `BEGIN`) and broke once the surrounding
  layout no longer left a spare value there by chance.

**Fix**: none of the above actually need the redefined `:`'s inherited
`DOES>` behavior - `FORWARD`/`RESOLVE`/`T'`/`>BODY-T` are ordinary host
words with no nested defining-word pattern of their own, and
`VARIABLE`/`CONSTANT`/the control-structure words each have their own
complete, self-contained `"HEADER`/`DOES>` (or no defining-word pattern
at all). All of them are now defined using the plain, original `:`/`;`
instead (wrapped in `T]`/`T[` where `STATE-T` still needs to be 1, for
`NUMBER?` to compile their own internal numeric literals correctly) -
removing the fragility rather than trying to preserve whatever made it
work by luck before. The redefined `:`/`;` itself is kept, but now
correctly scoped to its one remaining real purpose: `kernel.4`'s own
source uses `:`/`;` throughout to compile *target*-level colon
definitions, found via `CROSS-COMPILE`'s own restricted
`[TARGET, TRANSIENT]` search - which needs a `:`/`;` pair to exist in
`TRANSIENT` vocabulary, and that's genuinely safe now since nothing
else routes through it anymore.

An early, tempting-looking fix attempt - just adding `1 STATE !`/
`0 STATE !` to the redefined `:`/`;` - was tried and reverted twice,
for two different reasons worth recording so it isn't retried: first,
while `FORWARD` still used the redefined `:`, this made `FORWARD`'s own
`DOES>` (always immediate, by design, in any Forth) fire *during*
`FORWARD`'s compilation instead of at its later invocation, attaching
its runtime action to the wrong word and corrupting `FORWARD` itself.
Second, after moving `FORWARD` but before moving `VARIABLE`/`CONSTANT`,
the same conflict recurred for them, since they *also* have their own
`DOES>`. Setting `STATE` is fundamentally incompatible with any word
whose body itself contains a `DOES>`, when that word is defined via a
`DOES>`-based defining word - moving affected words off the redefined
`:` entirely, rather than patching `STATE`, was the only fix that
didn't just relocate the conflict.

### Bugs found — three unrelated forward-reference/hardcoded-width mistakes introduced earlier this same effort

Once the above was fixed, the bootstrap progressed far enough into
`kernel.4`'s own compilation to expose three small, independent
mistakes from this session's *own* earlier parameterization edits (not
pre-existing):

- **`J`** (`RP@ CELLBYTES-TOK 3 * + @`) used `*`, but `kernel.4` doesn't
  define `*` until ~150 lines later - a forward reference that never
  existed before this session (the original was a hardcoded `24`,
  needing no multiply at all). Fixed by replacing `CELLBYTES-TOK 3 *`
  with `CELLBYTES-TOK CELLBYTES-TOK CELLBYTES-TOK + + +` (repeated
  addition), avoiding the not-yet-available word entirely.
- **`ALIGNED`** (`CELLBYTES-TOK 1- + ...`) used `1-`, defined even
  later in `kernel.4` than `*`. Same category of mistake, same kind of
  fix: `CELLBYTES-TOK 1 - + ...` (the primitive `-` with a literal `1`,
  instead of the compound `1-`).
- **`2/`** (`DUP SIGNSHIFT-TOK LSHIFT AND SWAP 1 RSHIFT OR`) was missing
  a `1` before `SIGNSHIFT-TOK`: it shifted `n1` itself left by the sign
  position instead of shifting `1` left to build the sign-bit mask,
  computing garbage. Fixed by inserting the missing `1`
  (`DUP 1 SIGNSHIFT-TOK LSHIFT AND SWAP 1 RSHIFT OR`). Caught by the
  CORE test suite itself (`WRONG NUMBER OF RESULTS` on several `2/`
  cases) once the bootstrap finally completed - the first bug in this
  iteration caught by the test suite rather than by the bootstrap
  failing outright.

### Bug found — `DEPTH`'s hardcoded `3 RSHIFT`

With the 8-byte build fully passing (1892 OK, confirmed no
regressions), the first genuine 4-byte-cell (i386) bootstrap produced a
correctly-sized, correctly-tagged image and ran basic arithmetic
correctly - but failed the CORE suite extensively, on tests as basic as
`DUP`/`OVER`/`DEPTH` itself. Traced via direct, isolated manual tests
(not the test harness, which turned out to itself depend on `DEPTH`
being correct, making its own failures a symptom rather than a
separate bug) to `kernel.4`'s `DEPTH`: `SP@ S0 @ SWAP - 3 RSHIFT` -
the `3` (`log2(8)`) hardcoded, never updated to derive from
`TARGET-CELL-BYTES` like the rest of this iteration's changes. Fixed by
replacing it with `CELLSHIFT-TOK` (`log2(TARGET-CELL-BYTES)`, already
computed correctly elsewhere). A grep for the same `N RSHIFT`/`N
LSHIFT` pattern elsewhere in `kernel.4` found no other instances.

### Bug found — `@-T` didn't sign-extend for a narrower target

With `DEPTH` fixed, the 4-byte-cell bootstrap itself started crashing
at the very end (`SAVE-IMAGE`/final resolution), in `RESOLVE`
specifically. `RESOLVE`'s chain-termination check (`DUP -1 -`, testing
whether the current link equals the host's own full-width `-1`)
compares against a value read back via `@-T`, which accumulates only
`TARGET-CELL-BYTES` bytes and leaves the high bytes zero regardless of
the target value's actual sign. A target-level `-1` sentinel (stored as
4 bytes of `0xFF`) read back as `0x00000000FFFFFFFF`, not sign-extended
`-1` - so `RESOLVE`'s loop never saw the chain end, and walked off into
unrelated memory. Fixed by extending `@-T` to sign-extend its result
when `TARGET-CELL-BYTES` is narrower than this host's own cell width
(guarded so the shift-by-64 this would otherwise need in the "no
narrowing" 8-byte-cell case is never actually executed - undefined
behavior in C for a shift equal to the operand's own bit width).

### Verification

Both cell widths pass the full CORE test suite (`tester.fr` + the
`tests/*.fth` extras) cleanly from the same `cross.4`/`kernel.4`
source: **1892 OK markers, zero errors, on both the 8-byte-cell and
4-byte-cell (i386) builds.** `fib.4` (`FIB 34`, via `RECURSE`) also
gives the identical correct result (`9227465`) on both.
`tests/run_tests.sh` now builds and runs both automatically (the
4-byte-cell image is cross-compiled fresh each run, via a temporary
copy of `cross.4` with `TARGET-CELL-BYTES` set to 4, into a temp
directory - the committed `cross.4` itself stays at its 8-byte
default).

### Debugging infrastructure worth remembering for future sessions

Two purpose-built tools made the `STATE`/nested-`DOES>` bug (the
hardest one this iteration) tractable, after plain reasoning about the
Forth source repeatedly produced wrong theories:

- **`DBGDUMP`**: a temporary engine primitive (peeks `dsp`/`rp`/`ip`
  and 8 data-stack cells to stderr, no stack effect) added to a
  throwaway copy of the engine, with a corresponding
  `PRIMITIVE DBGDUMP IMMEDIATE` added to a throwaway copy of the
  *previously-working* `kernel.4` (bootstrapped via the
  *previously-working* `cross.4`, to get a debug-capable host without
  depending on the very code under investigation). Marking it
  `IMMEDIATE` was essential - it let it fire even while compiling,
  mid-definition, which ordinary `.`/`DEPTH` sequences can't do without
  changing what's being observed.
- **`TRACE-ON`/`TRACE-OFF`**: same approach, toggling a global flag the
  engine's dispatch loop checks on every primitive, logging each one
  (by name) plus `dsp`/`rp` to stderr. Comparing the primitive sequence
  between a known-working run and a failing one (`diff` on just the
  primitive names, ignoring addresses) pinpointed the exact divergence
  point directly, rather than continuing to guess which stack-state
  hypothesis to check next.

Both were built as one-off, uncommitted C/kernel.4 changes in scratch
directories, never merged into the real source - worth reconstructing
the same way if a similarly opaque bug shows up again, rather than
trying to keep them permanently wired into the committed engine.

### What this iteration deliberately did NOT do

- **ARM32.** Only i386 was actually built and tested. ARM32 should work
  through the same `gcc`-target-picks-`UINTPTR_MAX` mechanism in
  principle, but hasn't been tried - worth doing before claiming it
  works, given how many independent, non-obvious bugs turned up getting
  i386 working despite the design looking straightforward going in.
- **A clean, safe "pre-set `TARGET-CELL-BYTES` before including
  `cross.4`" mechanism.** The `DEFINED?`/`IF`/`THEN` attempt at this
  was the first bug found this iteration (see above) and was removed
  rather than reattempted - building for 32-bit now means directly
  editing one line in `cross.4` (documented in `README.md`), which is
  less convenient but has no equivalent failure mode.
- Auditing `cross.4` for *other* possible instances of the
  `STATE`-never-set fragility beyond what actually surfaced as
  failures. Everything that broke did so loudly (a crash or a test
  failure) once reached; anything that didn't break might still be
  relying on the same "happens to survive by luck" pattern without it
  having been exercised yet. Worth keeping in mind if something in this
  area breaks again after a seemingly-unrelated change.

## Iteration 5: POSIX shell, v0.1 (process-control primitives + shell.4)

Goal: a real, working shell built on top of RelF, as a first step
toward GOALS.md's broader "userland on RelF" ambitions. Scoped
deliberately small for this iteration - see "What this iteration
deliberately did NOT do" below - with the plan to grow it in later,
separate increments rather than attempting full POSIX grammar at once.

### New engine primitives (relf.c / kernel.4)

Ten new primitives, added purely additively (appended to the dispatch
table and to `kernel.4`'s `PRIMITIVE` declarations, in matching order -
existing token numbers are unaffected):

`FORK`, `EXECVE`, `WAITPID`, `PIPE`, `DUP2`, `GETENV`, `SETENV`,
`SYS-EXIT`, `CHDIR`, `GETCWD`. Each is a thin wrapper around the
matching libc call, following the same string-handling convention as
the existing `OPEN-FILE`/`SYSTEM` primitives (callers pass real host
pointers - RelF's addressing model makes this natural - and are
responsible for NUL-terminating any string handed to libc). `CLOSE-FILE`
is reused as-is for pipe file descriptors, since `fid` in this engine
has always been the raw OS fd directly (confirmed by reading
`L_openfile`/`L_closefile` before adding anything new).

Verified individually, directly at the Forth level, before building any
shell logic on top - fork/wait/exit semantics, execve with a
hand-built argv array actually running `/bin/echo`, a full pipe
round-trip (child's stdout redirected through a pipe via `DUP2`, parent
reading the result back), and getenv/setenv/chdir/getcwd. Full CORE
regression suite (1892 OK, both cell widths) re-run after adding the
primitives, before writing any shell code, and confirmed unaffected.

### shell.4 (v0.1)

A separate, layered `.4` file (not folded into `kernel.4`) - loaded on
top of an already-bootstrapped image via `S" shell.4" INCLUDED` then
`SH`. Kept separate deliberately: a shell is a specific application on
top of the core Forth system, not part of the core interpreter/compiler
that `kernel.4`/`cross.4` define, and this keeps the base image minimal
per GOALS.md's own stated preference.

v0.1 scope: whitespace-only tokenizing (no quoting/escaping), PATH-
searched external command execution via `FORK`/`EXECVE`/`WAITPID`, and
four builtins (`cd`, `pwd`, `export`, `exit`) that must run in the
shell's own process rather than a forked child, since their entire
point is changing *this* process's own state in a way a child's copy
couldn't propagate back from. Verified end-to-end, interactively, on
both cell widths: `echo` producing real subprocess output, `ls` on a
nonexistent path producing the real `ls` error text, `cd`/`pwd`
genuinely changing and reporting the process's own working directory,
`export` genuinely setting an environment variable retrievable via
`GETENV`, and `exit` terminating cleanly. A shell smoke test
(`run_shell_smoke_test` in `tests/run_tests.sh`) now runs after the
CORE suite on both engine builds, checking this same flow, so a future
regression here gets caught automatically rather than requiring someone
to remember to test the shell by hand.

### Bugs found and fixed this iteration

Getting from "primitives exist" to "the shell actually works" surfaced
several real bugs, distinct from a larger number of mistakes in the
*test scripts themselves* while directly exercising the new primitives
(stack-order confusion, forgetting to `DUP` a value before consuming
it, `S"`'s shared-pad gotcha when called twice on one line, using
`COUNT` - for Forth's length-prefixed strings - on a NUL-terminated
C string instead). Those test-script mistakes are not listed below;
they cost time but didn't point at anything wrong in the shipped code.
The real bugs:

- **Tokenizer never NUL-terminated the last token when the input line
  had no trailing whitespace.** `TOKENIZE`'s per-token NUL-write was
  guarded by `TOK-POS < TOK-END`, which is false exactly when the last
  token runs all the way to the end of the input with no separator
  after it - a completely ordinary case (`ls -la` typed normally, no
  trailing space). Fixed by removing the guard - `LINE-BUF` always has
  headroom for the one extra byte, since `LINE-MAX` is far larger than
  any real input line.
- **`SEARCH-PATH`'s own env-var-name NUL-termination bug: `4 ENVNAMBUF
  C!` stores the number 4 at `ENVNAMBUF`'s first byte, overwriting
  `'P'`, instead of writing a NUL at `ENVNAMBUF+4` (the byte *after*
  "PATH"'s four characters).** This silently broke every `$PATH`/`$HOME`
  lookup - `GETENV` was searching for a garbled variable name and
  correctly reporting "not found". Same bug, same fix, appeared in
  `DO-CD`'s `$HOME` lookup too. Caught by directly checking `GETENV`'s
  return value rather than assuming the surrounding logic was fine
  because it "looked" right.
- **`B-CSTR` (the C-string-append helper) had a stray `DROP` that
  discarded the source pointer instead of just advancing it via
  `CHAR+`**, corrupting the string-builder's walk after the first byte
  of any appended command name.
- **`SEARCH-PATH`'s directory-splitting loop had an erroneous `OVER
  SWAP` before calling `TRY-DIR`**, pushing an extra, uninquired-about
  stack item that `TRY-DIR` never consumed - the `(start len)` pair was
  already in the right order for `TRY-DIR`'s own `( c-addr u --- )`
  signature; the `OVER SWAP` was pure noise, added out of not fully
  trusting stack order this session's earlier debugging had already
  made unreliable-feeling.
- **`DISPATCH` opened with `ARGV @ ARGC @ IF`**, pushing two values but
  `IF` only consuming the top one - leaving `ARGV @` permanently
  orphaned on the stack for the rest of that call, corrupting every
  builtin check downstream. Fixed to just `ARGC @ 0 > IF`.
- **Every builtin-name comparison in `DISPATCH` called `STR0=` with its
  arguments backwards** (`ARGV @ S" cd" STR0=` instead of `S" cd" ARGV
  @ STR0=`) - `STR0=`'s signature is Forth-string-first,
  C-string-second (`( c-addr1 u1 c-addr2 --- f )`), and every one of
  the four checks had it the other way around.

Each of these was found by isolating the failing piece with a small,
targeted test (or `gdb` when the failure was a segfault rather than
wrong output) rather than trying to debug the whole shell loop at once
- consistent with the trace-diff/gdb-first approach documented for
Iteration 4's harder bugs.

### A build mistake worth recording

While setting up an i386 test of the finished shell, `relf32` was
built from `/home/claude/work/relf_multiarch.c` - a leftover scratch
copy of the engine from Iteration 4, predating this iteration's ten new
primitives entirely. The resulting binary's dispatch table was ten
entries short of what the (correctly rebuilt) `kernel.img` expected,
so invoking any of the new primitives jumped through a dispatch-table
read past its actual end, landing on whatever garbage followed in
memory - a segfault with a nonsensical backtrace (jumping to address
`0x1`, corrupted-looking frames) that had nothing to do with the
primitives' own logic. Confirmed via `diff` against the real,
current `relf.c` before spending time debugging the shell itself.
Worth remembering: scratch copies made mid-session for one purpose
(the i386 cell-width work in Iteration 4) silently go stale the moment
the real source moves on, and a segfault with a dispatch-table-shaped
signature is worth checking for source/binary mismatch before assuming
it's a logic bug.

### What this iteration deliberately did NOT do

- **Pipes and redirection (`|`, `<`, `>`, `>>`).** An earlier attempt at
  this within the same file got tangled - reaching for return-stack
  tricks (`2>R`/`2R@`) that don't exist in this kernel, and leaving a
  half-written placeholder mid-function - and was discarded rather than
  patched. `PIPE`/`DUP2` are already in place and individually verified
  (see above), so the primitive layer is ready; the shell-side wiring
  is a separate, focused piece of follow-up work, not attempted again
  this iteration to avoid repeating the same mistake under the same
  time pressure.
- **Any quoting or escaping.** A space always splits tokens, with no
  way to include one literally in an argument.
- **`$VAR` expansion, `` $(...) `` command substitution, control
  structures (`if`/`while`/`for`/`case`), shell functions, job
  control, or multi-stage pipelines (more than one `|` per line).**
  All out of scope for v0.1; noted here so the gap is explicit rather
  than discovered by surprise later.
- **ARM64/ARM32 verification of the shell.** The new primitives and
  shell.4 were verified on the 8-byte (x86-64) and 4-byte (i386)
  builds only, matching Iteration 4's own scope boundary. Nothing in
  the new primitives is architecture-specific (they're thin libc
  wrappers, same as the existing file-I/O primitives), so this is
  expected to work, but "expected to work" undersells how many
  supposedly-mechanical steps in this project have turned up real bugs
  on inspection - worth actually checking before relying on it.

## Iteration 6: shell `-c` mode + a real test suite for shell.4

Goal: give RelF's shell a normal single-executable invocation
(`relfsh -c 'command'`, matching `sh -c '...'`), motivated by wanting to
eventually point a real test harness at it - see the discussion that
preceded this iteration for why bash's own `tests/` (parameterized via
a `THIS_SH` env var) is the best-designed reference for this, but
wasn't directly usable yet (its content assumes far more shell than
v0.1 has, and its harness itself requires `-c`/script invocation,
which shell.4 didn't have). This iteration builds that missing piece
and a first real test suite structured the same way, scoped to what
shell.4 actually implements.

### New engine primitives: `SYS-ARGC`/`SYS-ARG`

Two new primitives exposing relf's own `argv` (beyond `argv[1]`, the
kernel-image path) to Forth: `SYS-ARGC ( --- n )` and `SYS-ARG
( n --- c-addr )`. `main()` now stashes `argc`/`argv` in two static
globals (`g_argc`/`g_argv`) before doing anything else, so the
primitives can read them later. Deliberately minimal and
generic - the engine doesn't know anything about `-c` itself; it just
exposes argv and lets shell.4 (Forth) decide what any of it means,
consistent with keeping engine changes small and pushing behavior to
the Forth layer wherever possible (same philosophy as every other
primitive added so far). Verified directly (`SYS-ARGC`/`SYS-ARG`
against `relf kernel.img -c "echo hello world"`) before wiring
anything into shell.4.

### shell.4: `RUN-LINE`, `SH-C`, `MAIN`

`SH1` (the interactive per-line handler) was refactored to extract its
tail (tokenize, then dispatch to a builtin or run externally) into a
shared `RUN-LINE ( u --- )`, so `-c` mode can reuse identical logic
rather than duplicating it. `SH-C ( c-addr --- )` takes a NUL-terminated
command string (from `SYS-ARG`), copies it into `LINE-BUF`, runs it via
`RUN-LINE`, and exits with `LAST-STATUS`. `MAIN` is the new suggested
entry point: if `SYS-ARGC` is 2 and the first arg is exactly `"-c"`,
it runs the second arg via `SH-C` (never returns); otherwise it falls
through to the ordinary `SH` loop. Only ever runs *one* command in
`-c` mode - no `;`/`&&` chaining, since `TOKENIZE` has no notion of a
statement separator yet (same scope boundary as always).

**A real bug found and fixed while adding this**: `LAST-STATUS` had
previously only ever been set by `RUN-EXTERNAL`, and stored the *raw*
`WAITPID` status rather than a decoded exit code - meaning `-c 'false'`
would have propagated the wrong status (the raw status's low byte,
which happens to be 0 for any normal exit, regardless of the actual
exit code, since the code lives in bits 8-15). Fixed by decoding
`WEXITSTATUS` (`8 RSHIFT 255 AND`) before storing, and by having every
builtin (`DO-CD`, `DO-PWD`, `DO-EXPORT`) set `LAST-STATUS` too, so `-c`
mode reports a sensible status regardless of whether the command it
ran was a builtin or external. Signal-terminated children aren't
distinguished from normally-exited ones with the same low byte - a
known, documented v0.1 simplification, not fixed here.

### `relfsh`: a single-executable wrapper

relf itself needs a kernel-image argument and a two-line Forth
bootstrap (`load shell.4, then call MAIN`) before it behaves like "a
shell" - `relfsh` is a small POSIX-`sh` script that hides that,
piping the bootstrap in ahead of relf's own stdin. Configurable via
`RELF_BIN`/`RELF_IMG` env vars (defaulting to the wrapper's own
directory) so one script drives either cell-width build - used this
way in `tests/run_tests.sh`.

**A real bug found and fixed while building this**: the first version
unconditionally chained the bootstrap output with `cat` (so
interactive/piped-script callers would still see their own stdin
*after* the two bootstrap lines). But `-c` mode's `SH-C` never reads
stdin again after running its one command and exiting - so `cat` sat
blocked waiting for EOF on `relfsh`'s own stdin that never came,
hanging the whole pipeline (surfaced as `timeout` killing the process
group, exit 124, even though relf itself had already finished and
printed its output). Fixed by only chaining `cat` when *not* in `-c`
mode.

### `tests/shell/`: a real, scoped test suite

Structural pattern (individual `run-<feature>` files under a master
`run-all` driver, a `THIS_SH`-style environment variable pointing at
whatever shell binary is under test) is deliberately borrowed from
bash's own `tests/` directory. Content is not borrowed from it - written
fresh, scoped to what shell.4 actually implements as of this iteration
(external command execution + exit status, `cd`/`pwd`/`export`), and
meant to grow feature-by-feature alongside shell.4 rather than testing
ahead of it. Unlike bash's own suite (which diffs raw output against a
fixed `.right` file), these use substring/status assertions
(`assert_output_contains`/`assert_status` in `lib.sh`) rather than
whole-output diffing - relf's own boot banner and CRLF line endings
would make literal full-output comparison fragile for little benefit
here.

Five test files, ten assertions total: `run-echo` (external command
output + exit status), `run-exit-status` (`true`/`false`/nonexistent
command → 0/1/127), `run-cd` (persists across a session; reports an
error for a missing directory), `run-export` (verified via a real `env`
child process, since shell.4 has no `$VAR` expansion yet to check this
from within the shell itself), `run-pathsearch` (bare name via `$PATH`
vs. a `/`-containing path bypassing the search).

**A real, previously-undetected bug caught immediately by `run-pathsearch`**:
`RUN-CHILD`'s direct-path branch (for a command name containing `/`,
which should bypass `$PATH` search entirely) called `ARGV @ ARGV @
EXECVE` - pushing `ARGV[0]` (the command string) as *both* of
`EXECVE`'s arguments, instead of `ARGV` (the array's own address) and
`ARGV[0]` (the string). Always failed with exit 127. This had slipped
through every manual test in Iteration 5, because none of them
happened to exercise a slash-containing command name - only the
`$PATH`-search branch got manually exercised. Fixed to `ARGV ARGV @
EXECVE`, matching the working pattern already used by `TRY-DIR`
elsewhere in the same file. Directly demonstrates the value of the new
suite: it caught a real bug in already-"working", already-tested code
within its very first run.

Wired into `tests/run_tests.sh`, replacing the earlier one-off shell
smoke test from Iteration 5 (superseded - the new suite covers
strictly more, and using `relfsh` end-to-end also now exercises the
new `-c` mode as part of every CI-style run). Runs against both engine
builds via `relfsh` with `RELF_BIN`/`RELF_IMG` overridden for the
4-byte-cell build. Full suite (CORE + shell) passes on both cell
widths after all of the above.

### What this iteration deliberately did NOT do

- **Adopting any of bash's actual test *content*.** Only the
  structural pattern was borrowed - see above. Pulling in real bash
  test cases remains blocked on the same gap as before (quoting,
  `$VAR` expansion, control structures), now joined by a smaller one:
  even bash's simplest `${THIS_SH} -c '...'` cases often assume more
  than a single bare command (e.g. `-c 'a; b'`), which `-c` mode here
  deliberately doesn't support yet (see `RUN-LINE`'s scope note above).
- **`.right`-style whole-output diffing.** Deliberately using
  substring/status assertions instead - see above for why.
- **Script-file invocation (`relfsh script.sh`, as opposed to `-c` or
  interactive/piped).** Not attempted; `MAIN`'s argv-inspection logic
  would need extending to recognize a bare filename argument and
  `INCLUDED`/read it as a sequence of commands rather than Forth
  source. Worth doing if a future test suite wants it.
- **Distinguishing signal-terminated commands' exit status from
  normally-exited ones with the same low byte** in `LAST-STATUS`'s
  decoding - noted above, a real POSIX shell distinguishes these
  (typically via the 128+signum convention); v0.1 doesn't.

## Iteration 7: pipes and redirection

Goal: the two features deliberately deferred out of Iteration 5 after
an earlier, abandoned attempt within that same session got tangled
(unverified return-stack tricks, a half-written placeholder - see that
iteration's "what this iteration deliberately did NOT do"). This
iteration builds both properly, from a clean slate, with the explicit
lesson from that earlier attempt in mind: avoid in-place index
shifting and unverified stack tricks in favor of plain, explicit,
easy-to-verify constructs, even at the cost of an extra small buffer
or two.

### New engine capability: `A/O` (append) file mode

Redirection's `>>` needs to create a missing file without truncating
an existing one - and none of the engine's six existing `open_flags[]`
entries do that (`W/O` truncates; `R/W` doesn't create). Added a
seventh/eighth pair of flags (`O_WRONLY | O_CREAT | O_APPEND`, plus
the binary-mode duplicate matching the existing even/odd convention)
to `open_flags[]`, and a matching `A/O` constant in kernel.4 alongside
the existing `W/O`/`R/O`/`R/W`. Verified directly (open the same file
twice with `A/O`, write to it each time, confirm both writes land
without the second truncating the first) before using it from shell.4.

### `PARSE-REDIRECTIONS`/`APPLY-REDIRECTIONS` (`<`, `>`, `>>`)

`PARSE-REDIRECTIONS` scans the tokenized `ARGV` for these three
operators; each one found records the filename token that follows it
into a dedicated variable (`REDIR-IN-FILE`/`REDIR-OUT-FILE`/
`REDIR-APPEND-FILE`) and both tokens are excluded from the command's
own argv. Built as a fresh copy into a second array (`ARGV2`/`ARGC2`),
then copied back over `ARGV`/`ARGC` - not in-place shifting - exactly
the choice the earlier abandoned attempt didn't make.
`APPLY-REDIRECTIONS` runs in the forked child, after `FORK` but before
`RUN-CHILD`/`EXECVE`: opens each recorded file with the matching mode
(`R/O`/`W/O`/`A/O`) and `DUP2`s it onto fd 0 or fd 1, closing the
original fd afterward - the same open-then-dup2-then-close pattern
already verified working for `PIPE`/`DUP2` in Iteration 5. Only
applies to external commands, not builtins (`pwd > file` doesn't
redirect the builtin's own output) - a deliberate v0.2 scope limit,
not an oversight.

**A real bug found immediately on first load**: a nested parenthesis
inside a `( ... )` Forth comment - `( c-addr, or 0 for none - ">"
(truncate) )` - broke parsing. This kernel's `(` comment word just
reads until the *first* `)`, so the inner `(truncate)` terminated the
comment early, leaving a stray `)` to be parsed as a word and failing
with "Undefined word `)`". Fixed by removing the nesting; a quick
audit confirmed no other new comment had the same problem (one
pre-existing line has two *sequential* comments on one line, which is
fine - parsed and reparsed as two separate `( ... )` spans, not one
nested inside the other).

Verified end-to-end via `relfsh -c`: `>` creates and truncates, `>>`
genuinely preserves prior content across two separate invocations
rather than truncating it, `<` feeds a real file's content to a
child's stdin, and `<`+`>` combined on one line (`cat < in > out`)
works. `tests/shell/run-redirect` (4 assertions) locks this in.

### `SPLIT-PIPE`/`RUN-PIPELINE` (a single `cmd1 | cmd2` per line)

`SPLIT-PIPE` scans tokenized `ARGV` for a `|` token and splits into
two fresh argv arrays (`ARGV-L`/`ARGC-L`, `ARGV-R`/`ARGC-R`) - same
copy-don't-shift discipline as redirection, using two small helper
predicates (`AT-END?`, `AT-PIPE?`) to keep the scanning loop readable.
`RUN-PIPELINE` creates a real `PIPE`, forks twice, and wires each side
up exactly the way Iteration 5's own directly-verified pipe test did
(`DUP2` the correct end onto fd 0 or fd 1, close both original pipe
fds in each child, close both in the parent too, `WAITPID` on both
children). Rather than duplicating or generalizing the PATH-search/
exec logic to take an arbitrary argv array as a parameter, each side's
child copies its own argv (`ARGV-L` or `ARGV-R`) into the *global*
`ARGV`/`ARGC` via a new `COPY-ARGV` helper, then calls the existing,
already-proven `RUN-CHILD` unchanged. This is safe specifically
because each side runs in its own forked child: `fork()` gives each
child an independent copy of all memory, so overwriting the global
`ARGV` there can't affect the parent or the other child. Deliberately
reused rather than refactored, to keep the pipe-execution surface area
small and built entirely from already-verified pieces.

**Scope decision, not a bug**: pipes and redirection are mutually
exclusive per line in v0.2. If a line contains `|`, `PARSE-REDIRECTIONS`
is skipped entirely for that line, and any `<`/`>`/`>>` tokens are
passed through as literal arguments rather than interpreted. Combining
the two correctly - figuring out *which side* of a pipe a trailing
redirection belongs to - is real, separate complexity, and risking an
under-tested guess at it alongside the first pipe support wasn't worth
it. Also v0.2: builtins aren't supported on either side of a pipe
(`RUN-PIPELINE` always uses `RUN-CHILD`, never `DISPATCH`) - a
reasonable limit matching how even real POSIX shells run pipelined
builtins in a subshell anyway (already more complexity than this
project's current v0.2 needs). The pipeline's own reported exit status
is the right-hand side's (matching ordinary, non-`pipefail` shell
behavior); the left side's status isn't exposed anywhere (a real shell
would offer this via something like `$PIPESTATUS` - not implemented).

Verified with real multi-process data flow, not just `cat`-based
plumbing checks: `echo hello world | wc -w` (word count actually
computed downstream), `echo ... | grep needle` matching and
`echo ... | grep xyz` not matching (confirming both real data transfer
through the pipe and correct exit-status propagation - 0 for a match,
1 for none). `tests/shell/run-pipe` (4 assertions) locks this in.

### Full state after this iteration

`tests/shell/run-all`: 18 assertions across 7 files (`run-cd`,
`run-echo`, `run-exit-status`, `run-export`, `run-pathsearch`,
`run-pipe`, `run-redirect`), all passing. Full suite (CORE + shell)
passes on both x86-64 and i386 after every change in this iteration,
checked incrementally rather than only at the end.

### What this iteration deliberately did NOT do

- **Combining pipes and redirection on one line** - see above.
- **Multi-stage pipelines** (`a | b | c`, more than one `|`) - `SPLIT-PIPE`
  only recognizes a single `|`; a second one is currently left as a
  literal argument to whichever side it lands in (untested, unspecified
  behavior - worth an explicit check before anyone relies on it either
  way).
- **Builtins on either side of a pipe** - see above.
- **Exposing the left side's exit status** from a pipeline (no
  `$PIPESTATUS`-equivalent).
- **Quoting/escaping** - a literal `|`, `<`, `>` inside a quoted string
  isn't possible yet, since there's no quoting at all; every occurrence
  of these characters as a whole token is currently treated as the
  operator.

## Iteration 8: quoting and escaping

Goal: the next natural gap identified at the end of Iteration 7 -
single quotes, double quotes (with minimal escape recognition), and
backslash-escaping - the foundational piece that both combining
pipes+redirection and any future `$VAR` expansion depend on (you
can't safely have `$VAR` expansion without a way to prevent it, i.e.
quoting, and you can't safely combine pipe/redirect syntax with
literal arguments containing those same characters without it either).

### Tokenizer rewrite: `SCAN-TOKEN` replaces `SKIP-TOKEN`

The old tokenizer only ever needed to find whitespace boundaries -
`SKIP-TOKEN` just walked forward until whitespace, and the token's
start/end addresses were exactly the raw input's own bytes. Quoting
breaks that assumption: `"a b"` should become the two-character
content `a b`, four bytes shorter than its six-byte raw span. The new
tokenizer compacts in place via a trailing write cursor (`TOK-OUT`)
that only ever lags behind or equals the read cursor (`TOK-POS`) -
safe because unquoting only ever removes bytes (quote marks,
backslashes), never adds them. Three small, individually-dispatched
helpers handle the three quoting forms: `COPY-SINGLE-QUOTED` (fully
literal, no escapes recognized at all inside, matching POSIX),
`COPY-DOUBLE-QUOTED` (recognizes `\"` and `\\` as escapes for a
literal `"` or `\` - not `$`/`` ` ``, since there's no expansion to
guard against yet), and `COPY-ESCAPED-CHAR` (a lone backslash outside
any quotes makes the next character literal). `SCAN-TOKEN` just reads
the current character and dispatches to the matching helper, or emits
it plain - adjacent quoted/unquoted/escaped spans concatenate into one
token this way, matching real shell behavior (`'ab'c"d e"f` becomes
one token, `abcd ef`). An unterminated quote consumes to the end of
input rather than erroring (a real shell would prompt for a
continuation line - not attempted here).

### Real bug #1: nul-terminator write destroyed the token separator

First working version passed a basic "does 'a b' become two tokens"
check but then produced an *empty* second token on anything past the
first. Root cause: the old tokenizer explicitly advanced its cursor
past the whitespace separator after nul-terminating each token; the
compacting rewrite's nul-termination now happens at `TOK-OUT`, which
for a plain unquoted token *coincides* with the separator's own
position (no compaction occurred, so the write cursor never fell
behind the read cursor) - so nul-terminating a plain token silently
overwrote the very whitespace byte the next iteration's `SKIP-WS` was
relying on to detect a boundary to skip. `SKIP-WS` then found a NUL
where it expected a space, didn't recognize it as whitespace, and left
the read cursor sitting exactly on that byte - so the next token
started life already nul-terminated, i.e. empty. Fixed by explicitly
advancing the read cursor past the separator after each token,
independent of the write cursor - the same thing the old tokenizer did
explicitly, which the rewrite had dropped by assuming SCAN-TOKEN's own
internal advances would cover it (they cover consuming a token's own
content, not the boundary after it).

### Real bug #2: leftover duplicate code from a bad edit

While applying the above fix, an `str_replace` left a stray, duplicate
tail of the old function body appended after the new one - two
mismatched `REPEAT`s, breaking the word's control-flow structure
entirely. Caught immediately: loading `shell.4` alone crashed with no
"OK" even for the load itself. Fixed by viewing the file directly
around the edit and rewriting the whole word cleanly rather than
patching around the leftover fragment.

### Quote-awareness for operator/builtin recognition

Stripping quote marks loses the information that a token was quoted -
without tracking that separately, a literal `'<'` typed by the user
would come out of `TOKENIZE` looking identical to a real, unquoted `<`
redirection operator, and `PARSE-REDIRECTIONS` would wrongly treat it
as one. Fixed with a parallel byte array, `ARGV-QUOTED` (one flag per
`ARGV` entry, set whenever any part of that token passed through a
quote or escape), and a `ARGV-QUOTED@` accessor. `PARSE-REDIRECTIONS`,
`AT-PIPE?` (used by `SPLIT-PIPE`), and `DISPATCH`'s builtin-name
checks were all updated to require "not quoted" alongside their
existing string match, so `echo a '<' b`, `echo a '|' b`, and
`'cd' /tmp` all now behave correctly - the quoted token is treated as
a literal argument (or, for `'cd'`, as an external command name to
search `$PATH` for, which doesn't exist as a real binary and correctly
fails with exit 127) rather than the operator/builtin it happens to
spell out.

Verified end-to-end via `relfsh -c`: single quotes preserving embedded
spaces and combining correctly with adjacent unquoted arguments,
backslash-escaping a space and a pipe character, double-quote escapes
producing a literal embedded `"`, unterminated quotes degrading
gracefully rather than crashing, and quoting composing correctly with
the existing pipe support (`echo 'hello world' | wc -w`).
`tests/shell/run-quote` (6 assertions) locks all of this in - 24
assertions across 8 files now, all passing on both x86-64 and i386.

### What this iteration deliberately did NOT do

- **`$` (variable expansion) or `` ` `` (command substitution) inside
  double quotes** - `COPY-DOUBLE-QUOTED` only recognizes `\"` and `\\`
  as escapes; `$`/`` ` `` have no special meaning yet at all, quoted or
  not, since there's no expansion mechanism to guard.
- **Multi-line quote continuation** - an unterminated quote just
  consumes to the end of the current input line; a real shell would
  prompt for more input (a secondary `>` prompt) until the quote
  closes.
- **Combining pipes and redirection on one line** - still the same
  Iteration 7 scope limit; quoting doesn't change that decision, since
  the two features remain independently untested together regardless
  of what's inside their arguments.

## Iteration 9: $VAR expansion

Goal: the more consequential of the two remaining gaps flagged at the
end of Iteration 8 - variable expansion, which makes the shell
substantially more useful day-to-day (control structures matter more
for scripting than interactive use, and were judged lower priority).

### New primitive: `GETPID`

A single, trivial addition (`GETPID ( --- pid )`, a direct `getpid()`
wrapper with no arguments and no string handling at all) needed for
`$$`. Added, rebootstrapped, and regression-checked using the same
established workflow as every other primitive this project has added.

### `EXPAND-VAR`: `$NAME`, `${NAME}`, `$?`, `$$`

Integrated into the tokenizer as a fifth dispatch case alongside the
existing quote/escape handling - `SCAN-TOKEN` (outside quotes) and
`COPY-DOUBLE-QUOTED` (inside double quotes) both now recognize `$` and
call `EXPAND-VAR`; `COPY-SINGLE-QUOTED` still never looks for it at
all, so single quotes remain fully literal, matching POSIX. `$NAME`
reads a maximal run of POSIX-portable name characters (letters,
digits, underscore, via a new `NAME-CHAR?` predicate) and looks it up
via `GETENV` - there's no separate "shell variable" concept here,
same simplification as everywhere else in this shell (`export` already
went straight to `SETENV`). `${NAME}` is the same lookup with explicit
`{`/`}` delimiters, useful for e.g. `${FOO}suffix` where the bare form
would otherwise consume "suffix" as part of the name. `$?` substitutes
`LAST-STATUS` and `$$` substitutes `GETPID`, both formatted via a new
`EMIT-DECIMAL` (an explicit divide/mod digit-extraction loop, chosen
over the pictured-numeric-output words `<#`/`#S`/`#>` to keep this
self-contained and directly verifiable, consistent with this
project's general preference for explicit, easy-to-verify constructs
over relying on words whose exact stack behavior hasn't been directly
tested here yet). A `$` not followed by anything that forms a valid
expansion (not a name-start character, not `?`/`$`/`{`) is left as a
literal `$`, matching POSIX's own fallback.

### Real bug found and fixed: reused a `DUP` pattern in the wrong context

Wiring `$` recognition into `COPY-DOUBLE-QUOTED` initially wrote `DUP
36 = IF ... ELSE ...` inside that word's existing `ELSE` branch (the
"character wasn't a backslash" case) - copying the cascading-`DUP`
dispatch style already proven correct in both `DISPATCH` and
`SCAN-TOKEN` itself. But this specific `ELSE` branch is different:
the *outer* `TOK-POS @ C@ 92 = IF` already fully consumed the fetched
character via `=` before branching, so nothing was left on the stack
to `DUP` - `DUP` there would duplicate whatever unrelated value
happened to be sitting underneath from earlier, unconnected code. The
cascading-`DUP` pattern only works when a value is deliberately kept
on the stack *specifically* for the next check to consume, which was
true in `DISPATCH`/`SCAN-TOKEN` (each `DUP N = IF...THEN` explicitly
preserves the original for the next comparison) but not true here,
where the outer condition had already resolved and moved on. Fixed by
re-fetching the character fresh (`TOK-POS @ C@ 36 = IF ...`) instead
of assuming something reusable was on the stack - a reminder that a
pattern being correct in one place doesn't mean it transfers safely to
a structurally different call site without checking what's actually on
the stack there.

**Also hit the same `>=` mistake as Iteration 7** (this kernel has no
`>=` word) while writing `NAME-CHAR?`'s range checks - by now a
familiar-enough mistake that it was caught and fixed (`DUP 48 < 0=` in
place of `DUP 48 >=`) in the same pass as the load-and-test cycle,
rather than needing a separate debugging round.

### Quote-awareness extends to expansion results too

`EXPAND-VAR` sets `TOK-WAS-QUOTED?` the same way quoting/escaping do,
so an expanded value that happens to match an operator character isn't
re-interpreted as one downstream - verified directly: `export
PIPECHAR=|` then `echo a $PIPECHAR b` prints `a | b` literally rather
than starting a pipeline, exactly the same reasoning `ARGV-QUOTED`
already provides for literal quoted operators (Iteration 8).

Verified end-to-end via `relfsh`: `$VAR` and `${VAR}` both expanding
correctly (including the delimiter case bare `$VAR` can't handle),
an unset variable expanding to empty rather than erroring, `$?`
correctly reflecting both a failing and a subsequent succeeding
command within one session, `$$` producing a plausible positive
integer PID, and the pipe-character quote-awareness case above.
`tests/shell/run-expand` (7 assertions) locks all of this in - 31
assertions across 9 files now, all passing on both x86-64 and i386.

### What this iteration deliberately did NOT do

- **Word-splitting of an unquoted expansion's result.** A real shell
  splits an unquoted `$VAR` containing spaces into multiple arguments
  (subject to `$IFS`); here the entire expanded value always becomes
  part of whichever single token it's embedded in, regardless of
  whitespace inside it or whether it was quoted. This is a real,
  user-visible difference from POSIX behavior, not just an omitted
  edge case - `echo $VAR` where `VAR="a b c"` produces one argument
  here (`"a b c"`), not three, unlike a real shell's default behavior.
- **`${VAR:-default}`/`${VAR:=default}`/`${VAR:+alt}`/`${#VAR}`**
  and any other parameter-expansion modifier - only bare `${NAME}`
  lookup is supported.
- **Positional parameters** (`$1`, `$@`, `$#`, `$0`) - there's no
  concept of "this invocation's own arguments" to expand yet, since
  there's no script-file execution or function-call mechanism for
  them to refer to.
- **Command substitution** (`` $(...) `` or `` `...` ``) - unrelated
  to parameter expansion but the other major "$"-adjacent POSIX
  feature; not attempted.
- **Nested/recursive expansion** (a variable's value itself containing
  `$OTHERVAR`) - `TYPE0-TO-TOK` copies `GETENV`'s result verbatim,
  with no re-scanning for further `$` sequences within it. This
  matches POSIX for single-quoted-at-source values anyway, but a real
  shell's parameter-value substitution semantics here are more subtle
  than what's implemented.

## Iteration 10: if/then/else/fi

Goal: the last major piece flagged at the end of Iteration 9 - a basic
control structure, the thing that starts to make this shell usable
for actual scripting rather than just interactive one-liners.

### Scope decision: `if` only, not `while`/`for`, and no nesting

`if` only ever needs to run each body line *once*, as it's read from
stdin - so a streaming design works: read a line, check whether it's
`then`/`else`/`fi`, and if not, either run it immediately or discard
it depending on which branch is currently active. `while`/`for` are
fundamentally different: a loop body has to be re-run multiple times,
which means it can't just be streamed and discarded after one read -
it needs to be buffered somewhere stable (stdin is a one-pass stream)
and re-scanned each iteration. That's a genuinely different mechanism,
not a small extension of `if`'s own approach, so it's deliberately
deferred rather than attempted here.

Nesting (a body containing another `if`) is also deliberately not
supported in v0.5. The reason is concrete, not just "not gotten to
yet": `DO-IF` uses a handful of global variables (`COND-TRUE?`,
`ARGV-SHIFT`/`ARGC-SHIFT`) to track its own state, and a body line
that triggers a *recursive* `DO-IF` call would overwrite those same
globals out from under the outer call once the inner one returns -
this isn't merely "unrecognized," it's actively broken if attempted.
Proper nesting support would need each `DO-IF` invocation to save and
restore its own state (or use its own private storage) rather than
sharing single global variables - real, additional work, not a free
side effect of the current design.

### `DO-IF`'s design: streaming, not buffer-and-replay

The condition (whatever follows `if` on the same line) is extracted
via a new `SHIFT-ARGV-DOWN`/`ARGV-SHIFT` (copies `ARGV[1..]` into a
fresh array, dropping the `if` token itself - same copy-don't-shift
discipline as `SPLIT-PIPE`/`PARSE-REDIRECTIONS`) and run through the
normal command path via a new `RUN-SHIFTED`, so `if cmd1 | cmd2` as a
condition works correctly too. `then`/`else`/`fi` are matched with a
new `LINE-IS?` (checks `ARGV[0]` against a literal, respecting
`ARGV-QUOTED` the same way `DISPATCH`'s builtin checks do - so a
quoted `'if'` is correctly treated as a literal argument, not the
keyword, verified directly). Body lines are read one at a time via a
new `READ-LINE-INTO-ARGV` (just `ACCEPT` + `TOKENIZE`, no
redirect/pipe parsing or dispatch yet - that's deferred to whichever
branch actually decides to run the line) and either executed
immediately or silently discarded depending on whether the condition
was true and which section (`then` vs `else`) is currently active. A
missing `then` prints an error and abandons the `if` statement
gracefully rather than hanging or crashing - a real shell would
instead treat the unclosed construct as needing more input (a
secondary prompt); that's not attempted here.

### A genuine mutual-dependency problem, solved with a deferred word

`RUN-TOKENIZED` (the word that inspects already-tokenized `ARGV`/`ARGC`
and either dispatches to a builtin, runs an external command, or now
also checks for `if`) needs to call `DO-IF`. But `DO-IF` needs to run
its own body lines through that same "act on tokenized ARGV" logic -
a genuine mutual dependency, not resolvable by simply reordering the
two definitions (Forth requires define-before-use). Resolved with the
standard deferred-word pattern: a `RUN-TOKENIZED-XT` variable and a
thin `RUN-TOKENIZED-CALL` stub (`RUN-TOKENIZED-XT @ EXECUTE`) defined
early, used by everything that needs to call "the real
`RUN-TOKENIZED`" before it exists yet; once `RUN-TOKENIZED` itself is
finally defined, `' RUN-TOKENIZED RUN-TOKENIZED-XT !` patches the
variable to its actual execution token. This is the first use of `'`
(tick)/`EXECUTE` anywhere in `shell.4` - confirmed both exist in the
base kernel (they're part of the CORE test suite, "TESTING ' ['] FIND
EXECUTE...") before committing to this design.

Verified end-to-end via `relfsh`/piped scripts: a true condition
taking the `then` branch, a false condition correctly skipping it and
the shell continuing normally with whatever comes after `fi`, a false
condition taking the `else` branch, a multi-line body running every
line in order, the condition itself being a real external command
(`test 1 -eq 1`, not just `true`/`false`), the `if` statement's own
exit status correctly reflecting the last command actually run inside
the taken branch (matching real shell semantics - `if true; then
false; fi; echo $?` reports `1`), a quoted `'if'` staying a literal
argument rather than triggering the parser, and the missing-`then`
error path degrading gracefully. `tests/shell/run-if` (8 assertions)
locks all of this in - 39 assertions across 10 files now, all passing
on both x86-64 and i386. No engine changes this iteration; purely
`shell.4`-level, like Iteration 8's quoting work.

### What this iteration deliberately did NOT do

- **`while`/`until`/`for` loops** - see the buffer-and-replay
  discussion above; a genuinely different mechanism from `if`'s
  streaming approach, not attempted here.
- **Nesting** - see above; would need per-invocation state rather than
  shared globals.
- **`;`-separated compound forms** (`if cmd; then ...; fi` on fewer
  lines) - `then`/`else`/`fi` must each be alone on their own line;
  there's still no `;` statement separator anywhere in this shell.
- **Multi-line continuation for an unclosed construct** - a missing
  `then` (or, if it existed, an unclosed loop) just errors out
  immediately rather than prompting for more input.
- **`elif`** - only a single `if`/`then`/`else`/`fi`, no
  `elif`/`then` chains; achievable today only by nesting a second `if`
  inside the `else` body, which (per above) isn't supported yet either.

## Iteration 11: while/do/done

Goal: the loop mechanism explicitly flagged as unfinished business at
the end of Iteration 10 - "the buffer-and-replay mechanism" a `while`
loop needs, unlike `if`'s streaming approach.

### The core design problem, worked through before writing any code

A `while` loop's condition and body have to run more than once, but
stdin is a one-pass stream - a line, once read, is gone. The naive fix
(save the *already-tokenized* `ARGV` from the first reading, re-run
that each iteration) turns out to be nearly useless: by the time
`RUN-TOKENIZED` detects the `while` keyword, `TOKENIZE` has *already*
destructively expanded any `$VAR`/`$?`/`$$` in that line, once, and
in-place. A condition like `while test $? -eq 0` - a completely
ordinary pattern - would freeze `$?`'s value from *before the loop
even started* and never update, making the loop either never run or
run forever regardless of what actually happens each iteration. Real
loop conditions need genuinely fresh re-evaluation, including fresh
expansion, every single time.

The fix: capture the *raw*, pre-`TOKENIZE` text of the condition and
each body line - before any expansion happens to it - into stable
storage, and re-copy-and-re-`TOKENIZE` that same raw text into
`LINE-BUF` fresh on every iteration. Since `TOKENIZE` already performs
expansion as part of tokenizing, "re-tokenize the raw text" and
"re-expand it" are the same operation - no separate expansion pass
needed once the raw-capture problem is solved.

This required a small, mechanical change reaching further back than
`while` itself: both `RUN-LINE` and `READ-LINE-INTO-ARGV` (the two
places a line ever gets read) now stash a copy of the just-`ACCEPT`ed
raw bytes, into a new `RAW-LINE-BUF`, *before* calling `TOKENIZE` -
otherwise there'd be no raw text left to capture by the time `while`
is even recognized.

### `SAVE-WHILE-COND`/`APPEND-RAW-LINE-TO-BODY`/`DO-WHILE`

`SAVE-WHILE-COND` independently re-scans `RAW-LINE-BUF` (skipping its
own leading whitespace, the literal `while`, and more whitespace) to
find where the condition text actually starts within the *raw* line -
deliberately not relying on `ARGV`'s own (post-`TOKENIZE`) positions,
since those describe the *compacted, expanded* form, not the raw
source. The extracted substring is saved into `WHILE-COND-BUF`.
`APPEND-RAW-LINE-TO-BODY` collects each raw body line (again, straight
from `RAW-LINE-BUF`, not `ARGV`) into `WHILE-BODY-BUF` as a sequence
of NUL-terminated strings, one after another - a flat list, walked
later by `DO-WHILE-BODY` via a running byte offset (`CSTRLEN` on each
entry to find where the next one starts, same technique used for
C-string handling throughout `shell.4` already).

`DO-WHILE` itself: save the raw condition, expect `do` on the next
line (else error out gracefully, same fallback as `if`'s missing
`then`), collect body lines (raw) until `done`, then loop: copy the
saved condition text into `LINE-BUF`, `TOKENIZE` it (fresh expansion,
every time), run it, check `LAST-STATUS`, and if true, run every
stored body line once (each one *also* freshly re-tokenized via
`RUN-STORED-LINE`) before looping back to re-check the condition
again.

### A genuinely thorough verification, since a subtly-wrong loop
### implementation could easily *look* right on a single pass

Getting real multi-iteration coverage without arithmetic or command
substitution took a specific, deliberate test design: a **3-file
shift-register** trick (three lock files; each pass removes the front
one and renames the other two down one slot via `mv`), which only
terminates after exactly 3 passes *and only if the condition is
genuinely re-checked against real, current filesystem state each
time* - a frozen condition would either never terminate or terminate
immediately, not after exactly 3. Verified this gives exactly 3
iterations. Also verified the specific failure mode this whole
architecture exists to avoid: a condition built entirely from `$?`
(`while test $? -eq 0`, driven by the last body command's own exit
status) correctly drives exactly 3 iterations too - directly
confirming fresh re-expansion, not just re-execution of static text.
Also verified: a single-iteration loop correctly stopping and control
returning to normal line processing afterward, quote-awareness (a
quoted `'while'` stays a literal argument via the same `LINE-IS?`
mechanism `if` already uses), and the missing-`do` error path.
`tests/shell/run-while` (6 assertions) locks all of this in - 45
assertions across 11 files now, all passing on both x86-64 and i386.
No engine changes this iteration; purely `shell.4`-level.

### What this iteration deliberately did NOT do

- **`for`/`until` loops** - `until` is a trivial variant of the same
  mechanism (invert the condition check); `for x in ...` is a
  different shape entirely (iterating over a word list rather than
  re-checking a condition) and wasn't attempted.
- **Nesting** - same limitation as `if` (Iteration 10), for the same
  reason: shared global state (`WHILE-COND-BUF`, `WHILE-BODY-BUF`,
  etc.) that a recursive call would corrupt. A `while` loop containing
  an `if` (or vice versa) is untested and likely broken.
- **`break`/`continue`** - no way to exit a loop early or skip to the
  next iteration from within the body.
- **A loop-iteration cap or other infinite-loop safeguard** - a
  buggy or intentional `while true; do ...; done` will run forever,
  same as in a real shell (terminated by Ctrl-C or external
  intervention, not by this shell itself). Not adding an artificial
  cap was a deliberate choice to match real shell behavior rather than
  diverge from it.
- **`WHILE-BODY-BUF`'s fixed size** - a 4096-byte buffer, guarded with
  a bounds check (a body line that would overflow it is silently
  dropped rather than corrupting adjacent dictionary memory - the
  first draft had no such check at all, a real memory-safety gap
  caught and fixed while writing up this entry rather than left as
  just a documented limitation, given how much earlier damage this
  session's accidental buffer overflows caused). Fine for any
  realistic interactive use so far, but a dropped line means that
  iteration's body silently runs incomplete, with no error reported.

## Iteration 12: unset

Goal: the smaller, straightforward half of "extended environment
variable support" requested to follow up on Iteration 11's shell
work - discussed and offered at the end of that session, since
`export` had no way to reverse itself.

### `UNSETENV` primitive + `DO-UNSET` builtin

A single, trivial engine primitive (`UNSETENV ( c-addr --- ior )`,
wrapping `unsetenv()` directly - no string-length handling needed at
all, matching how simple `GETPID` was), added and verified with the
same established rebootstrap-and-regression-check workflow as every
primitive before it. `DO-UNSET` in `shell.4` follows the exact shape
of `DO-CD`/`DO-EXPORT`: checks for an argument, calls `UNSETENV`, sets
`LAST-STATUS` from the result. Wired into `DISPATCH` alongside the
other builtins. Verified directly: export a variable, confirm it
expands, `unset` it, confirm the expansion is now empty and a
subsequently-run external `env` no longer lists it in its inherited
environment either. Unsetting a name that was never set is not
treated as an error, matching real shells.

`tests/shell/run-unset` (4 assertions) locks this in - 49 assertions
across 12 files now, all passing on both x86-64 and i386.

### A process note, not a design note

This iteration was extracted from a single working session that also
produced a substantial, not-yet-working attempt at `$(...)` command
substitution. Rather than commit both together (mixing solid,
verified work with a known, unresolved segfault), the command-
substitution code was cleanly separated back out of `shell.4` before
this commit - `unset` is complete and independently valuable on its
own, and doesn't need to wait on the harder problem. The command-
substitution work is preserved separately and picked back up as its
own, later effort - see the next section of this file once that's
resolved, or the commit history if it isn't yet.

## Iteration 13: $(...) command substitution

Goal: the harder half of "extended environment variable support" -
picked back up after Iteration 12 shipped `unset` alone and set this
work aside as a documented, not-yet-working WIP.

### The architectural problem

`$(...)` is encountered *during* the outer line's own tokenization
(`SCAN-TOKEN`/`COPY-DOUBLE-QUOTED` call `EXPAND-VAR`, which now also
handles `$(`, while `LINE-BUF`/`ARGV`/`ARGC`/`TOK-POS`/`TOK-END`/
`TOK-OUT` are all still mid-scan for the *outer* line). Reusing the
main `TOKENIZE`/`ARGV`/`LINE-BUF` for the *inner* substituted
command's own parsing would corrupt that in-progress outer state, so
`EXPAND-CMDSUB` uses an entirely separate, dedicated set of buffers
(`CMDSUB-LINE-BUF`, `CMDSUB-ARGV`, `CMDSUB-ARGC`) and a small,
deliberately simple whitespace-only tokenizer (`CMDSUB-TOKENIZE`) for
the inner command's text - no quoting, escaping, expansion, pipes, or
redirection *within* a `$(...)` command in v0.8, and no nested
`$(...)` either (the first unescaped `)` found closes it) - the same
kind of scope limit already accepted for if/while nesting.

`RUN-CMDSUB-CHILD` needs `COPY-ARGV`/`RUN-CHILD`, both defined much
later in the file (pipe/path-search sections) - broken via the same
deferred-word pattern already used for `RUN-TOKENIZED-CALL`: a stub
defined early, patched to the real word's execution token once it's
available.

The substituted command runs in a forked child (stdout redirected
into a pipe, same `PIPE`/`FORK`/`DUP2` shape as `RUN-PIPELINE`), the
parent reads everything from the pipe in a loop, strips all trailing
newlines (matching POSIX - internal newlines are preserved), and
splices the result into the token being built via the same
`EMIT-TOK-CHAR` path `$VAR` expansion already uses - no further
expansion or quote-processing is applied to the captured output
itself. Only external commands are supported inside `$(...)` (same
scope limit as pipe segments not supporting builtins either).

### The bug, and why it took so long to find

`CMDSUB-TOKENIZE` segfaulted on even the simplest input
(`$(echo hi)`), and a careful hand-trace of its logic looked correct -
every individual piece tested fine in isolation. The actual bug: `CS-
END` was stored as `CMDSUB-LINE-BUF + u` (an absolute address), while
`CS-POS` is a plain offset (0, 1, 2, ...) used consistently everywhere
else in the function. `CS-POS @ CS-END @ <` was therefore comparing a
small offset against a huge address - always true, so the bounds
check never actually bounded anything, and the scan ran past the
buffer until it happened to hit a byte in whatever followed that
looked like whitespace. Fix: `CS-END` stores the plain length `u`
directly, matching `CS-POS`'s own convention (`CMDSUB-LINE-BUF` is
added explicitly at every point of use, same as `CS-POS` already was).

Two things about *how* this was found, worth recording since they cost
real time: an isolated "mini-test" reproducing only part of the outer
loop (omitting the inner scan that advances the cursor) hung forever -
not a new bug, just an incomplete diagnostic mirroring the function
rather than exercising the real one. And once a proper, complete
diagnostic was written, typing it directly at `relf`'s interactive
stdin threw a spurious `Undefined word TH` - an artifact of a long
line hitting a different line-buffer path than file-`INCLUDED`
loading, unrelated to the actual bug. The diagnostic that actually
worked was a small standalone word, loaded via `INCLUDED` (matching
how `shell.4` itself loads) rather than typed interactively, with
`."` trace output at each step - printing the loop's own state showed
`CS-POS` overshooting its expected stopping point immediately, which
led straight to the address/offset mismatch above.

### Verified end-to-end via `relfsh`

- `echo $(echo hello)` → `hello`
- `echo pre_$(echo mid)_post` → `pre_mid_post` (concatenation with
  literal text, via the same token-building path as `${VAR}suffix`)
- `echo $(echo hello)_$X` → `hello_world` (concatenation with `$VAR`)
- `echo '$(echo literal)'` → literal, unexpanded (single quotes)
- `echo "$(echo quoted)"` → `quoted` (still substituted inside double
  quotes)
- `echo $(pwd)` → resolves via `$PATH` like any external command
- A script printing `line1\nline2\n` spliced as `START-$(...)-END`
  produces `START-line1\nline2-END` - internal newline kept, only the
  trailing one stripped.

`tests/shell/run-cmdsub` (7 assertions) locks all of this in - 56
assertions across 13 files now, all passing on both x86-64 and i386.

### Deliberate v0.8 scope limits

No quoting/escaping/expansion/pipes/redirection *within* a `$(...)`
command's own text (a bare whitespace split only), no nested `$(...)`,
and no builtins runnable inside `$(...)` (external commands only) -
all matching established patterns elsewhere in this shell rather than
being newly-invented gaps.

### Performance benchmark: env-variable manipulations (relfsh vs bash 5.2.21)

An earlier session benchmarked cold-start and sustained throughput for
`pwd` (builtin dispatch), `/bin/true` (fork+exec), a pipeline, and a
`while` loop, but that benchmark's numbers were never actually
recorded in this file (they only exist in that session's own
transcript) - this entry is the first performance benchmark to make
it into `PROGRESS.md`, and targets the specific workloads added by
Iterations 12 and 13: `export`, `unset`, `$VAR` expansion, and
`$(...)` command substitution. Methodology: single amortized session
per run (script piped via stdin, not `-c`, so `relf`/`shell.4`
compilation cost is paid once and N operations run inside that one
process), 3 runs averaged, cold-start baseline (a script containing
only `exit`) subtracted out to isolate true per-operation cost. relfsh
baseline: ~55ms (`shell.4` is recompiled from source on every
invocation - the same root cause identified in that earlier,
unrecorded session). bash baseline: ~3ms.

| Workload | relfsh (per-op) | bash (per-op) | ratio |
|---|---|---|---|
| `export VAR=value` ×2000 (builtin, no fork) | ~16 μs | ~1.5 μs | ~11x |
| `pwd $VAR` ×2000 (builtin + `$VAR` expansion) | ~14.5 μs | ~1.5 μs | ~10x |
| `unset VAR` ×2000 (builtin, no fork) | ~12.5 μs | ~1.5 μs | ~8x |
| `pwd $(pwd)` ×200 (real fork+pipe+capture) | ~915 μs | ~260 μs | ~3.5x |

**Pure builtin dispatch stays in a low-microsecond regime** matching
that earlier session's finding of ~10μs/op for bare `pwd`. Adding
`$VAR` expansion on top of a builtin call costs roughly **+4-5μs/op**
(14.5μs vs ~10μs) - real, but small, and still nowhere near
perceptible interactively. `unset` (~12.5μs) is a little cheaper than
`export` (~16μs): `UNSETENV` is a direct call, while `DO-EXPORT` first
scans the argument string for `=` before calling `SETENV`. The ~8-11x
ratio against bash across all three builtin-based workloads is
consistent with that earlier session's finding that Forth-interpreter
dispatch overhead is real but stays imperceptible in absolute terms
(tens of microseconds, not milliseconds).

`$(...)` command substitution is **syscall/fork-dominated**, similar
in character to that earlier session's pipe and fork+exec figures, and
the 3.5x gap here isn't purely interpreter overhead - it reflects a
genuine asymmetry rather than raw slowness: `relfsh`'s `$(...)` only
supports *external* commands (the documented v0.8 scope limit from
earlier in this iteration), so `$(pwd)` really execs `/bin/pwd`, while
bash can run its own *internal* `pwd` builtin inside the forked
subshell instead. Against that earlier session's bare fork+exec figure
(~750μs/op for `/bin/true`, syscall-dominated and near 1:1 parity with
bash), the pipe-creation/read-loop/splice machinery `$(...)` adds on
top costs roughly **+165μs/op** for relfsh.


## Assessment: reusing mrsh's test suite

Investigated https://github.com/emersion/mrsh (a minimal but far more
complete POSIX shell than `shell.4`) to see whether its test suite
could be reused directly.

**Not reusable wholesale.** Every one of mrsh's top-level `test/*.sh`
files (`case.sh`, `for.sh`, `function.sh`, `loop.sh`, `subshell.sh`,
`word.sh`, `async.sh`, `read.sh`, `readonly.sh`, `return.sh`, etc.)
depends on features `shell.4` doesn't have at all: `case`, `for`,
shell functions, subshells (`(...)`) and brace groups, background jobs
(`&`/`wait`/`$!`), `break`/`continue`, the `[ ]` test builtin,
arithmetic expansion (`$((...))`), tilde expansion, `IFS`-based field
splitting, positional parameters (`$@`/`$*`/`$#`/`set`), parameter-
expansion modifiers (`${VAR:-default}` etc.), backquote command
substitution, and multi-line/nested `$(...)`. mrsh's own test harness
also runs each script as a file argument and differential-tests it
against a reference shell (`"$MRSH" "$testcase"` vs `"$REF_SH"
"$testcase"`) rather than piping a script to stdin the way this
project's own harness does - a structural mismatch on top of the
feature-scope one.

The `test/conformance/` subdirectory is a better structural fit (one
file per POSIX spec section, `.stdout` files for exact-diff comparison,
`.fail.sh`/`.undefined.sh` naming for known-failing or
spec-undefined-behavior cases) but has only one test registered as
passing (`2.2-quoted-characters.sh`) plus a handful of `.fail`/
`.undefined` ones testing alias-expansion and backquote-nesting edge
cases that don't apply here (`shell.4` has neither aliases nor
backquotes). Even that one passing file mixes arithmetic expansion,
recursive `$(echo $(...))`, and backquote substitution in with the
parts that do overlap.

**What genuinely transferred**: the subset of
`2.2-quoted-characters.sh` that only exercises quoting/escaping
behavior `shell.4` actually implements - outside-quote backslash-
escaping of a run of shell metacharacters, single quotes keeping `$`,
backquote, and backslash literal, and double quotes keeping a literal
single quote alongside an escaped double quote. Verified directly
against `relfsh` before adapting (each of the three isolated lines
produces the expected output), then folded into `tests/shell/run-quote`
as three new assertions using `printf` as an external command (mrsh's
own approach, rather than the `echo` builtin), with a comment crediting
mrsh and explaining why the rest of that test doesn't transfer.
`run-quote` is now 9 assertions (up from 6) - 59 assertions across 13
files total, all still passing on both x86-64 and i386.

The honest summary: mrsh targets a much more complete shell than
`shell.4` currently is, so its test suite mostly tests things that
don't exist here yet rather than things that are broken. That's a
reasonable roadmap of what a next round of features could look like
(functions, `case`, `for`, arithmetic, positional parameters, IFS
splitting) more than it is a source of tests to reuse today.

## Iteration 14: adopt mrsh's test suite as goal 8, establish baseline

Goal: turn last session's assessment ("mrsh's tests aren't reusable
wholesale") into a formal, trackable goal - vendor mrsh's actual test
files unmodified, build a harness that runs them against `relfsh`,
and record an honest baseline to work against in future iterations.
See `GOALS.md`'s goal 8 for the full phased roadmap this produced.

### What got built

`tests/mrsh-suite/vendor/` - mrsh's `test/*.sh` and
`test/conformance/*.sh`/`*.stdout` files, copied verbatim at commit
`4c81598721bc5eeb28f9faa818b3102d0471b7f6` (2024-03-10), plus mrsh's
own MIT `LICENSE` (included per its terms) and a `README.md`
explaining provenance and - importantly - that these files must not
be hand-edited to make them pass. mrsh's own `harness.sh`/
`meson.build` files (its build/test-running tooling, not test
content) were deliberately not vendored.

`tests/mrsh-suite/run.sh` - a new harness adapted from mrsh's own two
harnesses (`test/harness.sh` and `test/conformance/harness.sh`),
categorized the same way mrsh's own `meson.build` categorizes them:

- **Differential tests** (all of `vendor/*.sh`): run the same script
  through `relfsh` and through `bash` (as the reference shell),
  PASS only if stdout and exit status both match - stderr is
  intentionally ignored, matching mrsh's own harness.
- **Conformance fixed-output test** (`2.2-quoted-characters.sh`):
  compared against its own vendored `.stdout` file, PASS requires
  exit status 0 and matching output.
- **Conformance expected-failure tests** (`*.fail.sh`): PASS means
  `relfsh`'s own exit status is nonzero - i.e. it correctly rejects
  invalid input, matching what mrsh's `meson.build` marks
  `should_fail: true`.
- **Conformance undefined-behavior tests** (`*.undefined.sh`): not
  scored at all - POSIX doesn't specify a required result for these,
  matching mrsh's own gated (`test-undefined-behavior` option)
  treatment.

`relfsh` has no file-argument invocation yet (only `-c`, interactive,
and piped stdin), so each vendored script is fed to it via
`< testcase` rather than `relfsh testcase`; `bash` is invoked the
standard way (`bash testcase`). Noted in the harness's own comments as
a known, temporary asymmetry - functionally equivalent for every
vendored test here (none inspect `$0` or script arguments in ways
that would affect output comparison), but real file-argument support
is itself goal 8's first roadmap item.

### The baseline

```
1 passed, 20 failed, 3 skipped (not scored)
```

The one pass (`2.2.3-alias-expansion.fail.sh`) is hollow - it only
"passes" because `shell.4` has no `alias` at all, so PATH search
fails outright (exit 127) before the test's actual question (whether
alias expansion incorrectly applies when finding `$(...)`'s closing
paren) is ever reached. Recorded as a real result of the scoring
criteria, not hidden, but not claimed as a genuine conformance win
either.

**Four of the twenty failures are segfaults, not wrong output**:
`async.sh` (background jobs, `&`), `function.sh` (shell functions),
`pipeline.sh` (subshells/brace groups inside a pipeline), and
`read.sh` (the `read` builtin, likely combined with `while` reading
piped stdin) all crash `relfsh` outright. This is worth treating as
an early, independent priority (phase A in goal 8) - a shell should
fail cleanly on syntax it doesn't support, regardless of how minimal
its scope is; a crash is a correctness bug on its own, separate from
whichever feature is actually missing.

### The roadmap

Broken into seven phases (A through G) in `GOALS.md`'s goal 8 entry,
roughly ordered by dependency: infrastructure to run the suite at all
and crash-hardening (A); foundational semantics needed almost
everywhere, most importantly shell-local (non-exported) variable
assignment as a standalone statement, which `shell.4` currently has
*no* mechanism for at all outside `export` (B); control structures -
`for`, `case`, functions, `break`/`continue` (C); expansions -
positional parameters, parameter-expansion modifiers, arithmetic,
tilde, `IFS` field splitting (D); command substitution completeness -
nesting, backquotes, and a `$(...)` body that runs the real tokenizer
instead of today's bare whitespace-split (E, revisiting the
"save/restore outer tokenizer state" approach set aside as too
complex during Iteration 13); remaining builtins - `[`/`test`, `read`,
`readonly`, `getopts`, background jobs, `alias`, `ulimit`, etc. (F);
and the remaining conformance edge cases (G). Each phase is expected
to be its own multi-iteration effort, comparable in scope to phases 5
or 6 of this project's own engine work - this is a large goal, set
deliberately rather than attempted in one pass.

`tests/mrsh-suite/run.sh` is the acceptance criterion going forward -
re-run it after each future phase/iteration and let the pass count
climb honestly, the same way `tests/run_tests.sh` and
`tests/shell/run-all` already track progress elsewhere in this
project.

## Iteration 15: goal 8, phase A - crash-hardening

Goal: the first concrete step on goal 8's roadmap - fix the four
segfaults found while establishing Iteration 14's baseline, before
attempting any of the actual missing features.

### Root cause: this kernel's DO/LOOP doesn't skip a degenerate range

ANS Forth leaves `start = limit` at `DO` as implementation-defined,
but the common, expected behavior (and the one every piece of
`shell.4` code written so far implicitly assumed) is that it runs
*zero* iterations - "already done." This kernel does the opposite: it
wraps around and runs through the *entire unsigned range* instead.
Confirmed directly with two minimal, standalone words loaded via
`INCLUDED` (typing long or degenerate cases directly at `relf`'s
interactive stdin turned out to be its own separate pitfall in
Iteration 13 - avoided here from the start): `0 0 DO ... LOOP` and
`1 1 DO ... LOOP` (an equal but nonzero start/limit) both loop
indefinitely rather than stopping immediately, confirming this is a
general "index equals limit at entry" gotcha, not something specific
to zero.

An earlier debugging attempt at this exact question (during Iteration
13's `CMDSUB-TOKENIZE` bug) tested `0 0 DO ... LOOP` in isolation and
concluded it correctly ran zero iterations - that conclusion was
itself wrong, an artifact of the test process exiting before ever
reaching the loop (the "confirming" output was suspiciously short).
Worth remembering: a **short, clean-looking output isn't the same as
a correct one** - re-run to make sure the process actually got where
it was supposed to before trusting silence as a "pass."

### Reproducing async.sh's segfault down to one command

`async.sh`'s tokenizer stage produced `kill: unknown signal name $?`
in stderr before crashing - a strong clue, since `async.sh` has no
line that should invoke `kill` at all. The explanation: **`shell.4`
has no `#` comment support whatsoever** - a `#`-prefixed line is
tokenized as an ordinary command (`ARGV[0]` literally starting with
`#`), which normally just fails PATH search (127) harmlessly. But one
of `async.sh`'s commented-out lines happens to contain a real
`$(kill -l $?)` construct, and `$(...)` triggers during tokenization
regardless of what the token it's embedded in was "supposed" to mean -
so that substitution actually ran, calling the real `kill` binary
(which errored, since `$?` inside `$(...)` isn't expanded by the
simplified `CMDSUB-TOKENIZE` - a separately known, documented
limitation from Iteration 13). Missing `#` support is itself a real,
independent gap worth fixing later (not part of this iteration's
scope - crash-hardening first), but it's what led to the actual
reproduction: bisecting down through `kill -l $?`'s failure and empty
output eventually isolated the crash to `echo $(true)` alone - a
single-word command inside `$(...)` that produces zero bytes of
output.

### The five vulnerable call sites

Searched every `DO` in `shell.4` for cases where the loop count could
legitimately be zero at runtime, given the confirmed wraparound bug:

- **`EXPAND-CMDSUB`'s output-splice loop** - `CMDSUB-OUT-LEN` is
  genuinely 0 whenever the substituted command produces no output at
  all (`$(true)`, `$(printf)`, any command run purely for its exit
  status). This was the actual crash.
- **`HAS-SLASH?`** - an empty `ARGV[0]`.
- **`B-STR`** (used by `TRY-DIR`) - an empty `$PATH` component
  (`PATH=:/usr/bin`), which POSIX defines as meaning `.`.
- **`DO-EXPORT`** - `export ""`.
- **`COPY-ARGV`** - an empty pipeline segment (`| cmd` or `cmd |`).

One additional `N DO` (`SHIFT-ARGV-DOWN`'s `ARGC @ 1 DO`) turned out to
already be safe: it's only reached inside `ARGC @ 1 > IF`, which
guarantees `ARGC >= 2` before the loop, so `start` (1) and `limit`
(`ARGC`, >= 2) can never coincide.

Each of the five is now guarded with an explicit `DUP 0 > IF ... ELSE
... THEN` around the loop, rather than relying on this kernel's
`DO`/`LOOP` to do the right thing on a degenerate range - each
carefully re-balances the data stack in both branches (`HAS-SLASH?`
and `DO-EXPORT` need an explicit `2DROP` in the zero-case branch,
since callers leave an extra item on the stack alongside the address
being scanned; `B-STR` and `COPY-ARGV` don't, since they consume their
inputs into variables before the loop rather than referencing the
stack from within it).

Verified directly, each previously either theoretical or crashing:
`echo x$(true)y` / `$(printf)` / `$(basename)` (all previously
crashed, ARGC=1, zero output) now produce clean output; `export ""`
followed by another command now continues normally instead of
crashing; `PATH=:/usr/bin` (empty leading component) resolves `pwd`
correctly instead of crashing on the empty segment; a leading or
trailing pipe (`| echo foo`, `echo foo |`) now produces empty output
cleanly rather than crashing on the empty pipeline segment.

### A false positive caught and fixed in the harness itself

Re-running `tests/mrsh-suite/run.sh` after the fix showed the pass
count go from 1 to 0, not up - `2.2.3-alias-expansion.fail.sh`
"regressed." Investigated rather than assumed: temporarily swapped
back the pre-fix `shell.4` and re-ran that one file directly, which
confirmed the previous "pass" was itself the exact crash bug just
fixed (status 139, a segfault) - not a clean rejection as Iteration
14's writeup described. The harness's expected-failure check
(`relfsh_ret != 0`) couldn't distinguish "crashed" from "correctly
rejected the input" - a segfault's exit status is nonzero too. Fixed
the harness itself: `is_crash_status()` now treats any status >= 128
(the POSIX convention for "killed by a signal," which both a real
crash and `timeout`'s own kill produce) as a crash, scored as FAIL
regardless of being nonzero, with the differential tests' own failure
messages updated to call out a crash explicitly too rather than just
printing a bare status number.

**Corrected baseline: 0 passed, 21 failed, 3 skipped.** Every failure
now has a clean status (0, or bash's own 1) - confirmed no crash
statuses remain anywhere in the suite. The number going down is a
correct, honest result of removing a false positive, not a
regression - the actual state of the world (four fewer crashes, zero
genuinely-passing tests) didn't get worse, the *measurement* of it got
more accurate. `GOALS.md`'s goal 8 baseline is updated to match.

Phase A's crash-hardening is now done; its remaining item (real
file-argument invocation for `relfsh`) is next.

## Iteration 16: goal 8, phase A - script-file invocation (phase A done)

Goal: the last item on phase A's list - `relfsh script.sh` (matching
`sh script.sh`), needed both as a generally useful capability and to
remove the stdin-piping asymmetry `tests/mrsh-suite/run.sh` had been
using as a workaround since Iteration 14.

### `SH-FILE`

A new word alongside `SH`/`SH-C`: opens the given path read-only
(`R/O OPEN-FOR`, already existed for redirection), reads it with the
kernel's own `READ-LINE` primitive (its `u2` lines up exactly with
what `RUN-LINE` already expects - the same per-line shape `SH1` uses
for one interactively-read line), runs each line via `RUN-LINE` until
EOF, then exits with the last command's status. `MAIN` now routes any
invocation with at least one argument that isn't exactly `-c` plus a
command string to `SH-FILE` (ignoring further arguments beyond the
path, since positional parameters aren't implemented yet). `relfsh`'s
own `-c`-vs-else branching collapsed into a single "don't chain `cat`
when an argument is given" test, since script-file mode has the exact
same reasoning `-c` mode already had for not touching relfsh's own
stdin (`SH-FILE` reads from the file's own fd, never stdin).

A missing/unreadable file exits 127 with no error message, matching
this shell's existing sparse error handling elsewhere (see
`APPLY-REDIRECTIONS`).

### A pre-existing bug this surfaced: `exit` always hardcoded status 0

Testing `exit` mid-script for real (rather than only via `-c`, where
nothing after `exit` could matter observably) surfaced that `exit`'s
own `DISPATCH` entry never looked at any argument at all - `exit 5`
behaved identically to bare `exit`, both always calling `0 SYS-EXIT`.
Also not POSIX-correct on its own terms: a bare `exit` should default
to the *previous* command's status (`$?`), not unconditionally 0.
Fixed alongside `SH-FILE` since it directly affects exit-status
correctness, which the whole point of adopting mrsh's suite depends
on: `PARSE-DECIMAL` (a small, explicit multiply/accumulate loop,
matching `EMIT-DECIMAL`'s own reasoning for not reaching for the
standard `>NUMBER` word) parses an optional argument; `exit N` now
uses it, bare `exit` now uses `LAST-STATUS`. `PARSE-DECIMAL`'s own
loop needed the same zero-guard treatment as Iteration 15's fixes
(an empty argument, e.g. `exit ""`, is a legitimate zero-length case).

### A more significant discovery: the *old* invocation method's exit status was always 0, regardless of the script

Updating `tests/mrsh-suite/run.sh` to use real file-argument invocation
(`"$RELFSH" "$1"` instead of `< "$1"`) changed several results, and
digging into why surfaced something important: the *old* stdin-piped
method (used because `relfsh` had no file-argument support yet) fed
each script into the ordinary interactive `SH` loop, which has no
natural EOF-driven exit at all on shell.4's own side - `relf`'s own
top-level interpreter loop is what actually notices EOF on stdin and
exits, and it always exits 0, never touching `LAST-STATUS`/`SYS-EXIT`
inside shell.4. Confirmed directly: the same vendored `args.sh`, run
the old way, reports `status=0` no matter what its last command
actually did; run through `SH-FILE`, it reports `127` (correctly -
its last command, `func`, doesn't exist as a real binary, since
shell.4 has no function support). **The Iteration 14/15 baselines'
exit-status numbers for every differential test were themselves an
artifact of this**, not a genuine reflection of `shell.4`'s behavior -
though it didn't change any pass/fail *verdicts* for the 18
differential tests, since all 18 were already failing on output
grounds independent of status. The one place it did change a verdict:
`2.2.3-alias-expansion.fail.sh` now genuinely passes (status 127,
confirmed not a crash) - still not exercising the alias-ordering
question the test actually intends to check, since `shell.4` has no
`alias` at all, but this time via an honest, correctly-propagated
status rather than a segfault happening to also be nonzero (Iteration
14's original mistake) or a piped-stdin artifact always reading 0
(this iteration's finding).

**Updated baseline: 1 passed, 20 failed, 3 skipped** - all crash-free,
and now measured through the same invocation method mrsh's own
harness uses (`relfsh testcase` vs `bash testcase`), no more
asymmetry. `tests/shell/run-script` (8 assertions) locks in script-file
invocation and `exit`'s corrected behavior - 67 assertions across 14
files now, all passing on both x86-64 and i386.

**Phase A is now complete.** Phase B (foundational semantics -
shell-local variable assignment without `export`, `;`, `&&`/`||`,
command grouping, if/while nesting) is next.

## Iteration 17: goal 8, phase B - shell-local variable assignment

Goal: the first, most foundational item on phase B's list - a
standalone `NAME=value` line sets a POSIX "shell parameter" distinct
from the OS environment, expanding via `$NAME`/`${NAME}` without being
inherited by a child process (unlike `export NAME=value`). `shell.4`
previously had no assignment mechanism at all outside `export`.

### Design

A simple linear table (`SHVAR-NAMES`/`SHVAR-VALUES`, name/value pairs
copied into fixed-size slots, not just pointers - `ARGV` entries point
into `LINE-BUF`, overwritten on the next line) - matches how this
shell already avoids hashing/dynamic structures everywhere else.
`$VAR`/`${VAR}` expansion (`EXPAND-VAR`) now goes through a new
`LOOKUP-VAR`, which checks the shell-local table first, falling back
to `GETENV` for anything this shell never itself assigned but
inherited from its own environment (e.g. `$HOME`). `DO-EXPORT` now
also calls `SET-SHVAR` (so `export NAME=value` sets both), and a bare
`export NAME` (no `=`) exports an existing shell-local value if there
is one. `DO-UNSET` now also calls a new `REMOVE-SHVAR`. Detecting a
standalone assignment: `ASSIGNMENT-EQPOS` scans `ARGV[0]` for a `=`
preceded by a valid, non-empty POSIX name (first character not a
digit, `NAME-CHAR?` throughout - already existed, reused directly),
wired into `RUN-TOKENIZED` ahead of the normal pipe/redirect/dispatch
path, but only when `ARGC = 1` and `ARGV[0]` is unquoted (a quoted
`"FOO=bar"` alone stays a literal command name, same `ARGV-QUOTED`
reasoning already applied to operators and builtin names elsewhere).

**Deliberately out of scope for now**: `NAME=value command args...`
(POSIX's *temporary*, per-command assignment prefix) - `ARGC` isn't 1
in that shape, so it currently falls through to being looked up as a
literal (and failing) command name. A real, acknowledged gap, not
silently mishandled.

### Bugs found along the way - several by testing directly, not by inspection

**A real logic bug in `SET-SHVAR`**: the first version didn't capture
`name-addr`/`value-addr` into variables before running the
`FIND-SHVAR`/`SHVAR-COUNT` bookkeeping logic underneath them on the
stack, so by the time `SAFE-CSTR-COPY` finally ran, the wrong address
was buried at the wrong stack depth - the name slot ended up holding
the *value* and vice versa. Found by testing directly (checking the
raw slot contents after a `SET-SHVAR` call showed them swapped), not
by re-reading the code - re-reading it had looked fine. Fixed by
capturing both arguments into variables immediately, before any other
stack operations, matching this shell's own established preference
for explicit variables over stack-juggling.

**Two more nonexistent-word mistakes**, the same class as `>=` earlier
in this project (Iteration 15's `HAS-SLASH?` fix) and `NIP` here too -
this minimal kernel doesn't have `0<>`, `>=`, or `NIP`; fixed to
`0 <>`, an explicit `< 0=`, and `SWAP DROP` respectively. All three
were caught immediately by `shell.4` simply failing to load
("Undefined word ..."), not by silent misbehavior.

**A process mistake, not a code bug, repeated from Iteration 13**:
testing `GET-SHVAR`'s result with `IF ... ELSE ... THEN` typed
directly at `relf`'s own interactive stdin (rather than inside a
`:...;` definition loaded via `INCLUDED`) silently corrupts this
kernel's dictionary, and looked exactly like a real crash in
`GET-SHVAR` at first - the same pitfall documented back in Iteration
13, hit again here before being recognized. `GET-SHVAR` itself turned
out to be correct on the first attempt; the diagnosis just needed
redoing properly (a small standalone word, loaded via `INCLUDED`).

**Two integration steps that were designed and written up in this
session's own planning but never actually applied to the file**: the
`RUN-TOKENIZED` wiring for `ASSIGNMENT-EQPOS`/`DO-ASSIGN`, and the
`DO-EXPORT`/`DO-UNSET` shell-local integration, were both fully
designed (with careful hand-traces) but the actual edits were never
made before testing began - end-to-end tests correctly showed the
feature doing nothing at all (`$FOO` stayed empty after `FOO=bar`)
until this was noticed and the edits actually applied. Worth
remembering: designing and hand-verifying a change is not the same as
having made it - test the actual file, not the plan for the file.

### Verified end-to-end via `relfsh`

`FOO=bar` then `echo $FOO` → `bar`; re-assignment (`FOO=bar` then
`FOO=baz`) updates the value; multiple shell-local variables coexist;
a plain `FOO=bar` is confirmed **not** inherited by a real child
process (`/usr/bin/env` doesn't list it) while `export FOO=bar` is;
bare `export FOO` exports an already-set shell-local value; `unset`
removes the shell-local copy as well as the environment one; a quoted
`'FOO=bar'` alone is treated as a (failing, 127) literal command, not
an assignment; a successful assignment sets `$?` to 0. Confirmed on
both x86-64 and i386.

`tests/shell/run-assign` (8 assertions) locks all of this in - 75
assertions across 15 files now, all passing on both architectures.
`tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3 skipped for
now - expected, since no single vendored test file passes purely from
variable assignment alone; the pass count moves once enough of phase
B/C accumulates.

## Iteration 18: goal 8, phase B - ';' (multiple commands per line)

Goal: the next item on phase B's list - `cmd1 ; cmd2 ; ...`, each run
in sequence regardless of the previous one's own exit status (unlike
`&&`/`||`, not yet implemented).

### Design

Same whitespace-delimited-token convention `|` already has - `;` only
acts as a separator when it's its own token (confirmed directly:
neither `;` nor `|` were ever self-delimiting without surrounding
whitespace - "a;b" and "a|b" are each one literal token today, a
pre-existing characteristic, not something new introduced here).
`AT-SEMI?`/`SPLIT-SEMI` mirror `AT-PIPE?`/`SPLIT-PIPE` exactly, except
`SPLIT-SEMI` only ever splits off the *first* `;` it finds, leaving
everything after it (which may itself contain further `;`s) in a
separate `ARGV-SEMI-REST` buffer for `RUN-TOKENIZED` to feed back
through the same logic on a follow-up call - unlike a pipeline
(exactly two sides, always), a `;`-separated line can have any number
of segments, so this needed to be a loop rather than a fixed split.
`RUN-TOKENIZED` checks for `;` first now, ahead of the if/while
keyword checks and the assignment-word check from Iteration 17: if
found, the left segment is copied into the global `ARGV`/`ARGC` (via
the already-existing `COPY-ARGV`) and run through `RUN-TOKENIZED-CALL`
(the same deferred-word recursion mechanism already used for
if/while's own body-line handling), then the rest is copied in and run
the same way - recursing naturally handles any number of further
semicolons. An empty segment (a leading or trailing `;`) safely
produces `ARGC = 0`, which every downstream check (`LINE-IS?`,
`SPLIT-PIPE`, `DISPATCH`, etc.) already treats as a no-op.

### A real, discovered limitation - not a bug introduced by this work, but newly visible because of it

`FOO=bar ; echo $FOO` does **not** print `bar` - it prints nothing,
same as `export FOO=bar ; echo $FOO`. Root cause: `$VAR`/`${VAR}`
expansion happens once, during the initial `TOKENIZE` pass over the
*entire* raw line, before any `;`-separated segment has actually run -
so a variable assigned or exported earlier in the same line via `;`
isn't visible yet to a `$VAR` expansion later in that same line, even
though it would be on a subsequent line (confirmed: `FOO=bar` then
`echo $FOO` as two separate lines correctly prints `bar`). This isn't
new breakage from adding `;` - it's an existing consequence of how
expansion was already timed (once per line, up front), just newly
observable now that a single line can contain multiple sequenced
statements at all. A proper fix means tokenizing (and thus expanding)
each `;`-separated piece independently, in sequence, rather than the
whole line up front - a real architectural change, not a small patch,
and deliberately left for its own future iteration rather than
attempted as part of this one. Documented here and in `GOALS.md`
rather than silently left for someone to rediscover.

### Verified end-to-end via `relfsh`

Two and three commands separated by `;` all run; a later command runs
regardless of an earlier one's failure; a trailing or leading `;` with
nothing on the empty side is harmless; a quoted `';'` stays a literal
character; `$?` reflects the last segment's own status.
`tests/shell/run-semi` (7 assertions) locks all of this in - 82
assertions across 16 files now, all passing on both x86-64 and i386.
`tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3 skipped -
expected, since no single vendored test file passes from `;` support
alone.

## Iteration 19: goal 8, phase B - '&&'/'||' (conditional chaining)

Goal: the next item on phase B's list - `cmd1 && cmd2` runs `cmd2`
only if `cmd1` succeeded; `cmd1 || cmd2` only if it failed.
Left-associative, equal precedence for both, evaluated left to right
(POSIX): `a && b || c` runs `b` (skipping `c`) if `a` succeeds, but
runs `c` (skipping `b`) if `a` fails - a skipped segment leaves the
"compound status so far" unchanged for the next decision. Tighter
precedence than `;`, looser than `|`.

### Design

Same whitespace-delimited-token convention `|`/`;` already have (a
quoted `&&`/`||` is a literal argument). `AT-AND?`/`AT-OR?` mirror
`AT-PIPE?`/`AT-SEMI?`; `SPLIT-ANDOR` mirrors `SPLIT-SEMI` (splits off
only the *first* `&&`/`||` found, recording which one in `ANDOR-OP`,
leaving the remainder - which may contain further operators - for a
follow-up call). The pipe/redirect/dispatch logic that used to sit
inline at the end of `RUN-TOKENIZED` was factored out into its own
`RUN-SIMPLE-OR-PIPELINE`, so it can be called once per `&&`/`||`-
separated piece rather than just once per line. `RUN-AND-OR-CHAIN`
runs the first piece unconditionally (nothing precedes it), then
loops: copy the remainder in, `SPLIT-ANDOR` it again, decide via
`AO-SHOULD-RUN?` (checking the *previous* iteration's remembered
operator against the *previous* piece's own exit status) whether to
run the next piece, and repeat until no more `&&`/`||` are found -
unlike `;`'s recursion-based approach (each segment is fully
independent), this needed an explicit loop, since whether a piece
runs depends on the *previous* piece's outcome, not just on splitting.
`RUN-TOKENIZED` calls `SPLIT-ANDOR` after the `;` and assignment-word
checks have ruled themselves out, matching POSIX's precedence.

### Two syntax-level mistakes, both caught immediately by load failures - no logic bugs found in testing

A multi-line `( ... )` comment on `AO-PENDING-OP`'s own `VARIABLE`
declaration caused `shell.4` to fail loading with "Undefined word it"
- `it` being a mid-comment word that somehow became live code. Root
cause not fully pinned down (bisected by replacing the comment with
`\` line-comments instead, which resolved it, rather than fully
tracing why the `(` form specifically broke) - worth remembering as
an empirical caution about multi-line `(...)` comments in this
kernel, alongside the already-documented `0 0 DO` wraparound quirk,
even though the exact mechanism here wasn't nailed down as precisely.
Second: `LAST-STATUS @ 0<>` - the third time this project has hit the
"this minimal kernel doesn't have that two-character word" mistake
(after `>=` in Iteration 15 and `NIP` in Iteration 17) - fixed to
`0 <>` (two tokens, `<>` already exists).

Notably, once those two syntax errors were fixed, **the actual
algorithm worked correctly on the first real test** - all five
precedence cases tested (`a && b && c` both directions, `a || b || c`,
and both directions of the trickier `a && b || c`) passed immediately,
including the subtle "skipped segment carries the previous status
forward" behavior, without needing any further debugging once the
file actually loaded. The hand-traces done during design (verifying
each new word's stack effect on paper before writing it) seem to have
paid off specifically for the part that's actually hard to get right
(the conditional-chaining logic itself) - the mistakes that did occur
were lower-level syntax gotchas specific to this kernel's word set and
comment parsing, not reasoning errors about the shell semantics being
implemented.

### Verified end-to-end via `relfsh` (and confirmed on i386)

All four basic cases (`&&`/`||` × success/failure); three-segment `&&`
and `||` chains; both directions of `a && b || c`; interaction with
`;` (looser precedence - a skipped `&&` segment doesn't prevent a
later `;`-separated command from running); a quoted `&&` staying
literal; a pipe within an `&&`-segment still working (`|` binds
tighter); a redirect staying scoped to its own segment; `$?` after a
skipped segment reflecting the earlier command's own status.

`tests/shell/run-andor` (12 assertions) locks all of this in - 94
assertions across 17 files now, all passing on both x86-64 and i386.
`tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3 skipped -
expected, since no single vendored test file passes from `&&`/`||`
support alone.

## Iteration 20: goal 8, phase B - command grouping ('( )' and '{ ; }')

Goal: the next item on phase B's list - `( list )` runs its body in a
subshell (a forked child, so `cd`/variable/`export` changes inside it
don't affect this shell); `{ list ; }` runs its body directly in this
shell instead, so those changes do persist. That difference is the
entire reason the two constructs exist separately.

### Design

A deliberate, consistent scope choice up front: both require
whitespace around `(`, `)`, `{`, `}` themselves - this shell's
established convention for every operator so far (`|`, `;`, `&&`,
`||` all need it too), even though real POSIX shells don't require it
around `(` specifically. This is a real, acknowledged gap against
mrsh's own tests, which write `(cmd)` with no spaces - verified
directly that a trailing `| sed s/a/X/` or `> file` after a group is
currently silently dropped rather than applied (the output is
unchanged, `X` never appears; the file is never created) - a proper
fix would need `(` to become a self-delimiting token even when fused
to adjacent text, a deeper tokenizer change than this iteration
attempted. Detected by `ARGV[0]` alone (reusing `LINE-IS?`, exactly
like if/while already are), and critically, this check runs *before*
`;`/`&&`/`||` splitting - a group's own `;` (used inside its body,
e.g. `( echo a ; echo b )`) has to stay scoped to that body rather
than being split as if it belonged to the outer line, which would
otherwise treat `( echo a` and `echo b )` as two independent, broken
top-level statements. `SPLIT-GROUP-PAREN`/`SPLIT-GROUP-BRACE` mirror
`SPLIT-SEMI`'s scanning shape (extract everything between the opening
and matching closing token into a separate buffer). `DO-SUBSHELL`
forks (same `FORK`/`WAITPID` shape `RUN-PIPELINE` already uses); the
child copies the body into the global `ARGV`/`ARGC` and runs it via
`RUN-TOKENIZED-CALL` (so the body's own `;`/`&&`/`||`/`|` all work
normally), then exits with whatever `LAST-STATUS` that left behind -
the parent takes the child's exit status as its own. `DO-BRACE-GROUP`
does the same without forking. Neither supports nesting (same "no
nesting" scope limit if/while already have, for the same underlying
reason: no real per-invocation state for control structures yet, only
shared globals).

### A placement mistake, caught immediately by a load failure

The new block was first written in the wrong place in the file -
before `RUN-TOKENIZED-CALL` (the deferred-word stub `DO-SUBSHELL`/
`DO-BRACE-GROUP` both call) was actually defined, since that
definition sits further down than where the day's earlier `&&`/`||`
work had left off. `shell.4` correctly refused to load
("Undefined word RUN-TOKENIZED-CALL"), and the fix was a precise,
line-indexed extract-and-reinsert (the same careful approach used for
Iteration 16's similar unset/cmdsub separation) rather than a
free-hand edit, to avoid corrupting either the moved block or what
was left behind.

### A test-writing mistake, self-diagnosed rather than blamed on the feature

`tests/shell/run-group`'s own first draft used `tail -1` to check a
brace group's `cd` had taken effect, and failed - but a direct,
manual re-check of the same scenario showed the feature working
correctly (`pwd` genuinely printed `/`). The test's own `tail -1` was
grabbing a trailing shell prompt line rather than `pwd`'s actual
output, not a real bug in the shell - fixed the test (`grep -qx`
against the whole output, after stripping `\r`) rather than
mis-diagnosing the feature as broken.

### Verified end-to-end via `relfsh` (and confirmed on i386)

Both `( echo a ; echo b )` and `{ echo a ; echo b ; }` run their
body's commands; a subshell's `cd` and variable assignment are both
confirmed **not** to affect this shell, while a brace group's
versions of the same **are** confirmed to persist; a subshell's exit
status reflects its own last command; an empty group (`( )`) is a
harmless no-op; a quoted `'('` stays a literal argument, not a group
start; a trailing pipe or redirect after a group is silently dropped
rather than applied (documented, not silently discovered later).

`tests/shell/run-group` (9 assertions) locks all of this in - 103
assertions across 18 files now, all passing on both x86-64 and i386.
`tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3 skipped -
expected, since mrsh's own tests use `(cmd)` without the whitespace
this iteration's scope requires, so this doesn't move that number yet.

## Iteration 21: fix if/while reading from the wrong input source in script-file mode

Goal: originally set out to tackle if/while nesting (phase B's last
item), but studying the current implementation in depth first
surfaced something more urgent - `if`/`while` were **completely
broken** whenever a script was run via `relfsh script.sh` (Iteration
16's `SH-FILE`) rather than piped into stdin, since their own
internal "read the next line" logic (`READ-LINE-INTO-ARGV`, used to
find `then`/`else`/`fi`/`do`/`done` and the body lines in between)
always called `ACCEPT` - which reads from the real process stdin
unconditionally, regardless of where the script's own lines were
actually coming from. Confirmed directly:
`if /usr/bin/true\nthen\necho yes\nfi` run via a script file printed
nothing at all - "then"/"echo yes"/"fi" were silently never read, so
the entire `if` command was a no-op. This is likely the single most
common way real scripts use `if`/`while` at all, so this took
priority over nesting.

### The fix

`READ-LINE`'s C implementation (a byte-by-byte `read()` loop) works
on any file descriptor, including stdin's own fd 0 - unlike `ACCEPT`
(a Forth-level word with its own backspace/delete line-editing, which
matters for a genuinely interactive session but has no notion of
reading from an arbitrary file). A new `SHFILE-ACTIVE?` flag (set by
`SH-FILE` right after opening its file) and a new
`READ-NEXT-INPUT-LINE` word dispatch between the two: `READ-LINE`
against `SHFILE-FID` when running via a script file, `ACCEPT`
otherwise - preserving interactive editing for genuinely interactive
sessions while fixing script-file correctness.
`READ-LINE-INTO-ARGV` (if/while's own body-line reader) now goes
through this instead of calling `ACCEPT` directly. A second, related
detail caught before it could become its own bug: the existing `CR`
after each line read (needed in interactive/piped-stdin mode, where
it puts the cursor on a fresh line the way a real terminal echoing
typed input would) had to become conditional on *not* being in
script-file mode - unconditionally, it would have printed a spurious
blank line into the script's own clean output on every body-line
read, since `SH-FILE`'s own output has no such prompts/echoes mixed
in at all otherwise.

A file-ordering slip happened again this iteration, same class as
Iterations 16 and 20: `SHFILE-FID`/`SHFILE-ACTIVE?` were first
declared right where `SH-FILE` itself lives, but `READ-LINE-INTO-ARGV`
(which needs them) is defined much earlier in the file - fixed via the
same precise line-indexed extract-and-reinsert approach used before,
moving the declarations up rather than restructuring anything else.
Also repeated - and this time caught *before* testing, having learned
from Iteration 19's unresolved multi-line-comment breakage - avoided
writing a new multi-line `( ... )` comment on `SHFILE-ACTIVE?`'s own
declaration in favor of `\` line-comments from the start.

### Verified end-to-end via `relfsh`

`if /usr/bin/true\nthen\necho yes\nfi` and a `while` loop (`while
/usr/bin/test $I -eq 1 do ... done`) both now work correctly when
invoked via a script file, with clean output (no spurious blank
lines). Confirmed the existing interactive/piped-stdin behavior is
unaffected: the full regression suite (1892 core assertions plus every
existing shell test, including the original `run-if`/`run-while`
suites) still passes unchanged on both x86-64 and i386.

`tests/shell/run-script` gained two new assertions covering exactly
this - `if`/`while` reading their own body from the script file, not
stdin - 105 assertions across 18 files now, all passing.
`tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3 skipped -
expected, since `if.sh`/`loop.sh` need considerably more than this fix
alone (functions, the `[`/`test` builtin as a real built-in rather
than an external binary, arithmetic) to pass as whole files, even
though this fix is itself a real, independently valuable correctness
issue resolved.

Nesting (the item originally intended for this iteration) is next.

## Iteration 22: goal 8, phase B - if/then/else/fi nesting (phase B done)

Goal: the last item on phase B's list - a body line that's itself
another `if` should work correctly, at any nesting depth, regardless
of whether the enclosing branch actually executes.

### First attempt: incomplete, caught by testing directly

The obvious fix: `COND-TRUE?` (the single shared variable tracking
whether the current `if`'s own condition succeeded) is saved via `>R`
at `DO-IF`'s entry and restored right before each of its exit points,
so a nested if can freely overwrite it for its own condition without
corrupting the enclosing if's value once the inner call returns -
standard Forth return-stack discipline. Verified directly and
correctly handled every case where the *enclosing* condition was
true: `if true; then if true; then ...; fi; ...; fi` and `if true;
then if false; then ...; fi; echo still-runs; fi` both behaved
exactly right on the first test.

Testing the *other* direction - enclosing condition false - surfaced
a deeper problem the >R/R> fix alone didn't touch: when
`COND-TRUE?` is false, `DO-IF`'s own loop simply never calls
`RUN-TOKENIZED-CALL` for that body line at all (`COND-TRUE? @ IF
RUN-TOKENIZED-CALL THEN`) - which is fine for an ordinary command,
but if that body line is itself the start of a nested `if`, skipping
the call means the nested if's own `then`/body/`fi` are never
consumed as a nested construct at all. The outer loop just keeps
reading line by line, treats the nested if's own `"then"` and body
lines as ordinary (skipped) body text, and then hits the nested if's
own `"fi"` - which the outer loop's `S" fi" LINE-IS?` check matches
just as readily as its own closing `fi`, since nothing distinguishes
them by depth. The result: the *outer* `DO-IF` exits early, mistaking
the inner `fi` for its own, and everything meant to still be inside
the outer construct (the rest of the outer body, and the outer's own
real `fi`) falls through to ordinary top-level execution instead -
confirmed directly: a line meant to be skipped along with the whole
outer body printed anyway, unconditionally, once the outer if had
already (incorrectly) ended.

### The full fix: always parse, but track a separate "suppress" state

A second variable, `SUPPRESS-EXEC?`, marks "this whole region must be
read (so nested control structures still correctly consume their own
`then`/body/`fi`) but must not actually execute anything." `DO-IF` now
*always* calls `RUN-TOKENIZED-CALL` for each body line, regardless of
whether this branch should run - what changes is `SUPPRESS-EXEC?`'s
own value beforehand (computed from the enclosing value, peeked via
`R@` without disturbing what's saved for `DO-IF`'s own later restore,
`OR`ed with this branch's own condition). `SUPPRESS-EXEC?` is checked
at the two actual points where something would otherwise execute -
`DO-ASSIGN` and `RUN-SIMPLE-OR-PIPELINE` - rather than only gating
whether the recursive call happens at all, which is exactly the gap
the first attempt had. Both `COND-TRUE?` and `SUPPRESS-EXEC?` are
saved via `>R` at entry (`COND-TRUE?` first, `SUPPRESS-EXEC?` on top)
and both restored via `R>`/`R>` right before every exit point.

A `DO-SUBSHELL`-forked child inherits whatever `SUPPRESS-EXEC?` was at
fork time as an ordinary consequence of `fork()`'s copy-on-write
semantics, so a suppressed subshell still forks (a minor, accepted
inefficiency - one wasted fork) but correctly does nothing once
inside, since the same `RUN-SIMPLE-OR-PIPELINE`/`DO-ASSIGN` checks
apply there too. `DO-BRACE-GROUP` doesn't fork and needs no special
handling of its own - it relies on `DO-IF`'s own >R/R> discipline
already keeping `SUPPRESS-EXEC?` correctly balanced across whatever
runs inside it.

Two file-ordering slips happened again this iteration (same class as
Iterations 16, 20, and 21): `SUPPRESS-EXEC?` was first declared near
`DO-IF`, but `DO-ASSIGN` (which also needs to check it) is defined
much earlier in the file, and after moving it once, `RUN-SIMPLE-OR-
PIPELINE` turned out to be earlier still - both caught immediately by
load failures and fixed via the same precise line-indexed extract-
and-reinsert approach used every previous time, ending with the
declaration moved all the way up next to `LAST-STATUS` near the top
of the file, the earliest point that works for every caller.

(`while`/`do`/`done` still does *not* support nesting - its condition
and body are buffered as raw text across dedicated, fixed-size
buffers rather than a single scalar, so nesting it would need
considerably more than what fixed `if` here; left as its own,
separate, still-open problem, not attempted in this iteration.)

### Verified end-to-end via `relfsh` and confirmed on i386

Outer true / inner true (both bodies run); outer true / inner false
(outer body still runs after the inner `if`); **outer false** (the
line after a nested `if` is also correctly skipped, along with
everything inside the nested `if` itself - the case the first attempt
got wrong); a nested `if` inside a taken `else` branch; a nested `if`
inside a *skipped* `else` branch; three levels deep with a false
condition in the middle (only the middle level's own body is skipped,
the outermost level's remaining body still runs).

`tests/shell/run-if-nesting` (10 assertions) locks all of this in -
115 assertions across 19 files now, all passing on both x86-64 and
i386. `tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3
skipped - expected, since `if.sh` needs considerably more than
nesting alone (shell functions, the `[`/`test` builtin, arithmetic)
to pass as a whole file.

**Phase B is now complete.** Phase C (control structures - `for`,
`case`, shell functions, `break`/`continue`) is next.

## Iteration 23: goal 8, phase C - for/in/do/done loops

Goal: the first item on phase C's list - `for VAR in word1 word2 ...`
runs its body once per word, with `VAR` set to each in turn.

### Design: reusing while's own body machinery

`for` and `while` share the exact same "capture body lines as raw
text, then replay them" mechanics (`WHILE-BODY-BUF`,
`APPEND-RAW-LINE-TO-BODY`, `DO-WHILE-BODY`, all from Iteration 11) -
only the *iteration control* differs: a fixed word list, expanded
once at the `for ... in ...` line itself (matching POSIX - not
re-evaluated each iteration the way `while`'s own condition is),
instead of a condition re-checked before every pass. `SAVE-FOR-WORDS`
copies `ARGV[1]` (the loop variable name) and `ARGV[3..]` (the word
list, skipping `ARGV[2]`'s assumed `"in"` without validating it,
matching this shell's sparse error handling elsewhere) into their own
dedicated buffers before `DO-FOR` starts reading the intervening
`do`/body/`done` lines, since those reads overwrite the global
`ARGV`/`ARGC` the original `for` line's own words were sitting in.
`DO-FOR-ITERATE` then walks the saved word list, calling `SET-SHVAR`
(the shell-local variable table from Iteration 17) and replaying the
stored body (`DO-WHILE-BODY`, entirely unmodified - it doesn't care
whether the stored lines came from a `while` or a `for`) once per
word. Requires `do` on its own, separate line, matching if/while's own
established convention (`for VAR in ...; do` on one line isn't
supported, same as `if cond; then` isn't). Respects an enclosing
`SUPPRESS-EXEC?` (a `for` loop sitting inside a skipped `if` branch
still correctly consumes its own `do`/body/`done`, but doesn't
actually iterate) - checked once, at the top of `DO-FOR-ITERATE`,
since expanding the word list itself (`SAVE-FOR-WORDS`) has no side
effects worth guarding, unlike `if`'s own condition command.

This iteration went unusually smoothly on the first pass: every
individual test (basic iteration, an empty word list running the body
zero times, the loop variable retaining its final value after the
loop ends, `$?` reflecting the last iteration's last command, and a
`for` loop inside a skipped `if` branch being correctly consumed but
not run) passed immediately, without needing a debugging round - the
first time that's been true for a new control-structure feature this
project.

### A real, pre-existing limitation confirmed (not introduced by this work): loop bodies can't contain another multi-line construct at all

Testing `if`/`then`/`fi` *inside* a `for` loop's body surfaced a
genuine bug - but confirmed directly that the same failure already
happens inside a *while* loop's body too, so this isn't something
`for` introduced; it's inherent to the "store body lines, replay them
one at a time" mechanism itself, which both share. `DO-WHILE-BODY`
dispatches each stored body line independently via
`RUN-TOKENIZED-CALL` - but `DO-IF`'s own search for `then`/`else`/`fi`
reads from the *real* input stream (`READ-LINE-INTO-ARGV`, going
through `READ-NEXT-INPUT-LINE`), not from the next stored body line.
So when a stored body line is itself `"if ..."`, `DO-IF` tries to read
`"then"` from whatever comes *after* the loop's own `done` in the real
script - which is usually nothing at all (EOF) - prints "if: expected
'then'", and gives up immediately, while the *rest* of the stored body
lines (`"then"`, `"echo ..."`, `"fi"`) get replayed as independent,
unconditional commands regardless of what the `if`'s own condition
was. Confirmed with a minimal repro: a body line meant to run only
when a condition holds prints on every iteration instead, since the
line carrying `echo` was never actually inside the `if` at all from
the replay loop's point of view - it was just the next line in the
list. A real fix would need loop bodies to support genuine read-ahead
into stored lines (essentially, `if`/`while`/`for` all sharing one
real notion of "the next line of input" regardless of whether that's
the live script or a replay buffer) - left as its own, separate,
substantial future item; not attempted here, and `for`'s own test
suite deliberately avoids exercising it rather than papering over it.

### Verified end-to-end via `relfsh` and confirmed on i386

Basic iteration over a word list, expanding `$i` inside the body; an
empty word list running the body zero times; the loop variable
retaining its final value after the loop ends; `$?` reflecting the
last iteration's last command; a `for` loop inside a skipped `if`
branch correctly consumed but not run.

`tests/shell/run-for` (7 assertions) locks all of this in - 122
assertions across 20 files now, all passing on both x86-64 and i386.
`tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3 skipped -
`for.sh` specifically still fails since it uses `; do` on the same
line as `for ... in ...` throughout, the same "do/then must be on its
own line" scope limit `if`/`while` already have, on top of the
loop-body-can't-contain-if limitation above and `$IFS`-based field
splitting (an explicit, longstanding non-goal) that several of its
later sections depend on.

## Iteration 24: operators no longer require surrounding whitespace

Goal: the highest-leverage remaining gap identified while assessing
distance to mrsh - every operator implemented so far (`|` from
Iteration 7, `;`/`&&`/`||` from Iterations 18/19, `(`/`)`/`{`/`}` from
Iteration 20) took the shortcut of requiring whitespace around it, a
deliberate, consistently-documented scope limit at each step - but
re-reading mrsh's own test files directly for the "how far to parity"
assessment showed this blocking real progress on almost everything:
`if true; then`, `(echo hi)`, and fused-operator style generally is
the norm in real scripts, not the exception.

### The hazard that ruled out the obvious approach

The first design considered - making `SCAN-TOKEN` itself recognize an
unquoted operator character as a token boundary, stopping mid-scan the
way it already stops at whitespace - has a real hazard: for an
unquoted word, `TOK-OUT` (the compaction write cursor) always
coincides with `TOK-POS` by the time `SCAN-TOKEN` returns, so the
existing NUL-termination write (`0 EMIT-TOK-CHAR`, right after
`SCAN-TOKEN`, in `TOKENIZE`'s own outer loop) would land exactly on
top of whatever character follows - destroying a fused operator
character before the *next* tokenize iteration could ever read it to
recognize it as its own token. Solving that properly (reading and
remembering the operator *before* the destructive write) is
substantially trickier and riskier than it first looks.

### The approach taken instead: a pre-pass, not a tokenizer rewrite

Rather than touch `SCAN-TOKEN`/`TOKENIZE`'s own proven, heavily-used
in-place compaction logic at all, a new `NORMALIZE-OPERATORS` runs
*before* `TOKENIZE` ever sees the line: it scans the raw text and
inserts a literal space before and after every *unquoted* occurrence
of `;`, `|`, `&`, `<`, `>` (recognizing the two-character doubled
forms `&&`, `||`, `>>` specially, so they aren't mistaken for two
separate one-character operators), tracking single/double-quote state
so an operator character *inside* a quote is left untouched - matching
real shells, where a quoted operator is literal text. "true;then"
becomes "true ; then" before the existing, entirely-unmodified
tokenizer ever sees it. Re-normalizing an already-spaced-out operator
is harmless (redundant extra spaces, which `SKIP-WS` already
tolerates) - relevant since a `while` loop's condition gets
re-tokenized fresh every iteration and would otherwise pass through
this twice. Wired into `RUN-LINE` (the single shared entry point for
both interactive/piped-stdin and `-c` mode, since `SH-C` already routes
through it - one comment fix along the way: `SH-C`'s own comment
claiming no `;`/`&&` chaining was stale, left over from before
Iterations 18/19 added those), writing the result into a separate,
generously-sized `NORM-BUF` and copying it back into `LINE-BUF` (with
a bounds check - if it wouldn't fit, falls back to tokenizing the
original, un-normalized text rather than truncating or corrupting
anything, an exceedingly rare case in practice).

The core logic passed every test on the first attempt, verified via a
standalone diagnostic (five hand-traced cases: `;`, a quoted `;`
staying untouched, `&&`/`||`, `>`, `>>`) before ever being wired into
`RUN-LINE` at all. Wiring it in did catch one real, self-inflicted
stack bug immediately (an unconsumed leftover value from a `DUP` that
should have been the sole input to the new normalization call) -
caught by carefully re-deriving the stack trace by hand before testing
further, not by a crash.

### Deliberately out of scope: '(', ')', '{', '}'

Unlike the five operators above, blindly spacing every unquoted
paren/brace would break `$(...)` command substitution outright -
`EXPAND-VAR`'s own detection needs `"$("` with no space in between.
Doing this correctly needs tracking "am I currently inside a `$(...)`
construct" during the same pre-pass, real additional complexity
deliberately left for its own future iteration rather than risked
here.

### A real regression found in an *existing test*, not the shell itself

Re-running the full shell suite surfaced one failure:
`export PIPECHAR=|` (unquoted) no longer worked the way an existing
Iteration-9-era test expected. Investigated rather than reverted:
real POSIX shells *also* treat an unquoted `|` inside what looks like
an assignment as a pipe operator, splitting `PIPECHAR=|` into an
empty-valued assignment followed by a syntax error (a pipe with
nothing after it) - `PIPECHAR=|` was never actually valid, unquoted,
in a real shell either. The *old* behavior (silently treating it as
part of the assignment's literal value) was itself the divergence from
real shells; this iteration's fix incidentally corrected it. Confirmed
directly that the properly-quoted form (`export PIPECHAR='|'`) still
expands to a literal `|` that stays uninterpreted as an operator -
the actual guarantee the test cares about - and updated the test to
use that quoting, matching what a real script would actually need to
write.

### A related, separate gap this surfaced but does *not* fix

`if true; then true; fi` still doesn't work, even though `;`/`then`
now tokenize correctly as their own tokens - `DO-IF`/`DO-WHILE`/
`DO-FOR` only ever look for `then`/`do` by reading a *new* line
(`READ-LINE-INTO-ARGV`), never by checking whether the remainder of
the *current* line's `ARGV` already has it. Getting `;`/operators
right was a necessary but not sufficient condition - the control-
structure words themselves would need a real redesign to also check
same-line continuation before falling back to reading another line.
Left as its own, separate, still-open item; not attempted here.

### Verified end-to-end via `relfsh` and confirmed on i386

`;`, `|`, `&&`, `||`, `>` all work correctly with zero surrounding
whitespace, individually and chained (`echo a;echo b;echo c`, mixed
`echo a|cat;echo b`); a quoted operator-looking string
(`'a;b|c'`) stays untouched; `$(...)` command substitution is
unaffected, as intended.

`tests/shell/run-operator-fusion` (8 assertions) locks all of this
in - 130 assertions across 21 files now, all passing on both x86-64
and i386. `tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3
skipped - expected, since no single vendored test file passes from
this alone (most also need `then`/`do` on the same line, which this
doesn't fix, plus various other missing features) - but this removes
a foundational parsing obstacle that was blocking progress on nearly
every remaining test file, independent of which specific feature each
one needs next.

## Iteration 25: same-line 'if COND; then BODY; fi' support

Goal: the natural follow-up to Iteration 24's operator-fusion fix -
getting `;` to tokenize correctly regardless of surrounding
whitespace was necessary but not sufficient for `if true; then` to
actually work, since `DO-IF` only ever looked for `then`/`else`/`fi`
by reading a *new* line, never by checking the remainder of the
*current* line's already-correctly-tokenized `ARGV`. This closes that
gap, for `if` specifically (`while`/`for` still require `do` on its
own separate line - extending this to them is real, separate future
work, given the added complexity of also needing it for their
buffer-based body-replay machinery).

### The mechanism: a "pending remainder" and depth-aware keyword scanning

A new `SPLIT-AT-KEYWORD ( c-addr u --- f )` scans the *global* `ARGV`
for the first unquoted token matching a given keyword - if found,
`ARGV`/`ARGC` are truncated to just what came before it, and
everything after the keyword becomes a new `PENDING-REMAINDER` for a
new `READ-NEXT-LOGICAL-LINE` to pick up next time, rather than
actually reading a new line of input. `DO-IF` now always does the
condition-extraction/`SPLIT-AT-KEYWORD` dance regardless of whether
`SUPPRESS-EXEC?` is set (parsing the structure correctly either way),
gating only whether the condition is *actually run* on that flag -
the same principle Iteration 22's suppress mechanism already
established for nesting.

### Three real bugs found and fixed along the way, each caught by testing directly, not by inspection

**First**: `RUN-TOKENIZED` was checking for `;` before checking for
the `if`/`while`/`for` keyword at all - so `"if true; then echo hi;
fi"` got split apart at the first `;` before `DO-IF` ever saw the
whole line intact, exactly the same class of problem `(`/`{` group
detection already had to solve by running before `;`-splitting.
Fixed by moving keyword detection earlier too. Confirmed this
wouldn't make `while`/`for` any *worse* off - `"while true; do"` was
already broken before this reordering too, an untested gap from
Iteration 24 that hadn't been caught at the time.

**Second, found via a same-line `if`/`then`/`else`/`fi` test that
printed nothing from either branch at all**: the body loop checked
for `fi` before checking for `else` in the remaining tokens. When
both are present on the same line (`"then a; else b; fi"`), checking
`fi` first finds the *later* one, incorrectly swallowing the real
`else` in between as if it were ordinary body text - both branches
got silently suppressed together, since the whole "then a; else b"
span got treated as one (correctly-skipped) then-branch body line.
Fixed with a new `SPLIT-AT-EITHER-KEYWORD`, scanning for both `else`
and `fi` in one pass and splitting at whichever is actually found
first.

**Third, found via a nested same-line if that printed the wrong
branch's output disappearing partway through**: neither
`SPLIT-AT-KEYWORD` nor `SPLIT-AT-EITHER-KEYWORD` originally accounted
for nesting depth at all - a *nested* if's own `else`/`fi` (still
inside its own span) got mistaken for the outer if's own, since the
scan just found the first textual match regardless of context. Fixed
by tracking `if`/`fi` nesting depth during the scan itself (an
unquoted `if` increments depth, an unquoted `fi` decrements it -
`else`/`fi` only count as *this* if's own keyword when depth is back
to 0) - verified via a standalone diagnostic before integrating,
confirming a hand-traced case (an outer `if`/`then`/`fi` wrapping a
complete nested `if`/`then`/`else`/`fi`) correctly found the *outer*
`fi`, not the inner one.

**A fourth, more subtle bug, found via a stray literal semicolon
appearing in output only when nesting was involved, never in
isolation**: `NORMALIZE-OPERATORS` (Iteration 24's whole point) had
only ever been wired into `RUN-LINE` - never into
`READ-LINE-INTO-ARGV`, the *separate* line-reading path `DO-IF`/
`DO-WHILE`/`DO-FOR` use internally to read a fresh `then`/`else`/`fi`
line when nothing is pending. A body line read this way kept its
operators fused together exactly as if Iteration 24 had never
happened, since it never went through the pre-pass at all - "echo
inner-else; fi", read this way, kept "inner-else;" as one literal
token rather than splitting off the `;`. Confirmed by testing the
identical construct in isolation (worked correctly, since that path
happened to go through `RUN-LINE`) versus embedded inside an outer
`if`'s body (broken, since that path goes through `READ-LINE-INTO-
ARGV` instead) - the same construct, two different code paths, only
one of which had been fixed. Applied the identical normalize-and-
fallback pattern to `READ-LINE-INTO-ARGV` too (after yet another
file-ordering relocation to keep `NORMALIZE-OPERATORS` defined before
its new caller - the fifth such relocation this project has needed).

### A documented, deliberate scope limit, re-confirmed rather than newly discovered

Content after the *final* `fi` on the same line (e.g. `"if x; then y;
fi; z"`) is silently dropped - `"z"` never runs, whether or not the
`if` is nested inside another one. This was already documented as an
accepted limitation when `SPLIT-AT-KEYWORD` was first designed
(preserving it correctly needs propagating a pending remainder *up*
the call stack to whatever called `DO-IF`, a bigger change than this
iteration attempted) - re-confirmed directly (both in a simple,
non-nested case and inside a nested construct) to make sure the
nested case's missing output was this known gap, not a new bug.

### Verified end-to-end via `relfsh` and confirmed on i386

`if true; then echo yes; fi` (basic); `if false; then ...; else ...;
fi` taking the else branch and vice versa; a same-line nested `if`/
`else` embedded inside a multi-line outer `if`, correctly running
only the inner branch that should run plus the outer body that
follows it; the original, fully separate-line style confirmed
unchanged; exit-status propagation for both a bare successful `if`
and a false condition with no `else`.

`tests/shell/run-if-sameline` (10 assertions) locks all of this in -
140 assertions across 22 files now, all passing on both x86-64 and
i386. `tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3
skipped - expected, since `if.sh` itself also needs `$#` (positional
parameter count) and `elif` (not implemented) before it can pass as a
whole file, even though this is real, necessary progress toward it.

## Iteration 26: fix a real, pre-existing token-corruption bug in $VAR/$(...) expansion

Goal: originally set out to implement `case`/`esac` (phase C), but while
testing it directly against a realistic script, found that `case`
wasn't broken - the *case word itself* was silently corrupted before
`case` ever saw it. Tracing that down surfaced a genuine, independent,
pre-existing bug in ordinary `$VAR` expansion, confirmed via `git
stash` to already exist in the committed Iteration 25 state - not
introduced by anything in this session's own work. This closes that
bug; `case`/`esac` itself is still not done and remains for a
follow-up.

### The bug

`echo $x in` (with `x=hello` set beforehand) printed `hellollo`
instead of `hello in` - both the trailing text and the token count
were wrong (`$ARGC` came out one short too). Narrowed down
methodically: confirmed the *stored* shell-variable value was correct
(`abc`, not corrupted, when checked directly via
`SHVAR-VALUE-SLOT`/`CSTRLEN` right after `export x=abc`), so the
corruption happens during *expansion*, not storage. Confirmed the
*pre-expansion* text is untouched (`NORMALIZE-OPERATORS`, Iteration
24's own pre-pass, correctly leaves `$x` alone, since neither `$` nor
`x` are operator characters) - so the corruption happens specifically
during `TOKENIZE` itself, inside `EXPAND-VAR`.

### Root cause

`TOKENIZE`'s in-place token compaction relies on an assumption stated
directly in its own comment: after `SCAN-TOKEN` returns, `TOK-OUT`
(the write cursor, where compacted/expanded characters get written)
"coincides with" `TOK-POS` (the read cursor, tracking how far into
the original line has actually been consumed) - true for quote-
stripping and escape-processing, since those only ever *remove*
characters, never add more than were there originally. `$VAR`
expansion breaks this assumption outright: `TOK-POS` advances by
`len("$" + name)` (2, for `$x`), while `TOK-OUT` advances by
`len(value)` (3, for `abc`) - whenever the value is *longer* than its
own reference text, `TOK-OUT` overtakes `TOK-POS`, and the write
lands on top of input `TOK-POS` hasn't read yet, destroying it before
it's ever seen. Worse: `SCAN-TOKEN`'s own loop then reads that
just-overwritten byte as if it were real input, and re-emits it one
position further along - which overwrites the *next* character too,
and the next, cascading in a self-propagating "smear" of whatever
character was last written, until the line runs out. Traced this
byte-for-byte against the real failing case (`echo $x in`, `x=abc`)
and it exactly reproduces `abcccc`: `a`, `b` written correctly at the
value's own first two bytes, then the third byte (`c`) overwrites the
line's own separator character, which `SCAN-TOKEN` then re-reads and
re-emits repeatedly until end of line - four `c`s total, matching
`abcccc` exactly.

Confirmed the same hazard exists in `$(...)` command substitution too
(`EXPAND-CMDSUB`'s own output-emitting loop has the identical shape:
`TOK-POS` is already fully advanced past the whole `$(cmd)` construct
before the captured output gets emitted character by character, with
no length check against the original reference text either) - fixed
both in one pass rather than only the one that was directly observed
failing.

### Why the existing test suite never caught this

Every existing expansion test happened to avoid the exact combination
needed to trigger it: either the expansion sat at the very end of the
line (nothing following it to corrupt, even if `TOK-OUT` did overtake
`TOK-POS`), or the expanded value was no longer than its own
`$NAME`/`${NAME}` reference text (an unset variable expanding to
nothing, `${FOO}suffix` where the value happened to be shorter than
`${FOO}` itself, `$PIPECHAR` expanding to a single `|` character). Not
a careless gap so much as an unlucky one - a genuinely common pattern
(`$VAR` followed by more text, with a value longer than the variable
reference) that the existing tests simply never happened to combine.

### The fix

A new `ENSURE-ROOM ( n --- )`, called right before writing an
expansion's value: if writing `n` bytes at `TOK-OUT` would overtake
`TOK-POS`, shifts `LINE-BUF[TOK-POS..TOK-END)` rightward by just
enough to prevent it - copying from the end of the range backward, so
the shift itself can't corrupt the very data it's relocating - and
updates `TOK-POS`/`TOK-END` to match. Bounds-checked against
`LINE-MAX`: if there's truly no room left, the shift (and the
expansion after it) is skipped rather than overflowing the buffer -
the pre-existing corruption bug would still occur in that rare
overflow case, but nothing crashes or corrupts memory outside the
buffer, matching this shell's established priority elsewhere. Wired
into both of `EXPAND-VAR`'s call sites (`${NAME}` and plain `$NAME`)
and into `EXPAND-CMDSUB`'s output-emitting loop.

Verified the shift logic itself in isolation first (a standalone
diagnostic setting up the exact byte layout from the real failing
case and checking the result byte-by-byte) before wiring it in -
caught one purely mechanical mistake while doing so (a test that set
`TOK-POS`/`TOK-OUT` to a small literal number like `5` rather than
`LINE-BUF + 5`, an actual address - comparing a real address against
a tiny literal made the shift's own bounds-check loop run far past
where it should have, corrupting/crashing on invalid memory; fixed by
correcting the test, not the shift logic, which was right the first
time once tested properly).

### Verified end-to-end via `relfsh`, confirmed on i386

`echo $x in` now correctly prints `hello in` for `x=hello`, and the
same fix confirmed across a range of value lengths (`a`, `ab`, `abc`,
`abcd`, `abcde`, `abcdef` - only length 3+ ever triggered the original
bug, matching the "value longer than `$x`'s own 2 characters"
threshold exactly), the `${NAME}` brace form, `$(...)` command
substitution with a long captured output, and multiple expansions on
one line.

`tests/shell/run-expand` gained five new assertions targeting this
specific combination directly - 135 assertions across 22 files now,
all passing on both x86-64 and i386. `tests/mrsh-suite/run.sh` wasn't
re-checked this iteration (no new feature added, only a correctness
fix) - expected to stay at 1 passed, 20 failed, 3 skipped, though this
fix is a real prerequisite for several of those files to ever pass,
since `$VAR followed by more text` is an extremely common pattern.

`case`/`esac` (phase C, the item this iteration originally set out to
implement) is still not done - the glob-matching machinery
(`GLOB-MATCH`, tested thoroughly and separately, 22/22 cases passing)
and `DO-CASE`/`CASE-ARM-MATCHES?` are written and load cleanly, but
hadn't been verified working end-to-end before this expansion bug was
found blocking accurate testing of them at all. Picking this back up
is the immediate next step.

## Iteration 27: goal 8 phase C - case/in/esac (with glob-pattern matching)

Goal: finishing what Iteration 26 set out to do but got detoured from
by a genuine, independent bug - `case WORD in PATTERN) <body> ;; ...
esac`, with full glob-pattern matching (`*`, `?`, `[...]` ranges and
negation) and `|` alternation, matching the very first arm whose
pattern matches and never falling through to any later one, the way a
C `switch` can.

### Design

`GLOB-MATCH ( pattern-addr pattern-len text-addr text-len --- f )`
implements the classic iterative two-pointer wildcard-matching
algorithm - no recursion needed. A `*` remembers where it was seen (in
both the pattern and the text) and initially matches zero characters;
if a later mismatch is hit, backtrack to the most recent `*` and let
it consume one more character of text instead, retrying from there.
Bracket expressions (`BRACKET-END` finds where one ends in the
pattern text; `BRACKET-MATCHES?` checks membership, including
`a-z`-style ranges and a leading `!`/`^` negation, with a `]`
immediately after the opening `[` or the negation correctly treated as
a literal member rather than the closer, per POSIX) are handled as a
single, variable-length unit within the same scan, rather than needing
their own separate backtrack state. Tested thoroughly in isolation
first (22 hand-picked cases - exact match, wildcards in every
position, character sets, ranges, negation, a literal `]` as a set
member, length-mismatch edges) before ever being wired into `case`
itself, all passing on the first attempt; the one hiccup along the way
was an unrelated, pre-existing kernel quirk (an empty `S" "` string
literal doesn't parse correctly in this dialect), not a bug in the
matcher.

`DO-CASE` extracts the case word from `ARGV[1]` (already `$VAR`-
expanded during tokenizing) into a dedicated buffer, then reads one
pattern-arm line at a time (`READ-LINE-INTO-ARGV`, matching while/for's
"no same-line support" scope). `CASE-ARM-MATCHES?` handles a real
tokenization wrinkle: a pattern arm's own trailing `)` isn't its own
token the way `;`/`|`/`&&` all became in Iteration 24 - `NORMALIZE-
OPERATORS` deliberately never touches `(`/`)` at all, to avoid breaking
`$(...)` command substitution - so `"he*)"` tokenizes as one fused
token, and the trailing `)` has to be stripped from specifically the
*last* token before testing it as a pattern. Multiple `|`-separated
alternatives are each tried independently; any one matching selects the
arm. Respects `SUPPRESS-EXEC?` throughout, the same principle
established for `if`/`while`/`for`'s own nesting-safety.

A small prerequisite fix, needed for `case`'s own arm terminator:
`;;` was tokenizing as two separate `;` tokens rather than its own
token, since `NORMALIZE-OPERATORS`'s doubled-form check only covered
`&`, `|`, `>` (from Iteration 24). Added `;` alongside them.

### A real bug found and fixed by testing against a realistic, multi-arm script - not by inspection

An early version correctly matched the *first* arm whose pattern
matched, and correctly ran its body - but then kept right on testing
*every later arm too*, and ran any of their bodies that also happened
to match. `CASE-MATCHED?` was being *set* once a match was found, but
never actually *checked* - a pure oversight, not a logic error in the
matching itself. Caught by testing all of mrsh's own `case.sh`
scenarios together in one script rather than one pattern type in
isolation: `he*)` followed by a `*)` default arm printed *both*
arms' output, when only the first should have run at all - the same
shape of bug across every scenario where the *first* arm was the one
that matched (glob, `|` alternation, bracket, `$VAR`-as-pattern), while
scenarios where the *second* arm happened to be the match (exact,
default-only) looked fine by coincidence, since there was nothing
left afterward to incorrectly run. Fixed by actually checking
`CASE-MATCHED? @ 0=` before testing a new arm's pattern at all - once
true, every later arm is still correctly read and discarded (so the
script's own subsequent lines are consumed properly), just never
tested or run.

### Verified end-to-end via `relfsh` and confirmed on i386

All of mrsh's own `case.sh`-style scenarios in one script: exact match,
`*` glob with a non-matching earlier arm and a matching later default,
`?` single-character wildcards, `[a-z]` ranges, `[!...]` negation,
`|` alternation, a `$VAR` expansion used as the pattern itself,
`;;` optional for the item right before `esac`. Also: no arm matching
at all is a harmless no-op (script continues normally afterward); a
matched arm's own exit status becomes the whole case statement's;
`case` inside a skipped `if` branch runs nothing, matching the
established suppress-propagation principle.

`tests/shell/run-case` (16 assertions) locks all of this in - 151
assertions across 23 files now, all passing on both x86-64 and i386.
`tests/mrsh-suite/run.sh` stays at 1 passed, 20 failed, 3 skipped -
`case.sh` itself still needs other features (arithmetic, `$IFS`
splitting in its later sections) before it passes as a whole file,
even though `case`'s own core mechanics are now genuinely correct.

**Phase C is now complete apart from shell functions, `return`, and
`break`/`continue`** - and the previously-noted loop-body-can't-
contain-another-multi-line-construct limitation, which likely
interacts with `break`/`continue` in ways worth thinking through
before starting them.

## Iteration 28: goal 8 phase C - shell functions (`name() { ... }`)

Definition, invocation, redefinition, and recursion for shell
functions. `return` and `break`/`continue` remain (see the end of this
entry).

### Design

A function's body is stored persistently (unlike `while`/`for`, which
replay their own body once immediately and discard it) - reuses the
same "raw text, NUL-separated lines" shape those already use, but each
function gets its own dedicated table slot keyed by name, sized
generously (2048 bytes) since a function body can be arbitrarily long.
`FIND-FUNC`/`SET-FUNC`/`RUN-FUNC-BODY` are the storage/lookup/replay
primitives; a later `SET-FUNC` call for an existing name overwrites
its slot in place (the same "update if found, append if not" shape
`SET-SHVAR` already established for shell variables), which is what
makes redefinition work for free.

`FUNCDEF-NAME?` detects a definition header: `ARGV[0]` ending in `()`
(unquoted, at least one character before the parens) - `name()`
tokenizes as one fused token since `NORMALIZE-OPERATORS` deliberately
never touches parens (to avoid breaking `$(...)`), so this is a
straightforward suffix check, not a new tokenization rule. `DO-FUNCDEF`
then requires a `{` - either later on the same line (the common
`name() {` style, via the same pending-remainder mechanism if's own
same-line `then`/`else`/`fi` detection already uses from Iteration 25)
or on its own line - but, a deliberate, simpler scope cut, each body
line and the closing `}` must be on their own separate line, not fused
with other content the way if's own same-line branches can be.

Recursion needed one more piece of care: `RUN-FUNC-BODY`'s own "which
line of the body am I replaying" position (`FUNC-CUR-I`/`FUNC-BODY-I`)
is saved via `>R` at entry and restored via `R>` before returning,
mirroring the exact principle `COND-TRUE?`/`SUPPRESS-EXEC?` already
established for if's own nesting safety in Iteration 22 - each
invocation's own position only ever reflects *that* invocation's
replay, so a function calling itself (directly, or via another
function) doesn't disturb an outer, still-in-progress call's own
iteration state.

Invocation is checked in `DISPATCH`, ahead of external `PATH` search
(`ARGV[0]` looked up via `FIND-FUNC`; if found, `RUN-FUNC-BODY-CALL`
replays it and reports handled, exactly like a builtin) - existing
builtins (`cd`/`pwd`/`export`/`unset`/`exit`) still take priority if a
function happens to share their name, matching POSIX's own treatment
of these as special builtins.

### A file-ordering complication, solved with the established
### deferred-word pattern rather than moving code around

`DISPATCH` is defined very early (line ~1000), long before a function
body's own storage/replay logic naturally wants to live (down near
`RUN-STORED-LINE`, its main dependency, at ~2100). Rather than
relocating that machinery earlier and risking new ordering slips
elsewhere, `RUN-FUNC-BODY-XT`/`RUN-FUNC-BODY-CALL` follow the same
deferred-word pattern already proven for `RUN-TOKENIZED-CALL`: a
variable holding an execution token, patched to the real word's own
`xt` right after it's defined further down, with a trivial stub
callable from anywhere already loaded. `FIND-FUNC` itself (and its own
minimal table: `FUNC-NAMES`/`FUNC-COUNT`/`FUNC-NAME-SLOT`) *was* moved
earlier, ahead of `DISPATCH`, since it has no such dependency problem
and `DISPATCH` needs to call it directly, not through a deferred stub.

### Two already-documented limitations resurfaced, not new bugs

Recursion needs a base case, which needs a condition, which surfaced
two limitations already on record rather than anything new:

- A function body can't contain another multi-line construct
  (`if`/`while`/`for`) - the same Iteration 23 limitation `while`/`for`
  loop bodies already have, since a function body replays via the
  identical mechanism (`RUN-STORED-LINE` re-tokenizes and runs each
  stored line independently - an `if` line has no way to find its own
  "then"/"fi" from the real input stream, since those aren't part of
  what's stored).
- `$VAR` doesn't expand inside `$(...)` - the Iteration 13 scope limit
  on command substitution's own internal text.

Worked around in testing (and in `tests/shell/run-func`) by using
`&&`/`||` for single-line conditional logic within a function body
instead of a nested `if`, and by advancing state across separate
lines rather than through arithmetic inside a command substitution.

### Two real, independent bugs found while testing recursion - neither specific to functions at all

**1. A standalone assignment inside an `&&`/`||`-chained segment was
never recognized as an assignment.** `x=hello && echo $x` silently
failed: `RUN-AND-OR-CHAIN` calls `RUN-SIMPLE-OR-PIPELINE` directly for
each chained segment, but the assignment-detection check
(`ARGC @ 1 = ... ASSIGNMENT-EQPOS ... DO-ASSIGN`) had only ever lived in
`RUN-TOKENIZED`'s own fall-through, never reached from inside a chain -
`x=hello` was path-searched as a literal, failing command name (status
127) instead, silently short-circuiting everything chained after it.
Fixed by moving that check into `RUN-SIMPLE-OR-PIPELINE` itself (the
one place both the plain, top-level case and every `&&`/`||`-chained
segment actually pass through) - via the same deferred-word pattern as
above (`TRY-ASSIGNMENT-XT`/`TRY-ASSIGNMENT-CALL`), since
`ASSIGNMENT-EQPOS`/`DO-ASSIGN` are themselves defined well after
`RUN-SIMPLE-OR-PIPELINE`.

**2. `COPY-ARGV` never touched `ARGV-QUOTED`, leaving stale flags that
could silently hide a real operator token.** Found via a three-segment
chain (`test ... && flag=second && echo made-it`) where the *second*
`&&` vanished - traced by direct inspection of `ARGV-QUOTED` at the
token's own index, which showed `255` (quoted) for a token that was
never quoted at all. Root cause: `$VAR`/`$(...)` expansion results are
correctly marked "quoted" (so they're never re-interpreted as an
operator or keyword) - but that flag is stored in a *global*,
position-indexed array, and `COPY-ARGV` (used throughout `;`- and
`&&`/`||`-splitting to swap a piece of a line into the global `ARGV`)
only ever copied the `ARGV` pointers themselves, never resetting or
restoring `ARGV-QUOTED` to match. If an earlier piece's own expansion
result had sat at some index *n*, and a later piece's own real
operator token later landed at that same index *n* after being copied
in, the stale "quoted" flag persisted and incorrectly hid it.

  Fixed properly rather than papered over: `SPLIT-SEMI`/`SPLIT-ANDOR`
  now each mirror every entry's own `ARGV-QUOTED` flag, at the moment
  they scan it, into a parallel byte array (`ARGQ-SEMI-LEFT`/
  `ARGQ-SEMI-REST`/`ARGQ-AO-LEFT`/`ARGQ-AO-REST`) alongside their
  existing pointer buffers. A new `COPY-ARGV-Q` (used in place of plain
  `COPY-ARGV` at exactly these call sites - `RUN-AND-OR-CHAIN` and
  `RUN-TOKENIZED`'s own `;`-split) restores the matching flag for each
  entry as it copies the pointer, so a piece's own genuine quoted-
  ness (or lack of it) travels with it correctly instead of picking up
  whatever happened to be at that index beforehand. Plain `COPY-ARGV`
  itself is untouched, and still used as-is everywhere this specific
  hazard doesn't apply (e.g. pipeline segments, group bodies) - not
  because those are known to be safe, just not yet verified, so this
  is noted here as a possible follow-up area rather than claimed fixed.

### A third bug, found by deliberately testing the interaction with `if`

A function *definition* itself never checked `SUPPRESS-EXEC?` at all -
`DO-FUNCDEF` always read and stored the body correctly (necessary, so
the surrounding script's own later lines are consumed properly
regardless), but also always called `SET-FUNC` unconditionally, even
when the definition sat inside a false `if` branch. A function defined
this way was, incorrectly, still callable afterward. Fixed by gating
only the `SET-FUNC` call itself on `SUPPRESS-EXEC?`, the same
"always read, only gate the effect" principle `if`/`while`/`for`/`case`
already established.

### Verified end-to-end via `relfsh` and confirmed on i386

Multi-line body definition and invocation; redefinition (a later
`name()` replaces the earlier one); one function calling another from
within its own body; a function's own exit status correctly reflecting
its last command's status; genuine self-recursion with a properly
gated base case (a bounded flag-progression countdown, avoiding both
resurfaced limitations above); a function defined inside a skipped
`if` branch correctly never taking effect; both new, independent bugs
fixed and confirmed via minimal, isolated reproductions before being
re-tested in the original failing scenario.

`tests/shell/run-func` (9 assertions) locks all of this in, including
the two independent `&&`-chain bugs (a standalone assignment as one
segment of a chain; a three-segment chain with an assignment in the
middle) directly, not just as incidental support for the recursion
test that originally surfaced them - 160 assertions across 24 files
now, all passing on both x86-64 and i386.

**Phase C now has only `return` and `break`/`continue` remaining** -
plus, still on record: the loop-body/function-body multi-line-
construct limitation (which `return` may help work around in some
cases, by giving a function an early-exit that doesn't need a nested
`if` at all, but `break`/`continue` will likely still need to
interact with directly), and the unverified extent of the
`COPY-ARGV`/`ARGV-QUOTED` hazard beyond the two call sites fixed here.

## Iteration 29: goal 8 phase C - `return`

`return [n]` exits the innermost currently-executing function
immediately: `$?` becomes `n` if given, or is left as whatever the
last command's own status already was otherwise (POSIX's own rule).
Everything else in that function's own body - later lines, and any
remaining `;`/`&&`/`||`-chained segments on the *same* line `return`
appeared on - is correctly skipped.

### Design: one flag, checked in exactly two places

`RETURN-PENDING?`, set by the new `return` builtin (alongside
`cd`/`pwd`/`export`/`unset`/`exit` in `DISPATCH`), is checked in:

1. `RUN-SIMPLE-OR-PIPELINE`, alongside the existing `SUPPRESS-EXEC?`
   check - both cause an immediate, no-op exit. This one place is
   reached by *every* individual command or assignment regardless of
   `;`/`&&`/`||` structure (plain fall-through, each `&&`/`||`-chained
   piece, and each `;`-separated recursive call all funnel through it
   eventually), so nothing further in the same logical line runs once
   `return` has fired, without needing a separate check bolted onto
   each splitting word individually - the same reasoning already
   established for why `SUPPRESS-EXEC?` itself is checked only there
   (and in `DO-ASSIGN`).

2. `RUN-FUNC-BODY`'s own replay loop condition, so the invocation
   also stops advancing to its own next stored body line - and,
   critically, `RUN-FUNC-BODY` resets `RETURN-PENDING?` back to false
   *before* returning to its own caller (restoring the saved
   `FUNC-CUR-I`/`FUNC-BODY-I` via `R>`), regardless of whether the loop
   ended normally or via a return. This is what keeps recursion safe:
   an inner, nested invocation's own return is fully "consumed" by
   that invocation alone and never leaks out to also stop an outer,
   still-in-progress caller - verified directly (`inner`/`outer` test
   below), not just asserted from the design.

A new `FUNC-DEPTH` counter (incremented/decremented symmetrically
around `RUN-FUNC-BODY`'s own body) lets a top-level `return` - outside
any function at all - be diagnosed with a message rather than
silently setting a flag nothing will ever consume, which would
otherwise wedge every following command in the entire remaining
script (nothing else resets `RETURN-PENDING?` except `RUN-FUNC-BODY`
itself).

### Verified end-to-end via `relfsh` and confirmed on i386

Went smoothly - every case passed on the first attempt, likely because
the two independent bugs the function feature itself surfaced
(Iteration 28's assignment-in-`&&`-chain and `COPY-ARGV`/`ARGV-QUOTED`
fixes) were already in place before this started, and because the
single-flag, two-check-point design was thought through fully before
writing any code, rather than discovered through trial and error.
Confirmed: a bare `return` stops the rest of its own function's body;
an explicit status (`return 5`) sets `$?`; a bare `return` after a
failing command leaves `$?` as that failure; `return` used as one
segment of an `&&`-chain stops the rest of that chain *and* the rest
of the function's body, not just that one chained piece; a nested
function's own `return` unwinds only that function, correctly letting
its caller continue normally afterward; and a top-level `return`
prints a diagnostic and the script continues rather than hanging or
crashing.

`tests/shell/run-return` (10 assertions) locks all of this in - 170
assertions across 25 files now, all passing on both x86-64 and i386.
mrsh-suite unchanged (1 passed, 20 failed, 3 skipped) -
`return.sh` itself still needs the `:` no-op builtin (not yet
implemented) and a `while` loop nested inside a function body (the
already-documented multi-line-construct limitation) before it can
pass as a whole file.

**Phase C now has only `break`/`continue` remaining.**

## Iteration 30: goal 8 phase C - `break`/`continue`

`break` exits the innermost enclosing `while`/`for` loop immediately;
`continue` skips the rest of the current iteration's own body and
proceeds to the next iteration as usual. Both are recognized even
when called from within a function that a loop's own body happens to
call - the trickiest case, thought through carefully before writing
any code rather than discovered through trial and error, and verified
directly, not just assumed correct from the design.

### Design: two flags, mirroring and extending `return`'s own approach

`RETURN-PENDING?` (Iteration 29) is "consumed" the moment its
enclosing function returns - break/continue can't work the same way,
since the loop they're meant for might be several function-call
frames further out than wherever they were actually called. This
needed two flags instead of one, plus a depth counter:

- **`LOOP-CONTROL-PENDING?`** - set by either `break` or `continue`.
  Checked in the same three places `RETURN-PENDING?` already is
  (`RUN-SIMPLE-OR-PIPELINE`, so nothing further in the same logical
  line runs; and both `RUN-FUNC-BODY`'s and `DO-WHILE-BODY`'s own
  replay loops) - but, unlike `RETURN-PENDING?`, only `DO-WHILE-BODY`
  ever resets it. `RUN-FUNC-BODY` *checks* it (stopping that
  function's own body early, the same as for a `return`) but
  deliberately *leaves it set* - so it keeps propagating outward
  through however many nested function calls separate the break/
  continue from the loop iteration it's actually meant for, until it
  finally reaches a `DO-WHILE-BODY` call, which is what "one loop
  iteration" actually corresponds to.
- **`LOOP-BREAK?`** - set only by `break`, not `continue`. Survives
  past `DO-WHILE-BODY`'s own reset of `LOOP-CONTROL-PENDING?` (which
  only marks *that iteration* as over), checked by the outer while/for
  loop itself (`DO-WHILE`/`DO-FOR-ITERATE`) right after each
  `DO-WHILE-BODY` call: if set, stop iterating entirely; if not
  (`continue` was called, or the body simply ran to completion),
  proceed to the next iteration exactly as normal - `continue` needs
  no special handling of its own beyond this, since "the iteration
  ended early" and "the iteration ended normally" already lead to the
  identical next step.
- **`LOOP-DEPTH`** - incremented/decremented around `DO-WHILE`/
  `DO-FOR-ITERATE` (the outer loop entry points), mirroring
  `FUNC-DEPTH`, so break/continue outside any loop can be diagnosed.
  Doesn't need `>R`/`R>` nesting the way `FUNC-DEPTH`'s own analogues
  do for recursion: a loop body (or a function called from one) can't
  yet contain another `while`/`for` construct at all (the existing
  multi-line-construct limitation), so two loops can never be
  simultaneously in progress - a plain reset at each loop's own
  entry/exit is enough.

`DO-WHILE`'s own outer Forth-level loop folds `LOOP-BREAK?` directly
into its own condition (`LOOP-BREAK? @ 0= IF [re-evaluate the real
condition] ELSE 0 THEN`), so a break during the previous iteration
skips even *evaluating* the real condition again, rather than
evaluating it and then discarding the result. `DO-FOR-ITERATE` does
the same, `AND`ed into its own "more words remain" check.

### Verified end-to-end via `relfsh` and confirmed on i386

Went smoothly given the design was thought through fully first - every
case passed on the first attempt. Two test-design missteps along the
way, neither a bug in `break`/`continue` themselves: an early loop
test tried to update a counter via `$(expr $x + 1)`, hitting the
already-documented "`$VAR` doesn't expand inside `$(...)`" limitation
again; and a first attempt at a bounded break condition chained two
`test ... && set ...` lines in the same iteration, so the flag
cascaded through both its states within one single pass rather than
across two - fixed by checking the flag's value *before* setting it
each iteration, so the check always reflects the previous iteration's
final state.

Confirmed: `break` stops a `while` loop after the iteration it's
called in; `continue` skips the rest of that iteration but the loop
still proceeds; both work equivalently in a `for` loop (stopping
before, or skipping just, the word being processed when called); and
critically, `break` called from within a function invoked by a loop
body correctly stops the outer loop, skipping both the rest of that
function's own body *and* the rest of the loop iteration's own body
(the line that called the function) - the exact scenario the two-flag
design above exists for. A top-level `break`/`continue` (outside any
loop) is diagnosed and the script continues rather than hanging or
corrupting later execution.

`tests/shell/run-break-continue` (12 assertions) locks all of this in
- 182 assertions across 26 files now, all passing on both x86-64 and
i386. mrsh-suite unchanged (1 passed, 20 failed, 3 skipped) -
`loop.sh` itself still needs `[ ... ]` bracket-test syntax and `if`
nested inside a `while` loop's own body (the multi-line-construct
limitation) before it can pass as a whole file.

**Phase C is now complete: `if`/`while`/`for`/`case`, shell functions,
`return`, and `break`/`continue` are all implemented.** Remaining,
carried-over items for future work: the loop-body/function-body
multi-line-construct limitation (now touched by three separate
features - `while`/`for` nesting, function bodies, and `break`/
`continue` - making it an increasingly valuable thing to eventually
fix properly via genuine read-ahead into stored lines); the unverified
extent of the `COPY-ARGV`/`ARGV-QUOTED` hazard beyond the two call
sites fixed in Iteration 28; and, next, Phase D (expansions:
positional parameters, parameter-expansion modifiers).

## Iteration 31: goal 8 phase D - positional parameters (`$1`-`$9`,
## `$#`, `$@`/`$*`, `set`)

The first Phase D feature. Positional parameters now work at both the
top level (from a script's own command-line arguments) and within a
function (from its own call arguments), including correct save/restore
across nested and recursive function calls.

### Design

Storage: `POS-PARAMS` (9 fixed-size slots - single-digit access only,
`$1`-`$9`, a documented scope limit; `${10}` and beyond would need
`EXPAND-VAR`'s own `${NAME}` braced path to accept a decimal name, not
just POSIX portable name characters, left for later) and
`POS-PARAM-COUNT`. `EXPAND-VAR` gained: `$1`-`$9` (a digit-range check
using subtraction rather than `>=`, which doesn't exist as a kernel
word - `char - 48` in `[1,9]`); `$#` (emits `POS-PARAM-COUNT` as
decimal); `$@`/`$*` (space-joined via a new `EMIT-ALL-POS-PARAMS` -
deliberately treated identically for now, since the two only actually
differ once quoted, and `IFS` field splitting doesn't exist yet to
make that distinction meaningful).

Three ways positional parameters get set, all funneling through the
same `SET-POS-PARAMS-FROM-ARGV` (reads whatever's currently in the
global `ARGV[1..]`/`ARGC`):

- **A function's own call arguments** - `RUN-FUNC-BODY` calls it right
  as invocation begins, while the global `ARGV` still holds the
  calling line (before the function's own first body line is replayed
  and overwrites it).
- **The `set` builtin** - `SET-POS-PARAMS-FROM-ARGV` already does
  exactly what `set a b c` needs, since `ARGV[1..]` at that point
  simply *is* `a b c`. Scope limit: real `set` also supports option
  flags (`-e`, `-x`, etc.) with no positional-parameter arguments at
  all - not handled here, so `set -e` would be (mis)treated as setting
  `$1` to the literal string `-e`.
- **A script's own command-line arguments** - a sibling,
  `SET-POS-PARAMS-FROM-SYS-ARGS`, reads `SYS-ARG(1)` onward (relf's
  own argv, exposed to Forth - `SYS-ARG(0)` is the script path itself,
  already consumed by `SH-FILE`), called once from the top-level
  dispatch right before `SH-FILE` runs.

Nesting: a `POS-PARAMS-SAVE`/`POS-PARAM-COUNT-SAVE` stack, indexed by
`FUNC-DEPTH`'s own current value - mirroring `FUNC-CUR-I`/
`FUNC-BODY-I`'s own `>R`/`R>` nesting conceptually (each invocation's
own state saved before going deeper, restored on the way back out),
just needing an explicit save/restore pair rather than `>R`/`R>` itself
since a whole parameter list isn't a single cell. `RUN-FUNC-BODY` saves
the caller's own positional parameters (keyed by `FUNC-DEPTH`'s
pre-increment value) before setting up the new ones, and restores them
(keyed by the same value, now post-decrement) right before returning -
so a function called from within another function, or a function
calling itself recursively, each see only their own arguments,
regardless of how deep the nesting goes.

### A file-ordering fix and a real bug found by testing

`ARGV@` was defined much later in the file than needed (after
`EXPAND-VAR`'s own new callers of it) - moved to right after `ARGV`
itself is declared, near the top of the file, rather than adding
another deferred-word indirection for something this trivial.

**Real bug**: `SAVE-POS-PARAMS`'s own `MOVE` call had its source and
destination backwards - it copied *from* the (stale, often
uninitialized) save slot *into* the live `POS-PARAMS`, rather than the
other way around, silently corrupting the current parameters instead
of preserving them. Invisible in a simple, single-level function-call
test (where nothing reads `$1` again after a nested call returns) and
even in a first recursion test (where the recursive call happened to
be the last line of its own caller's body) - only surfaced once a
nested (non-recursive) call test explicitly re-checked `$1` *after*
the inner call returned, expecting to see the outer function's own
argument still intact. Fixed with a single `SWAP` to correct the
`MOVE` arguments' order; `RESTORE-POS-PARAMS`'s own direction was
already correct.

### Verified end-to-end via `relfsh` and confirmed on i386

Confirmed: a function's own call arguments become `$1`/`$2`/`$#`/`$@`
within its body; an unset positional parameter (`$3` when only two
were given) expands to empty rather than erroring; a nested function
call's own arguments don't leak into the caller, and the caller's own
`$1` is correctly restored once the nested call returns (the case the
bug above was found in); a recursive function call's own `$1` is
independent per invocation; the `set` builtin populates `$1..` at the
top level; and a script's own command-line arguments become `$1..`
from the very start, without needing an explicit `set` call.

`tests/shell/run-posparams` (6 assertions) locks all of this in - 188
assertions across 27 files now, all passing on both x86-64 and i386.
mrsh-suite unchanged (1 passed, 20 failed, 3 skipped) - `args.sh`
itself needs `getopts` and parenthesized (subshell) function bodies,
neither related to positional parameters, before it can pass.

**Phase D remaining**: parameter-expansion modifiers (`${VAR:-word}`,
`${VAR:=word}`, `${VAR:+word}`, `${#VAR}`,
`${VAR%word}`/`${VAR%%word}`/`${VAR#word}`/`${VAR##word}`); arithmetic
expansion (`$((...))`); tilde expansion; `IFS`-based field splitting of
unquoted expansion results.

## Iteration 32: goal 8 phase D - parameter-expansion modifiers
## (default/assign/alternate value, length)

`${#VAR}` (length), `${VAR:-word}`/`${VAR-word}` (default value),
`${VAR:=word}`/`${VAR=word}` (assign default), `${VAR:+word}`/
`${VAR+word}` (alternate value). The `:`-prefixed variants trigger on
`VAR` being either unset *or* empty; the plain variants trigger on
unset only - a distinction that matters and is tested explicitly for
each pair. `${VAR%word}`/`${VAR%%word}`/`${VAR#word}`/`${VAR##word}`
(prefix/suffix removal) remain for a follow-up iteration - genuinely
new pattern-matching logic, not just string comparison, unlike
everything else here.

### Design: extracted into a dedicated `EXPAND-BRACED-VAR`, replacing the old inline `${NAME}` block

The previous `${...}` handling in `EXPAND-VAR` just read everything up
to the closing `}` as one blob and looked it up directly - workable
for a plain name, but a modifier like `${VAR:-word}` would have been
looked up (and fail to be found) as a single, literal variable name
`"VAR:-word"`. Replaced with a new word, `EXPAND-BRACED-VAR`, built
from two small, reusable pieces: `READ-VARNAME` (like the old parsing,
but stops at the first non-name character instead of consuming through
`}`, so the caller can inspect what follows) and `READ-PEWORD` (reads
the "word" portion up to the closing `}`).

Dispatch, in order: `${#VAR}` detected by `#` immediately after `{`
(before any name is even read, since `#` can't itself be a name
character); then the variable name; then whatever follows it - `}`
(the plain, unmodified case, unchanged from before), or an optional
`:` followed by one of `-`/`=`/`+`. Each of the three checks `LOOKUP-VAR`
directly (its 0-vs-address return already distinguishes "unset" from
"set", even set-to-empty, so no separate "is it set" check was
needed) and combines that with `CSTRLEN 0=` (is the value empty) `AND`
the colon flag to decide whether the modifier fires - one boolean
expression per case, mirrored across all three modifiers.

### Verified end-to-end via `relfsh` and confirmed on i386

Every case passed on the first attempt: length; default value on
unset; the actual value used when set and non-empty; the `:`-vs-plain
distinction on an empty variable (confirmed both ways, `:-` firing on
empty while plain `-` does not); assign-default (confirmed the
variable was genuinely set afterward, not just expanded once); and
alternate-value in all four combinations (set/unset × colon/no-colon).

`tests/shell/run-param-modifiers` (8 assertions) - 196 assertions
across 28 files now, all passing on both x86-64 and i386.

**Phase D remaining**: `${VAR%word}`/`${VAR%%word}`/`${VAR#word}`/
`${VAR##word}` (prefix/suffix removal); arithmetic expansion
(`$((...))`); tilde expansion; `IFS`-based field splitting.

## Iteration 33: goal 8 phase D - `${VAR%word}`/`${VAR%%word}`/
## `${VAR#word}`/`${VAR##word}` (prefix/suffix removal), plus a
## significant kernel-behavior discovery

`${VAR#pattern}`/`${VAR##pattern}` (shortest/longest matching prefix
removed), `${VAR%pattern}`/`${VAR%%pattern}` (shortest/longest
matching suffix removed) - the last of the parameter-expansion
modifiers listed in `GOALS.md`. **Phase D's remaining scope is now
just arithmetic expansion, tilde expansion, and `IFS` field
splitting.**

### Design

Built on `GLOB-MATCH` (already existing, from `case`/`esac`'s own
Iteration 27 pattern matching), but `GLOB-MATCH` only answers "does
this whole string match this pattern" - prefix/suffix removal needs
"what's the shortest/longest *partial* prefix/suffix that matches",
which is new. `FIND-SHORTEST-PREFIX-LEN`/`FIND-LONGEST-PREFIX-LEN`/
`FIND-SHORTEST-SUFFIX-LEN`/`FIND-LONGEST-SUFFIX-LEN` each try
candidate lengths one at a time against `GLOB-MATCH` - 0,1,2,...,
value-len for shortest, value-len,value-len-1,...,0 for longest -
stopping at the first length that matches (or reporting no match at
all if none does, all the way down to/up from 0). `TRIM-PARAM` ties
this together: looks up the variable, picks the right one of the four
helpers based on flags `EXPAND-BRACED-VAR` sets before calling it, and
emits either the matched-around remainder or (no match) the value
unchanged, per POSIX. A new `TYPE-N-TO-TOK ( addr n --- )` fills the
same role `TYPE0-TO-TOK` does for NUL-terminated strings, but for a
known-length span - needed because the "remainder after a match" isn't
itself NUL-terminated at the right point without a separate copy.

Since `GLOB-MATCH` is defined much later in the file than
`EXPAND-BRACED-VAR` (down near `case`/`esac`, sharing that machinery),
`TRIM-PARAM` lives there too, reached via the same deferred-word
pattern used throughout this project (`TRIM-PARAM-XT`/
`TRIM-PARAM-CALL`) - `EXPAND-BRACED-VAR` detects `%`/`%%`/`#`/`##`
after a variable name (distinct from `${#VAR}`'s own `#`, which is
checked before any name is even read), sets `PEW-SUFFIX?`/
`PEW-LONGEST?`, reads the pattern via the already-existing
`READ-PEWORD`, and calls through.

### A significant kernel-behavior discovery: multi-line `(...)` comments become unreliable once enough code precedes them in the file

While wiring this up, `shell.4` stopped loading at all, with a
cascading series of `Undefined word X` errors - X being different,
unrelated words each time a fix was attempted, which was the first
clue this wasn't an ordinary syntax mistake in the new code. Isolated
minimal-file tests of long comments, multi-line comments, and
comments with special characters all loaded fine on their own. A
custom Forth-token-aware paren-balance checker found no imbalance in
the real file. Bisection (truncating `shell.4` at successive, cleanly-
closed points and forcibly closing the word being tested) narrowed
the failure to a specific, six-line, unmodified, pre-existing comment
(the `$@`/`$*` one from Iteration 31) that had never been touched in
this session at all.

**Confirmed the root cause empirically**: inserting 200 completely
unrelated, trivial filler word definitions before that comment, in an
otherwise pristine, last-committed `shell.4`, reproduced the identical
failure - proving this has nothing to do with the actual feature code
being added. Collapsing that one, pre-existing multi-line comment onto
a single line (no content change, purely reformatting) fixed loading
immediately, with the full regression suite passing clean afterward
with no other changes needed.

**The empirical rule, going forward**: a `(...)` comment that spans
multiple physical lines can silently corrupt parsing once enough code
precedes it earlier in the file - the exact threshold is unclear (line
count vs. byte count vs. something else was not conclusively
isolated, and early attempts to pin it down produced inconsistent
results between test runs that aren't yet understood), but the fix
that works reliably is simple: **keep every `(...)` comment on a
single physical line**, however long, and use `\` line comments
(which are already used pervasively throughout this file, and were
never observed to have this problem regardless of length or
position) for anything that needs multiple lines. This is a
significant, project-wide risk given how many multi-line `(...)`
comments already exist in `shell.4` from earlier iterations, all
currently fine only because the dictionary hasn't yet grown enough to
expose them - **future iterations should watch for this specific
symptom** (a cascade of unrelated "Undefined word" errors right after
an edit that "should" be safe) and know to check for multi-line
`(...)` comments first, rather than assuming a logic bug in whatever
was just added.

### Verified end-to-end via `relfsh` and confirmed on i386

Confirmed: shortest prefix removal, longest prefix removal, shortest
suffix removal, longest suffix removal, a non-matching pattern
leaving the value unchanged, and an unset variable expanding to empty.

`tests/shell/run-param-trim` (6 assertions) - 202 assertions across
29 files now, all passing on both x86-64 and i386.

**Phase D remaining**: arithmetic expansion (`$((...))`); tilde
expansion; `IFS`-based field splitting.

## Iteration 34: goal 8 phase D - tilde expansion

A bare `~` at the very start of a word expands to `$HOME` - whether
it's the whole word (`~`) or immediately followed by `/` (`~/path`).
Scope limit: only this bare form is supported; `~user` (another
user's home directory, needing a password-database lookup this shell
has no access to) and `~+`/`~-` (`$PWD`/`$OLDPWD` - this shell doesn't
track `$OLDPWD` at all) are not implemented, and a `~` in either of
those shapes, or anywhere but the very start of a word, is left
untouched as a literal character.

### Design

`TRY-TILDE-EXPAND`, called once at the very start of `SCAN-TOKEN`
(before any other character of the token is processed, and before the
existing quote/escape/`$VAR` handling in its main loop even begins) -
since tilde expansion only ever applies right at the start of a word,
this is the one place it needs to be checked, not woven into the
per-character loop itself. A no-op unless `TOK-POS` is sitting on an
unquoted `~` that's either the whole token (followed by whitespace or
end of input) or immediately followed by `/`; otherwise the `~` is
left alone for the main loop to copy through as an ordinary character.
When it does fire, reuses the exact same `LOOKUP-VAR`/`TYPE0-TO-TOK`/
`ENSURE-ROOM` mechanism `$VAR` expansion itself already uses, so a
longer `$HOME` value correctly grows the token in place the same way.

A real bug found immediately by testing: the first attempt called
`LOOKUP-VAR` with `S" HOME"` directly - but `S" ..."` leaves `(addr
len)` on the stack, while `LOOKUP-VAR` expects a single NUL-terminated
`(name-addr)`. This silently corrupted the stack (consuming `len` as
if it were the name address, leaving the real address stranded) and
crashed with a segfault on the very first test of the feature actually
firing. Fixed by copying `"HOME"` into the already-existing
`ENVNAMBUF` scratch buffer first and NUL-terminating it - the same
established pattern this file already uses in two other places for
exactly this "reference a `GETENV`/`LOOKUP-VAR` key by name" need.

### Verified end-to-end via `relfsh` and confirmed on i386

Confirmed: a bare `~` expands to `$HOME`; `~/path` expands the `~` and
keeps the rest of the path; a `~` not at the start of a word is left
untouched; `~user` (out of scope) is left untouched; and a quoted
`"~"` is never expanded, matching POSIX (tilde expansion doesn't apply
inside quotes).

`tests/shell/run-tilde` (6 assertions) - 208 assertions across 30
files now, all passing on both x86-64 and i386.

**Phase D remaining**: arithmetic expansion (`$((...))`); `IFS`-based
field splitting.

## Iteration 35: goal 8 phase D - arithmetic expansion (`$((...))`)

A real, precedence-climbing recursive-descent expression grammar,
matching C/POSIX precedence: `||` (loosest) → `&&` → `==`/`!=` →
`<`/`>`/`<=`/`>=` → `+`/`-` → `*`/`/`/`%` → unary `-`/`+`/`!` →
literals/variables/parenthesized subexpressions (tightest). Scope
limits, all deliberate: no bitwise operators (`&`, `|`, `^`, `<<`,
`>>`, `~`), no ternary (`?:`), no assignment forms or `++`/`--` within
the expression, decimal literals only (no octal/hex). An unset
variable, or one whose value isn't itself a (possibly `-`-prefixed)
run of digits, is treated as 0 - this shell's own established
"harmless fallback over a hard error" style, used throughout for
`LOOKUP-VAR`/`EMIT-DECIMAL` and friends elsewhere in this file.

### Design

Seven mutually-recursive Forth words (`AE-OR`/`AE-AND`/`AE-EQ`/
`AE-REL`/`AE-ADD`/`AE-MUL`/`AE-PRIMARY`), each level calling the one
below it, with `AE-PRIMARY` reaching back up to `AE-OR` for
parenthesized subexpressions - via the same deferred-word pattern
used throughout this project (`AE-OR-XT`/`AE-OR-CALL`), since a
seven-level mutual-recursion chain is far more readable as separate,
named levels than one giant nested word. Operates on `ARITH-BUF`, a
private copy of the expression text with its own `AE-POS`/`AE-END`
position tracking, entirely separate from the main tokenizer's own
`TOK-POS`/`TOK-END` - the evaluator has no awareness of quoting,
`$VAR` expansion, or anything else about the outer command line, only
of the extracted expression text itself. `EXPAND-ARITH` does the
extraction: scans from right after `$((` for the matching `))`,
tracking how many extra, unmatched `(` are open *within* the
expression itself so a nested `$(( (1+2)*3 ))` isn't mistaken for the
expansion's own closing pair, then calls the evaluator and emits the
result as a decimal number. `PARSE-DECIMAL`/`PARSE-N` moved much
earlier in the file (same reasoning as `ARGV@` in Iteration 31) so the
evaluator's own numeric variable-lookup can call it directly.
`EXPAND-VAR`'s existing `$(` check now looks one character further
ahead: a doubled `(` means arithmetic expansion; otherwise, unchanged,
command substitution.

### Two real bugs found by testing before wiring into `shell.4`

Built and thoroughly verified in an isolated diagnostic first (22
cases: precedence, associativity, parentheses, unary minus, modulo,
every comparison operator, logical `&&`/`||`, variable references
including unset ones, nested parentheses) before touching `shell.4`
at all - both bugs below were caught and fixed at that stage, not
after integration:

1. `AE-PRIMARY` called itself by its own name for the unary-operator
   case - but a Forth colon definition isn't in the dictionary until
   its own closing `;` is reached, so referencing a word's own name
   from within its still-being-compiled body fails with "Undefined
   word". Fixed with `RECURSE`, the standard Forth word for exactly
   this.
2. The test harness's own evaluation helper consumed its length
   argument via `MOVE` before it was needed again to compute the
   buffer's end position - fixed with a saved-length variable, the
   same shape `AE-EVAL` itself (the real, shipped word) already uses
   correctly.

### A third, more significant bug found once wired into `shell.4`: `NORMALIZE-OPERATORS` corrupting arithmetic expressions

`$((2<=2))` returned `0` instead of the correct `1`. Traced to
`NORMALIZE-OPERATORS` (Iteration 24) running on the *entire* line
before `$((...))` is even recognized as arithmetic, with no awareness
of arithmetic-expansion regions at all - it inserted a space around
the `<` (one of the shell-level operators it normalizes), turning
`2<=2` into `2 < =2` before the evaluator ever saw it, so what should
have been a single `<=` comparison was parsed as `<` followed by an
unrecognized `=2` (evaluating to 0, since `=` isn't a valid start for
anything in the arithmetic grammar). Confirmed directly by printing
`NORMALIZE-OPERATORS`'s own output for the literal text `$((2<=2))`.

Fixed the same way quoted regions are already protected: two new
tracking variables, `NORM-IN-ARITH?`/`NORM-ARITH-DEPTH`, mirroring
`NORM-IN-SQ?`/`NORM-IN-DQ?`'s own shape exactly. `NORM-AT-ARITH-START?`
detects `$((` at the current position; once inside, every character
is copied through completely untouched (no operator spacing at all,
the same treatment quoted text already gets) until the real closing
`))` is found, tracking nested-paren depth within the expression the
same way `EXPAND-ARITH` itself does, independently, moments later in
the pipeline - the same problem, solved twice, in two different
places that both need it. Verified directly: `$((2<=2))` now survives
normalization completely unchanged, and shell-level `&&`/`<` outside
any `$((...))` region continue to be normalized exactly as before.

### Verified end-to-end via `relfsh` and confirmed on i386

Confirmed: basic arithmetic; `*`/`/`/`%` binding tighter than `+`/`-`;
parentheses overriding precedence; `-` left-associativity; unary
minus; modulo; variable references (set and unset); every comparison
operator; logical `&&`/`||`; nested parentheses within the expression
itself; plain `$(...)` command substitution still working correctly,
distinguished from `$((...))`; and arithmetic expansion used directly
as another command's own argument (e.g. inside a `test` invocation).

`tests/shell/run-arith` (15 assertions) - 223 assertions across 31
files now, all passing on both x86-64 and i386.

**Phase D remaining**: `IFS`-based field splitting of unquoted
expansion results - the last item in Phase D's own scope.

## Iteration 36: goal 8 phase D - `IFS`-based field splitting (Phase D complete)

An unquoted `$VAR`/`${...}`/`$(...)`/`$((...))` expansion result is
split into separate `ARGV` entries wherever a run of `IFS` whitespace
appears within it. Scope limits, both deliberate: only space/tab are
treated as `IFS` (not yet a customizable `$IFS` shell variable, and
not newline either); the split itself is per-character rather than
tied to a single, pre-parsed expansion boundary, so it composes
correctly with literal text before/after the expansion within the
same word (e.g. `foo$xbar` correctly merges the literal prefix/suffix
with the first/last split field, matching real shell behavior),
verified directly rather than assumed.

### Design

Built and verified in an isolated diagnostic first, mirroring a
minimal version of `TOKENIZE`'s own token-recording shape (`ARGV`/
`ARGC`/`TOK-OUT`), before touching the real tokenizer. `EMIT-EXPANDED-
CHAR` is the new per-character emission path used *only* for
expansion results (in place of `EMIT-TOK-CHAR`, still used for literal
characters and anything already inside real double quotes): an `IFS`
character sets `IFS-SPLIT-PENDING?` rather than emitting anything
immediately - the actual split (`IFS-SPLIT-HERE`: `NUL`-terminate the
current `ARGV` entry, advance `ARGC`, start the next entry right
after) is deferred until the *next* non-`IFS` character actually needs
writing. This single deferral does double duty: a run of consecutive
`IFS` characters collapses into one split rather than several empty
ones, and trailing `IFS` whitespace at the very end of the expansion
(or the token) never produces a spurious empty trailing field, since
nothing ever gets written to commit it. A parallel check (only split
if `TOK-OUT` has actually moved past where the current entry started)
handles the leading-whitespace case the same way, found necessary by
testing directly - without it, `$x` with `x=" ab"` produced a
spurious *empty* leading field.

Wired into `TOKENIZE`'s outer loop (resetting `IFS-SPLIT-PENDING?` per
token, alongside the existing `TOK-WAS-QUOTED?` reset) and every
expansion-result emission site across `$VAR`/`${...}` (including all
four parameter-expansion modifiers and prefix/suffix trimming from
Iterations 32-33), `$1`-`$9`, and `$@`/`$*` (switching their shared
`TYPE0-TO-TOK` calls to a new `TYPE0-TO-TOK-SPLIT`, and the `$@`/`$*`
join-separator itself from a plain space to `EMIT-EXPANDED-CHAR`, so
the separator participates in splitting exactly like any other `IFS`
character would).

### A real bug found immediately after wiring in: reused the wrong "am I quoted" flag entirely

First attempt checked `TOK-WAS-QUOTED?` to decide whether to split -
but that flag is set unconditionally by `EXPAND-VAR` for *every*
expansion it performs, quoted or not (marking the result as "quoted"
so it's never re-interpreted as an operator or keyword later,
regardless of real quoting context). Reusing it meant nothing ever
split at all - caught immediately by testing a bare, unquoted `$x`
directly. Fixed with a new, dedicated `IN-DQ-CONTEXT?` flag, set (and
cleared) only by `COPY-DOUBLE-QUOTED` around its own body - the one
place that actually represents "currently inside a real double-quoted
span."

### A second, independent, pre-existing bug found while testing with a quoted assignment value

`x="a b c"` (spaces requiring quotes) followed by any use of `$x`
produced completely empty output - traced not to field splitting at
all, but to `TRY-ASSIGNMENT` itself: it checked `ARGV-QUOTED@` (which
records "was *any part* of this token quoted") to reject the
assignment entirely whenever the value was quoted, since that flag
can't distinguish "the value happened to be quoted" from "the name
itself was quoted" (the latter genuinely shouldn't be treated as an
assignment - `'FOO=bar'`, fully quoted, is meant as a literal command
name, and an existing, correct test already covered exactly this
case). Confirmed this predates the current session entirely (`git
stash` back to the last commit reproduced the identical failure) -
unrelated to field splitting itself, just newly exposed by finally
testing a quoted, multi-word assignment value for the first time.
Fixed with a new, more precise `ARGV-NAME-QUOTED` array - true only if
a token's own very first character came from inside a quote - checked
in place of `ARGV-QUOTED@` in `TRY-ASSIGNMENT` specifically, leaving
`ARGV-QUOTED` itself, and every other place it's already used,
completely untouched.

### Verified end-to-end via `relfsh` and confirmed on i386

Confirmed: an unquoted multi-word `$VAR` splits into separate
positional parameters via `set`; the same value quoted does not
split, even with internal whitespace; multiple consecutive `IFS`
characters collapse into a single split (via `for`); trailing and
leading `IFS` whitespace each produce no spurious empty field; a
quoted assignment value with no whitespace still works correctly; a
fully-quoted `'NAME=value'` is still correctly rejected as an
assignment; and a plain, unquoted assignment still succeeds.

`tests/shell/run-ifs` (9 assertions) - 232 assertions across 32 files
now, all passing on both x86-64 and i386. mrsh-suite: 0 passed, 21
failed, 3 skipped - `2.2.3-alias-expansion.fail.sh` moved from passing
to failing, but this isn't a genuine regression: `GOALS.md` already
flagged that pass as hollow before this session even started (`alias`
isn't implemented at all, so the pass was accidental, not because
this shell handled the test's actual intent correctly). The script
assigns `var="$(myalias arg-two)"` - previously rejected outright by
the `TRY-ASSIGNMENT` bug fixed above, now correctly recognized and
executed as an assignment (exiting 0, matching what a real assignment
of a possibly-empty command-substitution result does) - a `git stash`
comparison confirms the identical script exits differently only
because the assignment itself is now genuinely working, not because
of anything specific to `alias`.

**Phase D is now complete**: positional parameters, all parameter-
expansion modifiers, arithmetic expansion, tilde expansion, and `IFS`
field splitting are all implemented. Documented scope limits carried
forward: single-digit positional parameters only; `$@`/`$*` treated
identically (no quote-sensitive distinction); the "word"/"pattern"
portion of a parameter-expansion modifier is a literal string, not
itself further expanded; only space/tab (not a customizable `$IFS`,
not newline) trigger field splitting.

## Iteration 37: goal 8 phase F - `:`, `test`/`[` (string, numeric,
## limited file-existence tests)

The first Phase F builtins. `:` is a pure no-op, always exiting 0 -
trivial, but genuinely needed (the mrsh-suite's own `loop.sh`/
`return.sh` use `while :` as an infinite-loop idiom). `test`/`[`
support string tests (`-z`, `-n`, `=`, `!=`, a bare non-empty check),
numeric comparisons (`-eq`, `-ne`, `-lt`, `-le`, `-gt`, `-ge`), `!`
negation (of a bare/1-arg test, or a full 3-arg `a op b` test), and an
approximate `-e`/`-f`/`-d` (existence only, via `OPEN-FILE` - this
kernel exposes no real stat/access primitive, so `-f`/`-d` can't
actually distinguish a regular file from a directory, only "does
something exist at this path at all"). Scope limits, all documented in
`EVAL-TEST-ARGS`'s own comment: no `-r`/`-w`/`-x`/`-s`, no `-a`/`-o`
(deprecated in POSIX anyway), no `(` `)` grouping, and `"! -z
STRING"`-style 3-arg negated unary tests aren't handled (only a
bare/1-arg operand, or a full 3-arg `a op b`, can be negated).

### Design

`EVAL-TEST-ARGS` dispatches purely on argument count (0 through 4;
5+ isn't supported) over `ARGV[TEST-START, TEST-END)`, a range rather
than a fixed starting point so the same evaluator serves both `test`
(the whole of `ARGV[1..ARGC)`) and `[` (excluding the trailing,
required `]`). `TEST-BINARY?`/`TEST-UNARY?` each compare the operator
argument against a small set of known literals (`S" op" ARGV@ STR0=`,
the same pattern this file already establishes everywhere a literal
needs comparing against a `NUL`-terminated string). Numeric comparisons
reduce to four cases of a single `<` via straightforward algebra
(`A -le B` is `NOT(B < A)`, `A -ge B` is `NOT(A < B)`, etc.), the same
approach the arithmetic evaluator's own relational operators already
use in Iteration 35. `TEST-PARSE-INT` handles an optional leading `-`
that bare `PARSE-DECIMAL` doesn't, mirroring the arithmetic
evaluator's own `AE-LOOKUP-NUMERIC`.

### A real bug found immediately by running the existing regression suite

Installing `test` as a builtin means it now takes priority over the
external `/usr/bin/test` binary any script invokes bare (matching real
shell precedence - a builtin shadows a same-named external command).
`tests/shell/run-while` broke immediately: it uses bare `test -f
FILE`, which the initial implementation didn't recognize at all
(only `-e`/`-z`/`-n` were handled), so every condition silently
evaluated false and the loop bodies never ran. Fixed by adding `-f`/
`-d` as approximate aliases for the same existence check `-e` already
uses - not a precise fix (still can't distinguish file types), but
correct for every case that matters in practice: something that exists
at all.

### Verified end-to-end via `relfsh` and confirmed on i386

Confirmed: every string test, every numeric comparison, 2-arg and
4-arg negation, `-e` on both an existing and a missing path, the `[
... ]` bracket form with its required closing `]`, and a bare
string's own non-empty/empty check.

`tests/shell/run-test-builtin` (19 assertions) - 251 assertions across
34 files now, all passing on both x86-64 and i386. mrsh-suite
unchanged (0 passed, 21 failed, 3 skipped) - `test`/`[` alone doesn't
carry any single test file all the way to passing, since most need
several more Phase F/G features together, but individual scripts using
`test`/`[`/`:` should now progress further before hitting whatever's
still missing.

**Phase F remaining**: `read`, `readonly`, `shift`, `getopts`,
`command`, background jobs/`wait`/`$!`, `alias`/`unalias`, `ulimit`.

## Iteration 38: `locals.4` - named, per-invocation locals

Not a shell feature. This is infrastructure, added because the same
missing facility keeps showing up as the root cause of separate
`shell.4` limitations.

`shell.4` has **181 global `VARIABLE`s**, and the kernel has no locals
wordset at all. Most of those globals are not global state: they are
per-word scratch cells, faked with a naming convention (`GM-*` 9 of
them, `NORM-*` 8, `TEST-*` 7, `SAEK-*` 6, `SEQ-*`/`AE-*`/`FPM-*`/`BM-*`
5 each). That convention costs correctness, not just readability. A
word whose scratch state lives in fixed globals cannot be re-entered,
which is precisely why:

- `while`/`for` don't nest - their condition/body live in one fixed
  `WHILE-COND-BUF`/`WHILE-BODY-BUF` set, so an inner loop stomps the
  outer one's body (`if` nests fine because its state is the single
  scalar `COND-TRUE?`, saved and restored across `>R`/`R>`).
- a loop or function body can't contain another multi-line construct,
  now noted against three separate features.

So the nesting limitation carried forward since Iteration 23 isn't an
accident of those features' designs; it's a direct consequence of fixed
global state where per-invocation state belongs. This iteration builds
the tool. It deliberately does **not** use it yet - `shell.4` is
untouched, so this commit changes no shell behavior at all.

### Design: a local is an ordinary VARIABLE, saved on entry and restored on exit

That one decision is what keeps this small (about 65 lines of actual
code). The alternatives were considered and rejected:

- *A real locals frame with its own namespace* would need the local
  names to be findable during compilation. Creating temporary
  dictionary headers is not viable here: `HEADER` builds at `HERE`,
  which is exactly where the colon definition being compiled is also
  being built, so a header created mid-definition splices itself into
  the middle of the body. Working around that means hooking name
  resolution or juggling a locals wordlist plus dictionary rollback -
  far more machinery than the problem justifies.
- *A frame pointer with `RP@`/`RP!`* would need engine changes; neither
  word exists in this kernel.

Saving and restoring an existing variable sidesteps both. Consequences,
all of them wanted:

- **No new dictionary machinery.** Local names are the `VARIABLE`s that
  already exist, found by the ordinary `FIND`.
- **Existing code converts mechanically.** A word's *body is unchanged*
  - `CA-SRC @` and `CA-N !` keep working, because a local still is a
  variable. Converting a word means adding one `{: ... :}` line and
  deleting its argument-popping stores. That matters a lot for
  converting 181 globals' worth of existing, tested code without
  reintroducing bugs.
- **Neither stack is touched**, so this composes with `shell.4`'s
  existing, load-bearing `>R`/`R>` use (`DO-IF`, `RUN-FUNC-BODY`)
  instead of competing with it.
- **The kernel and `cross.4` are untouched.** `locals.4` is an ordinary
  Forth source file using only what the kernel already exposes
  (`STATE`, `FIND`, `COMPILE,`, `LITERAL`, `POSTPONE`, `IMMEDIATE`,
  `'`). `kernel.img` is not rebuilt. This was a deliberate constraint:
  `GOALS.md` warns that `cross.4`/`kernel.4` hand-embed raw
  primitive-dispatch token numbers whose failure mode is segfaulting
  the *next* engine at an unrelated primitive, and no part of this
  feature needs to go near that.

The cost is copying N cells at entry/exit instead of moving a frame
pointer. Not worth optimizing for this codebase.

### Syntax

    : COPY-ARGV ( src-argv src-argc --- )  {: CA-SRC CA-N :}
      CA-N @ ARGC ! ...

Names before an optional `|` are initialized from the data stack, left
to right = deepest to top, matching the stack comment's own reading
order. Names after `|` are scratch: saved and restored identically, but
zeroed rather than taking an argument.

    : GLOB-MATCH ( pat plen text tlen --- f )
      {: GM-PATTERN GM-PLEN GM-TEXT GM-TLEN | GM-P GM-S :}

### Wrapping `EXIT` and `;`

The restore has to happen on *every* exit path, and `shell.4` uses
early `IF EXIT THEN` pervasively. Both `EXIT` and `;` are therefore
redefined as immediate wrappers that capture the previous definition
(`' EXIT CONSTANT L-OLD-EXIT`, `' ; CONSTANT L-OLD-SEMI`) and defer to
it, adding behavior rather than reimplementing any. `;` additionally
clears the declaration count, which is what stops one definition's
locals leaking into the next - so a definition with no `{:` sees a
count of zero and compiles no extra code whatsoever. Verified
transparent: everything in `tester.fr` and `core-extra.fth` is compiled
through the original definitions, `tests/locals.fth` loads `locals.4`
last, and all 1991 OK markers still pass.

Both wrappers were probed directly against the running system before
being designed around, rather than reasoned about from `kernel.4`'s
source - `;` is bootstrapped through a self-referential trick
(`EXIT-TOK , [ ?CSP REVEAL ;`) whose metacompiled semantics are not
obvious from reading, and `:` uses `HEADER` without `REVEAL`, so a new
`;` isn't findable until its own terminating `;` completes it. Probing
took two minutes and removed all doubt.

### A real bug found only on integration: `BASE`

Every case passed in isolation. Adding `tests/locals.fth` to the real
suite broke immediately, with `{: LT-A LT-B :}` reporting the entire
rest of the line as one undefined name.

Root cause: **`tester.fr` leaves `BASE` at 16**, and `locals.4` parsed
names with a bare `32 WORD`. In hex, `32` is 0x32 = the character `2`,
so `WORD` was delimiting on the digit `2` instead of on a space and
swallowing whole lines. Nothing about the failure pointed at the number
base; it looked like a parsing bug.

Fixed at the root rather than at the one literal: `locals.4` now saves
`BASE`, forces `DECIMAL` for its own source, and restores `BASE` at the
end, and every character constant is written `[CHAR] :` / `[CHAR] }` /
`[CHAR] |` / `BL` instead of `58` / `125` / `124` / `32`. The
`[CHAR]` form is both base-proof and more readable than the numbers
were.

The same trap then fired one level up: with parsing fixed, the *test
file* was still being read in hex, so `{ 8 LT-FACT -> 40320 }` was
comparing values that don't mean what they look like. `tests/locals.fth`
now forces `DECIMAL` too, with a comment explaining why
`core-extra.fth` gets away without it (every value it uses happens to
read identically in hex and decimal).

Worth remembering generally: **a Forth source file that is `INCLUDED`
into an unknown session should not inherit the caller's `BASE`.** This
is a close cousin of the multi-line `( )` comment hazard from Iteration
33 - a whole-file parsing failure whose symptom points nowhere near its
cause.

### Verification

`tests/locals.fth` (22 assertions) covers: argument order (left to
right = deepest to top); `|` scratch locals zeroed rather than popped;
an empty `{: :}` declaration; the caller's value surviving the call;
restore on early `EXIT`; restore on `EXIT` from inside a `DO` loop;
recursion (`LT-FACT`); nesting where two different words use the *same*
local name and one calls the other (`LT-OUTER`/`LT-INNER` - the case
fixed globals cannot express, and the whole point of the exercise);
scratch locals surviving recursion independently; and the save stack
returning to empty afterwards.

The harness is known to catch failures in this file rather than
silently skipping it: the pre-`BASE`-fix run reported `INCORRECT
RESULT` for these exact assertions.

1991 OK markers, no errors, on **both** 8-byte and 4-byte (i386) cell
widths. `tests/shell/run-all` unchanged at 251 assertions across 34
files, all passing on both. mrsh-suite unchanged at 0 passed, 21
failed, 3 skipped - expected, since `shell.4` was not modified.

### What this iteration deliberately did NOT do

- **No `shell.4` conversion.** Converting words to locals is its own
  iteration, and doing it in the same commit would have made a
  behavior-preserving refactor indistinguishable from a new feature if
  anything broke.
- **`{:` cannot introduce a brand-new name.** Every local must already
  be a defined `VARIABLE` (or any word returning an address); an
  undefined name is diagnosed, not silently accepted. This is the
  direct consequence of the "a local is an ordinary variable" design.
  It means the `VARIABLE` declarations stay in the file rather than
  disappearing, so converting `shell.4` will make its globals
  *re-entrant* without reducing their *count*. Removing them entirely
  would need the dictionary machinery this design deliberately avoids;
  worth revisiting only if the declarations themselves become a
  problem.
- **One physical line per declaration.** `WORD` does not refill, and a
  multi-line construct here would be a close cousin of the Iteration 33
  comment hazard. Diagnosed explicitly (`locals: missing :} on this
  line`) rather than looping or misparsing.
- **Fixed limits**, both checked with a diagnostic rather than left to
  corrupt silently: 16 locals per definition, 256 cells of live save
  stack across all nested invocations.
- **`ABORT` inside a locals-using word leaks its saved cells** -
  `LSAVE-SP` isn't reset on the abort path, so the variables keep the
  callee's values. Acceptable for now (`shell.4` doesn't use `ABORT`,
  and an abort is already a session-level event), but it's a real
  loose end if that changes.
- **Two lines of startup noise.** Redefining `EXIT` and `;` makes
  `HEADER` print its "Redefining:" warning twice. Harmless for the test
  harnesses, which use substring assertions, but `relfsh` already emits
  a boot banner on stdout and this would add to it - worth handling as
  part of wiring `locals.4` into `shell.4`, not speculatively now.

### Unrelated observation, noted for later

Running `tests/mrsh-suite/run.sh` leaves a stray file literally named
`&` in that directory (from `async.sh`). `shell.4` has no background-job
support, so a trailing `&` is ending up treated as an ordinary word or
redirect target rather than being rejected. Not investigated here;
relevant whenever background jobs are picked up in Phase F.
## Iteration 39: converting `shell.4` to locals, and two real deduplications

Iteration 38 built `locals.4` but deliberately left `shell.4` untouched.
This iteration wires it in and converts 31 words. **No shell behavior
changes** - this is a behavior-preserving refactor, and every one of
the 251 existing assertions passes unchanged throughout, on both cell
widths.

### Wiring it in

`relfsh`'s bootstrap now loads `locals.4` ahead of `shell.4`. That's
the only place it needed to go: `shell.4` is `INCLUDED` by absolute
path, so a relative `S" locals.4" INCLUDED` inside it would resolve
against whatever the caller's cwd happened to be, and the shell tests
run from several different directories.

Before converting anything, the suite was run with `locals.4` loaded
and `shell.4` untouched. All 251 assertions passed, which is the real
check that the `EXIT`/`;` wrappers are transparent: every word in
`shell.4` was compiled through them while declaring no locals, and
none of them changed.

### 31 words converted

The mechanical shape, exactly as designed in Iteration 38 - the body
is untouched, only the argument-popping line changes:

    : COPY-ARGV ( src-argv src-argc --- )        : COPY-ARGV ( src-argv src-argc --- )
      CA-N !  CA-SRC !                    -->      {: CA-SRC CA-N :}
      CA-N @ ARGC ! ...                            CA-N @ ARGC ! ...

Converted: the glob-matching cluster (`GLOB-MATCH`,
`GLOB-CHAR-MATCHES?`, `BRACKET-MATCHES?` - 17 globals between them),
`STR=`, `SAFE-COPY-NUL`, `SAFE-CSTR-COPY`, `COPY-ARGV`, `COPY-ARGV-Q`,
`FIND-SHVAR`, `SET-SHVAR`, `FIND-FUNC`, `TEST-BINARY?`, `TEST-UNARY?`,
`SET-POS-PARAMS-FROM-ARGV`, `SET-POS-PARAMS-FROM-SYS-ARGS`,
`SAVE-POS-PARAMS`, `RESTORE-POS-PARAMS`, `EMIT-ALL-POS-PARAMS`,
`READ-ALL-CMDSUB-OUTPUT`, `FUNCDEF-NAME?`, `CASE-ARM-MATCHES?`,
`ENSURE-ROOM`, `TRIM-PARAM`, `NORMALIZE-OPERATORS`, and the six words
sharing the `PR-I` cursor (`PARSE-REDIRECTIONS`, `SPLIT-SEMI`,
`SPLIT-PIPE`, `SPLIT-ANDOR`, `SPLIT-GROUP-PAREN`, `SPLIT-GROUP-BRACE`).

**The dynamic-scoping property carried its weight immediately.** Many
of these words share their scratch with helper words that read the
same variables - `GLOB-MATCH`'s own `GM-PATTERN`/`GM-PLEN` are read by
`BRACKET-END`, `BRACKET-MATCHES?` and `GLOB-CHAR-MATCHES?`; the six
`PR-I` words share that cursor with `AT-END?`/`AT-SEMI?`/`AT-PIPE?`/
`AT-AND?`/`AT-OR?`/`AT-CLOSE-PAREN?`/`AT-CLOSE-BRACE?`. Because a
local *is* the variable, those helpers keep working untouched: during
the call the variable holds the caller's value. A conventional locals
frame with its own namespace would have required rewriting every one
of those helpers to take parameters. Verified by `run-case` and
`run-param-trim` passing, which exercise exactly those paths.

### Deduplication 1: four trim searchers become one

`FIND-SHORTEST-PREFIX-LEN`, `FIND-LONGEST-PREFIX-LEN`,
`FIND-SHORTEST-SUFFIX-LEN` and `FIND-LONGEST-SUFFIX-LEN` were four
near-identical ~13-line words. They differed in exactly two things:
which end of the value the candidate substring is taken from, and
whether candidate lengths are tried upward from 0 or downward from the
full length. Both are now parameters of a single `FIND-TRIM-LEN
( pat-addr pat-len val-addr val-len suffix? longest? --- len | -1 )`,
with `FPM-CANDIDATE`/`FPM-MATCHES?` factored out. `TRIM-PARAM`'s own
six-line four-way `IF` nest collapses to one line:

    PEW-SUFFIX? @ PEW-LONGEST? @ FIND-TRIM-LEN

Locals are what made this comfortable to write - the unified word
takes six arguments, which is unpleasant to juggle on the stack and
trivial to name.

### Deduplication 2: SPLIT-AT-KEYWORD collapses into a wrapper

`SPLIT-AT-KEYWORD` and `SPLIT-AT-EITHER-KEYWORD` carried ~35 lines of
identical logic between them - the same ARGV scan, the same `if`/`fi`
nesting-depth tracking, the same truncate-and-stash-the-remainder
split. The one-keyword case is just the two-keyword case with both
alternatives the same, so it now is exactly that:

    : SPLIT-AT-KEYWORD ( c-addr u --- f )
      2DUP SPLIT-AT-EITHER-KEYWORD 0= 0= ;

With both alternatives identical the underlying word can only ever
answer 0 or 1, so `0= 0=` is just that normalized to this word's own
-1/0 convention. `SAK-KW-ADDR`/`SAK-KW-LEN` existed only for the old
implementation and are gone.

`shell.4` is 3997 lines, down from 4072, while gaining 32 locals
declarations - so the real reduction in logic is larger than the 75
lines net.

### A hidden blocker found in the acceptance criterion itself

While checking whether the two "Redefining:" lines `locals.4` adds to
startup would disturb the harnesses, something more important
surfaced. `tests/mrsh-suite/run.sh`'s differential tests require
`relfsh`'s stdout to match `bash`'s **byte for byte**. But `relfsh`
emits `relf`'s own boot output first:

    $ relfsh /tmp/t.sh          $ bash /tmp/t.sh
    Welcome to Forth \r\n       hello\n
    OK\r\n
    hello\n

Both lines come from `kernel.4` (the banner at load, `OK` from
`QUIT`'s interpreter loop), so they are baked into the committed
`kernel.img`. **No differential test can pass while they are there,
regardless of what `shell.4` implements.** That has been true since
the suite was adopted in Iteration 14.

Before acting on it, this was measured rather than assumed: every
vendored differential test was re-run with the fixed boot prefix
stripped from `relfsh`'s output. **Zero would pass.** So the banner is
a latent blocker, not the binding one - today's failures are genuine
feature gaps, and removing the banner right now would change the count
by nothing. Deliberately left alone: fixing it means changing
`kernel.4` and regenerating the committed `kernel.img`, which deserves
its own iteration and its own decision, not a drive-by in the middle
of a refactor. Recorded in `GOALS.md` so the acceptance number is read
honestly - the count cannot rise above the 2 status-only conformance
tests until this is dealt with.

### A marginal test timeout, raised after measuring rather than guessing

`tests/run_tests.sh` capped the shell suite at `timeout 60`. It began
failing at exit 124. The obvious suspicion was that locals' save/restore
had slowed the shell down - `STR=` and `COPY-ARGV` are called
constantly.

Measured instead: 59.272s with the conversion, 59.256s with it stashed
out entirely. The conversion costs nothing detectable. The 60s limit
had simply always been about a second away from failing on this
machine. Raised to 180s.

**The explanation written here at the time was wrong, and is corrected
in Iteration 40's entry**: this said the runtime was "dominated by
forking a real process per assertion, not by anything inside
`shell.4`". The first half is right that it isn't the locals
conversion; the causal claim is not. It is dominated by *compiling*
`shell.4` inside each of those forked processes - ~253ms of every
~254ms `relfsh` invocation. The lesson: "measured that A didn't change
it" does not license a story about what B is, and the story cost
nothing to check.

### Verified

1991 OK markers and 251 shell assertions, all passing, on **both**
8-byte and 4-byte (i386) cell widths. mrsh-suite unchanged at 0 passed,
21 failed, 3 skipped, as expected for a behavior-preserving refactor.

### What this iteration deliberately did NOT do

- **`while`/`for` still don't nest, and this could not have fixed
  them.** Their state is `WHILE-BODY-BUF`, a fixed 4096-byte *buffer*,
  not a cell - and a local saves and restores one cell. Making loop
  bodies per-invocation needs the buffer to become a pointer into an
  arena, so that the *pointer* is what locals save. That is a genuine
  design change to how loop bodies are stored, and it is the natural
  next iteration now that the tool exists. Same for `CASE-WORD-BUF`,
  `FUNC-BODIES`, `ARITH-BUF` and the other fixed buffers.
- **The remaining ~150 globals are untouched.** What is converted here
  is every word whose scratch is genuinely cell-sized and whose
  conversion is mechanical. The rest are either real global state
  (`ARGC`, `LAST-STATUS`, `SUPPRESS-EXEC?`, the shell-variable and
  function tables) or buffer-backed.
- **No `forth` builtin yet.** It belongs after `DISPATCH` becomes
  table-driven - adding one more hand-written `S" name" ARGV @ STR0=`
  comparison to a chain that is about to be replaced means writing it
  twice. See GOALS.md's named-locals section for the ordering.
- **The two "Redefining:" lines are still printed at startup.** Bundled
  with the banner problem above rather than fixed separately, since
  both are the same question about `relfsh`'s stdout hygiene.
## Iteration 40: prebuilt shell image - ~128x faster startup, and the
## acceptance criterion unblocked

Your idea, and it paid off more than either of us expected. Three
numbers, 50 runs each, measured before starting:

| | 50 runs | per run |
|---|---|---|
| `relfsh -c true` | 12.68s | ~254ms |
| bare `relf kernel.img` | 0.061s | ~1.2ms |
| `/bin/true` | 0.040s | ~0.8ms |

**~99.5% of every `relfsh` invocation was compiling `locals.4` +
`shell.4` from source**, which the bootstrap did afresh every single
time. This had been true since Iteration 5 and nobody had looked.

Result: `relfsh` now boots a prebuilt image in ~1.8ms (**~128x**), the
shell test suite went from **59.3s to 1.18s** (**50x**), and the
mrsh-suite went from 0 passed to 2 - one of them genuine, the first
vendored file ever carried across by real shell features.

This also corrects Iteration 39's entry, which asserted the suite's
runtime was "dominated by forking a real process per assertion, not by
anything inside `shell.4`". That was invented. The measurement it was
attached to (that the locals conversion cost nothing) was fine; the
causal story bolted onto it was never checked, and was wrong.

### Three pieces

**`save-system.4`** - `SAVE-SYSTEM ( c-addr u -- )` writes the
*running* system out as a bootable image: the 8-byte magic header,
then memory from `START` to `HERE`. This is much simpler than it
sounds, because RelF images are relocatable by design - that is the
entire point of RelF's relative addressing. `COLD` is the authority on
what is absolute in a live system:

    : COLD  START ! START @ FORTH-WORDLIST +! START @ DP +! ...

Exactly two cells. So subtracting `START` back out of `DP` and
`FORTH-WORDLIST` before writing, and adding it back after, is the whole
of "relocation". `HERE` is read *before* unrelocating (unrelocating
changes `DP`, and therefore `HERE`), and the window in which the system
sits in its on-disk form contains nothing but the two writes - no
`ALLOT`, no `WORD`, no `ABORT"` that could strand it there.

Needs no engine change and no kernel change: `START`, `DP`,
`FORTH-WORDLIST`, `HERE` and the file words all already existed. Proved
in isolation first, against an unmodified `kernel.img`, by saving an
image containing a word and a variable defined just beforehand and
checking both survived a reboot.

Deliberately not confused with `cross.4`'s own `SAVE-IMAGE`, which is a
host-side word writing the target image the cross-compiler is building
- a different thing.

**`BOOT` in `kernel.4`** - the one kernel change, so `kernel.img` is
regenerated. 0 in a plain image; when set it holds the xt of a word to
run at startup:

    BOOT @ ?DUP IF START @ + EXECUTE THEN

Stored as an offset from `START` and never relocated in place, so it
stays valid if the image is saved again. This is what skips the banner.
`OK` needed no work at all: those lines were `QUIT` acknowledging
`relfsh`'s bootstrap lines, and a prebuilt image has no bootstrap.

**`relfsh`** rebuilds the image whenever any input is newer, writing to
a temporary name and `mv`-ing it into place so concurrent invocations
can't see a half-written file, with a fallback to the old source
bootstrap if the build fails. The image is **built, never committed**:
a committed binary derived from `shell.4` is a second source of truth
that goes stale silently the first time someone edits the shell and
forgets. The name is derived from the kernel image
(`kernel.img` -> `kernel-shell.img`), so both cell widths work without
collision.

### Position-independence is now load-bearing, and two things weren't

An image reloads at a different address every run, so any absolute
address compiled into a word's body is stale the moment it boots. Both
offenders were found the same way - by the turnkey image segfaulting -
and both are the same mistake:

1. **`shell.4`'s six deferred-word xts.** `' RUN-TOKENIZED
   RUN-TOKENIZED-XT !` stores an absolute address. Fine for as long as
   `shell.4` was recompiled on every startup; fatal once it isn't. Now
   stored as offsets via new `!XT`/`@XT` helpers. Bisected to this by
   testing boot words of increasing scope until `1 SYS-ARG SH-C`
   crashed while `SYS-ARGC`, `SYS-ARG` and `S"` all worked.
2. **`locals.4`'s slot addresses.** `L-EMIT` compiled the variable's
   absolute address as a literal into *every* locals-using word. Found
   when the next crash landed in `NORMALIZE-OPERATORS` - the first
   locals-using word on the startup path.

The fix for (2) is worth recording, because the first attempt was
wrong in an instructive way. It compiled `LIT off | START | @ | + |
call` inline, which is correct but **quadruples the code emitted per
local**. That overflowed the dictionary and corrupted compilation of
`shell.4`, reported as two `Undefined word` errors against an *empty
name* - a symptom pointing nowhere near its cause. The right answer is
to pass the offset *to* the runtime words and let `LSAVE`/`LRESTORE`/
`LZERO`/(new) `L!` add `START` themselves: same two cells the original
absolute version emitted, no growth at all, and simpler.

**Anything added in future that stores or compiles an address must do
the same.** Recorded in `GOALS.md`.

### The dictionary was nearly full, and nobody knew

Chasing that overflow surfaced something worth having found: `relf.c`'s
`MEMSIZE` was 256K, and a prebuilt shell image measures **253,256
bytes**. `kernel.img` + `locals.4` + `shell.4` had come within a few KB
of the ceiling, with the return and data stacks living in what was
left. It had not bitten yet only because nothing had pushed it over.

Raised to 1M. Worth emphasising that this does *not* fail cleanly: the
symptom is corrupted compilation surfacing as `Undefined word` against
an empty name, arbitrarily far from the actual cause.

### The mrsh count moved, and only half of it is real

**2 passed, 19 failed, 3 skipped.** Checked both rather than reporting
the number:

- **`case.sh` is genuine.** Full `case`/`esac`: variable expansion in
  the case word, `*`, `?`, `[a-z]` and `|` patterns, a quoted pattern,
  an expanded pattern, and an omitted final `;;`. All of it really
  implemented (Iterations 27, 33-36). `GOALS.md` had predicted this
  file needed arithmetic and `$IFS` splitting, which landed in 35/36 -
  so this is the first vendored file carried across by actual features
  rather than by measurement artifact.
- **`ulimit.sh` is hollow**, and is recorded as such. `shell.4` has
  neither `ulimit` nor backquote substitution. Both shells simply exit
  1, and their stdout coincides only because of the single `grep` line
  that runs in both. Exactly the shape of the old
  `2.2.3-alias-expansion.fail.sh` accident.

### Verified

1991 OK markers and 251 shell assertions, all passing, on **both**
8-byte and 4-byte (i386) cell widths, with the regenerated `kernel.img`
and prebuilt shell images. `relfsh`'s stdout is now byte-identical to
`bash` for a script that both can run.

### What this iteration deliberately did NOT do

- **Compiling new code inside a turnkey image still doesn't work.**
  `locals.4`'s compile-time machinery holds absolute xts
  (`L-OLD-EXIT`/`L-OLD-SEMI`, `['] LSAVE` inside `L-EMIT`), stale in a
  reloaded image. Running compiled code is fine; only compilation is
  affected. **This has to be fixed before the `forth` builtin can work
  in a prebuilt image**, which is the main reason it matters.
- **`while`/`for` still don't nest.** Unchanged from Iteration 39, and
  still the highest-value structural item: the buffers need to become
  pointers into an arena.
- **`kernel.img` is regenerated but the cross-compiler is untouched.**
  Adding a `VARIABLE` and editing `COLD` changes neither the primitive
  list nor its stride, so the hand-embedded dispatch tokens
  `GOALS.md` warns about were never in play.
## Iteration 41: pool allocator, memory outside the image, and
## reproducible images

Answering the question "why is shell.img almost 256K?" - the answer
was buffers, and fixing it turned into three related pieces of work.

### The measurement that started it

Of the 253,528-byte prebuilt image:

| | bytes | share |
|---|---|---|
| `POS-PARAMS-SAVE` | 73,728 | 29% |
| `FUNC-BODIES` | 32,768 | 13% |
| other `CREATE`d buffers | 29,080 | 11% |
| **buffers total** | **135,576** | **53%** |
| compiled code + headers | 88,464 | 35% |
| `kernel.img` underneath | 23,152 | 9% |

**77.3% of the file was zero bytes**, and the longest single run of
zeros was 73,707 - `POS-PARAMS-SAVE`, entirely empty. It is
`MAX-POS-PARAM-DEPTH(32) x MAX-POS-PARAMS(9) x POS-PARAM-MAX(256)`:
room for 32 levels of function nesting each saving 9 parameters of 256
bytes, reserved whether or not a single function is ever called.

`CREATE name n ALLOT` takes *dictionary* at compile time, and
`SAVE-SYSTEM` writes everything from `START` to `HERE`, so every
reserved byte lands in the image.

### ALLOCATE / FREE / RESIZE

Three new primitives, backed by libc `malloc`/`free`/`realloc`. This is
Forth-2012's own memory-allocation wordset rather than an invention,
which matters for a project whose top priority is minimalism: it is a
standard interface other Forth code already expects.

Appended at the **end** of `kernel.4`'s `PRIMITIVE` list deliberately.
Tokens are `1 + (position-1) x stride`, so adding at the end leaves
every existing token untouched, while inserting anywhere earlier would
silently renumber them - the exact failure `GOALS.md` warns about,
whose symptom is the *next* engine segfaulting at an unrelated
primitive.

This is memory **outside** the image: it costs no dictionary space,
`SAVE-SYSTEM` does not write it, and it is not bounded by `MEMSIZE`.

### `pool.4` - `BUFFER:`

    MAX-FUNCS FUNC-BODY-MAX * BUFFER: FUNC-BODIES

Declares a buffer whose name behaves exactly like a `CREATE`d one -
executing it pushes the address - so no call site changes. What changes
is that only a three-cell descriptor goes in the dictionary, and the
space is `ALLOCATE`d on **first use**, so a buffer that is declared but
never touched costs nothing at runtime either.

The descriptors are a linked list rather than a table, so there is no
fixed maximum number of buffers to pick and get wrong; the link is an
offset from `START`, not an address. `RESET-BUFFERS` walks the chain,
`FREE`s everything and marks it unallocated - `SAVE-SYSTEM` calls it,
so an image is always written in a clean, freshly-booted state.

Seven buffers converted (every one at or above 1KB): 124,160 bytes,
92% of all buffer space, and all cold-path - none is touched
per-character by the tokenizer, so the extra indirection on first use
cannot show up in the hot loop. `LINE-BUF`, `ARGV` and the other small
hot buffers were deliberately left as plain `CREATE`.

**Image: 253,536 -> 131,784 bytes, a 48% reduction.** Zeros fell from
77.3% to 55.7%.

### Reproducible images

Two builds of identical sources must produce identical bytes. They did
not. Three separate causes, each found by building twice and diffing:

1. **The build machine's path and the builder's PID**, left in the
   interpreter's include buffer - the first image literally contained
   `S" /home/claude/relf/kernel-shell.img.tmp.476" SAVE-SYSTEM`.
2. **A dozen cells holding absolute addresses** that differ every run:
   `SRC`, `LAST`, `CURRENT`, `CONTEXT`, `CSP`, `S0`, `R0`, `START`
   itself, and `SAVE-SYSTEM`'s own working variables (which held the
   heap address of the copy being written).
3. **`locals.4`'s compile-time machinery**, which held absolute xts -
   `['] LSAVE` compiled as a literal into `L-COMPILE-ENTRY`, and
   `L-OLD-EXIT`/`L-OLD-SEMI` as `CONSTANT`s.

`SAVE-SYSTEM` was restructured to assemble the image in a heap copy and
scrub it there, rather than mutating the live system - which is better
anyway, since nothing is ever written to disk from a system that is
temporarily half-unrelocated. Everything scrubbed is re-initialized by
`COLD`, `WARM` or `QUIT` before anything reads it, so zeroing costs
nothing.

Cause (3) was fixed properly rather than scrubbed, by storing those
xts as offsets (`!XT`/`@XT`, moved from `shell.4` to `locals.4` since
both files need them and `shell.4` already requires `locals.4` for `{:`
itself). **That removed the limitation recorded in Iteration 40**:
compiling new code inside a reloaded image now works. Verified by
saving a non-turnkey image, then defining a new locals-using word and a
new `BUFFER:` inside it and checking both behave correctly. That
limitation was the blocker in front of the `forth` builtin.

### Concerns raised about the longer-term direction

Recorded in `GOALS.md` under "Memory policy" rather than only here,
since they are standing constraints:

- **`RESIZE` can move a block, and this codebase stores interior
  pointers into buffers.** `ARGV` entries point into `LINE-BUF`.
  Growing such a buffer would silently invalidate them, and it would
  look like data corruption rather than an allocation failure. `RESIZE`
  is safe for a self-contained arena nothing points into from outside,
  and unsafe for the shell's line and token buffers as written today.
- **Heap memory can never be saved in an image**, by construction. That
  is the right default and it is what keeps images small and
  reproducible, but it means an image carries buffer *declarations* and
  never *contents*.
- **`malloc` deepens the libc dependency**, against this file's stated
  "no libraries" end state. That tension predates this change (phase 5
  traded it away for portability), and if the goal is revived these are
  three well-isolated primitives to reimplement on `mmap`/`brk` with
  nothing above them changing.

### Verified

1991 OK markers and 251 shell assertions on **both** 8-byte and 4-byte
(i386) cell widths. mrsh-suite unchanged at 2 passed, 19 failed, 3
skipped. Image byte-identical across two separate build processes.
`relfsh`'s fallback path (source bootstrap when the image can't be
written) exercised directly by making the directory read-only.

### What this iteration deliberately did NOT do

- **Sizes are still fixed, just no longer preallocated.**
  `POS-PARAMS-SAVE` still reserves 32 nesting levels' worth on first
  use; it is simply not in the image and not paid for until a function
  is called. Making it grow on demand is the `RESIZE` work above, and
  wants the interior-pointer question answered per buffer first.
- **The small hot buffers are unconverted**, on purpose - 8% of the
  buffer bytes for the buffers touched most often.
- **`while`/`for` still don't nest.** `WHILE-BODY-BUF` is now
  heap-allocated, which is a prerequisite for making it
  per-invocation, but the arena work itself is still ahead.
## Iteration 42: replay as an input source - nested constructs inside
## loop and function bodies

The limitation carried since Iteration 23, and since noted against
three separate features: a while/for body or a function body could not
contain another multi-line construct. A nested `if` inside a loop body
silently ran its own body unconditionally, because `DO-IF`'s search for
`then`/`else`/`fi` reads a *new* line, and that read went to the real
process input rather than to the next stored body line.

### The fix is one idea, not a special case

A stored body was being replayed by *dispatching* each line directly
(`RUN-STORED-LINE`). Replay is now a third **input source**, alongside
the real stdin and an open script file:

    : READ-NEXT-INPUT-LINE ( c-addr max --- u2 )
      REPLAY-SRC @ IF REPLAY-NEXT-LINE EXIT THEN
      SHFILE-ACTIVE? @ IF ... ELSE ACCEPT THEN ;

Everything that reads a line already funnels through that one word, so
once replay is one of its cases, every construct nested inside a body
reads from the body automatically - and no construct needs to know
replay exists. `DO-IF` is unchanged. So are `DO-CASE`, `DO-FUNCDEF`
and the rest.

`REPLAY-SRC`/`REPLAY-LEN`/`REPLAY-POS` are declared as **locals** by
`DO-WHILE-BODY` and `RUN-FUNC-BODY`, which is what makes replays nest:
an inner body's replay saves and restores the outer one's position.
This is the first place the locals facility built in Iteration 38 has
been used for something that could not reasonably have been written
without it - the two words' state genuinely has to be per-invocation.

It also gets a subtlety right for free. A construct that *captures*
lines while a replay is active - a nested `while` reading its own body,
say - consumes them from the outer body through the same path, leaving
the outer position correctly advanced past them.

### Simplifications that fell out

`RUN-STORED-LINE` is gone entirely: replayed lines now go through
`READ-LINE-INTO-ARGV` like every other line. That also fixes a
quiet inconsistency - `RUN-STORED-LINE` tokenized without calling
`NORMALIZE-OPERATORS` first, so an operator fused to adjacent text
(`a>file`) behaved differently inside a loop body than outside it.
`RUN-FUNC-BODY` lost its `>R`/`R>` juggling and its `FUNC-BODY-I`
cursor, taking `FUNC-CUR-I` as a local instead; `RSL-LEN` and
`FUNC-BODY-I` are gone.

### What now works

`tests/shell/run-nesting` (9 assertions): `if` inside `for`, `if`
inside a function, `if` inside `while`, and `for` inside a function -
all checked against the branch actually taken, not merely that
something ran. 260 assertions across 35 files now, all passing on both
cell widths.

### What still does not, and why

**A loop nested directly inside another loop still fails** - it
produces no output rather than misbehaving. This is a *different*
cause, and the one this iteration did not address: `while` and `for`
capture their body into the single shared `WHILE-BODY-BUF`, so an
inner loop's capture overwrites the outer's body. Replay-as-input-
source was the prerequisite; making those buffers per-invocation is the
remaining half.

The shape of that fix is clear now. `WHILE-BODY-BUF`/`WHILE-COND-BUF`
become pointers into an arena, with the arena's bump pointer preserved
across a construct by declaring it as a local. Note the idiom that
gives "save and restore the current value", since a `|` scratch local
is zeroed rather than preserved:

    BODY-ARENA-TOP @  {: BODY-ARENA-TOP | ... :}

pushing the current value and taking it straight back as an argument
local. Freeing is then automatic and exception-safe: the local restores
the bump pointer on every exit path, including an early `EXIT`.

### A self-inflicted detour worth recording

The edit was applied with a Python script whose quoting was wrong,
leaving a stray `'` at the start of `DO-WHILE-BODY`. `shell.4` then
failed to compile, `relfsh` fell back to its source bootstrap, and the
symptom was `Undefined word ':` plus a suddenly reappearing "Welcome to
Forth" banner. The banner was the useful clue: it only prints on the
fallback path, so it meant "the image build failed", not "the shell is
broken". Worth remembering as a diagnostic.
## Iteration 43: per-invocation body storage - loops nest

The other half of Iteration 42. A loop nested directly inside another
loop now works, along with every combination tested: `for` in `for`,
`for` in `while`, `if` inside both, and a loop inside a function body
called repeatedly. Verified against `bash` on a three-deep
`while` > `for` > `if` script producing identical output.

### Two independent causes, both real

Iteration 42 fixed the input source. Testing a nested loop directly -
rather than assuming that fix was sufficient - showed it produced no
output at all, and the reason turned out to be two separate problems
stacked on each other.

**1. Shared capture buffers.** `while`/`for` captured into a single
`WHILE-BODY-BUF`, so an inner loop's capture overwrote the outer's
body. `WHILE-COND-BUF`, `FOR-WORDS-BUF` and `FOR-VARNAME-BUF` had the
same problem.

These are now pointers into a bump arena (`BODY-ALLOC`), and
`DO-WHILE`/`DO-FOR`/`DO-FUNCDEF` each declare `BODY-ARENA-TOP` as a
**local**, which restores the bump pointer on every exit path
including an early `EXIT`. Nothing is ever freed explicitly; the
locals machinery provides exactly the stack discipline nested
constructs need. The idiom is worth recording, since a `|` scratch
local is *zeroed* rather than preserved:

    BODY-ARENA-TOP @  {: BODY-ARENA-TOP | ... :}

pushing the current value and taking it straight back as an argument
local, so it is saved on entry, untouched during the body, and
restored on exit.

The arena is a `BUFFER:` (Iteration 41), so it costs nothing in the
image and nothing at runtime until the first loop or function is
actually seen.

**2. The capture loop had no nesting depth.** Even with private
buffers, the outer capture stopped at the *inner* loop's `done`, so
the outer body was truncated and the outer `done` was left to execute
as a stray top-level line. `CAPTURE-CONTINUE?` now counts: `while` and
`for` open a `done`, `do` and `if` do not. Same shape as
`SPLIT-AT-KEYWORD`'s existing if/fi depth tracking, and `BODY-DEPTH`
is a local too, so captures nest as well as replays do.

Neither cause would have been found by inspection; both surfaced by
running a nested loop and looking at the actual output.

### A self-inflicted error worth recording

The first attempt failed to compile with `locals: missing :} on this
line`, because I wrote the declarations across two physical lines -
violating a restriction `locals.4` documents and diagnoses explicitly,
which I had written myself in Iteration 38. The diagnostic did its job
and pointed straight at the cause, which is the argument for
diagnosing this case rather than letting `WORD` loop or misparse.

Worth noting why the restriction stays rather than being lifted:
making `{:` refill across lines means calling `REFILL` mid-parse,
which is exactly the mechanism behind the multi-line `( )` comment
corruption documented in Iteration 33. Not worth the risk to save a
line wrap.

### Verified

`tests/shell/run-nesting` grew from 9 to 19 assertions - now covering
`for` in `for`, `while` > `for` > `if` three deep with the outer loop
terminating correctly, and a loop inside a function invoked twice
(which checks the arena is genuinely released, not merely unused).
270 assertions across 35 files, plus 1991 core OK markers, all passing
on both cell widths. mrsh-suite unchanged at 2 passed, 19 failed, 3
skipped.

Size: 158,008 bytes on x86-64, 91,864 on i386 - up ~2,400 from
Iteration 42, which is the arena machinery and the new tests' worth of
code.

### What this iteration deliberately did NOT do

- **`BODY-ARENA-MAX` is a hardcoded 65,536**, against the memory
  policy agreed in Iteration 41. A bump arena needs a size, and
  growing it with `RESIZE` is precisely the case that policy flags as
  unsafe: the live `WHILE-BODY-BUF`/`FOR-WORDS-BUF` pointers point
  *into* the arena, so moving it would invalidate them silently.
  Growing safely means a chunked arena (allocate a new chunk, never
  move an existing one), which is real work and wants its own
  iteration. Overflow is diagnosed (`loop/function nesting too deep`)
  and degrades rather than corrupting.
- **`WHILE-BODY-MAX` is still 4,096 per body**, unchanged - now
  charged against the arena instead of the image, but still a fixed
  per-loop ceiling with the same silent-drop behavior
  `APPEND-RAW-LINE-TO-BODY` always had.
- **Nested function definitions** are untouched: `DO-FUNCDEF` gets its
  own arena body but its capture still stops at the first `}`.
## Iteration 44: offset-based growable arena - two hardcoded limits gone

Iteration 43 left `BODY-ARENA-MAX` as a hardcoded 65,536 and I claimed
growing it needed a *chunked* arena, because `RESIZE` could relocate
the block and live pointers point into it. You pushed back: doesn't
`realloc` just extend in place? Worth settling by measurement rather
than argument, so I wrote the test:

    realloc to      128 bytes MOVED 0x55af879942a0 -> 0x55af87995300
    realloc to   131072 bytes MOVED 0x55af87995300 -> 0x7f94b3637010
    ...
    total moves: 7   (out of 15 calls)

It moves. glibc extends in place when the adjacent chunk is free, which
is why it usually *looks* like it never does; it can't when something
is in the way, and past the mmap threshold a grow is a fresh mapping
nearly every time.

But the conclusion I drew from that was wrong, and your instinct was
right. Chunking is not the answer - **offsets** are. This project
already stores offsets rather than addresses everywhere it matters:
`START`-relative xts, the `BOOT` hook, locals' slot addresses, the
`BUFFER:` descriptor chain. The arena was the one place still holding
raw pointers into a relocatable block. Making the buffer variables hold
offsets and dereference through `BODY@` means `RESIZE` can move the
arena freely, because nothing outside holds a pointer into it.

That is strictly better than chunking: fewer moving parts, no chunk
size to pick, and consistent with the rule already written down rather
than a special case.

### `BODY-ARENA-MAX` is gone

The arena now starts at 4,096 and doubles on demand via `RESIZE`
(`BODY-GROW`). There is no maximum. It is heap memory, so it costs
nothing in the image and nothing at runtime until the first loop or
function is seen, and `MAIN` resets its base at boot because a heap
address is meaningless after an image is saved and reloaded.

### `WHILE-BODY-MAX` as a per-body cap is gone too

Testing the growable arena with a generated 60-loop script showed
output that quietly diverged from bash. The cause was not the arena:
`APPEND-RAW-LINE-TO-BODY` had always dropped any line that would not
fit a fixed 4,096-byte body, **silently, with no error**. So a
sufficiently large loop body produced wrong output rather than
failing - a real correctness bug that predates this work and that no
existing test was large enough to reach.

Bodies now grow. `BODY-ENSURE` extends the body in place, which works
because a body being captured is always the topmost arena allocation:
nothing else allocates while lines are being appended, since a nested
loop inside the body is still just text at that point and does not
allocate until it runs. The residual "cannot grow" case is now
reported instead of ignored.

### Two bugs found along the way, both mine

- **First arena allocation has offset 0**, and
  `READ-NEXT-INPUT-LINE` used "`REPLAY-SRC` is non-zero" to mean "a
  replay is in progress". So the outermost loop in any script silently
  did not replay at all. Fixed with an explicit `REPLAY-ACTIVE?` flag.
  A good argument against overloading a value with "and zero means
  absent" when the value's range legitimately includes zero.
- **File ordering**, again: `BODY@` was defined down with while/for but
  first used by the replay machinery above it. Moved.

`REPLAY-SRC` needed care of its own: it holds an arena *offset* for a
loop body but a plain address for a function body, which lives in
`FUNC-BODIES` and never moves. `REPLAY-ARENA?` distinguishes them, and
the address is resolved per line rather than cached - necessary,
because a nested loop inside the body being replayed allocates its own
storage, and therefore may relocate the arena, before it reads a line.

### A third hardcoded limit, found but NOT fixed

The 60-loop script also exposed `MAX-SHVARS` (32). The script sets 60
distinct shell variables; from the 33rd on, `SET-SHVAR` silently does
nothing, so `$b31` onward expanded to empty. Same failure shape as the
body cap: a fixed table, silently full, producing wrong output rather
than an error. `MAX-FUNCS` (16), `MAX-POS-PARAM-DEPTH` (32) and
`MAX-ARGS` (64) are the same pattern.

Deliberately left for its own iteration rather than bundled in here -
the shell-variable table is on the hot path of every expansion, so
making it growable wants its own measurement. Recorded in `GOALS.md`.

### Verified

`tests/shell/run-nesting` now 22 assertions, including a >4KB loop body
diffed against bash (which forces at least one arena `RESIZE`) and
8-level nesting producing exactly 256 lines. 273 assertions across 35
files plus 1991 core OK markers, on both cell widths. mrsh-suite
unchanged.
## Iteration 45: `#` comments and same-line `; do` - mrsh 2 -> 4 passed

Chosen by measuring rather than guessing. Running every failing
vendored test and looking at where each one first diverges from `bash`
showed two gaps blocking far more files than anything else, both cheap:

- **`#` comments did not exist at all.** Every vendored script starts
  `#!/bin/sh`, which was being executed as a command, and `echo d # e f`
  printed `d # e f`.
- **`while`/`for` had no same-line `; do`.** `if` gained the equivalent
  in Iteration 25; the loops were explicitly left out, so `for i in
  1 2 3; do` failed with `for: expected 'do'`.

Both now work. **mrsh-suite: 2 passed -> 4**, with `loop.sh` and
`syntax.sh` newly passing, both genuinely (12 and 6 lines of real
output matching `bash` exactly, exit 0).

### Comments

Implemented in `NORMALIZE-OPERATORS`, which already tracks single/
double-quote and `$((...))` state, so a quoted or escaped `#` is
handled by the branches that already exist. A comment simply jumps the
read position to end of line.

The interesting part is what must NOT become a comment. POSIX starts
one only at the beginning of a word, so `NORM-COMMENT-START?` requires
the `#` to be at line start or follow whitespace. That is exactly what
keeps `$#`, `${#VAR}`, `${VAR#pattern}` and a literal `a#b` working -
in all of those the `#` follows a non-blank. All four are now
regression-tested, since getting this wrong would break parameter
expansion in a way no existing test covered.

Body lines stored for replay keep their comments, because they are
stored raw; the comment is stripped when the line is re-read and
re-normalized. A body line that is entirely a comment tokenizes to
nothing and is a no-op.

### Same-line `; do`

Two different problems, because `for` and `while` store their setup
differently.

`for` keeps its word list as *tokens*, so the fix is to stop the list
at an unquoted `;` (`FOR-AT-SEMI?`).

`while` keeps its condition as *raw text* - deliberately, so `$VAR`,
`$?` and `$$` re-expand fresh on every iteration (Iteration 11's whole
design problem). So the `; do` tail has to be trimmed from raw text,
not from `ARGV`, which needs its own quote-aware scan
(`RAW-LAST-SEMI`). It takes the *last* unquoted `;` so that
`while a; b; do` keeps the whole compound condition.

Both then skip reading a separate `do` line, gated on `SAME-LINE-DO?`,
which checks whether the **last** token is an unquoted `do` rather than
whether a `do` appears anywhere - so `while grep do file` is not
mistaken for the same-line form.

### Verified

`tests/shell/run-comments` (13 assertions) covers comment stripping,
the four `#`-must-survive cases, quoted `#` in both quote styles,
same-line `do` for `for` and `while`, and two same-line loops nested.
286 assertions across 36 files plus 1991 core OK markers, both cell
widths.

### Noted, not fixed

`relfsh -c 'set a b c; echo $#'` reports 0 where bash reports 3. Not
caused by this work: it is the architectural limitation recorded in
Iteration 18 - `$VAR` expansion happens once for the whole raw line
during the initial tokenize, before any `;`-separated segment has run.
The proper fix is tokenizing and expanding each `;` segment in
sequence, still its own future iteration.

### The remaining gap to a full mrsh pass

Measured, in the order I would take it:

1. **Multi-stage pipelines** (`a | b | c`) - `SPLIT-PIPE` handles
   exactly one `|`. Blocks pipeline.sh, readonly.sh, command.sh,
   redir.sh.
2. **`elif`** - if.sh.
3. **Builtins**: `read`, `readonly`, `command -v`, `alias`/`unalias`.
4. **fd redirection** (`2>&1`) - redir.sh.
5. **Bitwise/shift and `?:` in `$((...))`** - arithm.sh.
6. **Background `&`, `wait`, `$!`** - async.sh.
7. **`(cmd)` with no surrounding spaces** - subshell.sh; needs
   `NORMALIZE-OPERATORS` to become `$(...)`-aware, deferred since
   Iteration 24.
8. **Tilde beyond bare `~`**: `~user`, `~` after `=`, inside
   `a=~/x:~/y` - word.sh.
9. Quoting conformance edge cases, and rejecting unterminated quotes.

`args.sh`/`function.sh`/`return.sh` still fail for reasons now hidden
behind earlier failures; expect the list to shift slightly as the top
items land.
## Iteration 46: multi-stage pipelines, `!` negation, and a real
## pre-existing expansion bug

`SPLIT-PIPE` handled exactly one `|` per line. It now handles any
number, which was the largest single item on the measured gap list.

### n-stage pipelines

The old code split the line into fixed left/right arrays. Instead of
generalizing that to an array-of-segments, `SPLIT-PIPE` now copies the
whole tokenized line into `PIPE-ARGV`/`PIPE-ARGQ` and just counts the
unquoted `|`s; `RUN-PIPELINE` extracts each segment lazily as it goes.
That keeps the state to one cursor rather than a two-dimensional
structure.

`RUN-PIPELINE` is the old two-child shape generalized to a loop
carrying a single file descriptor forward: create this segment's
outgoing pipe unless it is the last, fork, and in the child wire the
previous read end onto stdin and this write end onto stdout. The parent
closes both ends it no longer needs - which is what makes each stage
actually see EOF - and carries the read end forward.

**Every child is reaped**, not just the last. The old version waited
for both of its two; a loop that forgot the middle stages would
accumulate zombies for the life of the shell. Only the last segment's
status becomes the pipeline's, matching POSIX. Tested with 20
consecutive three-stage pipelines.

Empty segments (`a | | b`, a trailing `|`) are rejected by
`PIPE-SEGMENTS-OK?` rather than misbehaving, matching the old
"both sides non-empty" guard.

### `!` pipeline negation

`! cmd` runs the rest and inverts the status. Placed ahead of
`SPLIT-PIPE` because POSIX negates the whole pipeline, not a command.
Needed by `pipeline.sh`, and three lines given `RECURSE`.

### The bug that was actually blocking pipeline.sh

Diagnosing why `pipeline.sh` still failed after all that turned up
something much more interesting than a pipeline problem:

    echo $? x     ->  "12777"      (bash: "127 x")
    echo $((2+3)) tail -> "5tail"-ish smear

**Every numeric expansion was corrupting the rest of its line.** `$?`,
`$$`, `$#`, `${#VAR}` and `$((...))` all write digits straight into the
token being built via `EMIT-DECIMAL`, and every one of them can be
longer than the text it replaces - `$?` is two characters, `127` is
three. That is precisely the in-place compaction hazard `ENSURE-ROOM`
exists for, and precisely the self-propagating smear Iteration 26
found... and fixed for `$VAR` only. The numeric paths never called
`ENSURE-ROOM` at all, so they kept the bug for twenty iterations.

Fixed with one `EMIT-DECIMAL-EXPANDED` wrapper used at all five sites.
Confirmed pre-existing, not introduced here - it reproduces with no
pipeline involved.

Worth drawing the general lesson: Iteration 26 fixed *an instance*
rather than *the class*. The fix was correct and the analysis was
right, but nobody checked whether the other writers into the token
buffer had the same problem. When a bug is found in one path, the
question to ask is which other paths share the shape.

### Verified

`tests/shell/run-pipeline-multi` (11 assertions): three- and four-stage
pipelines, two-stage still working, status coming from the last stage
and ignoring earlier ones, `!` inverting both ways, both smear cases,
and 20 consecutive pipelines completing. 297 assertions across 37
files plus 1991 core OK markers, both cell widths.

mrsh-suite stays at 4 passed. `pipeline.sh` now differs only on its
last case, `(echo "a b"; echo "c d") | sed s/c/C/` - a subshell inside
a pipeline, which needs both `(cmd)` without surrounding spaces and
builtins/groups as pipeline segments. Both are on the list already.

### Two file-ordering slips, again

`BODY@`-style ordering problems bit twice more this iteration:
`LINE-IS?` and `SHIFT-ARGV-DOWN` were defined after
`RUN-SIMPLE-OR-PIPELINE`, which now uses both. Moved. That is the
fifth or sixth time this file's ordering has caught something; it is
the standing cost of a single linear source file with mutual
dependencies broken by hand.
## Iteration 47: `elif`, and closing a hazard open since Iteration 28

`elif` chains work, at any length, in both the multi-line and
same-line (`if C; then A; elif D; then B; else E; fi`) forms.

### DO-IF became one flat branch loop

The previous shape had a nested loop: scan for `else` or `fi`, and on
`else`, enter a second inner loop scanning only for `fi`. That nesting
existed solely to stop looking for a second `else`, and it does not
extend to an arbitrary number of `elif`s.

It is now a single loop over the remaining branches, with `COND-TRUE?`
reinterpreted from "the first condition was true" to **"some branch has
been taken"**. That one change is what makes chaining work: each `elif`
evaluates its condition only if nothing has been taken yet, `else` runs
only if nothing has, and the old nested loop becomes an ordinary
iteration.

`SPLIT-AT-EITHER-KEYWORD` was generalized to `SPLIT-AT-3` (needed to
scan for `elif`/`else`/`fi` in one pass, keeping the `if`/`fi` depth
tracking). The two-keyword form now delegates to it by passing its
second keyword twice, and `SPLIT-AT-KEYWORD` still delegates to that -
so all three remain one implementation, as of Iteration 39.

### A bug in my first version, worth recording

`if true; then A; elif true; then B; fi` printed **AB**. The elif's
body suppression was derived from `COND-TRUE?` alone - but by then
`COND-TRUE?` is true *precisely because an earlier branch ran*, so the
body ran too. The skip decision and the body-suppression decision are
different questions and now use different values. Caught by testing the
"branch already taken" case explicitly rather than only the cases where
elif is supposed to fire.

### The hazard from Iteration 28, finally hit

The same-line form printed `two ;` - echoing a literal semicolon.

`READ-NEXT-LOGICAL-LINE` restores a split's pending remainder with
`COPY-ARGV`, which does not carry `ARGV-QUOTED` with it, so a stale
"quoted" flag left at that index by an earlier expansion hid the real
`;` operator from `SPLIT-SEMI`. That is exactly the hazard Iteration 28
found and fixed for the `;`/`&&` splitters, and exactly the
"unverified extent at other `COPY-ARGV` call sites" that `GOALS.md` has
carried as an open item ever since. This was one of those sites.

Fixed at the root: `SPLIT-AT-3` now captures each pending token's
quoted flag into `ARGQ-PENDING`, and `READ-NEXT-LOGICAL-LINE` uses
`COPY-ARGV-Q`. Notable that it took nineteen iterations to be hit -
it needs an expansion and a same-line operator to land at the same
`ARGV` index - and that when it did surface it looked like an `elif`
bug rather than a quoting one.

### Verified

`tests/shell/run-elif` (7 assertions): elif taken, all-false reaching
else, **branch-already-taken not running a later elif**, a two-elif
chain, the same-line form, and a nested `if` inside `else` still
working. 304 assertions across 38 files plus 1991 core OK markers,
both cell widths.

mrsh-suite stays at 4. `if.sh` now gets past its elif section and
stops at `( exit 10 )` inside an if body followed by
`[ $# -eq 10 ] || { ...; }` - needing subshells and brace groups as
ordinary commands, which is the same `(cmd)`/group work `pipeline.sh`
and `subshell.sh` are waiting on. That is now the single highest-value
remaining item: it is the last thing standing between three separate
test files and passing.
## Iteration 48: `(` and `)` as self-delimiting operators

Deferred since Iteration 24, because blindly spacing parens breaks
`$(...)` outright. Now done, and it took four collisions to land.

`NORMALIZE-OPERATORS` gains a `$(...)` mode mirroring the `$((...))`
one it already had: on seeing `$(` (and not `$((`) it copies verbatim,
tracking nested parens, until the matching `)`. Everywhere else `(`
and `)` are ordinary self-delimiting operators, so `(echo hi)` parses
the same as `( echo hi )`.

### Four things collided with it, three of which broke tests

1. **`$((...))`'s closing `))`.** The arith branch left arith-mode on
   the *first* `)` and let the second fall through - harmless while
   `)` was an ordinary character, fatal once it became an operator,
   since a space got inserted and `$((x*2))` became `$((x*2) )`. Every
   arithmetic expansion broke. The closing `))` is now consumed as a
   unit. Caught by `run-arith`.
2. **Function headers.** `f() {` tokenizes as four tokens now -
   `f`, `(`, `)`, `{` - not one fused `f()` token, which is what
   `FUNCDEF-NAME?` looked for. Every function test broke, and
   `run-break-continue` *hung*. Now matched as the three-token shape.
   Caught by the suite; the hang is what made it obvious.
3. **`case` pattern arms.** `hello)` used to keep its `)` fused, and
   `CASE-ARM-MATCHES?` stripped it from the last token. With `)` split
   off, `run-case` still passed - **by luck**: the real patterns became
   separate tokens that matched directly, and the leftover `)` became
   an empty pattern that happened to match nothing. It would have
   wrongly matched a `case` on an empty word. Now skipped explicitly
   alongside `|`, and that exact case is a test.
4. `{`/`}` were considered and left alone: POSIX requires a blank
   after `{` and a `;` or newline before `}` anyway, so brace groups
   already tokenize correctly.

Point 3 is the one worth remembering. The suite went green on a change
that was still wrong; only reading *why* it passed found it. A passing
test says the observed behaviour is right, not that the reasoning is.

### Verified

`tests/shell/run-paren` (10 assertions): subshells with and without
spaces, `$(...)` and `$((...))` unaffected including nested parens and
a variable operand, function headers in both spellings, a `case` arm
still matching the right pattern, and an empty `case` word correctly
falling through to `*`. 314 assertions across 39 files plus 1991 core
OK markers, both cell widths.

mrsh-suite stays at 4 passed. `subshell.sh` gets further but still
diverges; `pipeline.sh` and `if.sh` need what is now clearly the next
item - **a subshell or brace group used as an ordinary command**:
as a pipeline segment (`(a; b) | c`), and with a trailing redirect.
Today `DO-SUBSHELL`/`DO-BRACE-GROUP` only trigger when the group is
the *entire* line, and a trailing pipe or redirect after one is
silently dropped - the scope limit recorded back in Iteration 20.
Three test files are waiting on that single item.
## Iteration 49: groups as ordinary commands - mrsh 4 -> 6 passed

`pipeline.sh` and `if.sh` both pass now. A subshell or brace group can
be used anywhere a command can: as a `&&`/`||`/`;` segment, as a
pipeline stage, and still as a whole line. This retires the scope limit
recorded in Iteration 20 ("a trailing pipe or redirect after a group is
silently dropped").

### One mechanism, not three special cases

Following the note from Ramey's bash chapter that a real grammar gets
this for free, the flat-token-array equivalent is a **depth count**.
`GRP-TRACK` maintains `GRP-DEPTH` as each token is consumed, and
`AT-SEMI?`/`AT-AND?`/`AT-OR?`/`AT-PIPE?` only recognise their operator
at depth 0. So `{ a; b; } && c` splits at the `&&` and not at either
`;`, without any of the splitters knowing what a group is.

With that in place the rest is two guards and a fallthrough:

- `AT-GROUP-END?` answers "is this whole line/segment one group?".
  The group is handled directly only then; otherwise it falls through
  to the splitters, which now split correctly around it.
- `RUN-SIMPLE-OR-PIPELINE` gained the same group check, because
  `&&`/`||`/`;` segments never pass through `RUN-TOKENIZED` at all -
  that is why `[ x ] || { ...; }` never worked.
- A pipeline stage that is a group runs in the forked child directly
  rather than being exec'd. Everything else still goes straight to
  `exec`, so an ordinary pipeline costs no extra process.

### The flags-on-word fix, and it earned its keep immediately

Also from the bash chapter: bash attaches flags to the word
(`WORD_DESC`), while this file keeps `ARGV-QUOTED` as a parallel array
that copies routinely leave behind. Every stale-flag bug this project
has had is that. The two remaining uncarried copies - group bodies and
`ARGV-SHIFT` - now have parallel flag arrays and use `COPY-ARGV-Q`,
and pipeline stages carry their flags too.

That was not speculative tidying: `(echo "a b"; echo "c d") | sed` was
*failing on it* mid-iteration. The group body was copied without
flags, the inner `;` looked quoted, and both echoes collapsed into one
command. Third occurrence of the same root cause (Iterations 28, 47,
here), now closed at every call site.

### Two bugs of my own, both the same mistake

The segment-level and line-level group checks each fired before the
pipe was considered, so `(echo hi) | tr a-z A-Z` printed `hi` - the
group ran alone and the pipeline was discarded. Both now sit behind
`AT-GROUP-END?`. Worth noting the shape: "handle the special case
first" is wrong whenever the special case can be *part of* a larger
construct.

Also three file-ordering moves (`LINE-IS?`, `RUN-TOKENIZED-CALL`, the
whole group block ahead of `RUN-PIPELINE`). That is now routine enough
to be a real cost.

### Verified

`tests/shell/run-group-cmd` (12 assertions): groups as `||`/`&&`
segments, as the first pipeline stage, a multi-command subshell into a
pipe, a group's own `;` staying inside it, the operator after a group
still being seen, and the subshell-vs-brace-group scoping distinction
(`(a=2)` does not escape, `{ a=3; }` does). 326 assertions across 40
files plus 1991 core OK markers, both cell widths.

**mrsh-suite: 4 passed -> 6.** `pipeline.sh` and `if.sh`, both
genuine. Remaining 15: `read`, `readonly`, `command -v`, `alias`,
`ulimit`, background `&`/`wait`/`$!`, fd redirection (`2>&1`), bitwise
and `?:` in `$((...))`, `~user` tilde forms, `args.sh`/`function.sh`/
`return.sh`/`for.sh` (to be re-diagnosed - their first divergence has
moved), and the quoting conformance cases.
## Iteration 50: duplication audit - two merges, two latent bugs

A refactor iteration, done on its own rather than alongside a feature,
now a standing convention in `GOALS.md`. The finding worth generalizing
is that **merging duplicated code kept fixing bugs**: in both cases the
two copies had already drifted, and one of them was wrong.

### Six predicates became one

`AT-SEMI?`, `AT-PIPE?`, `AT-AND?`, `AT-OR?`, `AT-CLOSE-PAREN?` and
`AT-CLOSE-BRACE?` were the same four lines each, differing only in the
literal. Now `AT-TOKEN? ( c-addr u --- f )` plus `AT-OP?` (the same,
restricted to group depth 0), with the named predicates as one-liners
so no call site changed.

The drift the merge exposed: the four operator predicates had gained
the `GRP-DEPTH` check in Iteration 49; the two close-bracket ones never
did, because they were separate copies nobody thought to update.

### Two group splitters became one, fixing nested groups

`SPLIT-GROUP-PAREN` and `SPLIT-GROUP-BRACE` were twenty near-identical
lines differing only in the closing token. Now one `SPLIT-GROUP`
parameterized by the closer.

Neither original counted depth, so **`( a ( b ) c )` stopped at the
inner `)`** and ran a truncated body. Counting depth in the merged word
fixed that as a side effect. Nested subshells and nested brace groups
both work now, and are tested.

### And a real reentrancy bug the new test found

`{ echo x; { echo y; }; echo z; }` printed `x` and `y` but never `z`.

`RUN-TOKENIZED` splits at `;` into the *global* `ARGV-SEMI-REST`, runs
the part before the `;`, and then reads the remainder back. But running
that first part can recurse all the way into `SPLIT-SEMI` again - a
brace group does exactly that, since its body goes through
`RUN-TOKENIZED` - which overwrites the remainder before it is used.
Pre-existing, and it needed a group nested inside a `;` list to
surface.

Fixed by copying the remainder into per-invocation arena storage before
running the left part, released automatically by the locals holding the
arena's bump pointer.

**The same shape exists in `RUN-AND-OR-CHAIN`**, which also keeps its
segments in globals across a call that can recurse. Not hit by any test
yet and not fixed here - recorded rather than quietly left. It is the
same fix when it comes up.

### Verified

`run-group-cmd` grew to 17 assertions (nested subshells, nested brace
groups, and the `;`-list case above). 331 assertions across 40 files
plus 1991 core OK markers, both cell widths. mrsh-suite unchanged at 6
passed, as expected for a refactor.

`shell.4` is 4559 lines - down slightly despite three added tests'
worth of behaviour, and the duplicated shapes are gone.
## Iteration 51: `shift`, `readonly`, `command -v`

Three Phase F builtins, chosen because they are independent of the
parser and of each other. mrsh-suite unchanged at 6 — none of these
carries a vendored file on its own, as expected; `readonly.sh` and
`command.sh` each need several more features together.

- **`shift [n]`** drops the first n positional parameters; an
  out-of-range n is an error leaving them untouched, per POSIX.
- **`readonly NAME` / `readonly NAME=value`** marks a slot via a
  parallel `SHVAR-RO` byte array. The refusal is enforced **inside
  `SET-SHVAR`**, not at each caller, so every path that can set a
  variable — plain assignment, `export`, `${VAR:=word}`, a `for`
  loop's control variable — is covered by one test rather than four
  that could drift apart.
- **`command -v NAME`** reports functions, builtins and `PATH` hits.

### Reuse rather than a second copy

`readonly NAME=value` needs exactly the splitting `DO-ASSIGN` already
does, so `DO-ASSIGN-AT ( c-addr eqpos --- )` was factored out and
`DO-ASSIGN` now calls it. That required moving the assignment block
ahead of `DISPATCH` — the usual file-ordering cost — but the
alternative was a second copy of the split, which
`FORTH-STYLE.md` was written to stop.

`command -v` needed a PATH walk that *tests* rather than execs.
Deliberately a separate `PATH-LOOKUP?` rather than a flag on
`SEARCH-PATH`, whose entire contract is "only returns on failure";
adding a mode to it would have made that contract conditional.

### One duplication accepted, and flagged

`BUILTIN-NAME?` lists the builtin names, and that list must be kept in
step with `DISPATCH`'s own chain by hand — exactly what this project
just wrote a rule against. Recorded in the code, with the fix named:
**make `DISPATCH` table-driven** (name → xt), after which both read
one table and registering a builtin is adding a row. That refactor
also removes ~60 lines of repeated `S" name" ARGV @ STR0= IF` and is
the prerequisite for the `forth` builtin discussed back in Iteration
38. It is the next item.

### Verified

`tests/shell/run-builtins2` (9 assertions): `shift` and `shift n`,
`shift` past the end erroring, `readonly` refusing reassignment while
ordinary variables still assign, `readonly NAME` on an existing
variable, and `command -v` on a builtin, a `PATH` command, a function
and a nonexistent name. 340 assertions across 41 files plus 1991 core
OK markers, both cell widths.
## Iteration 52: table-driven DISPATCH, and the `forth` builtin

`DISPATCH` was sixty lines of `S" name" ARGV @ STR0= IF DO-name -1
EXIT THEN`, one per builtin, and Iteration 51 had to add a *second*
hand-maintained copy of the same name list for `command -v`. Both are
now one table.

Registering a builtin is a row:

    ' DO-CD  S" cd"  BUILTIN

A linked list built in the dictionary, not a fixed array, so there is
no maximum count to pick and get wrong. Entries are
`[ link | xt | len | name ]`, with link and xt stored as **offsets
from START** — they go into a saved image, where an absolute address
is stale on reload. `BUILTIN-NAME?` is now `FIND-BUILTIN 0= 0=`, and
the duplicated list flagged in Iteration 51 is gone.

Six builtins that were written inline in the chain (`:`, `exit`,
`return`, `break`, `continue`, `set`) became ordinary words, which is
what let them go in the table at all.

### The `forth` builtin, discussed in Iteration 38 and finally cheap

Because `BUILTIN` is an ordinary runtime call rather than compiled-in
syntax, Forth loaded at runtime can register builtins itself. That was
the whole argument for the table, and it now works end to end:

    forth ': GREET ." hello from forth" CR ;'
    forth "' GREET S\" greet\" BUILTIN"
    greet          # -> hello from forth

Defining a Forth word does **not** by itself make it a shell command;
registering it does. That separation seems right: the shell's namespace
stays explicit.

Documented caveats, not papered over: arguments arrive already
tokenized and expanded, so anything Forth must parse itself (a `."`
string) has to be protected with shell quotes; a Forth error `ABORT`s
the whole shell; and a word that unbalances the stack corrupts *this*
process, because there is no isolation. That is the nature of an
escape hatch into the interpreter the shell is written in.

### A latent hazard this surfaced

`forth` segfaulted immediately. A turnkey image boots from `COLD`
straight into `MAIN`, so `WARM` and `QUIT` — which set up the search
order and the input source — **never run**. Nothing in the shell had
needed them; `EVALUATE` calls `FIND`, which walked an empty search
order.

`MAIN` now does that initialization itself, at the boot word, rather
than changing `COLD`: it keeps the kernel unchanged and keeps the
setup next to the reason for it. Worth recording that Iteration 40
noticed WARM/QUIT don't run in a turnkey image and judged it harmless;
it was harmless for exactly twelve iterations.

### Verified

`tests/shell/run-forth` (11 assertions): `forth` evaluating an
expression, a shell-registered builtin running, every builtin still
reachable through the table via `command -v`, and `command -v`
correctly silent on a nonexistent name. 351 assertions across 42 files
plus 1991 core OK markers, both cell widths. mrsh-suite unchanged at 6,
as expected for a refactor plus an extension mechanism no vendored
test uses.

`shell.4` grew slightly (4759 lines) because six inline builtins became
named words with their own comments — the repeated *shape* is gone,
which was the point.
## Iteration 53: bitwise/shift operators and arithmetic assignment
## — mrsh 6 -> 7 passed

`arithm.sh` passes. Four separate gaps had to close together, which is
why re-diagnosing after each one mattered.

### Bitwise and shift operators

The arithmetic grammar gained four precedence levels, in C/POSIX
order: `AE-SHIFT` (`<<`, `>>`) between relational and additive, and
`AE-BITAND`/`AE-BITXOR`/`AE-BITOR` between `&&` and `==`. The
recursive-descent shape made this purely additive — each new level
calls the next tighter one and nothing else changed.

The lexing needs care, and `AE-SINGLE-OP?` is where it lives: `&` is
the bitwise operator only when *not* doubled, since `&&` binds looser
and is handled further out. Likewise `|` versus `||`, and `AE-REL` had
to learn not to read `<<` as `<`. Verified against `bash` on eight
precedence-interaction cases (`1+2<<3`, `3&1|4`, `2^3^1`, `2|1||1`,
`5&3==3`, …), not just the operators in isolation.

### Arithmetic assignment

`$((a=42))`, `$((a+=1))` and friends, right-associative, at the lowest
precedence. Not an assignment falls straight through to `AE-OR`, so it
costs one lookahead per expression.

Two things had to survive the recursive evaluation of the right-hand
side, because it can itself be an assignment (`a=b=5`): the operator
rides on the data stack, and the target *name* gets a slot in the body
arena, released by the local holding the bump pointer. My first
version parked the name in `AE-NUMBUF` — the same buffer `N>STR` then
wrote the result into. Classic aliasing: it worked for the value and
silently destroyed the name.

`N>STR` builds digits from the *end* of its buffer backwards and
returns a pointer to the first one, which avoids a reversal pass. My
first attempt did the reversal in place and was wrong.

### Two conformance fixes found on the way

- **`\$` inside double quotes.** POSIX makes backslash special before
  `$`, `` ` ``, `"`, `\` and newline; only the last two were handled,
  so `"\$a"` kept its backslash.
- **A `$` sigil inside `$((...))`.** `$(($a+2))` reaches the evaluator
  unexpanded, because `NORMALIZE-OPERATORS` copies an arithmetic region
  verbatim. POSIX allows a variable there with or without the sigil, so
  `AE-PRIMARY` now skips it. This was the *last* difference in
  `arithm.sh` — everything else already matched.

### Verified

`tests/shell/run-arith2` (9 assertions): the operators, the precedence
interactions, plain and compound assignment, nested right-associative
assignment, the `$` sigil, `\$` in double quotes, and negative results.
360 assertions across 43 files plus 1991 core OK markers, both cell
widths.

**mrsh-suite: 6 passed -> 7.** Remaining 14 need `read`, fd
redirection (`2>&1`), background `&`/`wait`/`$!`, `alias`, `ulimit`,
`~user` tilde forms, a subshell function body (`f() ( ... )`), and the
quoting conformance cases.
## Iteration 54: the `read` builtin

`read [-r] NAME...` reads one line from the real stdin, splits it on
whitespace, one field per name, with the **last** name receiving
everything that remains and trailing blanks trimmed — matching `bash`
byte for byte on the shared test.

### Two details that mattered

**It reads fd 0 directly, not through `READ-NEXT-INPUT-LINE`.** That
word reads the *script* when one is running, which is exactly what
`if` and `while` need for their body lines. `read` must take the
process's own stdin instead, or `while read line; do ...; done` over a
pipe would consume the script it is running rather than the data.
Two input sources that look interchangeable and are not.

**`READ-LINE`'s flag distinguishes EOF from an empty line.** `ACCEPT`
returns 0 for both, which would have made a blank line end a
`while read` loop early — the kind of bug that only shows up on real
input. Tested explicitly: an empty line reads successfully with status
0, EOF gives status 1.

`-r` is accepted and ignored, honestly rather than silently: this
shell does no backslash processing on the line either way, so `-r` is
already the behaviour.

### Verified

`tests/shell/run-read` (8 assertions): field splitting with the last
variable taking the remainder, blanks trimmed, EOF status, `-r`, an
empty line not being EOF, and a `while read` loop over a pipe running
to completion. 368 assertions across 44 files plus 1991 core OK
markers, both cell widths.

mrsh-suite stays at 7. `read.sh` needs more than the builtin — it uses
`printf` with operands this shell mishandles and a here-document.
Recorded rather than assumed: the builtin is right, the test needs
other features.

### Remaining gap to a full mrsh pass

`read.sh` (here-documents), `redir.sh` (fd redirection, `2>&1`),
`async.sh` (background `&`, `wait`, `$!`), `command.sh`/
`2.2.3-alias-expansion` (`alias`), `ulimit.sh` (`ulimit`),
`word.sh` (`~user` tilde forms), `args.sh` (`getopts`, and `f() ( ... )`
subshell function bodies), `function.sh`, `for.sh`, `return.sh`,
`subshell.sh`, `readonly.sh`, and the two quoting conformance cases.
## Iteration 55: file-descriptor redirection — mrsh 7 -> 8 passed

`redir.sh` passes. `2>file`, `2>&1`, `1>&2` and combinations all work.

### A list, not one slot per operator

Redirections were three fixed variables — `REDIR-IN-FILE`,
`REDIR-OUT-FILE`, `REDIR-APPEND-FILE` — which cannot express a
redirection on any descriptor but the default, and cannot express
duplication at all. They are now an ordered list of
`(target fd, operation, filename-or-source-fd)`.

**Order is the point, not an implementation detail.** `> f 2>&1` sends
both streams to the file; `2>&1 > f` sends stderr to the terminal and
only stdout to the file. A list applied in sequence gets that right by
construction, where three slots could not represent the difference at
all. There is a test for it.

### Two tokenizer details

`>&` and `<&` are single operators and must not be split into `>` and
`&` — `&` alone means something entirely different. Added to
`NORMALIZE-OPERATORS` alongside the existing doubled-operator handling.

A leading digit (`2>file`) arrives as its own token, and the digit and
operator are recognised as a *pair* in `PARSE-REDIRECTIONS` rather than
being fused in the tokenizer. That keeps the tokenizer ignorant of
redirection syntax; the alternative would have meant teaching it when a
digit is an fd and when it is an ordinary argument, which is a
context question the parser is already answering.

### A self-inflicted one

Replacing the old block deleted `VARIABLE PR-I` along with it — the
scan cursor several other words declare as a local. "Undefined word
PR-I", one line to restore. Worth noting only because it is the same
hazard as always: this file's single linear ordering means a block
move is never purely a move.

### Not done, deliberately

Redirection still only applies to external commands, in the forked
child. `pwd > file` does not redirect a builtin's output. Fixing that
needs the **undo list** from Ramey's bash chapter (see `GOALS.md`):
the effects of a redirection must not persist beyond the command, so
the shell has to record how to reverse each one. Recorded as the next
piece of redirection work rather than half-done here.

### Verified

`tests/shell/run-fd-redir` (8 assertions): `2>/dev/null` actually
suppressing stderr, `2>&1`, `2>file`, `>`/`>>` in order, `<`, and
`> f 2>&1` putting stderr in the file. 376 assertions across 45 files
plus 1991 core OK markers, both cell widths.

**mrsh-suite: 7 passed -> 8.** Remaining 13: here-documents
(`read.sh`), background `&`/`wait`/`$!` (`async.sh`), `alias`
(`command.sh`, `2.2.3-alias-expansion`), `ulimit`, `~user`
(`word.sh`), `getopts` and `f() ( ... )` subshell function bodies
(`args.sh`), `function.sh`, `for.sh`, `return.sh`, `subshell.sh`,
`readonly.sh`, and the two quoting conformance cases.
## Iteration 56: here-documents

`cmd <<DELIM` and `cmd <<-DELIM` work: the following input lines up to
a line equal to the delimiter become the command's standard input, with
`<<-` stripping leading tabs (tabs only, not spaces — which is what
makes it usable for indenting a here-document inside a loop without
indenting its contents).

### Design notes

**The body is fed through a pipe, not a temporary file.** No temp path
to invent, clean up, or collide on. The write happens before anything
reads, so a body larger than the pipe buffer would block —
`HEREDOC-MAX` is 8K, well under it, and that is the reason for the
limit rather than an arbitrary size.

**It reads through `READ-NEXT-INPUT-LINE`**, so a here-document inside
a loop body or a function reads from the stored body exactly like
everything else — the input-source work from Iteration 42 paying off
again, with nothing here needing to know about replay.

That required the deferred-word pattern: `READ-NEXT-INPUT-LINE` is
defined far below `PARSE-REDIRECTIONS` (it needs the script-file and
replay machinery), and here-documents must read input at
redirection-parsing time. Same shape as `RUN-TOKENIZED-CALL`.

Tokenizer: `<` joins the doubled-operator set so `<<` is one token, and
`<<-` keeps its dash attached.

### Three limits, all pre-existing, all now visible

Writing the tests surfaced two cases I had assumed would work and did
not — both inherited, neither introduced here:

- **A here-document cannot feed a builtin.** `read a b <<EOF` produces
  nothing, because redirection is applied in the forked child and
  builtins do not fork. This is the same gap as `pwd > file`, and it
  needs the redirection **undo list** from Ramey's bash chapter
  (Iteration 55).
- **A here-document cannot be combined with a pipe.**
  `cat <<EOF | tr a-z A-Z` fails, because pipeline stages bypass
  `PARSE-REDIRECTIONS` entirely — the pipe/redirect exclusion recorded
  back in Iteration 7 and never revisited.
- **Redirection on a compound command** (`done <<EOF`, `done < file`)
  is not supported at all; redirection attaches to simple commands
  only.

I removed both invalid assertions rather than leaving tests that
asserted behaviour the shell does not have. The limits are written into
the test file so the next person meets them there rather than
rediscovering them.

Also not done: no expansion is performed on the body. POSIX expands
`$VAR` unless the delimiter is quoted.

### Verified

`tests/shell/run-heredoc` (7 assertions): body lines delivered,
execution continuing past the delimiter, `<<-` stripping tabs and
finding an indented delimiter, and an empty here-document. 383
assertions across 46 files plus 1991 core OK markers, both cell widths.

mrsh-suite stays at 8.

**Correction (made while answering a question about `<<<`):** the
sentence that stood here claimed `read.sh` uses `read x <<EOF` and was
therefore blocked on the undo list. That is wrong, and was never
checked — `grep '<<' vendor/` finds exactly one file, `arithm.sh`,
using it as the *shift operator*. The mrsh suite does not use
here-documents at all.

`read.sh` actually uses `printf | read a` and
`printf "a\nb\nc\n" | while read line; do ... done`. It is blocked on
**builtins and compound commands as pipeline stages**, not on
redirection. Today a pipeline stage is exec'd, so `read` is not found
and the stage exits 127.

That is a much cheaper fix than the undo list, and the shape already
exists: Iteration 49 made a stage that is a *group* run via
`RUN-TOKENIZED-CALL` in the child instead of being exec'd. Extending
that test to cover builtins and reserved words gets `read.sh`, and
costs no extra process for ordinary external stages.

The lesson is the one this project keeps relearning: I stated a
dependency without running the one-line check that would have
falsified it, and it went into the log as fact. `FORTH-STYLE.md`'s
"measure before concluding" is about causes; this is the same failure
about *requirements*.
## Iteration 57: builtins as pipeline stages

`printf x | read a` and `pwd | tr a-z A-Z` work. This retires the
"builtins aren't supported on either side of a pipe" limit recorded in
Iteration 7.

The shape already existed: Iteration 49 made a stage that is a *group*
run via `RUN-TOKENIZED-CALL` in the forked child instead of being
exec'd. `PIPE-STAGE-INTERNAL?` now answers that question for groups,
builtins and functions alike, and everything else still goes straight
to `exec` — so an ordinary external pipeline costs no extra process.

A builtin in a pipeline runs in the child, so it cannot affect this
shell: `printf new | read a` leaves `$a` unchanged. That is POSIX's
own behaviour and matches bash, not a limitation of the
implementation — asserted as a test so it is not "fixed" later by
mistake.

### What I tried, and backed out

I first included `if`/`while`/`for`/`case` in the same test, aiming
directly at `read.sh`'s `printf "a\\nb\\nc\\n" | while read line; ...`.
It does not work, and the reason is structural rather than a bug to
chase: those constructs read their body lines from the input *after*
the stage has started, and the forked child shares the script's file
offset with the parent, so the two race for the same lines. The
observed symptom was `while: expected 'do'` repeating while the loop
produced empty output.

Groups are fine precisely because `SPLIT-GROUP` has already captured
their entire body from the current line before any fork happens.

Making multi-line compound commands work as pipeline stages means
capturing the body *before* forking — the same "capture, then replay"
machinery `DO-WHILE` already has, but hoisted above the pipeline
split. That is its own iteration, and it is what `read.sh` still needs.
Recorded here rather than left as a mystery for the next attempt.

### Verified

`tests/shell/run-pipe-builtin` (6 assertions): a builtin as the first
stage, as the last stage with its status propagating, a builtin's
assignment correctly *not* escaping the subshell, external pipelines
unchanged, and groups as stages still working. 389 assertions across 47
files plus 1991 core OK markers, both cell widths. mrsh-suite unchanged
at 8, for the reason above.
## Iteration 58: redirection on pipeline stages

`echo hi | cat > file`, `cat < file | tr`, `ls 2>/dev/null | cat` and
`cat <<EOF | tr` all work. This retires the "pipes and redirection are
mutually exclusive" limit recorded in Iteration 7 — a stage used to go
straight to `RUN-CHILD` with its redirection tokens still in `ARGV`,
where the command saw them as ordinary arguments (`cat: '>': No such
file or directory`).

Two lines in the pipeline child: parse and apply the stage's
redirections **after** the pipe's own `dup2`s, so an explicit
`> file` on a stage overrides the pipe, as POSIX requires. It works for
internal stages too, since a builtin running in that child inherits
the descriptors just as an exec'd command would.

Here-documents into pipelines came for free, which retires one of the
three limits recorded in Iteration 56 — the test file's note is
updated rather than left stale.

### The attempt I abandoned, and why

This iteration was meant to be compound commands as pipeline stages,
for `read.sh`'s `printf "a\\nb\\nc\\n" | while read line; ...`. The plan
from Iteration 57 was to capture the construct's body before forking.
Working through it found a **second** structural obstacle beyond the
file-offset race:

`DO-WHILE` takes its condition from the **raw line text**
(`SAVE-WHILE-COND` skips the literal `while` at the start of
`RAW-LINE-BUF`). For a pipeline stage the raw line is the whole
pipeline — `printf ... | while read line` — so the condition text would
be wrong. And the condition cannot simply be taken from the already
tokenized `ARGV` instead, because it is deliberately kept raw so
`$VAR`/`$?` re-expand on every iteration; that was the entire design
problem of Iteration 11.

So making this work needs the raw text of *one stage*, which means
splitting the raw line at unquoted `|` the way `RAW-LAST-SEMI` splits
at `;` for `while COND; do`. That is a real piece of work and now a
known one. Recorded rather than half-attempted: shipping a broken
capture would have been worse than shipping this instead.

### Verified

`tests/shell/run-pipe-redir` (7 assertions): `>` on the last stage,
`<` on the first, `2>/dev/null` on a stage with stderr confirmed not
leaking, a here-document into a pipeline, and plain pipelines
unaffected. 396 assertions across 48 files plus 1991 core OK markers,
both cell widths. mrsh-suite unchanged at 8.
## Iteration 59: `alias` and `unalias`

Aliases are expanded **textually, before the line is interpreted** —
"completely lexical", as Ramey's chapter puts it, which is why an alias
can introduce operators and change the grammar of the line it appears
in. `alias greet="echo hi;echo there"` really does run two commands.

`TRY-ALIAS` sits at the very top of `RUN-TOKENIZED`: it rebuilds the
line with the alias body in place of the first word, re-normalizes,
re-tokenizes, and runs the result through every check below as if it
had been typed that way. That placement is the whole design — putting
it after the `;`/`&&` splitting would have made an alias unable to
contain them.

`ALIAS-DEPTH` caps expansion at 8. Real shells instead suppress
re-expansion of the alias currently being expanded, which is more
precise; a depth cap needs no per-expansion state and fails by
diagnosing rather than hanging. `alias r="r"` terminates, and there is
a test for it.

### Reuse rather than a third copy

`alias NAME=value` needs the same `NAME=value` splitting that
`DO-ASSIGN` and `readonly` already use, so `SPLIT-ASSIGN-AT` was
factored out of `DO-ASSIGN-AT` — the split without the decision about
what to store. Three callers, one implementation. That is the second
time this particular splitting has been about to be duplicated
(Iteration 51 was the first).

### Verified

`tests/shell/run-alias` (8 assertions): simple expansion, an alias
introducing operators, arguments after the alias being kept,
`unalias` removing one with execution continuing, a self-referential
alias terminating, and redefinition replacing. 404 assertions across 49
files plus 1991 core OK markers, both cell widths.

mrsh-suite stays at 8. `command.sh` needs `alias` *and* `getopts`,
`command -v` on more shapes, and `ls -la` output matching; the
alias-expansion conformance case needs the shell to *reject* the
invalid usage it contains, which is Phase G work rather than a feature
gap.
## Iteration 60: unterminated quotes are a syntax error — mrsh 8 -> 9

The first Phase G item. `2.2.2-nested-single-quotes.fail.sh` passes:
POSIX says single quotes cannot contain single quotes, so `'''` is an
empty string followed by an unterminated quote. `bash` rejects it with
status 2; this shell accepted it silently and now reports
`syntax error: unterminated quote` and exits 2 as well.

`NORMALIZE-OPERATORS` already tracked quote state for its own purposes;
the change is to record whether a quote is still open at end of line
and refuse to run the line if so.

### A latent bug this exposed immediately

`run-quote` failed the moment the check went in: `echo "a\"b"` was
reported as unterminated. The double-quote tracking in
`NORMALIZE-OPERATORS` did not honour `\"` — it counted the escaped
quote as the closing one, so the *real* closing quote re-opened the
string.

That had been wrong all along and had never mattered, because nothing
acted on the leftover state; the actual unescaping happens later in
`COPY-DOUBLE-QUOTED`. Adding a consumer of the state turned an
approximation into a bug in one step.

Worth generalizing: **state that is only ever an approximation stops
being harmless the moment something reads it.** Nothing about the
tracking changed between it being fine and being wrong — only that a
second caller appeared. The existing test caught it, which is the
argument for keeping tests for behaviour that seems settled.

### Verified

`tests/shell/run-syntax-err` (6 assertions): both unterminated cases
rejected with status 2, and four lookalikes that must still work — a
properly closed quote, an escaped quote inside double quotes, a single
quote inside double quotes, and an empty quoted string. 410 assertions
across 50 files plus 1991 core OK markers, both cell widths.

**mrsh-suite: 8 passed -> 9.** Remaining 12: `getopts` and `f() ( ... )`
(`args.sh`), background jobs (`async.sh`), `ulimit`, `~user`
(`word.sh`), compound commands as pipeline stages (`read.sh`),
`command.sh`, `for.sh`, `function.sh`, `return.sh`, `subshell.sh`,
`readonly.sh`, `2.2-quoted-characters.sh`, and the alias conformance
case (which needs the shell to reject an invalid alias usage).
## Iteration 61: `getopts`, and `set --`

`getopts OPTSTRING NAME` parses the positional parameters one option at
a time: flag options, options taking an argument either attached
(`-cX`) or separate (`-c val`), clustered options (`-ab`), unknown
options reported as `?`, and stopping at the first non-option with
`OPTIND` left pointing at it. Checked case by case against `bash`; the
stdout now matches exactly.

`OPTIND` is a shell variable so a script can reset it to restart
parsing. The position *within* a clustered argument is internal state
(`GO-CPOS`), reset whenever `OPTIND` changes underneath us — which is
what makes `OPTIND=1` work.

### Two bugs, both found by comparing with bash rather than by reading

- **`set -- -a -b` made `--` into `$1`.** The `--` marks the end of
  options precisely so a value beginning with `-` is not mistaken for
  one, and it must not itself become a parameter. Nothing had exercised
  `set --` before; `getopts` is the first thing that needs it. Fixed in
  `DO-SET`.
- **`OPTARG` was not cleared for options that take no argument**, so a
  value left by an earlier `-c val` showed up against a later `-a`.
  Exactly the kind of stale-state difference that only appears when
  diffing against a reference implementation.

### Verified

`tests/shell/run-getopts` (11 assertions) covering all of the above.

One of those assertions was initially **wrong, and I committed it
failing** before reading the output — it asserted that
`set -- -- -x` leaves `$1` as `-x`. Running the same script through
bash shows `$1` is `--`: only the *first* `--` is consumed, and the
point of `set --` is that the next word is taken literally even if it
begins with a dash. The shell was right and the expectation was wrong.
Two lessons, the second more useful than the first: check the suite
output before committing, and write the expectation by running the
reference implementation rather than by reasoning about what it
probably does.
420 assertions across 51 files plus 1991 core OK markers, both cell
widths. mrsh-suite stays at 9 — `args.sh` also needs `f() ( ... )`,
a function body written as a subshell, and `command.sh` needs more
besides.
## Iteration 62: subshell function bodies — mrsh 9 -> 10 passed

`args.sh` passes. POSIX allows a function body to be any compound
command, so `f() ( ... )` is as valid as `f() { ... }` — and it means
something different: the body runs in a subshell, so its assignments,
`cd` and `exit` do not reach the caller.

Which form was used is recorded per function (`FUNC-SUBSH`), and
`RUN-FUNC-BODY` forks when the flag is set, recursing into itself with
the flag cleared in the child rather than duplicating the body loop.

### The bug this produced, and why it is instructive

My first version looked for the body opener with
`S" {" S" (" SPLIT-AT-EITHER-KEYWORD` — scanning the whole line for
either. For `f() {` the tokens are `f ( ) {`, so it matched the `(` of
the **parameter list** at index 1 and classified *every brace function*
as a subshell one. `run-func`, `run-return` and `run-nesting` all
failed at once.

The fix is to drop the three header tokens (`name`, `(`, `)`) before
looking for the opener. What is worth extracting is that Iteration 48
made parens self-delimiting precisely so `(` would be its own token —
and that same change is what put a stray `(` in the middle of a
function header, where a later feature then tripped over it. A change
that makes something uniform also makes it *ambiguous* in places that
previously had no reason to care.

Three existing test files caught it immediately, which is the argument
for the regression suite doing more than confirming the new feature.

### Verified

`tests/shell/run-func-subshell` (6 assertions): the subshell body
running, its assignments *not* reaching the caller, a brace body still
doing so, `exit` inside a subshell body setting the status without
exiting the shell, and arguments reaching the body. 426 assertions
across 52 files plus 1991 core OK markers, both cell widths.

**mrsh-suite: 9 passed -> 10.** Remaining 11: background jobs
(`async.sh`), `ulimit`, `~user` (`word.sh`), compound commands as
pipeline stages (`read.sh`), `command.sh`, `for.sh`, `function.sh`,
`return.sh`, `subshell.sh`, `readonly.sh`, `2.2-quoted-characters.sh`,
and the alias conformance case.
## Iteration 63: nested function definitions

A function definition (or a multi-line brace group) inside a function
body no longer truncates it. `DO-FUNCDEF`'s capture counts `{` depth
instead of stopping at the first `}` — the same shape as
`CAPTURE-CONTINUE?` for loops and `SPLIT-AT-3`'s `if`/`fi` tracking.
This retires the "nested function definitions are not supported" limit
recorded in Iteration 43.

### Re-diagnosing first paid off

I checked the remaining failures rather than working from the list I
had written, and two entries were wrong: `for.sh` and `subshell.sh`
both fail *later* than I had assumed — their opening constructs
(`for i in 1 $two $(echo 3); do`, `(a=b)`) already work, verified
against bash directly.

`function.sh` turned out to need two distinct things, only one of which
was on my list: nested definitions (this iteration) **and** a function
whose body is a bare compound command with no braces at all —
`func_d() if true; then echo func_d; fi`. POSIX allows any compound
command as a body; this shell accepts `{ }` and `( )`. That is a real
remaining gap and now a known one.

### Verified

`run-func-subshell` grew to 10 assertions, adding a self-redefining
function (both the outer body running in full and the redefinition
taking effect) and a multi-line group inside a body not truncating it.
430 assertions across 52 files plus 1991 core OK markers, both cell
widths. mrsh-suite stays at 10, since `function.sh` needs the
braceless-body form too.
## Iteration 64: multi-line groups — mrsh 10 -> 11 passed

`subshell.sh` passes. A group whose opener is alone on its line now
works:

    (
        echo a
    )

`SPLIT-GROUP` only handles a group contained within one line, so this
captures the body the way `DO-WHILE` and `DO-FUNCDEF` do and replays it
through `DO-WHILE-BODY`. A `(` group runs in a fork, a `{` group in
this shell — the same distinction `SPLIT-GROUP`'s two callers already
make.

### The diagnosis was the interesting part

`subshell.sh` and `return.sh` both produced output **identical to
bash** and still failed. Their exit statuses were 127 and 124 (a
timeout). The stdout matched only by accident: the lines of the group
body ran as ordinary top-level commands, printing the same thing, while
the bare `(` and `)` were each treated as a command that did not exist.

Two things worth taking from that. A test comparing stdout *and* status
caught something stdout alone would have called a pass. And "identical
output" was the strongest possible hint that the failure was
structural rather than a missing feature — the work was being done,
just not by the construct that was supposed to do it.

`MG-END?` is the fourth place this codebase counts nesting depth to
find a construct's own terminator (after `CAPTURE-CONTINUE?`,
`SPLIT-AT-3` and `FD-BODY-END?`). Four instances of one shape is worth
a note for the next duplication audit, though they differ in which
tokens open and close.

### Known wart, recorded rather than hidden

Reusing `DO-WHILE-BODY` for the replay means it also clears
`LOOP-CONTROL-PENDING?` on the way out, so a `break` inside a
multi-line group nested in a loop is swallowed instead of propagating.
Still better than a second copy of the replay loop; the flag handling
wants factoring out when something actually needs it.

### Verified

`tests/shell/run-multiline-group` (7 assertions): a subshell body
running with its assignment not escaping, a brace group's assignment
persisting, a sane exit status, and a nested multi-line group with the
outer body continuing past it. 437 assertions across 53 files plus 1991
core OK markers, both cell widths.

**mrsh-suite: 10 passed -> 11.** `return.sh` hangs (status 124) and is
next; `for.sh` needs field splitting of an unquoted variable in a `for`
word list.
## Iteration 65: `return` inside a loop — mrsh 11 -> 12 passed

`return.sh` passes. A `return` inside a `while` or `for` inside a
function now ends the function, rather than only ending the body line.

### A hang, not a wrong answer

`return.sh` had been failing with status 124 — a timeout. The cause:

    func_c() {
        while :
        do
            return
        done
    }

`return` sets `RETURN-PENDING?`, and `RUN-FUNC-BODY` checks it — but
nothing between the two did. `DO-WHILE-BODY` checked only
`LOOP-CONTROL-PENDING?` (set by `break`/`continue`), and `DO-WHILE`'s
iteration loop checked only `LOOP-BREAK?`. So the return was recorded,
the body ended, and the loop re-evaluated its condition — which was
`:`. Forever.

Three loop conditions now also stop on `RETURN-PENDING?`:
`DO-WHILE-BODY`, `DO-WHILE`'s iteration loop, and `DO-FOR-ITERATE`.
The flag is deliberately *not* cleared in any of them — only
`RUN-FUNC-BODY` consumes it, which is what lets it propagate outward
through however many nested loops sit between the `return` and the
function boundary.

Worth noting the general shape: this shell has three "stop what you are
doing" flags (`RETURN-PENDING?`, `LOOP-CONTROL-PENDING?`,
`LOOP-BREAK?`) and every construct that loops has to know which of them
apply to it. Adding a construct means auditing all three, and adding a
flag means auditing every construct. The bug was a missing cell in that
matrix, not a mistake in any one word. Something to keep in view if a
fourth flag ever appears.

### Verified

`run-return` grew from 10 to 17 assertions, adding `return` inside a
`while :` (body running exactly once, function ending, shell
continuing, nothing after the return executing) and `return 4` inside
a `for` (one iteration, status preserved, loop not continuing). 444
assertions across 53 files plus 1991 core OK markers, both cell widths.

**mrsh-suite: 11 passed -> 12.** Remaining 9: background jobs
(`async.sh`), `ulimit`, `~user` (`word.sh`), compound commands as
pipeline stages (`read.sh`), field splitting in a `for` word list
(`for.sh`), a braceless compound function body (`function.sh`),
`command.sh`, `readonly.sh`, `2.2-quoted-characters.sh`, and the alias
conformance case.
## Iteration 66: field splitting of command substitution, and the
## assignment exception

An unquoted `$(...)` is now subject to IFS field splitting, so
`for c in $(echo a s d f)` runs four times. One word changed in the
command-substitution splice: `EMIT-EXPANDED-CHAR` instead of
`EMIT-TOK-CHAR`, the same word an unquoted `$VAR` already used.

### Which immediately exposed a bigger, older bug

That one-word change broke `x=$(echo a b)` — the value got split and
the variable ended up empty. Checking whether this was new found that
**`q=$p` was already broken the same way**, and had been since IFS
splitting landed in Iteration 36. POSIX does not field-split the value
of an assignment; this shell was splitting both, and only the
command-substitution path had been accidentally exempt by not
splitting at all.

So the honest fix was not to revert but to implement the exception:
`TOKEN-IS-ASSIGN-PREFIX?` asks whether the token accumulated so far
looks like `NAME=`, and `EMIT-EXPANDED-CHAR` suppresses splitting when
it does — alongside the `IN-DQ-CONTEXT?` check it already had.

It is computed from the token being built rather than kept as a flag,
so there is no reset discipline to get wrong: no "clear it at the start
of each token" that a later code path could skip. Given how many bugs
in this project have been stale state (Iterations 28, 47, 49, 61), a
derived answer beat a stored one here.

**Net: two POSIX conformance bugs fixed, one of which nothing had
noticed for thirty iterations.** Reverting would have hidden it again.

### Verified

`tests/shell/run-split-cmdsub` (7 assertions): unquoted `$(...)`
splitting, quoted `$(...)` staying one word, assignment from `$(...)`
*and* from `$VAR` keeping their blanks, and unquoted `$VAR` still
splitting. 451 assertions across 54 files plus 1991 core OK markers,
both cell widths.

mrsh-suite stays at 12 — `for.sh` also needs `IFS=':'` set inside a
subshell to affect splitting there, which is the next thing in that
file.
## Iteration 67: `$IFS` actually controls field splitting — mrsh 12 -> 13

`for.sh` passes. `IFS-CHAR?` was hardcoded to space and tab: the
variable could be set and was simply never read, so `IFS=':'` had no
effect at all. It now consults `$IFS`, defaulting to space/tab/newline
per POSIX when unset. An IFS that is set but *empty* correctly
disables splitting, since nothing is a member of an empty set.

### An obsolete test caught by the change

`run-cmdsub` failed immediately, asserting that an unquoted
`$(printf 'line1\nline2\n')` keeps its internal newline. Checked
against bash: it prints `START-line1 line2-END` — the newline is an
IFS character, so it separates fields and `echo` rejoins them with a
space. Our shell now produces exactly that.

The assertion was encoding the behaviour from *before* IFS splitting
existed (Iteration 36), and had survived because newline had never
been in the separator set. The shell became right and the test became
wrong in the same commit. Fixed the assertion, and recorded why in
the test itself so it is not "corrected" back.

That is the second time in three iterations that a test encoded a
pre-conformance behaviour (see also Iteration 61's `set --`). The
lesson from `FORTH-STYLE.md` — write expectations by running the
reference implementation — applies to *updating* an assertion as much
as writing one.

### Verified

`tests/shell/run-ifs` (5 assertions): `IFS=':'` splitting on colon, a
space no longer splitting once IFS is set, and the default still
splitting on space. 460 assertions across 55 files plus 1991 core OK
markers, both cell widths.

**mrsh-suite: 12 passed -> 13.** Remaining 8: background jobs
(`async.sh`), `ulimit`, `~user` (`word.sh`), compound commands as
pipeline stages (`read.sh`), a braceless compound function body
(`function.sh`), `command.sh`, `readonly.sh`,
`2.2-quoted-characters.sh`, and the alias conformance case.
## Iteration 68: `readonly -p` — mrsh 13 -> 14 passed

`readonly.sh` passes. `readonly -p`, and bare `readonly` with no
operands, now list the read-only variables in the form POSIX
specifies — `readonly NAME=VALUE`, re-readable as input.

Small, and the whole of what that test needed: it does
`readonly -p | grep mrsh_readonly_param | wc -l` and expects 1, which
was 0 because the listing form printed nothing at all.

### Verified

`run-builtins2` grew to 12 assertions, adding that `readonly -p` lists
a read-only variable, does *not* list an ordinary one, and that bare
`readonly` behaves the same. 463 assertions across 55 files plus 1991
core OK markers, both cell widths.

**mrsh-suite: 13 passed -> 14**, i.e. two-thirds of the 21 scored
tests. Remaining 7: background jobs (`async.sh`), `ulimit`, `~user`
(`word.sh`), compound commands as pipeline stages (`read.sh`), a
braceless compound function body (`function.sh`), `command.sh` (which
needs `command -v` to report a *function* ahead of a same-named
external, plus `ls -la` output matching), the newline-escape case in
`2.2-quoted-characters.sh`, and the alias conformance case.
## Iteration 69: `command -v` for reserved words and aliases, and
## LF-only output

### The systemic bug this uncovered

`command.sh` came down to a one-byte-per-line difference: **`\r`**.

This kernel's `CR` emits CRLF (13 then 10) — correct for a Forth
console, wrong for a shell. Every builtin that printed a line — `pwd`,
`command -v`, `readonly -p`, every diagnostic — had been emitting a
stray carriage return since the first iteration, so their output
differed from every other shell by one byte per line.

It had gone unnoticed for 68 iterations because the shell's own test
harness uses substring assertions, which `\r` does not disturb, and
because `echo` is an external command that never went through this
path. Only a byte-exact comparison against a reference implementation
surfaced it. Fixed by redefining `CR` once at the top of `shell.4`, so
every later definition in the file gets it and nothing outside is
affected.

That is the strongest argument yet for the differential test being the
acceptance criterion rather than the hand-written suite: 463 local
assertions all passed while every builtin emitted a wrong byte.

### `command -v` extended

Reserved words (`if`, `then`, `while`, …) and aliases are now reported,
per POSIX — `command -v if` prints `if`, `command -v ll` prints
`alias ll='ls -l'`. The alias *table* moved ahead of `DO-COMMAND`,
leaving the expansion machinery where it needs `NORMALIZE-OPERATORS`.

### A spec conflict, recorded rather than papered over

`command.sh` still fails, on one line, and the reason is worth stating
precisely: **bash does not expand or report aliases in non-interactive
shells**, so `command -v ll` gives status 1 there. That is a documented
bash deviation; POSIX says alias substitution applies, which is what
this shell does.

So on this one line the acceptance criterion (match bash byte for byte)
and the goal (POSIX conformance) disagree, and this shell is on the
POSIX side. Contorting to match bash's extension would make the shell
less correct to make a number go up. Left as is, and recorded in
`GOALS.md` so the failing count is read accurately.

### Verified

`tests/shell/run-newline` (3 assertions) checks directly that `pwd` and
`command -v` emit no carriage return and still print their answer. 466
assertions across 56 files plus 1991 core OK markers, both cell widths.
mrsh-suite stays at 14 for the reason above.
## Iteration 70: line continuation

A backslash at end of line joins it to the next, per POSIX. Both the
backslash and the newline are removed and the result is one logical
line.

Done at the **reading** end — `JOIN-CONTINUATIONS`, called from
`RUN-LINE` and `READ-LINE-INTO-ARGV` — before quote tracking or
tokenizing, so every consumer sees a single line and nothing
downstream needs to know line continuation exists. It reads through
`READ-INPUT-CALL`, which means a continuation inside a loop body or
function reads from the stored body like everything else; that is
tested, not assumed.

`\\` at end of line is an *escaped backslash*, not a continuation,
which is why the preceding character is checked too — also tested.

This also retires a limitation asserted in `NORMALIZE-OPERATORS`'
own comment since Iteration 60 ("this shell has no line
continuation, so end of line really is the end of the word").

### Verified

`tests/shell/run-continuation` (5 assertions): a continued line
becoming one command, execution continuing afterwards, a doubled
backslash *not* continuing, and a continuation inside a `for` body
working on every iteration. 471 assertions across 57 files plus 1991
core OK markers, both cell widths.

mrsh-suite stays at 14. `2.2-quoted-characters.sh` needed this and
still differs further down the file; the remaining differences are in
its own later sections rather than in continuation itself.
## Iteration 71: quoting inside `$(...)`

`$(echo "one two")` now passes **one** argument. The inner tokenizer
(`CMDSUB-TOKENIZE`) was deliberately whitespace-only — a documented
scope limit since Iteration 13 — so a quoted argument became several
words and its quotes were passed through literally.

It is now quote-aware: a quoted run is one token with its quotes
removed, compacted in place (safe, since the output can only be
shorter — quotes are dropped and nothing is inserted). `EXPAND-CMDSUB`'s
search for the closing `)` also skips quoted regions, so a `)` inside
the command text no longer ends the substitution early.

This is a piece of Phase E rather than the whole of it. What remains
there: backquotes (`` `cmd` ``), and *nested* `$(...)`. Ramey's chapter
argues for solving both by reusing the real parser with `)` flagged as
a context-dependent terminator, rather than by continuing to grow this
second tokenizer — which is exactly what he says went wrong with
bash's own `parse_comsub`. This iteration improves the duplicate
because the improvement was small and self-contained; the next step
there should be the parser reuse, not more of this.

### Known remaining edge

`$(echo "a)b")` yields `a ) b`. `NORMALIZE-OPERATORS` copies a `$(...)`
region verbatim but does not itself track quotes *within* it, so the
`)` inside the string ends its cmdsub-mode early and the rest gets
operator spacing. Recorded rather than fixed: it wants the same quote
tracking one level up, and is a narrow case next to the parser work
above.

### Verified

`tests/shell/run-cmdsub-quotes` (4 assertions): a double-quoted
argument staying one word, single quotes likewise, unquoted still
working, and several arguments with one quoted. 475 assertions across
58 files plus 1991 core OK markers, both cell widths. mrsh-suite stays
at 14 — `2.2-quoted-characters.sh` needed this and still needs
backquotes.
## Iteration 72: braceless compound function bodies, and functions
## inside `$(...)` — mrsh 14 -> 15 passed

`function.sh` passes. Two independent gaps, both found by diffing:

**POSIX allows any compound command as a function body**, not only
`{ }` or `( )`. `f() if true; then echo yes; fi` is valid, and is what
`function.sh` uses. `DO-FUNCDEF` now detects a compound keyword where
the body opener would be, stores the rest of the header line as the
body's first line (`FD-RAW-AFTER-PAREN` shifts `RAW-LINE-BUF` past the
`)`, which is safe once the header tokens have been read out of
`ARGV`), and reads further lines only when the construct is not
already complete on that line — `FDC-BALANCED?` decides which.

**A function or builtin inside `$(...)`** now runs. `output=$(func_a)`
had been exec'ing, which simply fails to find a function.
`RUN-CMDSUB-CHILD` moved below `PIPE-STAGE-INTERNAL?` so it can reuse
that same test — the third caller of it now, after the pipeline and
groups. Worth noting the shape: "does this have to run inside the
shell rather than be exec'd" turned out to be one question with three
callers, not three separate judgements.

### Two bugs of my own, both off-by-one in a depth counter

`FDC-BALANCED?` used `0 <=`, which this kernel does not have — caught
at load. And the capture loop started its depth at 1 rather than 0, so
the body's own closing `done` was counted as an inner construct's and
the capture ran past it: the multi-line braceless case produced
nothing at all. The depth counts constructs opened *inside* the body;
the outer one's terminator is what ends the capture.

That is the fifth depth-counting site in this codebase and the second
to get its starting value wrong. Worth a note for the next audit:
they are not textually similar enough to merge, but the *initial
value* is the part that keeps being subtly different.

### Verified

`run-func-subshell` grew to 16 assertions, adding a one-line braceless
`if` body, a multi-line braceless `while` body (with its body
correctly not running), and a function and a builtin each inside
`$(...)`. 481 assertions across 58 files plus 1991 core OK markers,
both cell widths.

**mrsh-suite: 14 passed -> 15** of 21 scored. Remaining 6: background
jobs (`async.sh`), compound commands as pipeline stages (`read.sh`),
`~user` (`word.sh`, needs a password-database primitive the kernel does
not expose), backquotes (`2.2-quoted-characters.sh`), the alias
conformance case, and `command.sh` — which is the one deliberately
left failing on the POSIX-versus-bash alias conflict recorded in
`GOALS.md`.
## Iteration 73: backquote command substitution

`` `cmd` `` works, in a bare word and inside double quotes, and is
literal inside single quotes.

### One parameter, not a second implementation

The backquote form is `$(...)` with a different terminator and nothing
else. So `EXPAND-CMDSUB` gained a `closer` parameter — `)` for the
dollar form, `` ` `` for this one — and both call the same word. A
second copy would have been precisely the duplication
`FORTH-STYLE.md` exists to prevent, and precisely what Ramey names as
the mistake in bash's own `parse_comsub`.

`NORMALIZE-OPERATORS` also needed a backquoted region copied verbatim,
for the same reason a `$(...)` one is: the operators inside belong to
the substituted command, not to the enclosing line.

### What is left in Phase E, and why it should not be built here

`2.2-quoted-characters.sh` now differs on one line: a **nested**
`$(...)` inside a substitution. That is the last piece, and it is the
one that should *not* be added to this second tokenizer.

Ramey's chapter is explicit that bash's equivalent "knows an
uncomfortable amount of shell syntax and duplicates rather more of the
token-reading code than is optimal", and recommends instead using the
real parser with `)` flagged as a context-dependent EOF and parser
state saved and restored around a recursive parse. This shell now has
what that needs: replay as an input source (Iteration 42), locals for
cheap state save/restore (38), and `GRP-DEPTH`-style nesting counts.
Three iterations have each added a little to `CMDSUB-TOKENIZE`; the
fourth should replace it.

### Verified

`tests/shell/run-backquote` (6 assertions): backquotes inside double
quotes, bare in a word, containing a quoted argument, in an
assignment, `$(...)` still working alongside, and backquotes literal
inside single quotes. 487 assertions across 59 files plus 1991 core OK
markers, both cell widths. mrsh-suite stays at 15 for the reason
above.
## Iteration 74: background jobs — mrsh 15 -> 16 passed

`async.sh` passes. `cmd &` runs in the background, `$!` gives the most
recent background pid, and `wait` waits — for one pid if given, for
all children if not.

The `&` is dropped from `ARGV` before anything else looks at the line,
so every construct below sees an ordinary command; the forked child
then runs it by recursing into `RUN-SIMPLE-OR-PIPELINE`. That means
background works with pipelines, groups and builtins without any of
them knowing about it.

`wait` with no children is not an error, and a *quoted* `&` stays a
literal argument — both tested, since both are easy to get wrong in
the direction of a hang or a misparse.

### A separate gap found while writing the tests

My first test used `case "$p" in [0-9]*) echo num ;;` — a `case` arm
with its body on the **same line** as the pattern. That produces
nothing here; bash prints `num`.

It is not a regression, and not about bracket patterns: `DO-CASE`
expects the pattern alone on its line with the body following, and
since Iteration 48 split `)` into its own token the same-line form
puts the body in `ARGV` alongside the pattern, where
`CASE-ARM-MATCHES?` tries each word as an alternative. Same-line arms
are a documented gap in `DO-CASE`'s own comment; this is the first
time something ran into it. Recorded rather than worked around
silently — the test was rewritten to use `if`, which is what it was
actually testing.

### Verified

`tests/shell/run-background` (6 assertions): `$!` being a pid, `wait`
returning, a background command not blocking the shell, its output
still arriving, a quoted `&` staying literal, and `wait` with no
children. 493 assertions across 60 files plus 1991 core OK markers,
both cell widths.

**mrsh-suite: 15 passed -> 16** of 21 scored. Remaining 5: nested
`$(...)` (`2.2-quoted-characters.sh` — the parser-reuse work),
compound commands as pipeline stages (`read.sh`), `~user` (`word.sh`,
needs a kernel primitive), the alias conformance case, and
`command.sh`, still deliberately failing on the POSIX-versus-bash
alias conflict.
## Iteration 75: same-line `case` arms

`case "$p" in [0-9]*) echo num ;; *) echo other ;; esac` — pattern,
body and `;;` all on one line — now works. Found in Iteration 74 while
writing an unrelated test, and recorded then rather than worked
around; this is the fix.

### Reusing the mechanism that already existed

`DO-CASE` now splits an arm line at its `)` with `SPLIT-AT-KEYWORD`,
leaving the patterns in `ARGV` and the body as the pending remainder,
and splits a body line at `;;` the same way. That is exactly how
`DO-IF` has handled a same-line `then`/`else`/`fi` since Iteration 25 —
no new machinery, just two more callers of it.

### And it deleted code

`CASE-ARM-MATCHES?` had been stripping a trailing `)` from the last
pattern token, with its own buffer and length variable. That became
vestigial when Iteration 48 made `)` a self-delimiting token, and
outright wrong once `DO-CASE` splits the arm at the `)` itself — it
would have stripped a real character from the last pattern. Removed:
every remaining token is now simply a whole pattern.

Worth noting the shape. Iteration 48 changed how `)` tokenizes, and
that change has now rippled into four separate places — function
headers (62), `case` pattern stripping (48 and again here), the
multi-line group check (64), and this. A tokenization change is not
local, and the places it reaches are not all found at once.

### Verified

`run-case` grew from 16 to 20 assertions: a same-line arm with a
bracket pattern matching, a later arm correctly *not* also running,
falling through to `*`, and `|` alternatives on a same-line arm. 497
assertions across 60 files plus 1991 core OK markers, both cell
widths. mrsh-suite unchanged at 16 — no vendored test uses this form,
which is why it went unnoticed for fifty iterations.
## Iteration 76: compound commands as pipeline stages — attempted and
## reverted, with the design established

`printf "a\nb\nc\n" | while read line; do ...; done` (mrsh's
`read.sh`) still does not work. This iteration attempted it, got the
design right, and ran out of room to land it cleanly — so it was
**reverted rather than committed half-done**. The tree is green at 16
passed; what follows is what the attempt established, so the next one
starts from it rather than rediscovering it.

### The design, confirmed by building most of it

Three pieces are needed, and the first two were written and worked:

1. **Capture the stage's body in the parent, before forking.**
   `CAPTURE-PIPE-BODY` reads the construct's remaining lines into a
   `BUFFER:` using `FDC-LINE-END?`'s depth counting. This is the fix
   for the file-offset race found in Iteration 57: a forked child
   shares the script's offset with the shell, so the two race for the
   same lines. The parent consuming them is also *correct* — they
   belong to the construct.
2. **Give the stage its own raw text.** `DO-WHILE` stores its
   condition as raw text deliberately, so `$VAR` re-expands each
   iteration (Iteration 11), but for a stage the whole pipeline line
   is not its own text. `RAW-AFTER-LAST-PIPE` shifts `RAW-LINE-BUF`
   past the last unquoted `|`. This also generalized `RAW-LAST-SEMI`
   into `RAW-LAST-CHAR ( c-addr u c --- pos )`, which is worth keeping
   whatever happens next.
3. **Install the captured body as the child's input source** —
   `REPLAY-SRC`/`LEN`/`POS` set before `RUN-TOKENIZED-CALL`, exactly
   as `DO-WHILE-BODY` does.

### Why it did not land: file ordering, four times

Every piece needs words defined far below the pipeline section —
`RAW-LINE-BUF`, `READ-NEXT-LOGICAL-LINE`, `RAW-LAST-CHAR`,
`FDC-DEPTH`/`FDC-LINE-END?`. Each move to satisfy one dependency
exposed the next. Two deferred-word indirections were added and the
replay variables were hoisted, and it still was not resolved when the
budget ran out.

That is the real finding, and it is not about this feature. This file
is 4,900 lines in one linear definition order, and a change that spans
the tokenizer, the pipeline and the loop machinery now costs more in
reordering than in logic. The deferred-word pattern has been used
**nine** times to break such cycles. It works, but each use is a hole
in the ordering rather than a fix for it.

**Recommendation for the next session:** before attempting this again,
consider splitting `shell.4` into loadable sections with an explicit
dependency order, or introducing a forward-declaration convention
rather than a per-case deferred variable. The feature is ~60 lines;
the ordering is what makes it expensive.
## Iteration 77: `DEFER` / `IS`

Acting on Iteration 76's own recommendation rather than filing it.

Forward declaration was hand-written fourteen times: a `VARIABLE`
holding an offset xt, a one-line caller word, and a patch line after
the real definition. Three pieces of boilerplate per site, and the
attempt in Iteration 76 ran aground partly because adding two more was
enough friction to lose the thread.

Now one line each way:

    DEFER RUN-TOKENIZED-CALL
    ...
    : RUN-TOKENIZED ... ;
    ' RUN-TOKENIZED IS RUN-TOKENIZED-CALL

Built on `CREATE`/`DOES>` and `>BODY`, which the kernel already had.
The stored value stays a `START`-relative offset — these go into a
saved image — and **an unpatched `DEFER` is a no-op rather than a jump
to address zero**, so a forgotten patch shows up as "nothing happened"
instead of a segfault. That is deliberate: it is the difference
between a puzzling result and a crash in a language with no type
checking.

All seven remaining sites converted mechanically. Two patch lines the
script missed were caught by the loader on the next build, which is
the ordinary way this file reports a mistake and cost a minute each.

This does not by itself fix the ordering problem Iteration 76 hit —
the file is still one linear definition order — but it makes each
forward reference cheap enough that reaching for one is no longer a
small design decision. Splitting `shell.4` into sections with an
explicit dependency order remains the larger recommendation.

### Verified

Behaviour-preserving refactor: 497 assertions across 60 files plus
1991 core OK markers, both cell widths, and mrsh-suite unchanged at 16
passed. `FORTH-STYLE.md`'s define-before-use rule now documents
`DEFER`/`IS` instead of the hand-rolled pattern.
## Iteration 78: compound pipeline stages, second attempt — reverted

Retried Iteration 76's feature now that `DEFER` makes forward
references cheap. **The ordering problem is gone**: all three pieces
compiled and loaded cleanly on the first try, where the previous
attempt never got that far. `DEFER` did what it was added for.

The feature itself is still wrong, and it was reverted. Tree green at
16 passed.

### Symptom, precisely

`printf "a\nb\nc\n" | while read line; do echo "got:$line"; done`
prints `got:` unbounded — 4,660 lines in five seconds. The loop body
runs, `$line` is never set, and the loop never ends.

That signature says the **condition text is empty**: an empty
condition leaves `LAST-STATUS` at 0, so `DO-WHILE` loops forever
without ever running `read`. It is not the pipe (a builtin as a
pipeline stage has worked since Iteration 57) and not the body capture
(the body clearly replays).

So the suspect is `RAW-AFTER-LAST-PIPE`, which trims `RAW-LINE-BUF` to
what follows the last unquoted `|` before `SAVE-WHILE-COND` skips the
literal `while`. Either the trim is producing nothing, or
`RAW-LINE-BUF`/`RAW-LINE-LEN` are not what that word assumes at the
point the child calls it.

### Why revert rather than push on

The previous behaviour was "produces no output"; this one is "loops
without terminating". Shipping it would trade a missing feature for a
hang, and the local suite would not have caught it — no existing test
uses this shape, which is precisely why it is worth being careful
here.

**Next step is a narrow one**, not a redesign: instrument
`RAW-AFTER-LAST-PIPE` in isolation (print `RAW-LINE-BUF` before and
after) rather than reasoning about it. The isolated-diagnostic-first
habit from `FORTH-STYLE.md` is what both attempts skipped — the design
was verified by reading, and the one word doing string surgery was
not.

### Kept

`RAW-LAST-CHAR` — the generalization of `RAW-LAST-SEMI` to any
character — was part of the reverted change and is worth re-adding
first next time; it is independently useful and was not implicated.
## Iteration 79: third attempt — the isolated diagnostic paid off, and
## found the *next* obstacle

Followed `FORTH-STYLE.md`'s own rule this time: built the suspect word
standalone before touching anything.

**The trim was correct all along.** Loaded `shell.4`, set
`RAW-LINE-BUF` to `printf x | while read line`, ran the scan and the
trim in isolation: last `|` at offset 9, result `[while read line]`.
Exactly right. Two iterations had blamed the wrong word, on the
strength of reading it rather than running it.

### The actual bug, and the one after it

**Bug 1 — ordering of trim vs capture.** Capturing the body reads
lines, and reading a line overwrites `RAW-LINE-BUF`. Doing the capture
first left `RAW-LINE-BUF` holding `done`, so the condition came out
empty and `DO-WHILE` spun forever — Iteration 78's unbounded loop.
Trimming and *saving* the stage text before capturing fixed it: the
loop now terminates and reaches the line after `done`.

**Bug 2, found immediately after — the same class, one level deeper.**
The body still does not run. `SPLIT-PIPE` copies the pipeline's tokens
into `PIPE-ARGV`, but those are **pointers into `LINE-BUF`** — and
capturing overwrites `LINE-BUF` too. By the time the pipeline forks,
its own segment text is gone.

That is `FORTH-STYLE.md` §9 (globals do not survive a call that can
reach them) landing twice in one feature, on two different buffers.
The shape is now unmistakable: **anything that reads a line destroys
the current line**, and this feature has to read lines in the middle
of processing one.

### The fix that follows, recorded for next time

Capture *before* `SPLIT-PIPE`, not after:

1. detect a compound last stage from `ARGV` (still valid at that point)
2. save the whole raw pipeline line
3. capture the body — freely clobbering `LINE-BUF`/`ARGV`
4. restore the saved line, re-normalize, re-tokenize, then `SPLIT-PIPE`
5. run the pipeline as usual

Reverted rather than shipped: the tree is green at 16 passed, and a
half-working pipeline stage is worse than a missing one.

Three attempts, three distinct obstacles, each now named: file
ordering (fixed by `DEFER`, Iteration 77), trim-versus-capture order,
and `LINE-BUF` lifetime. None was visible from reading the code; each
took running it.
## Iteration 80: compound pipeline stages — mrsh 16 -> 17 passed

`read.sh` passes. `printf "a\nb\nc\n" | while read line; do ...; done`
works. Four attempts; this one landed because the previous three each
named a distinct obstacle instead of guessing.

### The order that works, and why each step is there

    save the raw line          \ reading destroys it (Iteration 78)
    capture the body           \ freely clobbering LINE-BUF/ARGV
    restore the line
    derive the stage's raw text
    restore again, re-tokenize \ PIPE-ARGV points INTO LINE-BUF (79)
    SPLIT-PIPE, run

All in the parent, before any fork — a forked child shares the
script's file offset and would race for the body lines (Iteration 57).

Every one of those steps exists because of a specific failure that was
*observed*, not anticipated. The feature is about sixty lines; the
four iterations went on buffer lifetime, which no amount of reading
the code revealed.

### The four obstacles, in the order they appeared

1. **File ordering** — every piece needs words defined far below the
   pipeline section. Fixed by `DEFER`/`IS` (Iteration 77), and this
   attempt compiled first try.
2. **Trim after capture** — capturing overwrites `RAW-LINE-BUF`, so
   the condition came out empty and the loop spun forever (78).
3. **`LINE-BUF` lifetime** — `PIPE-ARGV` holds pointers into it, and
   capturing overwrites it too, so the pipeline lost its own segment
   text (79).
4. **Capturing an already-complete construct** — found while writing
   the tests here: with the whole loop on one line there is nothing to
   capture, and capturing anyway swallows the *next* line.
   `FDC-BALANCED?` guards it.

### Verified

`tests/shell/run-pipe-compound` (5 assertions): a `while` stage
receiving each piped line, the shell continuing afterwards, ordinary
pipelines unaffected, and a plain loop outside a pipeline unaffected.
502 assertions across 61 files plus 1991 core OK markers, both cell
widths.

A fully one-line `while ...; do ...; done` remains unsupported — here
*and* outside a pipeline, since `DO-WHILE` reads its body from
following lines. Verified directly rather than assumed, and
deliberately not asserted either way: pinning down the failure mode of
an undesigned shape would be asserting behaviour nobody chose.

**mrsh-suite: 16 passed -> 17** of 21 scored. Remaining 4: nested
`$(...)` (`2.2-quoted-characters.sh` — the parser-reuse work), `~user`
(`word.sh`, needs a kernel primitive), the alias conformance case, and
`command.sh`, still deliberately failing on the POSIX-versus-bash
alias conflict.
## Iteration 81: the alias conformance case is the same conflict

Diagnosed `2.2.3-alias-expansion.fail.sh` rather than assuming it was
Phase G work like the unterminated-quote case (Iteration 60). It is
not:

    alias myalias="echo )"
    var="$(myalias arg-two)"

bash exits 127 — not because it rejects anything, but because it does
not expand aliases in non-interactive shells, so `myalias` is simply
not a command. This shell expands it, per POSIX, and exits 0.

That is the *same* deviation already recorded for `command.sh`. Both
remaining alias tests are one disagreement between the acceptance
criterion (match bash byte for byte) and the goal (POSIX conformance),
and on both this shell is on the POSIX side.

**`GOALS.md` now states the realistic ceiling: 19 of 21, not 21.** It
matters that the number is honest — a project tracking a score should
not leave two permanently-unreachable tests looking like unfinished
work, and someone picking this up cold would otherwise spend an
iteration discovering what took one command to check.

The two genuinely reachable ones are named where they belong: nested
`$(...)`, which should come with replacing `CMDSUB-TOKENIZE` rather
than extending it a fourth time, and `~user`, which needs a
password-database primitive the kernel does not expose — an engine
change, not shell work.

### Status at 81 iterations

17 of 21 mrsh tests pass, 2 of the remaining 4 by deliberate choice.
502 assertions across 61 test files plus 1991 core Forth OK markers,
green on both 8-byte and 4-byte cell widths. `relfsh` starts in ~1.8ms
from a prebuilt, byte-reproducible image; the i386 build is
90KB of engine plus image, against `dash`'s 121KB.
## Iteration 82: auditing the 17 passes for hollowness

This project has twice had a pass that was not real — the
alias-expansion accident (Iterations 14-36) and `run-case` staying
green through a wrong change (48). At 17 of 21 it is worth knowing
which passes actually mean something, so each was re-run and its
output measured rather than trusted.

**Fifteen are substantive**, producing between 4 and 41 lines of real
output that matches bash exactly: `arithm` (41), `for` (26), `case`
(18), `pipeline` (16), `if` (13), `loop` (12), `function` and
`subshell` (8), `syntax` (6), `async` (5), `read`, `redir` and
`return` (4), `readonly` (2), plus
`2.2.2-nested-single-quotes.fail.sh`, which is status-only *by
design* — it checks that the shell rejects `'''`, which it does since
Iteration 60.

**Two are weak, and should be read as such:**

- **`ulimit.sh` is hollow**, as recorded back in Iteration 40 and
  still true: `command -v ulimit` finds nothing, so the builtin does
  not exist. Both shells fail at the same point and their single line
  of output coincides. It will become real when `ulimit` and
  backquote-free `$(...)` both land.
- **`args.sh` is thin.** It produces *no output at all* — it defines
  `func() ( getopts "abcd" opt )` and calls it four times. What it
  genuinely verifies is that a subshell function body parses and that
  `getopts` exits 0 on a valid option; without `getopts` at all the
  script would exit 127 rather than 0. It verifies nothing about
  `OPTARG`, `OPTIND` or clustering — that assurance comes from
  `tests/shell/run-getopts` (11 assertions), not from here.

### Why bother

The mrsh count is the headline number in `GOALS.md`, and a headline
number that includes an accident is worse than a smaller honest one.
Recording *which* passes are thin also says where the local suite is
carrying the weight: `getopts` is well covered locally and barely
covered by the vendored test, which is the opposite of the impression
"args.sh passes" gives.

Nothing changed in the shell this iteration. 502 assertions across 61
files plus 1991 core OK markers, both cell widths, mrsh 17 of 21.
## Iteration 83: a differential test suite, and two bugs it found
## immediately

Prompted by the question "should we use bash's tests for getopts?".
Two separate things are bundled in that: bash's test *files*, and
bash's *answers*.

**Not the files.** Bash is GPLv3 and this project is GPLv2 (GOALS.md)
— a licence incompatibility, not a preference. Its tests also exercise
bash extensions this shell deliberately does not have, so importing
them would mean importing failures that are bash-isms.

**Yes to the answers**, and we already have them: the mrsh harness
runs bash live. The real weakness was elsewhere — `tests/shell/*`
assert expectations *written by hand*, and twice those were simply
wrong about POSIX while the shell was right (`set -- -- -x`,
Iteration 61; an unquoted multi-line command substitution, 67).

So: `tests/diff/`. Every script in `cases/` is run through `relfsh`
and through a reference shell and both stdout and exit status must
match. Nothing is hand-written but the input, so that whole class of
mistake cannot occur. It skips silently where no reference shell
exists, and is wired into `tests/run_tests.sh`.

### It found two bugs on its first run

**A real splitting bug, now fixed.** `echo unquoted=$(printf 'l1\nl2\n')`
printed two lines where bash prints one. `TOKEN-IS-ASSIGN-PREFIX?`
(Iteration 66) treated *any* word containing `=` as an assignment and
suppressed field splitting — but `echo a=$(...)` is an ordinary
argument that happens to contain `=`, and POSIX splits it. Now
restricted to assignment position (first word of the command). A
second assignment in `a=1 b=$p cmd` is still not covered; POSIX allows
a run of them, and that narrowing is documented in the code.

**A hang, recorded not fixed.** `g() ( x=1; echo $x )` — a subshell
function body entirely on one line — never terminates. The multi-line
form works. Related to the one-line `while`/`for` limitation but not
identical, since that one merely fails. It has its own note; the case
file uses the multi-line form so the suite tests what it means to,
rather than pinning down the failure mode of an unsupported shape.

Three case files so far: `getopts.sh` (flags, attached and separate
arguments, clustering, unknown options, `OPTIND`, `OPTARG` not
lingering), `expansion.sh` (the two previously-mistaken expectations,
plus arithmetic), and `control.sh` (braceless and subshell function
bodies, `return` from inside a loop, a same-line `case` arm, a
compound pipeline stage).

502 assertions across 61 files, 3 differential cases, 1991 core OK
markers, both cell widths, mrsh 17 of 21.
## Iteration 85: performance baseline

Measured before deciding anything, since "reasonable results" was the
gate on what comes next. `tests/bench` compares three shapes of work
(not run by `run_tests.sh`; run deliberately):

| shell  | loop | spawn | startup |
|--------|-----:|------:|--------:|
| relfsh | 568  | 122   | 328     |
| dash   | 3    | 59    | 64      |
| bash   | 6    | 80    | 108     |

(milliseconds: 2000 pure loop iterations; 100 iterations running
`/bin/true`; 100 start-and-exit cycles.)

**Three very different verdicts, and quoting one alone would
misrepresent the shell.**

- **Real scripts: ~2x dash, ~1.5x bash.** Anything that runs external
  commands is dominated by `fork`/`exec`, where this shell is only
  modestly behind. That is the number most scripts actually feel.
- **Startup: ~5x dash**, 3.3ms against 0.64ms. Fine in absolute terms
  and already 128x better than before the prebuilt image (Iteration
  40).
- **Pure interpretation: ~190x dash.** 0.28ms per loop iteration. This
  is the number that is not reasonable.

### Why the loop number is what it is, and what would fix it

Every iteration re-does work a real shell does once. `DO-WHILE` stores
its condition as **raw text** and re-tokenizes it each time round
(deliberately, so `$VAR` re-expands — Iteration 11), and each body line
is re-normalized and re-tokenized on every pass. `dash` parses to a
command tree once and re-executes it.

That is the same architectural item already recorded from Ramey's
chapter: **parse first, expand after**. It is the root of the stale-`$?`
and `ENSURE-ROOM` smear classes *and* of this. One change addresses a
bug class and a 100x, which is unusual and worth weighing accordingly.

A cheaper intermediate exists: cache the tokenized form of a body line
and re-run only the expansion step, rather than re-normalizing and
re-tokenizing text that cannot have changed. That keeps the raw-text
condition semantics and should recover most of the loop cost.

Nothing was changed this iteration beyond adding `tests/bench`.
## Iteration 86: an unquoted empty expansion yields no field

`echo A ${nope:-} B` passed three arguments where POSIX (and bash)
give two. An unquoted expansion that produces nothing yields **no
field at all**; a quoted empty word (`""`) still yields one.

### The flag that could not answer the question

The obvious test — "was this word quoted?" — is `TOK-WAS-QUOTED?`, and
using it did nothing. That flag is *also* set by `EXPAND-VAR`, as its
signal that an expansion result must not be re-read as an operator. So
it cannot distinguish `""` from `${nope:-}`: both set it.

`ARGV-NAME-QUOTED` records an actual leading quote character, which is
the question actually being asked. Worth noting as a small instance of
a recurring theme here: a flag that accumulated a second meaning
silently stopped being usable for its first.

### Scope note on `word.sh`

This is one of several differences in that test, which is a broad
expansion suite. Still outstanding there: tilde expansion in an
assignment (`a=~/stuff`) and after each `:` in one, `~user` (which can
be done by reading `/etc/passwd` — no kernel primitive needed, contrary
to the earlier note), `$@` expanding to multiple fields, and a
`${x##...}` case. Each is independent; the file needs all of them.

### Verified

New differential case `empty-field.sh` covering both directions
(unquoted empty dropped, quoted empty kept, `$#` counting a quoted
empty operand). 502 assertions across 61 files, 4 differential cases,
1991 core OK markers, both cell widths, mrsh 17 of 21.
## Iteration 87: a written plan for parse-then-expand

Agreed to do the architectural change before the remaining `word.sh`
pieces, so those get written once against the new structure rather than
twice. For a change this size the first move is a plan, not an edit —
`PARSE-EXPAND-PLAN.md`, referenced from `GOALS.md`.

### What the plan says, in short

Move from `TOKENIZE` (which expands inline at 24 call sites) to
`TOKENIZE` (boundaries and flags only) → `EXPAND-WORDS` (per command,
immediately before it runs). The per-*command* timing is the point: it
is what makes `FOO=bar; echo $FOO` work.

Four stages, each committed separately and each leaving the suite
green: split tokenize from expand; cache tokenized body lines
(performance); nested `$(...)` by recursive tokenize with `)` as a
context terminator, *replacing* `CMDSUB-TOKENIZE`; then retire the two
recorded limitations and delete their notes.

### Why write it down rather than start

Three things this project has learned the hard way argue for it:

- **Tokenizer changes are not local.** Iteration 48 changed how `)`
  tokenizes and the consequences appeared in four places across
  fourteen iterations. This change is larger.
- **Buffer lifetime is where the bugs are.** Four iterations went on
  it for one 60-line feature (76–80), and the plan makes "list which
  buffers each stage reads and writes" an explicit precondition.
- **Two reverts came from starting with an edit.** The plan requires an
  isolated diagnostic per piece and differential cases *before* each
  stage, which is the habit that broke the deadlock in 79.

The plan also states what is *not* changing — `RUN-TOKENIZED`, the
splitters, `DISPATCH`, the builtins, replay-as-input-source, the arena.
Bounding it is most of what makes it safe.

No code changed this iteration.
## Iteration 88: a segfault found by the plan's own first step

The plan says: add differential cases *before* each stage. Doing that
for Stage 1 — a broad probe of expansion behaviour against bash —
found a **crash** on the third line.

`${p%%/*}`, `${p##*}` and `${p%%*}` all segfault. The common factor is
that the trim consumes the *entire* value, so the remainder is
zero-length — and `TYPE-N-TO-TOK` did `0 DO ... LOOP` with no zero
guard. This kernel's `DO` with `start = limit` runs the whole unsigned
range rather than zero iterations.

That hazard is documented in `FORTH-STYLE.md` §12, caused four
segfaults in Iteration 15, and had a rule written about it — and here
it was, still present in a word added later. **Writing a rule down does
not retire the class**; only a check does. Every remaining `DO` in
`shell.4` whose count can be zero is worth an audit on that basis.

The four prefix/suffix forms now all match bash, including the
empty-result cases.

### Stage 1's net is in place

`tests/diff/cases/expansion-broad.sh` — 14 numbered checks covering
`$VAR`, all six `${...:-+=}` forms with and without the colon, `${#x}`,
all four prefix/suffix trims, quoting interactions, field splitting,
arithmetic, `$(...)` and backquotes, positional parameters, and
adjacency (`x${a}x`). It passes byte-for-byte against bash, so the
refactor now has something that will catch a silent change.

Two shapes were deliberately left out rather than asserted: a fully
one-line `for`, and `$*`/`$@` as multiple fields. Both are known gaps
(the latter is one of the several `word.sh` still needs), and asserting
their current behaviour would freeze something nobody designed.

### Verified

5 differential cases, 502 assertions across 61 files, 1991 core OK
markers, both cell widths, mrsh 17 of 21.
## Iteration 89: auditing every `DO` — one more hang

Followed through on Iteration 88's own recommendation rather than
filing it: checked all 14 `DO` loops in `shell.4` for whether their
count can reach zero.

Twelve were already guarded. One more was not: **`shift 0` hung** —
valid POSIX and a no-op, but the count of 0 reached `DO` as `0 0 DO`,
which in this kernel runs the entire unsigned range. Same hazard as
`TYPE-N-TO-TOK` yesterday, found by looking rather than by anything
tripping over it.

That makes **six** segfaults or hangs from this one kernel behaviour:
four in Iteration 15, then `TYPE-N-TO-TOK` (88) and `DO-SHIFT` (89) —
both in words written *after* the rule about it was documented.
`FORTH-STYLE.md` now says so explicitly: writing the rule down did not
retire the class, and what retired it was the audit. The entry now
tells the reader to check every new loop and to prefer a differential
case that exercises the zero path.

`tests/diff/cases/zero-counts.sh` does exactly that — trims that
consume the whole value, `shift 0` and `shift n`, an empty `$(...)`,
`$((0))` and `$((5-5))`, and `${#n}` on an empty variable. These are
the zero paths, in one place, checked against bash.

### Verified

6 differential cases, 502 assertions across 61 files, 1991 core OK
markers, both cell widths, mrsh 17 of 21.
## Iteration 90: auditing the fixed tables — a silent failure, a crash,
## and two limits that pre-empted a diagnosis

Continued reading rather than running. `GOALS.md`'s memory policy says
"a full fixed table must never fail silently"; this checked whether
that was true. It was not.

**Three defects, escalating:**

1. **`SET-SHVAR` failed silently.** Past 32 variables it just `EXIT`ed,
   so the 33rd was never set and every later use expanded to empty —
   wrong output, no error. Found in Iteration 44 and *recorded*; never
   actually diagnosed until now. Same for `SET-FUNC` past 16.
2. **`SAVE-POS-PARAMS` had no bound at all.** It indexes
   `POS-PARAMS-SAVE` by function depth, and past
   `MAX-POS-PARAM-DEPTH` it would `MOVE` a full parameter block past
   the end of that buffer. Nothing had hit it, which was luck rather
   than design.
3. **Two lower limits pre-empted the diagnosis, turning an error into
   a crash.** With a guard finally added, deep recursion still died —
   because `locals.4`'s save stack (256 cells) ran out at ~15 levels,
   and then, once raised, the engine's 2KB return stack overflowed and
   segfaulted, both before the shell's own limit of 32 could report
   anything.

`LSAVE-MAX` 256 → 4096 and `RSTACK_BYTES` 2048 → 65536. Deep recursion
now prints `shell: function recursion too deep` and the script carries
on.

### The general shape

**A limit that pre-empts a higher-level one turns a diagnosable error
into a crash.** Three limits were stacked here — the shell's, the
locals facility's, the engine's — and they were ordered exactly wrong,
with the most informative one last. That ordering is not visible from
any single file; it only shows when the deepest one is reached.
Recorded in both `locals.4` and `relf.c` next to the numbers, since
that is where someone would consider lowering them again.

### Verified

`tests/shell/run-limits` (5 assertions): ordinary recursion working,
deep recursion diagnosed *and survived*, and a full variable table
reported with execution continuing. 507 assertions across 62 files, 6
differential cases, 1991 core OK markers, both cell widths, mrsh 17
of 21.
## Iteration 91: the recorded and-or reentrancy bug, demonstrated and
## fixed

Iteration 50 fixed `RUN-TOKENIZED` holding the `;`-remainder in globals
across a recursive call, and noted that `RUN-AND-OR-CHAIN` had the
identical shape but had never been hit. Went looking for the case that
hits it:

    { true && echo inner; } && echo outer     -> "inner inner"

The left-hand group's body contains `&&`, so running it recurses into
`SPLIT-ANDOR` and overwrites the outer chain's saved remainder — the
outer `echo outer` was replaced by the inner one's remainder.

Three *more* globals had the same exposure and would have been the next
bug: `ANDOR-OP` (read after the piece runs), `AO-PENDING-OP` (which
`AO-SHOULD-RUN?` consults) and `AO-CONTINUE` (the loop's own control).
All are now locals, and the remainder is copied to per-invocation arena
storage before anything runs — the same fix as Iteration 50.

Worth noting how it was found: not by a failing test, but by taking a
recorded "same shape, never hit" note seriously enough to construct
the input that hits it. The note had been sitting there for forty-one
iterations.

### A different gap, found alongside and not fixed

`if true; then true && echo n; fi && echo m` prints `n` but not `m`.
That is not reentrancy — it is an `&&` *after* a compound command,
which `DO-IF` consumes without looking for what follows. The group
equivalent was fixed in Iteration 49 (`AT-GROUP-END?` falls through to
the splitters); `if`/`while`/`for`/`case` never got the same treatment.
Recorded rather than bundled in.

### Verified

`tests/diff/cases/andor-nesting.sh` — six chains including nested
groups on both sides and `||` chains. 507 assertions across 62 files,
7 differential cases, 1991 core OK markers, both cell widths, mrsh 17
of 21.
## Iteration 92: an operator after `fi`, and the status an untaken `if`
## leaves

`if ...; fi && echo m` dropped the `&& echo m` — recorded last
iteration, fixed here. `DO-IF` was discarding the pending remainder
after `fi`; it now runs it through `RUN-TOKENIZED` like any line. A
leading `&&` then splits with an *empty* left-hand side, which tests
the if's own exit status — exactly the semantics wanted, with no
special case.

### Which exposed a second, older bug

With something finally looking at the status, `if false; then ...; fi`
turned out to leave the failed *condition's* status. POSIX says an if
with no branch taken exits **0**. Verified against both bash and dash
before changing anything.

The status had been wrong all along and could not be observed: nothing
in the shell or its tests examined `$?` after an `if` until an operator
could follow `fi`. A second consumer of existing state turning an
invisible bug visible — the same shape as the double-quote tracking in
Iteration 60 and the `TOK-WAS-QUOTED?` overload in 86.

### A wrong assertion, the third of its kind

`run-if-sameline` asserted "an if with no else and a false condition
exits with the condition's own status", expecting 1. That is not what
POSIX says and not what either reference shell does. Corrected, with
the reason in the test.

That is the third hand-written expectation in this suite found to be
simply wrong (after `set --` in Iteration 61 and the multi-line command
substitution in 67), and the second one this project's own code was
right about while its test was not. `tests/diff/` exists precisely
because of this failure mode; this is one more argument for moving
assertions there when the answer is checkable against a reference.

### Not done

`while`/`for`/`case` still discard what follows `done`/`esac` the same
way `if` did. Same fix, three more places; left for its own iteration
rather than changed blind.

### Verified

`tests/diff/cases/compound-suffix.sh` — five operator-after-`fi`
shapes plus both exit-status cases. 507 assertions across 62 files, 8
differential cases, 1991 core OK markers, both cell widths, mrsh 17
of 21.
## Iteration 93: multi-line quoted strings

    echo "a
    b"

now works. A quote still open at end of line means the string
continues, so `JOIN-OPEN-QUOTES` reads further lines — joined by the
newline that separated them — until it closes.

This corrects an over-reach from Iteration 60, which made an open quote
a syntax error. That is right at end of *input* and wrong at end of
*line*, and the check now fires only where this word gives up. It is
the first time a fix here has narrowed an earlier fix rather than
extending it.

### The `-c` case, which hung

`relfsh -c "printf '%s\n' '''"` went from a clean `status 2` to
hanging. With `-c` the command string is the entire input, so asking
for a continuation line blocks on `ACCEPT` reading the terminal.
`NO-MORE-INPUT?`, set by `SH-C`, makes an open quote there the genuine
syntax error it is. Interactive mode deliberately still continues,
matching every shell's `PS2` behaviour.

Worth noting the shape: the feature was correct for two of the three
input sources (script, replay) and catastrophic for the third. "Which
input source am I on" has now been the deciding question three times
— `read` reading fd 0 rather than the script (Iteration 54), the
compound pipeline stage (80), and this.

### What it bought

`2.2-quoted-characters.sh` gets past its multi-line section and now
differs on **one** line: the nested `$(echo $(echo "cmd 3"))`, which is
Stage 3 of `PARSE-EXPAND-PLAN.md`. `word.sh` still needs its tilde
forms, positional parameters inside `${...}`, and a `${var#pattern}`
case.

### Verified

`tests/diff/cases/multiline-quote.sh` — both quote styles, a
multi-line assignment, and execution continuing afterwards. 507
assertions across 62 files, 9 differential cases, 1991 core OK
markers, both cell widths, mrsh 17 of 21.
## Iteration 94: is startup cost the reason the loop is slow? No — but
## the wrapper is 43% of startup

Asked whether the ~190x pure-loop gap comes from `relf` loading a
separate image file where `dash` loads only a binary, and whether
embedding the image would fix it. Measured rather than reasoned.

**For the loop: no, and not close.** Timing the same script at 0, 1000,
2000 and 4000 iterations gives a **fixed cost of 4ms** and about
**0.25-0.3ms per iteration**. On the 2000-iteration benchmark that is
4ms of 600ms — 0.7% — and the image read is a fraction of even that.
The gap is interpretation, exactly as `PARSE-EXPAND-PLAN.md` says: work
redone every iteration that a real shell does once.

**But the question found something real in startup:**

| invocation | per start |
|---|---:|
| `relfsh -c true` (wrapper) | 3.5ms |
| `relf kernel-shell.img -c true` (direct) | 2.0ms |
| `dash -c true` | 0.72ms |

`relfsh` is a `/bin/sh` script that stats sources and rebuilds the
image if stale. **That wrapper costs 1.5ms — 43% of startup** — and it
is pure overhead at run time. Reading the 230KB image costs on the
order of 0.1-0.2ms by comparison.

So embedding the image in the binary is worth doing, for two reasons
that are *not* the one asked about: it removes the need for the wrapper
at all (nothing to locate or rebuild), and it makes RelF's shell a
genuine single executable — which fits the no-dependencies goal better
than an engine plus a data file plus a shell script. Expected result is
startup around 2ms or a little under, against dash's 0.72ms; the
remainder is `MAIN`'s own setup, not I/O.

It would not move the loop number at all, and should not be sold as
performance work.

`tests/bench` now measures the direct invocation alongside the wrapper,
so the wrapper's cost stays visible rather than being rediscovered. Its
own numbers confirm the split cleanly:

| shell | loop | spawn | startup |
|---|---:|---:|---:|
| relfsh (wrapper) | 694 | 146 | 383 |
| relf (direct)    | 691 | 128 | 179 |
| dash             | 4   | 72  | 74  |

Startup halves; the loop does not move at all. That is the whole answer
in one table.
## Iteration 95: positional parameters inside `${...}`, and what
## `word.sh` actually needs

`${2}`, `${3:+posix}`, `${#1}`, `${2#pat}` all expanded to empty: only
the bare `$2` spelling worked, because `EXPAND-VAR` special-cased
digits while `EXPAND-BRACED-VAR` went straight to `LOOKUP-VAR`, which
knew only named variables.

Fixed in `LOOKUP-VAR` itself rather than at each call site, so every
braced form gets it at once. A single digit `1`-`9` names a positional;
`0` deliberately does not (it is the script name), and an out-of-range
digit expands to empty like an unset variable. `LOOKUP-VAR` sits above
the positional machinery in the file, so this is one more `DEFER` — the
cheapness of that now matters, which is the payoff from Iteration 77.

### Re-diagnosing `word.sh` changed the plan

With that fixed, the remaining differences are:

- **tilde forms** — `~root`, and tilde in an assignment (`a=~/stuff`,
  and after each `:` within one).
- **`c=""; echo ${c:=GOOD}` on one line** — prints the *old* value.
  This is the stale-expansion limitation: expansion happens once per
  raw line, before any `;`-separated command on it has run.
- two further lines needing their own look.

That second item is not a gap to fill — it is **Stage 1 of
`PARSE-EXPAND-PLAN.md`**, the parse-then-expand separation.

So both remaining reachable mrsh tests now converge on the plan:
`word.sh` needs Stage 1, and `2.2-quoted-characters.sh` needs Stage 3
(nested `$(...)`). "Finish the mrsh tests, then embed the image" and
"do the architectural change" turn out to be the same instruction,
which is worth knowing before starting either.

The tilde forms are still independent and can be done first if a
smaller piece is wanted.

### Verified

`tests/diff/cases/positional-braced.sh`. 507 assertions across 62
files, 10 differential cases, 1991 core OK markers, both cell widths,
mrsh 17 of 21.
## Iteration 96: `~user` expansion

`~root` and `~root/x` now expand. The home directory comes from reading
`/etc/passwd` directly: this engine exposes no `getpwnam`, and the file
format is two short words of Forth — `PW-FIELD` to pick a
colon-separated field and `PASSWD-HOME` to scan for the name. An
unknown user is left literal, which is what POSIX requires and what
`~nosuchuser` should do.

This also corrects a comment in `TRY-TILDE-EXPAND` claiming `~user`
needed "a password-database lookup this shell has no access to". It had
access all along; nobody had checked.

### A shared scratch variable, one call deep

First version dropped the `/x` from `~root/x`. `PW-I` was used both as
the username-scanning cursor *and* by `PW-FIELD` inside
`PASSWD-HOME` — so by the time the length was needed again it held a
field offset.

That is `FORTH-STYLE.md` §9 (a global that does not survive a call
which can reach it) at its smallest scale: not recursion, just one
helper two levels down reusing the same name. The per-word prefix
convention (`PW-*`) actively encouraged it, since both words are
legitimately "PW". Worth noting that the convention which prevents
collisions *between* subsystems does nothing within one.

### Still outstanding in `word.sh`

Tilde in an assignment (`a=~/stuff`, and after each `:` within one) is
separate and not done. The rest of that file needs Stage 1 of the plan.

### Verified

`tests/diff/cases/tilde.sh` — bare, with a path, `~user`, `~user/path`,
unknown user, and both quoted forms staying literal. 507 assertions
across 62 files, 11 differential cases, 1991 core OK markers, both cell
widths, mrsh 17 of 21.
## Iteration 97: recording that `~user` via `/etc/passwd` is a shortcut

Raised in review, and correct: `/etc/passwd` is one NSS source among
several. On a host using LDAP, SSSD, NIS or systemd-homed, a real user
may not be in that file, and `~alice` would silently stay literal.

What makes this worth writing down rather than remembering is the
*shape* of the failure. It is quiet — no error, just a word that does
not expand — and environment-dependent in the worst direction: it
cannot fail on a developer machine, and fails on exactly the hosts
where centrally managed accounts are the reason the feature is used.
Nothing in this project's test suites can catch it, because both
suites run here.

Recorded in two places, deliberately:

- **`GOALS.md`, under a new "Known shortcuts to revisit" heading** —
  for deliberate compromises that work today, are wrong in general, and
  will not show up locally. `~user` is the first entry; the heading
  exists so there is somewhere obvious for the next one.
- **In the code at `PASSWD-HOME`**, since that is where someone would
  otherwise conclude the behaviour is intended.

The fix is `getpwnam(3)` as an engine primitive — one name in, one
string out — which goes through NSS and returns whatever the system is
configured to use. Noted that it should **replace** the file reader
rather than supplement it: two code paths disagreeing about who exists
would be worse than either alone.

Kept for now because it needs no engine change and unblocks `word.sh`.
Not kept because it is right.

No behaviour changed this iteration.
## Iteration 98: tilde in assignments

`a=~/stuff` and `PATH=~/bin:~/sbin` expand, per POSIX — after the `=`
and after each unquoted `:`. Elsewhere in a word, and inside quotes, a
tilde stays literal, so `echo other=~/y` is unchanged.

`ASSIGN-TILDE-POINT?` asks the two questions that matter: is this an
assignment word (reusing `TOKEN-IS-ASSIGN-PREFIX?`, itself narrowed to
assignment position in Iteration 83), and is the previous emitted
character `=` or `:`.

### Placed in the wrong word first

My first attempt matched on the surrounding text and landed in
`COPY-DOUBLE-QUOTED` rather than `SCAN-TOKEN` — the two have a nearly
identical dispatch chain since backquotes were added to both in
Iteration 73. It failed to load, which caught it, but it would have
been *wrong even if it had loaded*: a tilde inside double quotes is
literal.

Worth noting because the two chains are now similar enough that a
pattern match can land in either, and only one is right for any given
character. That is a duplication smell the next audit should look at:
`SCAN-TOKEN` and `COPY-DOUBLE-QUOTED` differ in which characters are
special, not in how they dispatch.

### `word.sh` after this

The whole tilde section now matches. What remains in that file is the
stale-expansion case (`c=""; echo ${c:=GOOD}` on one line — Stage 1 of
the plan) and `$@`/`$*` expanding to multiple fields. No independent
pieces left.

### Verified

`tests/diff/cases/tilde.sh` extended with the assignment forms and the
two shapes that must stay literal. 507 assertions across 62 files, 11
differential cases, 1991 core OK markers, both cell widths, mrsh 17
of 21.
### Correction to the above

I committed Iteration 98 with a **failing differential case**, again
without reading the output first — the second time (see Iteration 61).
The failure was real and informative:

`echo other=~/y` — bash expands the tilde, **dash does not, and
neither do we**. I had asserted our behaviour was correct without
checking, and it *is* correct: POSIX applies tilde-after-`=` to
assignment *words*, and an argument to `echo` is not one. bash is being
permissive with any `name=value`-shaped word.

So this is a third POSIX-versus-bash divergence, alongside the two
alias ones. `GOALS.md` now has a heading for them —
**"Where bash and POSIX disagree, and this shell follows POSIX"** —
with the rule that each entry must be checked against a *second*
reference before being recorded, because "bash does X" and "X is
correct" are different claims. Having only one oracle made that
distinction invisible; `dash` settled it in one command.

The case is removed from `tilde.sh` rather than asserted, since that
file uses bash as its oracle and always will.
## Iteration 99: `$*` lost characters after it

`echo "[$*]"` with two parameters printed `[a b c` — the closing
bracket gone. With one parameter it was fine.

`EMIT-ALL-POS-PARAMS` reserves room for each parameter's text but
emitted the **separator** between them without reserving anything, so
each space overwrote a byte of unread input. One parameter means no
separator, which is why the simple case worked and hid it.

This is the in-place-growth hazard again, and the third distinct
instance: `$VAR` (Iteration 26), the numeric expansions
`$?`/`$$`/`$#`/`$((...))` (46), and now the one place that emits a
character *of its own* rather than copying a value. Each time the fix
was one `ENSURE-ROOM`; each time it was found by output going missing
rather than by inspection.

That is the class `PARSE-EXPAND-PLAN.md` says disappears entirely once
expansion produces a new word list instead of rewriting the input
buffer. Three instances is a reasonable argument that the fourth is out
there.

### Found while chasing something else

The visible symptom was `$@`. `"$@"` gives one field where bash gives
one per parameter — a real gap, and the last independent item in
`word.sh`. Chasing it turned up this unrelated corruption first, which
is worth noting as a pattern: a wrong *count* was masking a wrong
*string*.

`"$@"` itself is not fixed. It needs a forced field break between
parameters even inside double quotes, where splitting is otherwise
suppressed — the one expansion POSIX allows to produce multiple fields
from a quoted word.

### Verified

`tests/diff/cases/posparams.sh` — `$*` alone, embedded, with a
space-containing parameter, `$#`, indexed access and the empty case.
507 assertions across 62 files, 12 differential cases, 1991 core OK
markers, both cell widths, mrsh 17 of 21.
## Iteration 100: `"$@"` as separate fields

`"$@"` now produces one field per positional parameter — the last
independent item in `word.sh`.

It is the one expansion POSIX allows to yield several fields from a
*quoted* word, so it cannot go through `EMIT-EXPANDED-CHAR`, which
suppresses splitting inside quotes correctly for everything else. It
calls `IFS-SPLIT-HERE` directly instead. `$@` and `$*` differ only
inside quotes; unquoted they behave alike, because the joining space is
then an ordinary IFS character and normal splitting finishes the job —
which is why one shared word had sufficed until now.

**And an unsatisfied `"$@"` produces no field at all.** With no
positional parameters, `n "$@"` passes zero arguments where any other
quoted empty word passes one. That interacts with the empty-field rule
from Iteration 86, which deliberately keeps quoted empties: the
exception is recorded when `$@` expands to nothing at the start of a
word and acted on when the token ends, since `"x$@y"` is still the
single field `xy` and that is not knowable at expansion time.

### On the process

Three attempts at the edit failed on stale `assert` text — the source
had moved under comments written in Iterations 99 and earlier. Reading
the current text first would have cost one command instead of three.
Worth remembering that a patch keyed to a comment is keyed to the most
volatile part of the file.

### Where `word.sh` stands

One difference left: `c=""; echo ${c:=GOOD}` on a single line, which
prints the old value. That is the stale-expansion limitation — Stage 1
of `PARSE-EXPAND-PLAN.md` — and nothing smaller remains.

### Verified

`tests/diff/cases/posparams.sh` extended with all four `$@`/`$*` field
counts, an empty `"$@"`, and `"x$@y"`. 507 assertions across 62 files,
12 differential cases, 1991 core OK markers, both cell widths, mrsh 17
of 21.
## Iteration 101: `done`/`esac` suffixes — diagnosed precisely, not
## implemented

Confirmed the gap recorded in Iteration 92 for the three constructs
`if` did not cover:

    while ... done && echo m      -> m never runs
    for ... done && echo n        -> n never runs
    case ... esac && echo q       -> q never runs

with multi-line bodies in each case, since the fully-one-line forms are
separately unsupported and would have confounded the test.

### The fix, specified

Same shape as Iteration 92's, with one addition. `CAPTURE-CONTINUE?`
detects the terminator by `LINE-IS?`, which looks only at `ARGV[0]`, so
everything after `done` is silently dropped. The remainder must be
split off with `SPLIT-AT-KEYWORD` at that point and run after the
construct finishes.

The addition: **the remainder must be copied to arena storage first.**
Running the loop body reads lines, and reading a line clobbers the
pending-remainder arrays — the same hazard as `RT-SAVE-REST`
(Iteration 50) and `AO-SAVE-REST` (91). `DO-IF` did not need this
because its `fi` is reached *after* its body has run; a loop's `done`
is reached before.

That distinction is why this was not a mechanical repeat of Iteration
92 and why it is recorded rather than rushed.

### Stopping here deliberately

This is iteration 101 of a long session, and the remaining work is now
two well-specified pieces plus Stage 1. Locating code has started
costing more than changing it, which is the point at which a fresh
start is worth more than another edit. Everything needed is written
down:

- **this gap**, specified above, three constructs, one shape;
- **Stage 1** (`PARSE-EXPAND-PLAN.md`), which both remaining reachable
  mrsh tests now depend on and which also addresses the ~190x loop cost
  and the in-place-growth bug class — three problems, one change;
- **image embedding**, measured in Iteration 94: removes the wrapper
  (53% of startup) and makes a single executable, but is packaging
  work, not performance work;
- **`getpwnam`**, under GOALS.md's "Known shortcuts to revisit".

### Status at 101 iterations

mrsh-suite 17 of 21, with 2 of the remaining 4 failing by deliberate
choice (the POSIX-versus-bash alias divergence) and the other 2 gated
solely on Stage 1 and Stage 3. 507 assertions across 62 test files, 12
differential cases against a live reference shell, 1991 core Forth OK
markers, green on both 8-byte and 4-byte cell widths. `relfsh` starts
in ~2ms from a byte-reproducible prebuilt image; the i386 build is
~90KB of engine plus image against dash's 121KB.
## Iteration 102: a trailing backslash run, counted by parity

`2.2-quoted-characters.sh` had two differences from its expected
output. This is the smaller one, and it is independent of the other.

    printf '%s\n' "\$\`\"\\\
    test"

The double-quoted string ends the line with **three** backslashes: an
escaped backslash, then a continuation. `JOIN-CONTINUATIONS` decided
"escaped or continuation?" by looking at the single character before
the final backslash — a backslash there meant "escaped, do not
continue". That is right for two and wrong for three, five, seven.

The test is the parity of the whole trailing run: each pair is one
escaped backslash, and an odd one left over continues the line.
`JC-CONTINUES?` scans the run backwards and returns
`run-length 1 AND 1 =`.

### Why the existing tests missed it

`run-continuation` covered one backslash and two — the two cases the
old comment named. Nothing covered three. That is the shape
`FORTH-STYLE.md` §13 warns about under "test the negative case": the
old code was not missing a case so much as encoding a rule that
happened to agree with the rule on every input anyone had tried.

### Verified

`tests/diff/cases/continuation.sh` — runs of one through five
backslashes, inside double quotes and bare, against bash. Runs of
four and five are what distinguish parity from any "look back one
character" rule, in both directions.

`2.2-quoted-characters.sh` is now down to one difference: the nested
`$(echo $(echo "cmd 3"))` on its line 27.

507 assertions across 62 files, 13 differential cases, 1991 core OK
markers, both cell widths, mrsh 17 of 21.

**A correction to the numbers in earlier entries.** The assertion
count recorded from Iteration 95 onward was 507, but the actual sum of
`tests/shell/run-all`'s own per-file counts was 505 before this
iteration's two additions; it is 507 now by coincidence. The file
count of 62 is `ls tests/shell | wc -l`, which includes `lib.sh` and
`run-all` themselves, so 60 files really run. Left as-is going
forward, with the method stated here so the series stays comparable.
## Iteration 103: the fourth in-place-growth bug, where Iteration 99
## predicted it

    set a b c
    echo "1  $@  2"     ->  1  a b c

The `  2` is gone. One parameter works; two or more lose everything
after the `$@`.

`IFS-SPLIT-HERE` writes a NUL and advances `TOK-OUT`, so it grows the
output by one byte. That is *balanced* when `EMIT-EXPANDED-CHAR` calls
it — the IFS character that triggered the split was consumed from the
input and never emitted, so one byte in pays for one byte out. The
quoted `"$@"` path added in Iteration 100 has no such character: it
synthesises a field break between parameters out of nothing. One byte
of unread input clobbered per break, which is why the single-parameter
case looked fine.

One `ENSURE-ROOM` again, and the same shape as `$VAR` (26), the
numeric expansions (46) and `$*`'s joining space (99). Iteration 99
wrote that three instances was a reasonable argument the fourth was
out there; it was, and it was the sibling branch of the very word 99
fixed — 99 reserved room for the `$*` separator and left the `$@`
break beside it unreserved.

### The audit 99 should have done, done now

Every site that writes through `EMIT-TOK-CHAR`/`EMIT-EXPANDED-CHAR`,
asking of each whether it emits more than it consumed:

- **Balanced, no reservation needed.** `COPY-DOUBLE-QUOTED`'s
  `92 EMIT-TOK-CHAR EMIT-TOK-CHAR` (two out for the backslash and the
  character it failed to escape, two in); the literal `$` at 1811 and
  1872; the ordinary character copies; `TOKENIZE`'s own NUL, which
  lands on the separator `SCAN-TOKEN` stopped at.
- **Shorter than their source by construction.** The `PEWORD-BUF`
  emissions in `EXPAND-BRACED-VAR` (`${VAR:-word}` and friends) have
  no `ENSURE-ROOM` and do not need one: the word came from inside
  `${VAR:-`…`}`, so the text consumed is always at least seven bytes
  longer than the word emitted. Their siblings on the *value* branch
  do call it, correctly — a variable's value has no such bound.
- **Reserved.** Everything else already was.

So this is the last of the class that is reachable today. It stops
being a class at all under Stage 1, where expansion writes into a
fresh word list instead of over the input.

### Verified

`tests/diff/cases/posparams.sh` extended: text after `"$@"` with
three parameters and with six, `"[$@]"`, `"x$@y"`, the same as a
function argument, and the one-parameter case that hid it.

509 assertions across 62 files, 13 differential cases, 1991 core OK
markers, both cell widths, mrsh 17 of 21.

### Where `word.sh` stands, re-measured

Iteration 100 recorded one difference left. There are four, and this
fixes one. The others:

- `${null:-"$@"}` and `${x#$HOME}` — the *word* and the *pattern*
  inside `${...}` are never expanded. Documented in the code as a
  scope limit since Iteration 32, not a regression, but two of the
  four.
- a `$(` whose body spans several physical lines.
- `c=""; echo ${c=BAD} $c` on one line — the stale-expansion case,
  Stage 1, as recorded.

Recording the re-measurement because the earlier count was not wrong
when written — the `$@` fix in 100 changed what the remaining diff
lines were, and nobody re-read them afterwards.
## Iteration 104: the word in `${VAR:-word}` is word text

`${null:-"$@"}` printed a literal `"$@"`, and `${x#$HOME}` trimmed
nothing. The word and the pattern inside `${...}` were read by
`READ-PEWORD`, which copied bytes and expanded none of them — a scope
limit documented since Iteration 32, and two of `word.sh`'s four
remaining differences.

The fix is not to add expansion to `READ-PEWORD`. It is to stop having
a second reader at all: the word in `${VAR:-word}` *is* ordinary word
text, so `EXPAND-BRACED-WORD` runs the same per-character dispatch that
`SCAN-TOKEN` runs, in place, into the token being built. Nested
`${...}`, quoting, backquotes, `$(...)` and `$((...))` inside the word
all work without being arranged for, because the dispatch already
consumes each of those regions whole — which is also why a top-level
`}` can end the word while one inside quotes cannot.

`SCAN-TOKEN`'s loop body became `SCAN-TOKEN-CHAR` so both callers share
it, reached from `EXPAND-BRACED-WORD` through a `DEFER` (the shared
word lives far below, after `COPY-DOUBLE-QUOTED`).

Three consequences had to be handled:

- **The untaken branch must still find the end of the word.**
  `EXPAND-BRACED-WORD-ASIDE` runs the *same* scan with `TOK-OUT`
  declared as a local, so everything written is rewound on exit;
  `IN-DQ-CONTEXT?` set, so a `"$@"` in the discarded word cannot
  advance `ARGC`; and a new `EXPAND-SUPPRESSED?`, checked in
  `EXPAND-CMDSUB` after the text is consumed but before the fork, so
  `${set:-$(cmd)}` does not run `cmd`. A separate hand-written skipper
  would have been a second answer to "where does this word end", which
  is FORTH-STYLE.md §11's whole subject.
- **A pattern is not emitted.** `CAPTURE-BRACED-WORD` expands into the
  token buffer and then copies out and rewinds, so `ENSURE-ROOM` keeps
  comparing a `TOK-OUT` and a `TOK-POS` that live in the same buffer.
  Expanding into a *separate* buffer would have made that comparison
  arithmetic between two unrelated addresses — it would have worked or
  not depending on which of two `malloc` results happened to be lower.
- **Literal text in the word is field-split when unquoted.**
  `n ${nope:-a b c}` passes three arguments. An ordinary word never
  needs this, because `SCAN-TOKEN` stops at the separator instead of
  emitting it, so the split is gated on a new `IN-BRACED-WORD?`.

### The bug this introduced, and where it came from

`${x#$HOME}` gave empty. `EXPAND-BRACED-WORD` recurses into
`EXPAND-VAR`, which writes the *inner* name into `VARNAME-BUF` — and
`TRIM-PARAM` reads that buffer after the scan returns, so it trimmed
`$HOME` from `HOME` rather than from `x`. `${X:=$y}` assigned to `y`
for the same reason.

FORTH-STYLE.md §9 names this exactly: a global that does not survive a
call which can reach it. What made it easy to miss is that the
reentrancy is *new* — `READ-PEWORD` copied bytes and could not recurse,
so `VARNAME-BUF` had never needed to survive anything. Adding recursion
to a word makes every global it touches a question again, and the file
gives no signal about which ones were already answered.

Fixed with per-invocation arena storage for the name (`BODY-ALLOC`,
with `BODY-ARENA-TOP` as a local so it is released on every exit path)
rather than a second fixed buffer, since `${a#${b#$c}}` has no bound.

### Found, not fixed

A function defined entirely on one line — `n() { echo "$#"; }` —
**hangs**. Confirmed by `git stash` to predate this iteration. GOALS.md
records that each body line and the closing `}` must be on their own
line, so this is a documented scope limit; hanging rather than
diagnosing it is not. Worth its own iteration.

### Verified

`tests/diff/cases/braced-word.sh` — parameter, command and arithmetic
expansion inside the word, quoted and unquoted; the untaken branch not
running its `$(...)`; field splitting of literal and of `"$@"`;
`${VAR:=word}` assigning the expanded value; expanded trim patterns;
a `}` inside quotes; and nesting.

507 assertions across 62 files, 14 differential cases, 1991 core OK
markers, both cell widths, mrsh 17 of 21.

`word.sh` is down to two differences: the multi-line `$(` on its line
104, and the stale-expansion case. `2.2-quoted-characters.sh` is down
to one: nested `$(...)`.
## Iteration 105: `$(...)` gets the whole language, by deleting the
## parser that gave it a subset

`CMDSUB-TOKENIZE` was a private whitespace-only tokenizer for the text
inside a command substitution. It had been extended three times —
quoting (71), backquotes (73), and again in 104 — and still could not
do `;`, pipes, redirection, several commands, a body spanning lines, or
nesting.

GOALS.md already said what to do about it, quoting Ramey on bash's own
`parse_comsub`: it *"knows an uncomfortable amount of shell syntax and
duplicates rather more of the token-reading code than is optimal"*, and
the instruction recorded against this word was to **replace** it rather
than improve it. That is this iteration.

The substituted text is now installed as a **replay input source** and
read line by line through `READ-LINE-INTO-ARGV` in the forked child —
the identical machinery a loop body uses since Iteration 42. The child
has its own copy of `LINE-BUF`/`ARGV`/`TOK-*`, which is what made
reusing the real tokenizer safe here where it was not safe in the
parent.

Everything the private tokenizer could not do now works because
nothing implements it: several commands, `;`, `&&`, pipes,
redirection, `if`/`while`/`for`, functions, quoting. `CMDSUB-TOKENIZE`,
`CMDSUB-ARGV`, `CMDSUB-ARGC`, `CMDSUB-SKIP-WS`, `CMDSUB-WS?` and their
scratch variables are all gone; `CMDSUB-SPLIT-LINES`, which turns
newlines into the NUL separators every replay source already uses, is
sixteen lines.

**Nested `$(...)` came almost free.** The inner substitution is
expanded by the ordinary tokenizer running in the child, so the only
thing missing was finding the right closing paren: `CS-DEPTH` counts a
nested `$(` in the outer scan, exactly as `NORMALIZE-OPERATORS` already
counted one. That closes `2.2-quoted-characters.sh`.

**A body spanning several lines** needed the other half.
`NORMALIZE-OPERATORS` now reports `UNTERMINATED-CMDSUB?` alongside
`UNTERMINATED-QUOTE?`, and `JOIN-OPEN-QUOTES` continues on either — an
open `$(` at end of line means the command text continues, the same as
an open quote since Iteration 93. One flag, one `OR`.

### A latent bug the flag exposed

`NORM-IN-CMDSUB?` and `NORM-CMDSUB-DEPTH` were plain globals, absent
from `NORMALIZE-OPERATORS`' scratch-local list while every other piece
of its state was there. Nothing reset them, so a line ending inside a
`$(...)` left cmdsub-mode set for the *next* line, which would then be
copied through verbatim with no operator spacing at all. Nothing had
reached it because nothing acted on the state at end of line — the same
shape the quote tracking had before Iteration 60 made it matter. Both
are locals now.

### The cost, taken deliberately

A plain `$(cmd)` used to `EXECVE` straight out of the substitution
child. It now goes through `RUN-TOKENIZED`, which forks again for an
external command: one extra process per substitution. The alternative
is keeping a second, weaker parser to avoid it, which is the trade
GOALS.md already refused. Worth measuring against `tests/bench` when
Stage 2 is done, not before.

`RUN-CMDSUB-CHILD` moved far down the file, after
`READ-LINE-INTO-ARGV` and the `REPLAY-*` declarations it now needs.
Reaching it from `EXPAND-CMDSUB` was already through
`RUN-CMDSUB-CHILD-CALL`, so nothing else changed.

### Verified

`tests/diff/cases/cmdsub-body.sh` — several commands, nesting two
deep, a multi-line body in both `$( )` and backquote form, a pipeline,
a multi-line `for` and a same-line `if` inside the body, quoting, exit
status, the empty and blank bodies, and text either side.
`tests/shell/run-cmdsub` extended with three of the same.

510 assertions across 62 files, 15 differential cases, 1991 core OK
markers, both cell widths.

**mrsh-suite 17 -> 18 of 21.** `2.2-quoted-characters.sh` passes on
its merits. `word.sh` is down to one differing line — `c=""; echo
${c=BAD} $c`, the stale-expansion case — which is Stage 1 of
`PARSE-EXPAND-PLAN.md` and the only thing now standing between this
project and 19 of 21, its recorded ceiling.

### Found, not fixed

`echo $(for i in 1 2 3; do printf "%s" "$i"; done)` reports
`for: expected 'do'`. A loop written entirely on one line is not
supported anywhere — `SAME-LINE-DO?` looks for `do` as the *last*
token, and here `done` is — so this is the pre-existing gap, not
something the substitution rewrite introduced. It is the same family as
Iteration 104's one-line function definition, which hangs. Both want
one iteration together.
## Iteration 106: the `done`/`esac` suffix, as specified in 101

    while ... done && echo m
    for ... done && echo n
    case ... esac && echo q

None of the three ran their suffix. Iteration 101 diagnosed this
precisely and stopped rather than implementing it; this is that
implementation, and the specification held.

`CAPTURE-CONTINUE?` and `DO-CASE` both detect the closing line with
`LINE-IS?`, which looks only at `ARGV[0]`, so everything after the
keyword was dropped in silence. `SAVE-COMPOUND-SUFFIX` takes the rest
of the line and `RUN-COMPOUND-SUFFIX` runs it once the construct
finishes, as an ordinary line — a leading `&&` then splits with an
empty left-hand side and so tests the construct's own status, which is
the trick DO-IF has used after `fi` since Iteration 92.

**The addition 101 predicted was the important part, and it was not
the one 101 named.** 101 said the remainder must be copied to arena
storage first, citing `RT-SAVE-REST` and `AO-SAVE-REST`. Those copy the
*pointer arrays*, which solves a shared-array problem — and that is not
this problem. `ARGV` entries point into `LINE-BUF`, and running a loop
body reads lines, which overwrites the text itself. So what is saved
here is the **raw text**, the way loop bodies already are. The reason
`DO-IF` needed none of this is the one 101 gave: its `fi` is reached
after the body has run; a loop's `done` is reached before.

### A second bug, found only because something finally looked

With the suffix running, `while false; do ...; done && echo m` still
printed nothing. A loop that runs zero iterations was exiting with the
status of the *condition that stopped it* — which for a `while` is
always a failure, so `&&` after any completed while loop could never
fire.

POSIX: a loop's status is that of the last body it ran, or zero if it
ran none. Exactly the rule Iteration 92 applied to an untaken `if`, in
the two other constructs that needed it, and invisible for exactly the
same reason: nothing had ever looked at a loop's exit status before
this iteration gave it a way to be looked at. A `LOOP-RAN?` local in
each of `DO-WHILE` and `DO-FOR`.

That is twice now that adding a suffix to a compound command has
immediately exposed a wrong exit status underneath it. Worth expecting
a third if any construct is still missing one.

### Verified

`tests/diff/cases/compound-suffix.sh` extended: `&&` and `||` after
`done` and `esac`, a loop that iterates and one that does not, an
empty `for` list, a matching and a non-matching `case`, `$?` after
each, a `;` suffix that is a whole further command, and a nested loop
whose inner suffix must not be taken for the outer's.

510 assertions across 62 files, 15 differential cases, 1991 core OK
markers, both cell widths, mrsh 18 of 21.

### What is left

One item, and it is the one everything now converges on: **Stage 1 of
`PARSE-EXPAND-PLAN.md`**. `word.sh` differs on a single line,
`c=""; echo ${c=BAD} $c`, which is the stale-expansion limitation — and
the same change also removes the in-place-growth bug class (four
instances found, the last in Iteration 103) and is where the ~190x
loop cost is addressed. The other two mrsh failures are the deliberate
POSIX-versus-bash alias divergence and cannot be fixed without making
the shell less correct.
## Iteration 107: an unterminated compound command hangs

    n() { echo "$#"; }

hung. Found in Iteration 104 and confirmed by `git stash` to be old.
It turned out not to be about one-line functions at all: **every**
capture loop in this file spun forever at end of input.

`READ-NEXT-INPUT-LINE` reports an empty line and end-of-input
identically, as its own callers' comments have said since Iteration
54 - `HD-READ` works around it with a 4096-iteration guard. So
`FD-BODY-END?` kept asking "is this line `}`?", kept being told no,
and kept reading nothing forever. The same for `done`, `fi`, `esac`
and a group's closer.

`INPUT-EOF?` is set by the two input sources that can actually tell:
a replay knows its own length, and `READ-LINE` returns a flag that
was being discarded. `ACCEPT` cannot distinguish the two, so the
interactive path is deliberately untouched - a real shell prompts for
continuation there indefinitely too, and that is correct behaviour
rather than a hang.

Each terminator predicate now reports "stop" at end of input and says
which keyword was missing, and `DO-WHILE`/`DO-FOR`/`DO-MULTILINE-GROUP`
run nothing rather than executing however much of the body was read
before the input ran out. Status 2, matching the unterminated-quote
error from Iteration 60.

### Why this was worth an iteration of its own

A hang is the worst failure mode a shell has - worse than a wrong
answer, because nothing downstream reports it and a test harness only
learns about it from a timeout. FORTH-STYLE.md §13 already says "a
hang is a test result"; this is the other half of that, which is that
a hang should never be the *product*. Seven constructs shared one
cause, and the fix is one flag plus a check in each predicate.

### Verified

`tests/shell/run-unterminated` - while, for, if, case, group and
function, each unterminated, plus the one-line function definition
that started this. Deliberately not a differential case: bash accepts
several of these forms outright, so it is the wrong oracle for them.
What is asserted is only that the shell stops and says so.

524 assertions across 63 files, 15 differential cases, 1991 core OK
markers, both cell widths, mrsh 18 of 21.

### Still open, and unchanged by this

A one-line `for i in 1 2 3; do ...; done` and a one-line function
definition are still *unsupported* forms - they are now diagnosed
rather than hung, which is a different and smaller problem. Supporting
them means extending the pending-remainder mechanism (which `if` has
had since Iteration 25) to the capture loops, and is its own piece of
work.
## Iteration 108: expansion stops writing over its own input

The first part of Stage 1 of `PARSE-EXPAND-PLAN.md`, and the one that
stands on its own: **`TOKENIZE` now writes expanded words into a
separate `TOK-BUF` instead of compacting them back over `LINE-BUF`.**

In-place compaction was correct for quote-stripping, where the output
is always shorter than the input. It was never correct for expansion,
where a value can be longer than the `$name` it replaces — so
`ENSURE-ROOM` existed to shift the unread input rightward and keep the
write cursor behind the read cursor, and **every call site had to
remember to call it**. Four bugs were one such call being missing:
`$VAR` (Iteration 26), the numeric expansions (46), `$*`'s joining
space (99) and `$@`'s field break (103). Iteration 99 wrote that three
instances made a reasonable argument for a fourth; 103 found it four
iterations later, in the sibling branch of the word 99 had just fixed.

With separate buffers there is no shared buffer to overrun, so the
hazard does not exist rather than being guarded against.
`ENSURE-ROOM` is deleted, along with its twenty call sites and
`EMIT-DECIMAL-EXPANDED`, which existed only to pair a reservation with
`EMIT-DECIMAL` and is now `EMIT-DECIMAL` itself. The only remaining
limit is one bounds check in `EMIT-TOK-CHAR`.

Two things fall out:

- **An expansion may now exceed `LINE-MAX`.** It could not before:
  `ENSURE-ROOM` had nowhere to shift to and silently skipped both the
  shift and the expansion, leaving the old corruption in that rare
  case by explicit choice. `TOK-BUF` is 4096 against `LINE-MAX`'s 256.
- **`LINE-BUF` survives tokenizing intact.** Nothing needs that yet.
  It is the prerequisite for the rest of Stage 1: re-expanding a line
  per command means the line has to still be there afterwards.

### On how this went

Green on the first run, on both cell widths, with no test changes —
which is worth recording precisely because the plan warned this was
the tokenizer and to budget for consequences surfacing over many
iterations. The reason it went cleanly is that the change removes a
coupling rather than adding one: every site that was juggling two
cursors in one buffer now just writes forward into a buffer of its
own. Iterations 104 and 105 had already moved the two places that
cared about the coupling (`CAPTURE-BRACED-WORD`'s rewind, and the
command-substitution child) onto footing that did not depend on it.

### Verified

`tests/diff/cases/expansion-grows.sh` — an expansion thirty times its
own reference text, one exceeding the input line's own length with
text on both sides, and the exact shapes of all four historical
`ENSURE-ROOM` bugs.

524 assertions across 63 files, 16 differential cases, 1991 core OK
markers, both cell widths, mrsh 18 of 21.

### Found, not fixed

`x=0123456789...` repeated past 256 characters truncates the value to
the first repetition rather than to `SHVAR-VALUE-MAX`. Confirmed by
`git stash` to predate this iteration. It belongs to the fixed-table
family already listed in GOALS.md's memory policy, all of which
truncate or fail silently.

### What Stage 1 still needs

Expansion still happens once per raw line, during tokenizing. What
remains is to stop `TOKENIZE` calling the `EXPAND-*` words at all —
recording each word's raw text and a "needs expansion" flag instead —
and to run a new `EXPAND-WORDS` per command, immediately before it
runs. That is what makes `c=""; echo ${c=BAD} $c` work, and it is the
last thing between this project and 19 of 21.
## Iteration 109: deleting the word rather than auditing its callers

`COPY-ARGV` moved words between `ARGV` arrays without their
`ARGV-QUOTED` flags. Every stale-flag bug this project has had was a
call to it - Iteration 28's vanishing `&&`, 47's literal `;`, 49's
group body surviving into a pipeline stage - and each was fixed by
changing that call site to `COPY-ARGV-Q`. Iteration 28 fixed two of
them and recorded, honestly, that the extent of the same hazard at the
other call sites was *unverified*. GOALS.md has carried that sentence
under phase C ever since, through eighty iterations.

It is verified now, and not by auditing: the last caller of the bare
word disappeared along with `CMDSUB-TOKENIZE` in Iteration 105, so the
word had none left. Deleted, and its loop folded into `COPY-ARGV-Q`'s,
which now does one pass carrying the word and its flag together.

The point is the shape of the fix rather than its size. An open item
that says "we are not sure whether the other call sites are safe"
cannot be closed by looking harder, because the answer changes every
time someone adds a call site. It closes when the unsafe spelling
stops existing. FORTH-STYLE.md §8 says every copy carries the flags;
that is now true by construction rather than by remembering, which is
the same reason §11 says to merge duplicated shapes.

No behaviour changed. 524 assertions across 63 files, 16 differential
cases, 1991 core OK markers, both cell widths, mrsh 18 of 21.
## Iteration 110: one word for normalize-then-tokenize, and the caller
## that was missing it

Scoping Stage 1b turned up that `TOKENIZE` has a caller which never
normalizes: `DO-WHILE` re-tokenizes its stored condition text
directly, because `SAVE-WHILE-COND` keeps the line as it was typed.
So `while test x != y;do` never had its `;` spaced out - the condition
was tokenized as if operator normalization did not exist. Nobody had
hit it because conditions are usually written with spaces.

The same five-line shape - normalize, check the length, copy `NORM-BUF`
back over `LINE-BUF`, tokenize, or fall back to tokenizing the
original - appeared verbatim in four places and was *absent* in the
fifth. That is the FORTH-STYLE.md §11 pattern exactly, with the twist
that here the copies had not drifted: one had never been written.
`NORM-TOKENIZE` is that word, and all five sites call it.

### A real failure the change caused, and what it taught

Two `run-syntax-err` assertions went red: an unterminated quote
stopped being a syntax error. Folding normalization into
`NORM-TOKENIZE` moved it *after* the `UNTERMINATED-QUOTE?` check that
two callers make, and that flag is set by `NORMALIZE-OPERATORS` - so
the check was reading whatever the previous line had left. It looked
fine in a script, where `JOIN-OPEN-QUOTES` normalizes on the way in,
and failed in `-c` mode, where that word gives up early without
normalizing because there is no next line to ask for.

The check now runs after `NORM-TOKENIZE`. Tokenizing an unterminated
line first is harmless - an unclosed quote consumes to end of input
and nothing is run - but the ordering dependency was invisible until
the suite found it, which is the argument for the suite rather than
for inspection.

### Verified

`tests/diff/cases/control.sh` extended with three while loops whose
`do` and condition operators are fused to adjacent text.

524 assertions across 63 files, 16 differential cases, 1991 core OK
markers, both cell widths, mrsh 18 of 21.

This clears the obstacle recorded in `PARSE-EXPAND-PLAN.md` against
Stage 1b: every path into `TOKENIZE` now goes through
`NORMALIZE-OPERATORS` first, which is the precondition for that word
being able to hand `TOKENIZE` the raw word boundaries it found.
## Iteration 111: tokenize the normalized line where it already is

`NORM-TOKENIZE` normalized into `NORM-BUF`, copied the result back
over `LINE-BUF`, and tokenized that. The copy needed a fallback,
because `NORM-MAX` is 512 and `LINE-MAX` is 256: when the normalized
text did not fit, the **original** line was tokenized instead -
silently, with every operator left fused to whatever it touched. A
long enough line simply stopped having operators.

`TOKENIZE` now reads `NORM-BUF` directly. The copy, the ceiling and
the fallback all go at once, and `NORM-TOKENIZE` is two words.

This is only safe because of Iteration 108: `ARGV` used to point into
`LINE-BUF`, so what the tokenizer read from and what it left behind
had to be the same buffer. Since expansion writes into `TOK-BUF`, the
input buffer is just an input, and which one it is stopped mattering.

### The mistake, which the file's own rule names

First attempt failed everywhere at once - every shell test, not a
subset. `NORM-BUF` is declared beside `NORMALIZE-OPERATORS`, two
thousand lines *below* `TOKENIZE`, and this is one linear source:
"define before use", FORTH-STYLE.md §12. The symptom was not an
undefined-word error at the point of use but `relfsh` silently falling
back to a source bootstrap and printing `Welcome to Forth`, because
the image build is what failed. Worth knowing that this is what a
load-order mistake looks like from the outside once a prebuilt image
is in the picture: not a Forth error, a banner.

`NORM-BUF` is declared next to `LINE-BUF` now, with a note saying why
it is there.

### Verified

`tests/diff/cases/expansion-broad.sh` extended with a line whose
normalized form is longer than `LINE-MAX` and which is all operators -
it would have been tokenized unnormalized before.

524 assertions across 63 files, 16 differential cases, 1991 core OK
markers, both cell widths, mrsh 18 of 21.
## Iteration 112: word boundaries recorded by the pass that finds them

`NORMALIZE-OPERATORS` now records where each word starts and ends, and
`TOKENIZE` expands those spans instead of re-deriving the boundaries
itself. This is the piece Stage 1b needs: expansion of a word becomes
"run the scanner over this span", which is a thing that can be done
later, per command, rather than only during one pass over the line.

It goes here because this pass already tracks single quotes, double
quotes, `$(...)`, backquotes and `$((...))` — it must, or it would
space out operators inside them. "Does this whitespace separate two
words" is the same question, already answered. `NORM-EMIT` opens a
word at the first non-blank emitted while none is open; `NORM-CLOSE`
ends one at unquoted whitespace, around each operator (so the operator
is its own word), at a comment, and at end of line. `TOKENIZE`'s own
`SKIP-WS` loop is gone.

### The disagreement this exposed, which is the whole point of §11

Two shell tests went red: a quoted argument inside `$(...)`, and the
same inside backquotes. The two scanners disagreed, and the *new* one
was wrong.

`NORMALIZE-OPERATORS`' double-quote branch did not recognise a command
substitution at all, so in `"cmd: $(echo "one two")"` the inner quote
read as the outer one's closer. From there the space in `one two` was
unquoted, and the word ended in the middle of the substitution.
`SCAN-TOKEN` had always got this right, because `COPY-DOUBLE-QUOTED`
consumes a `$(...)` whole.

The inaccuracy was old and harmless while nothing acted on it — the
same shape as the `NORM-IN-CMDSUB?` state leak found in Iteration 105
and the approximate backslash tracking that only started mattering in
Iteration 60. Making this pass the authority on word boundaries is
what made it matter. `NORM-SKIP-CMDSUB` and `NORM-SKIP-BQ` copy those
regions verbatim from inside double quotes, counting parens.

Worth stating plainly: the merge did not create a bug, it *revealed*
one that had been latent for a hundred iterations, and it took two
existing tests to find it rather than inspection. That is the argument
for merging duplicated shapes even when both copies appear to work —
one of them does not, and you cannot tell which by reading.

### Also fixed, in passing

`NORM-EMIT` left the character on the data stack when `NORM-BUF` was
full instead of dropping it. Never reached, since the buffer is 512
bytes and a line is at most 256, but a stack leak on an overflow path
is not something to leave sitting there.

### Verified

`tests/diff/cases/cmdsub-body.sh` extended with quotes inside a
substitution inside quotes, in both `$( )` and backquote form, nested
two deep, two substitutions in one word, and inside an assignment.

524 assertions across 63 files, 16 differential cases, 1991 core OK
markers, both cell widths, mrsh 18 of 21.

### What Stage 1b still needs

`TOKENIZE` still expands as it walks the spans. The remaining step is
to make that walk *not* expand — recording each word's raw text and a
"needs expansion" flag — and to run a new `EXPAND-WORDS` per command
instead. Then the audit of `ARGV`'s readers in
`PARSE-EXPAND-PLAN.md`, which is where the quiet failures will be.
## Iteration 113: expansion becomes a word you can call later

`TOKENIZE` is now `TOKENIZE-RAW` followed by `EXPAND-WORDS`.

`TOKENIZE-RAW` copies each word recorded by `NORMALIZE-OPERATORS` into
`TOK-BUF` verbatim - quotes, `$`, backquotes and all. `EXPAND-WORDS`
takes that list, runs `SCAN-TOKEN` over each word into `EXP-BUF`, and
rebuilds `ARGV` from the results.

Not expanding turned out to cost nothing, which was not true a week
ago. The obstacle had always been that the scanner which *found* the
words was the same one that expanded them, so a raw pass meant a
second "raw mode" through every region-consuming word - and every one
of those modes would have been a chance to disagree with its
expanding twin about where a region ends. Iteration 112 moved boundary
finding into `NORMALIZE-OPERATORS`, so `TOKENIZE-RAW` has no scanner
in it at all. It is a `MOVE` and a NUL.

Three details:

- The raw list is **snapshotted** before `ARGV` is rebuilt. One raw
  word can yield several fields (IFS splitting) or none (an unquoted
  empty expansion), so the two lists cannot share an array.
- `ARGV-NAME-QUOTED` is recorded by the raw pass, while the quotes are
  still there to see. `EXPAND-WORDS` needs it after they are gone, to
  tell `""` (a field) from `${nope:-}` (no field).
- `EMIT-TOK-CHAR` now bounds-checks against a `TOK-OUT-END` variable
  rather than a fixed buffer, since the same emit path fills `TOK-BUF`
  with raw words and `EXP-BUF` with expanded ones.

**No behaviour changed.** `TOKENIZE` still calls `EXPAND-WORDS`
immediately, so a line is still expanded in one pass before any of it
runs. Moving that call to the execution paths - so a word is expanded
after everything earlier on its line has finished - is the last step,
and it is a change of behaviour rather than of structure, which is why
it is not in this commit.

524 assertions across 63 files, 16 differential cases, 1991 core OK
markers, both cell widths, mrsh 18 of 21.
## Iteration 114: a word is expanded when its command runs

    FOO=bar; echo $FOO      ->  bar

`TOKENIZE` no longer calls `EXPAND-WORDS`. The splitters, the keyword
checks, alias lookup and group detection all run on the raw words;
`EXPAND-WORDS` runs at the point one command is about to execute, by
which time everything earlier on its line has finished.

**mrsh-suite 18 -> 19 of 21.** `word.sh` passes. That is the recorded
ceiling: the remaining two failures are the deliberate POSIX-versus-
bash alias divergence, which cannot be fixed without making this shell
less correct.

This closes the stale-expansion limitation recorded in Iteration 18
and carried in GOALS.md ever since, and it is Stage 1 of
`PARSE-EXPAND-PLAN.md` complete.

### Where expansion had to be asked for

`RUN-SIMPLE-OR-PIPELINE` covers every builtin, every external command,
every pipeline stage and both loop conditions. Three paths read `ARGV`
directly and never reach it, exactly as the plan's audit predicted:

- **`DO-FOR`** - the word list, so `for i in $list` iterates over what
  `$list` expands to.
- **`DO-CASE`** - twice: the case word, and each arm's patterns. The
  pattern call goes *after* the `)` split, so the arm's body is left
  raw and expanded later, per command, when it runs.
- **`PREPARE-COMPOUND-PIPE`** - it re-tokenizes the whole line from
  raw text, so `PREPARE-PIPE-CALL` had to move above the expansion
  point rather than below it. Where it sat was fine while tokenizing
  and expanding were one act; now it would have thrown away an
  expanded `ARGV` and left a raw one behind.

Group handling also had to move *above* the expansion call, so a
group's body is carved out of raw words rather than expanded ones.

### The bug that took the longest, and what it really was

`(echo "a b") | cat` printed `a`. The group's body was being expanded
twice - once as part of the enclosing line, again when the body ran -
and the second pass truncated it. `SCAN-TOKEN` stops at unquoted
whitespace. Inside a raw word that cannot happen, because the spans
were cut at exactly those points; inside an already-expanded word it
can, and everything after the space was silently dropped.

The first fix was a flag: expand once per tokenization, refuse
after. It broke same-line `elif`, because the flag is global and the
`;`-remainder of a line is raw while a group's body is not - the same
"parallel state that does not travel with the words" problem as
`ARGV-QUOTED`, which Iteration 109 had just finished deleting the
unsafe half of. Refusing was the wrong shape.

`EXPAND-WORDS` now scans each word until its span is used up, treating
any whitespace left in the middle as a field break. For a raw word
there is never any, so nothing changes; for a word expanded twice it
re-splits instead of truncating, which is both harmless and the more
defensible reading. No flag, no state to keep in step.

### Verified

`tests/diff/cases/same-line-expansion.sh` - an assignment and a later
use of it on one line, across `;`, `&&`, `${c=...}`, arithmetic,
`set --` word splitting, and a `for` list and `case` word read when
the construct runs.

524 assertions across 63 files, 17 differential cases, 1991 core OK
markers, both cell widths, **mrsh 19 of 21**.
## Iteration 115: retire the limitation notes Stage 1 made false

Written retrospectively in Iteration 122, from commit `cd7ff9a`, which
made a real change to two documents and left no entry here. Recording
it because the gap was load-bearing: both `GOALS.md` and
`PARSE-EXPAND-PLAN.md` cite "Iteration 115" as where Stage 4 was done,
and following that citation led nowhere.

No code. Iteration 114 made three recorded limitations false, and a
limitation that has stopped being true is worse than one that never
got written down, because it is believed. Four notes retired:

- **`GOALS.md`, phase B.** `FOO=bar; echo $FOO` not seeing the
  assigned value was described as needing "a real architectural
  change left for its own future iteration". It had just had one; the
  note now points at Iteration 18 for the original account and 114 for
  the fix.
- **`GOALS.md`, Ramey item 2** ("parse first, expand after") marked
  **done** for Iterations 108-114, with the honest remainder stated
  rather than dropped: bash expands words hanging off a command
  *tree*, and this is still a flat token array with splitting passes
  over it. Closer to the destination, not at it.
- **`GOALS.md`, Ramey item 3** ("command substitution should reuse the
  real parser") marked done for Iteration 105 — but *not by the route
  sketched there*. Saving and restoring parser state around a
  recursive parse turned out to be unnecessary once the work moved
  into the forked child, which has its own copy of every buffer. The
  original route is kept in the entry so a future session can see that
  it was considered and bypassed, not overlooked.
- **`PARSE-EXPAND-PLAN.md`, Stages 3 and 4** marked done, with each
  stage's original text kept below its status line for the same
  reason.

Ramey item 1 (flags attached to the word, not a parallel array) was
deliberately *not* marked done. Iteration 109 deleted the unsafe
spelling; the parallel arrays remain, and 114 hit the same shape from
a different direction. "Half-addressed" is the accurate word and is
what it now says.

### What this iteration is really about

The project has two documents that make claims about the present
tense (`GOALS.md`, `PARSE-EXPAND-PLAN.md`) and one that makes claims
about the past (`PROGRESS.md`). Only the first two can go stale, and
they go stale silently, in the direction of describing finished work
as unfinished. Iteration 122 found five more of these and is the
argument for auditing them on a schedule rather than opportunistically.

No behaviour changed. 524 assertions across 63 files, 19 differential
cases, 1991 core OK markers, both cell widths, mrsh 19 of 21.
## Iteration 116: measuring what Stage 1 cost

`tests/bench` had not been run in this whole run of work. It has now,
here and at the Iteration 101 handoff, on the same machine:

| | loop-ms | spawn-ms | start-ms (engine) |
|---|---|---|---|
| relfsh @ 101 | 689 | 145 | 210 |
| relfsh @ 115 | 944–966 | 150–160 | 236–239 |
| dash | 4 | 71–74 | 97–101 |
| bash | 8 | 88–91 | 131–133 |

**Stage 1 made the pure loop about 37% slower.** Startup and spawn are
roughly flat, within noise of a 10% rise. The gap against dash on the
loop went from ~172x to ~236x; the "~190x" figure carried in GOALS.md
was measured somewhere in that range and is now wrong in the unhelpful
direction.

The cause is not mysterious: a line is walked more times than it used
to be. `NORMALIZE-OPERATORS` now records word boundaries as it goes,
`TOKENIZE-RAW` copies every word into `TOK-BUF`, and `EXPAND-WORDS`
then reads each word back out and writes it again into `EXP-BUF`. That
is one more full copy of every line than before, and loop bodies are
re-tokenized every iteration.

Recording it plainly because the alternative is that it gets found
later and read as a surprise. Stage 1 was worth it — it fixed four
`ENSURE-ROOM` bugs, two recorded limitations and took mrsh to its
ceiling — but it was not free, and "no behaviour changed" in
Iterations 111 and 113 meant no *observable* behaviour, not no cost.

### Why this makes Stage 2 the right next thing

Stage 2 is caching tokenized body lines, and it attacks exactly the
work this iteration added. A loop body is stored as raw text and
re-tokenized on every iteration: normalized, word-boundaried, copied
into `TOK-BUF`, then expanded. Only the last of those depends on
anything that changes between iterations. Caching the first three per
body line should recover this 37% and then some, which is the first
time that stage has had a number attached to it rather than an
argument.

Measure again after, on the same machine, and put both numbers in the
entry.

### A note on the first attempt at measuring

The Iteration 101 numbers were nonsense on the first run - 7ms for the
loop, 6ms for a hundred `fork`/`exec` pairs, which is physically
impossible. `git worktree` gave a checkout with no built `relf` in it,
`relfsh` failed to exec, and `tests/bench` timed the failure. It
redirects to `/dev/null`, so a shell that cannot start looks
tremendously fast.

`tests/bench` now runs a probe script through each shell first and
refuses to report if it does not come back with the expected output. A
benchmark that silently times a crash is worse than no benchmark,
because it produces a number and numbers get believed.

Checked by output rather than by exit status, which was the first
attempt and rejected two working shells: the raw-engine row
(`./relf kernel-shell.img`) does not report a script's exit status at
all, so a status check called it broken.
## Iteration 117: a loop written entirely on one line

    for i in 1 2 3; do echo "i=$i"; done
    while [ $i -lt 3 ]; do i=$((i+1)); done

Both were a syntax error - `for: expected 'do'`, because
`SAME-LINE-DO?` looks for `do` as the *last* token, and here it is in
the middle. Found while writing Iteration 105's own differential case,
which had to be rewritten around it.

`ONE-LINE-LOOP?` finds an unquoted `do` that is not last and an
unquoted `done` after it. `CAPTURE-ONE-LINE-LOOP` then produces
exactly the three things the multi-line path produces by reading
further lines: the body, stored as text through the existing
`APPEND-RAW-LINE-TO-BODY`; the suffix after `done`, through the
existing `SAVE-COMPOUND-SUFFIX`; and a header left in `ARGV`. Nothing
downstream knows the difference - `DO-WHILE-BODY`, nesting,
`break`/`continue`, the suffix, all unchanged.

**This became easy only because of Iteration 114.** Carving a body out
of the token list requires the tokens to still be the words as
written, and until 114 they were expanded during tokenizing - the body
would have been expanded once, at the header, before the loop
variable existed. Now `ARGC` is simply cut back to the header before
the caller expands anything, and the body's words are expanded on each
iteration when they run, because that is where expansion happens.

`while` needs one thing more: its condition is stored as raw text, and
`SAVE-WHILE-COND` trims that text at the last unquoted `;` - which for
a one-line loop is the one before `done`, not the one before `do`. So
`JOIN-WHILE-COND` rebuilds `RAW-LINE-BUF` as just `while COND` from
the tokens before the `do`, and `SAVE-WHILE-COND` then reads it the
way it reads any while line. Body and suffix are captured first, since
all three rebuild that buffer.

The last `done` is the outer loop's, so a one-line loop nested inside
another works: the inner one is then a body line and is recognised
again when it runs.

### A blank line before every iteration

Under `-c`, each iteration printed an empty line first.
`READ-LINE-INTO-ARGV` echoes a newline when `SHFILE-ACTIVE?` is false,
which is the echo of an interactively *typed* line - and a loop body
is replayed, not typed. It had never shown because `-c` had no way to
run a loop at all before this iteration. Now gated on
`REPLAY-ACTIVE?` too.

### Verified

`tests/diff/cases/one-line-loop.sh` - `for` and `while`; a word list
from a variable; a body whose value changes each iteration; a
multi-command condition; nesting; a suffix after `done`; `$?` from a
loop that ran nothing; `break` and `continue`; `"do"` and `"done"`
quoted so they are not keywords; and the multi-line form still
working.

524 assertions across 63 files, 18 differential cases, 1991 core OK
markers, both cell widths, mrsh 19 of 21.
## Iteration 118: a function defined entirely on one line

    f() { echo hi; }

The form that hung before Iteration 107 and was diagnosed after it now
works. Same technique as 117's one-line loop, and possible for the
same reason: since Iteration 114 the tokens are still the words as
written, so a body can be carved out of them and stored unexpanded.

`FIND-BODY-CLOSE` locates the brace that closes the body **by depth**,
not by taking the last token. The first attempt did take the last
token, and `outer() { inner() { echo deep; }; inner; }` failed on it -
the inner definition's own tokens continue past its closing brace, so
`ARGV` ends in `;` rather than `}`. Depth also gives the other half
for free: whatever follows the closing brace is the rest of the line
and still has to run, which is how that example manages to define
`inner` and then call it, both from the outer body's single stored
line.

`tests/shell/run-unterminated` lost its "one-line function definition"
case, which asserted a syntax error, and gained an *unterminated*
one-line definition instead - the thing that file is actually about.

### Verified

`tests/diff/cases/one-line-funcdef.sh` - arguments and `$#`; the
caller's own positional parameters surviving the call; a body read
when it runs rather than when it is defined; the `f() ( ... )`
subshell form; `return` and the resulting `$?`; nesting; redefinition;
and the multi-line form still working.

524 assertions across 63 files, 19 differential cases, 1991 core OK
markers, both cell widths, mrsh 19 of 21.

With this, every form GOALS.md listed as an unsupported same-line
construct now works, and that entry is gone from the limitations list.
## Iteration 119: normalizing each line once instead of twice

Every line went through `NORMALIZE-OPERATORS` twice.
`JOIN-OPEN-QUOTES` runs it to find out whether a quote is still open,
and then `NORM-TOKENIZE` ran it again on the same bytes. Its own
comment said so and called it "a pass over the line and nothing else",
which was true when it was written and stopped being true once loop
bodies started going through it on every iteration.

`RUN-LINE` and `READ-LINE-INTO-ARGV` now call `TOKENIZE` directly,
since `JOIN-OPEN-QUOTES` has just left `NORM-BUF` and the word spans
exactly as they need them. `DO-WHILE`'s condition and the three other
callers still use `NORM-TOKENIZE`; they have no `JOIN-OPEN-QUOTES`
before them.

The invariant that makes this safe - "`JOIN-OPEN-QUOTES` returns with
a valid `NORM-BUF`" - was *almost* true. Its `-c` early exit returned
without normalizing at all, which is why the first attempt broke every
arithmetic and `&&` test in that mode. It normalizes once on that path
now, which also removes the stale-flag hazard Iteration 110 had to
work around by moving the `UNTERMINATED-QUOTE?` check.

**Measured: 944-966ms down to 914ms on the loop benchmark**, about 4%.
Smaller than it looks like it should be, because only body and script
lines were paying twice - a `while` condition goes through
`NORM-TOKENIZE` and was already normalizing once. Recorded rather than
rounded up: the change is worth keeping as one less redundant pass
over every line, not as a performance result.

Stage 2 proper - caching the tokenized form of a body line so
iterations two onward skip normalizing and tokenizing entirely - is
still the thing that addresses the 37% Stage 1 cost.

524 assertions across 63 files, 19 differential cases, 1991 core OK
markers, both cell widths, mrsh 19 of 21.
## Iteration 120: `~user` through NSS instead of /etc/passwd

The last entry under GOALS.md's "Known shortcuts to revisit", recorded
in Iteration 96 as "kept for now because it needs no engine change and
unblocks `word.sh`; not kept because it is right".

`/etc/passwd` is one NSS source among several. On a host using LDAP,
SSSD, NIS or systemd-homed a real user need not appear in that file at
all, and `~alice` stayed literal - a failure that could never show up
on a developer machine and would show up on exactly the hosts where
centrally managed accounts are the point.

`GETPWHOME` is a new engine primitive wrapping `getpwnam(3)`: a
NUL-terminated name in, a pointer to the home directory out, 0 for an
unknown user. `PASSWD-HOME` now calls it and the file reader is gone,
rather than the two sitting side by side - two code paths disagreeing
about who exists would be worse than either alone, which is what the
GOALS.md entry said when it was written.

The result points into `getpwnam`'s own static storage, valid only
until the next call, so it is copied out immediately.

### The engine change this needed

`relf.c` gains one label and one entry at the **end** of the
primitive dispatch table, and `kernel.4` one `PRIMITIVE` line at the
end of its list. The two are positional and must stay in step;
appending is the only safe place. `kernel.img` then has to be
cross-compiled again (`extend.4`, `cross.4`) so the new word exists in
the dictionary - the committed image is a build artifact and does not
update itself.

Both cell widths rebuilt and pass. This is the first engine change
since the shell work began, and the first new primitive since
Iteration 96 wanted one.

524 assertions across 63 files, 19 differential cases, 1991 core OK
markers, both cell widths, mrsh 19 of 21.
## Iteration 121: what a fresh machine needs, written down

No code. Three gaps in the handoff documentation, each of which cost
time in this run of work and would have cost it again.

**Build environment.** Everything is checked in except the toolchain,
and there is no `Makefile` or package manifest to read it off, so
GOALS.md now lists it: a `cc`, **32-bit support for it**, `bash`,
`dash`, `timeout`. The 32-bit point is the one that matters. Every
commit must pass on both cell widths, but when `cc -m32` cannot link,
`tests/run_tests.sh` prints `SKIP:` and carries on green - so a
container with only 64-bit libraries looks entirely healthy while
testing half of what it claims to. This session began by installing
`gcc-multilib` and would have reported false greens without it.

Also recorded there: how to rebuild `kernel.img` after adding an
engine primitive, including that the cross-compiler runs *on* the
existing image, so deleting it first is the one thing not to do.
Iteration 120 did exactly that and had to recover with
`git checkout kernel.img`.

**The four test layers.** `tests/`, `tests/shell/`, `tests/diff/` and
`tests/mrsh-suite/` existed with no single place saying what each is
*for* - in particular that the differential suite is the strongest and
should be reached for first, and that hand-written assertions are for
the cases where bash is the wrong oracle. Plus the trap that cost
twenty minutes here: `lib.sh` defaults `THIS_SH` to `../../relfsh`, so
running a `run-*` file from the repository root tests a shell that
does not exist and reports every assertion as failed. I misread that
as a real regression and reverted a correct change because of it.

**Tracked numbers brought current.** The size table was Iteration 41's
and eighty iterations stale. The image has grown ~1.85x since then,
all of it shell functionality - the engine has not changed size at
all. Worth stating plainly: the i386 build is no longer smaller than
`dash`, it is ~1.25x it, having passed it somewhere in the eighties.
The section already said the comparison "currently flatters this
project"; it no longer does, and that is the fact the deferred size
levers exist for. `tests/bench` is now listed as a tracked number with
Iteration 116's figures, rather than living only in a PROGRESS entry.

524 assertions across 63 files, 19 differential cases, 1991 core OK
markers, both cell widths, mrsh 19 of 21.
## Iteration 122: the documents that can rot

No code. `PROGRESS.md` had no index and `GOALS.md` had become a log,
and the second of those was actively misleading.

### PROGRESS.md: an index, not a trim

The obvious move was to compact this file, and measuring first said
not to. 119 entries, ~456K, ~114k tokens — over half a context window.
But the only large mechanically-removable category is the 63
`### Verified` blocks, 12% of the file, most of which name a test file
that is checked in and then restate what it covers. Deleting all of
them perfectly still leaves 400K. Reaching a readable size means
deleting about 78% of the entries.

And the entries that look stalest are the ones being used. The other
four documents make 139 citations to specific iterations, and **108 of
them point at iteration 50 or below**. The oldest half is the
most-cited half, so archiving by age would break exactly the pointers
that get followed. The problem was never bulk, it was that finding the
entry a citation meant took scanning 8,896 lines.

The Index at the top lists every entry in one screen (~2k tokens),
grouped into nine eras, marking the 16 entries that moved the mrsh
count and bolding the 53 cited elsewhere. Index plus three entries is
~4k tokens against ~114k. Nothing was rewritten or deleted.

**An index nobody is told to use is worth nothing**, so
`GOALS.md`'s conventions now say to read this file through it. That
sentence is the load-bearing half of the change.

### The missing Iteration 115

Commit `cd7ff9a` changed two documents and wrote no entry here, while
both of those documents cite "Iteration 115" as where Stage 4 was
done. Reconstructed from its own diff and marked as retrospective. The
gap was found by the index generator, which noticed a number with a
commit and no heading — worth knowing that building the index was what
made the hole visible.

### GOALS.md had become a log, and had gone stale

Its own header says it "changes rarely... not a log". The `## Phases`
section was 38,575 characters — 44% of the file — of narrative
duplicating `PROGRESS.md` entries it also links to. That matters more
than this file's size ever did: **`GOALS.md` is the document every new
session reads in full, by its own instruction.** ~22k tokens, every
session.

Five claims said finished work was unfinished:

| claim | actually done in |
|---|---|
| phase 7: nesting, IFS splitting, `${VAR:-default}`, positional parameters "not yet done"; pipes and redirection not combinable | 42/43, 36, 32, 31, 58 |
| phase B: `while`/`do`/`done` nesting "remains not done" | 42/43 |
| phase C: "Still open: nested function *definitions*" | 63 |
| phase D: "not yet a customizable `$IFS`" | 67 |
| phase F: `read`, `readonly`, `shift`, `getopts`, `command`, background jobs, `alias`/`unalias` open | 51, 54, 59, 61, 74 |

Some had been wrong for eighty iterations. A session that trusts them
either rebuilds something that works or spends its first hour finding
out it needn't — which is precisely the failure this log exists to
prevent, occurring in the file with priority over it.

Phases is now status plus pointers, 38,575 -> 7,853 chars; GOALS.md
87,486 -> 57,629, about 22k tokens to 14k. Every remaining open item
was re-verified **by running it**, not inherited: the
`NAME=value command` prefix still fails, `pwd > file` still does not
redirect a builtin, and the 33rd shell variable now diagnoses rather
than failing silently (Iteration 90) but is still capped.

### mrsh: at the ceiling, and one pass is hollow

Re-ran the suite rather than trusting the recorded number: 19 passed,
2 failed, 3 skipped, and the two failures are the alias divergence, as
recorded. The 3 skips are `*.undefined.sh` cases POSIX does not
specify — not outstanding work, and worth saying plainly because
"19 of 21 with 3 skipped" reads like 24 tests with 5 to go.

Then checked *why* the passes pass, per FORTH-STYLE.md §13.
**`ulimit.sh` is hollow.** `ulimit` is not implemented at all; the
harness is differential and bash also fails this test on a modern host,
because its last assertion greps `/proc/self/limits` for a 512-byte
block count bash reports in 1024-byte blocks. Both shells emit the
same stdout and status 1. Iteration 82 audited the then-17 passes for
exactly this; two have landed since and this is one of them, so the
rule is to re-audit **when the count moves**, not when it stalls.

That test also surfaced a real gap: **`set -e` is not implemented**,
in either spelling. It is inert here because the harness runs
`relfsh file` and `bash file`, which ignores the shebang for both — so
five vendored tests run with error-exit disabled on both sides, more
forgivingly than upstream intends. Symmetric, so not a false pass, but
the suite is testing something weaker than mrsh meant.

### A caveat on this iteration's own verification

**Only the 8-byte-cell half was run.** This host has no 32-bit
toolchain, `cc -m32` cannot link, and `tests/run_tests.sh` prints
`SKIP:` and carries on green — exactly the trap Iteration 121 wrote
down, confirmed live one iteration later. No code changed here, so the
risk is nil, but the convention says every commit passes on both
widths and this one has not been shown to.

8-byte cells: 1991 core OK markers, 524 assertions across 63 files, 19
differential cases, mrsh 19 of 21. 4-byte cells: not run.
## Iteration 123: correcting Iteration 122, from upstream's own harness

122 wrote that five vendored tests "run with error-exit disabled on
both sides, more forgivingly than upstream intends." The second half
of that is **wrong**, and it was inferred rather than checked. This
log is append-only, so 122 stands as written; this is the correction.

mrsh's `test/harness.sh` and both `meson.build` files were fetched at
the vendored commit `4c81598` — the parts `vendor/README.md` records as
deliberately *not* vendored, which is why nobody here had read them.

### `set -e` is inert upstream too

Upstream's harness runs `"$MRSH" "$testcase"` and
`"$REF_SH" "$testcase"`, passing the script as an argument. That is
exactly what `tests/mrsh-suite/run.sh` does, so `#!/bin/sh -e` is a
comment on both sides, for mrsh as much as for us. Our invocation is
faithful to upstream's, which is the reassuring half.

The consequence for the open question that prompted this:
**implementing `set -e` would not change this suite's verdict on any
file.** It is still a real POSIX gap and `ulimit.sh` is still a hollow
pass — neither of those findings depended on the claim being retracted
— but the argument that goal 8's own criterion was being measured too
weakly does not survive contact with the harness.

Worth naming the mistake precisely: 122 established a true fact (the
shebang is ignored), attached a plausible consequence to it (so we are
more lenient than upstream), and did not check the consequence when
one `curl` would have. FORTH-STYLE.md §13 already says "measure before
concluding" and cites a wrong PROGRESS entry that survived an
iteration. This one survived a turn.

### The criterion here is stricter than mrsh's own

Found in the same file. `2.2.3-alias-expansion.fail.sh` is **commented
out of upstream's `test/conformance/meson.build`**, against a TODO
pointing at mrsh issue #145. Upstream does not run it. The undefined
cases are likewise behind a `test-undefined-behavior` option, which
matches what `run.sh` already does by skipping them.

So there are two defensible denominators, and GOALS.md now carries
both: **19 of 21** by this harness's arithmetic, **19 of 20** against
the set mrsh itself runs. One genuine failure either way, `command.sh`,
and it is the alias divergence.

`run.sh` is deliberately left scoring the file. Dropping a vendored
test to improve a number is the exact move this suite was adopted to
prevent, and the fix for a misleading denominator is to write down
what it means, not to change it. But "19 of 21" should not be quoted
as though 21 were mrsh's own count.

### What this says about the vendoring decision

`vendor/README.md` records that `harness.sh` and `meson.build` were
not vendored because they are tooling rather than test content. That
was right for `harness.sh` — `run.sh` reimplements it — but
`meson.build` is not tooling: it is upstream's statement of *which
tests count and in which category*, and not having it meant this
project silently invented a stricter criterion than the one it
believed it had adopted. The classification was reconstructed by
reading filenames instead. Worth a re-read of both files whenever the
vendored commit is bumped.

No code. 1991 core OK markers, 524 assertions across 63 files, 19
differential cases, mrsh 19 of 21 (19 of 20 upstream-active), 8-byte
cells only — this host still has no 32-bit toolchain.
## Iteration 124: the reference shell was the ceiling

`tests/mrsh-suite/run.sh` compared against `bash`. Upstream's
`meson_options.txt` defaults `reference-shell` to **`sh`**. Nobody had
read that file, for the same reason nobody had read `harness.sh`:
`vendor/README.md` records both as tooling not worth vendoring, and
Iteration 123 already noted that `meson.build` is not tooling but
upstream's statement of what counts. `meson_options.txt` is the other
half of that statement, and it names the oracle.

The harness now uses `${REF_SH:-sh}`. On this host `/bin/sh` is dash.
Same count, different members, and both changes are in the honest
direction:

| | vs bash | vs sh |
|---|---|---|
| `command.sh` | FAIL | **PASS** |
| `ulimit.sh` | **PASS** | FAIL |
| total | 19 | 19 |

### Both movements say the same thing

`command.sh` failed because bash does not expand aliases in
non-interactive shells — a documented bash deviation from POSIX.
`GOALS.md` has a whole section saying this shell follows POSIX where
the two disagree, and listing this exact case as costing two tests.
Checked directly rather than reasoned about: on `alias ll="ls -l";
command -v ll`, dash prints `alias ll='ls -l'` and exits 0, relfsh
prints **the identical line** and exits 0, and bash prints nothing and
exits 1. This shell was right and was being marked wrong by an oracle
the project's own documentation calls wrong.

`ulimit.sh` is the hollow pass from Iteration 122, and it evaporated
exactly as predicted. bash fails that test on a modern host because
its last assertion greps `/proc/self/limits` for a 512-byte block
count that bash reports in 1024-byte blocks — POSIX specifies 512, and
dash reports 512 and passes. Against bash, two shells failed for
unrelated reasons and matched; against `sh`, the missing builtin shows
up as a missing builtin.

That the same one-line change fixed a false failure *and* exposed a
false pass is the strongest evidence available that it is a correction
rather than a way of moving a number.

### What this does to goal 8

The recorded "ceiling of 19 of 21, and the remaining two are
deliberate divergence we will not fix" was **an artifact of the
oracle**, not a property of this shell. It had been believed since
Iteration 81 and repeated in `GOALS.md` ever since.

What is actually left:

- **`ulimit.sh`** — a real, missing builtin. Needs a
  `getrlimit`/`setrlimit` engine primitive.
- **`2.2.3-alias-expansion.fail.sh`** — which upstream does not run,
  per Iteration 123.

**So the target is 20 of 20 against the upstream-active set, and one
builtin stands in the way.** `run.sh` still scores the disabled file,
and bash remains one `REF_SH=bash` away for anyone who wants the
second opinion; keeping both oracles reachable is worth more than
picking one.

### The pattern, now three for three

Three iterations in a row have found that a number this project
believed was a property of `shell.4` was a property of how it was
measured: 122 (a hollow pass), 123 (a stricter denominator than
upstream's), 124 (the wrong oracle). Iterations 15/16, 40 and 116
found the same shape earlier. **When a count stops moving, suspect
the harness before concluding the ceiling is real** — and read the
build files of a vendored suite, not just its tests.

19 passed, 2 failed, 3 skipped against `sh`; unchanged against bash.
1991 core OK markers, 524 assertions across 63 files, 19 differential
cases, 8-byte cells only.
## Iteration 125: `ulimit`, and goal 8 is met

    20 passed, 1 failed, 3 skipped

**The mrsh suite is fully passed against the set mrsh itself runs.**
The remaining failure is `2.2.3-alias-expansion.fail.sh`, which is
commented out of upstream's own conformance `meson.build` (Iteration
123). `run.sh` keeps scoring it rather than quietly dropping it.

Iteration 124 left exactly one real feature in the way, and this is
it.

### Two primitives, deliberately narrow

`GETFSIZE ( --- n )` and `SETFSIZE ( n --- ior )`, wrapping
`getrlimit`/`setrlimit` on `RLIMIT_FSIZE`. Appended to `relf.c`'s
dispatch table and `kernel.4`'s `PRIMITIVE` list — positional, so the
end is the only safe place — and `kernel.img` cross-compiled again,
following the recipe Iteration 121 wrote down. It worked first time,
which is the recipe earning its keep.

They traffic in POSIX's **512-byte blocks**, not bytes. Two reasons,
both real: POSIX specifies `ulimit` in 512-byte units, and a byte
count of a large limit does not fit a 4-byte cell on a 32-bit build.

`RLIMIT_FSIZE` is the *only* resource POSIX's own `ulimit` covers, so
one pair of primitives is the whole job rather than a first
instalment. Goal 3 says minimalism above completeness; here they
agree.

### The bug, which the vendored test caught and a smaller test would not

First version set `rl.rlim_cur` alone. `ulimit` and `ulimit -f 100`
both then reported correctly, and `ulimit.sh` still failed — on its
last line, which greps `/proc/self/limits`, a file with *two* columns.
POSIX: with neither `-H` nor `-S`, `ulimit` sets the soft and hard
limits both. The soft column read 51200 and the hard column still read
`unlimited`.

Worth noting how thin the margin was. Every assertion I would have
written by hand — report, set, read back — passed against the broken
version. What caught it was a third-party test asserting on a
*side effect* in a file outside the shell. That is the argument for
`tests/mrsh-suite/` being a layer of its own rather than redundant
with the hand-written ones (GOALS.md's four layers).

### `run-ulimit`, and a wrong expectation of mine

`tests/shell/run-ulimit`, 8 assertions. Deliberately hand-written
rather than differential: bash reports 1024-byte blocks, so it is the
wrong oracle here — exactly the case GOALS.md's layer 2 exists for.

One assertion I wrote was wrong, not the shell.
`ulimit -f 100; ulimit -f unlimited` fails, because setting `-f`
without `-H` lowers the *hard* limit too and an unprivileged process
may not raise it back. Checked against dash before changing anything:
dash refuses identically. The test now asserts the refusal. Its status
is 1 here and 2 in dash; POSIX requires only nonzero, so this is left
alone rather than matched — recorded because a future POSIX-derived
differential case against `sh` would trip on it.

### What goal 8 being met does and does not mean

It means `shell.4` handles everything mrsh's acceptance tests
exercise. It does **not** mean POSIX conformance: the suite is 21
files, and the gaps under GOALS.md's "Still open" — `set -e`, the
`NAME=value command` prefix, redirection of builtins, `trap`/`exec`/
`hash`/`type` — are real and entirely unmeasured by it. The external
yardstick has been useful precisely because it was external; the
successor is a criterion derived from the POSIX specification itself,
which is the next direction.

532 assertions across 63 files, 19 differential cases, 1991 core OK
markers, mrsh 20 of 21, 8-byte cells only — this host still has no
32-bit toolchain, and this iteration **does change the engine and
`kernel.img`**, so the 4-byte build genuinely needs running before
this is trusted on both widths.
## Iteration 126: a conformance harness scored by consensus, not by bash

`tests/posix/` — cases derived from POSIX.1 XCU "Shell Command
Language" rather than from another shell's suite, and scored against
**the agreement of every reference shell present** rather than against
one.

Goal 8 was met in Iteration 125 and it is 21 files. Passing it says
`shell.4` handles what mrsh's acceptance tests exercise and nothing
about the rest of the specification. This is the successor yardstick.
The harness first; the corpus is scoped next.

### The design decision, and what it is a reaction to

A case is scored only when every reference agrees on stdout **and**
exit status. Where they disagree the verdict is `INCONCLUSIVE` and
nothing is scored.

This is a direct reaction to Iteration 124. `tests/diff/` compares
against bash alone, which means each case has to be hand-checked for
forms where bash and POSIX legitimately differ — and the mrsh harness
made exactly that mistake, silently, for eighty iterations, at a cost
of one real pass and one hollow one. **One shell is not POSIX.** It is
one implementation's reading plus its extensions, and a suite that
treats it as the standard will encode the extensions along with the
standard and never notice.

Consensus makes the oracle self-checking. A case that accidentally
depends on a bash-ism cannot become the criterion, because dash
disagrees and the *case* gets flagged rather than the shell failed.
The property worth stating plainly: **adding a reference shell can
only make this harness stricter about what it scores**, never more
permissive.

`INCONCLUSIVE` is deliberately not a skip. It is one of two findings:
the case needs narrowing to what POSIX actually specifies, or it has
documented a genuine divergence between implementations. Both are
worth having written down.

### Five seed cases, one per verdict path

A harness with no cases is an unverified harness, so each path is
exercised by something real rather than by a fixture:

| case | verdict |
|---|---|
| `2.6.2-parameter-expansion-defaults.sh` | PASS |
| `2.5.2-special-parameters.sh` | PASS |
| `2.2.2-unterminated-single-quote.fail.sh` | PASS |
| `2.6.1-tilde-after-equals-in-argument.sh` | INCONCLUSIVE |
| `2.9.1-assignment-prefix.sh` | FAIL |

The inconclusive one is the tilde-after-`=` divergence already in
GOALS.md — bash expands, dash does not — kept permanently as the
worked example of what that verdict means. The failure is
`NAME=value command`, the recorded Phase B gap, which the harness
found on its first run without being told to look for it. Verbose
mode shows it exactly: the reference prints the value in the child and
then `unset-after`; `shell.4` prints only the second line, because the
prefix form is not recognised at all.

### Details that came from prior mistakes here

- **Symlinks are resolved during discovery.** `/bin/sh` is dash on
  this host, so `sh` and `dash` would otherwise count as two
  independent opinions. Two agreeing copies of one shell look exactly
  like consensus, which is the false confidence the whole design
  exists to avoid.
- **A single reference is reported as a degradation**, in the output,
  not in a comment: with one shell present the run is no stronger than
  `tests/diff/` and says so. This container has only dash and bash.
- **A crash is never a rejection.** `.fail.sh` cases require nonzero
  *and* not 128+signum, the same distinction `tests/mrsh-suite/run.sh`
  makes after an earlier version there scored a segfault as a pass.
- **`printf`, not `echo`**, in cases. `echo`'s treatment of `-n`, `-e`
  and backslashes is implementation defined and would produce
  inconclusive verdicts on content unrelated to the section under
  test. Written into the README as a rule rather than left to be
  rediscovered.

### Not wired into `run_tests.sh`

Same as the mrsh suite: a separately-run tracked number, now listed in
GOALS.md alongside it, reporting passed / failed / **inconclusive**
plus which references were present. A rising inconclusive count means
the references disagree more, not that the shell got worse — worth
saying because it is the one number here that goes up for a good
reason.

532 assertions across 63 files, 19 differential cases, 1991 core OK
markers, mrsh 20 of 21, posix 3/1/1, 8-byte cells only.
## Iteration 127: seven reference shells, and the 32-bit half finally run

Two provisioning gaps closed, and both had been hiding something.

### The 4-byte-cell build was never verified for `ulimit`

Iterations 120 through 126 all reported "8-byte cells only" because
`cc -m32` could not link here. Iteration 121 wrote that trap down and
Iteration 122 confirmed it live; **125 then changed `relf.c` and
`kernel.img` anyway**, adding the `GETFSIZE`/`SETFSIZE` primitives,
and shipped with half the convention unmet.

`gcc-multilib` installs from Ubuntu's own archive, which was
allowlisted the whole time. The earlier attempt failed for an
unrelated reason worth recording: a third-party `nodesource` entry in
`sources.list.d` returns 403, and `apt-get update` exits nonzero
because of it even though every Ubuntu repository fetched fine. One
broken source makes the whole update look like no network at all.
Disabling that entry was the entire fix.

Both cell widths now pass, primitives included:

    PASS (8-byte cells): 1991 OK markers
    PASS (8-byte cells shell test suite)
    PASS (4-byte cells, i386): 1991 OK markers
    PASS (4-byte cells, i386 shell test suite)
    19 differential cases, 0 failed

Sizes, against Iteration 121's table: i386 151,748 -> **152,308**,
x86-64 272,864 -> **273,848**. The `ulimit` builtin cost ~560 bytes of
image on the narrow build. The engines are unchanged in size.

### Seven reference shells

`mksh`, `ksh93`, `yash`, `posh` and `busybox ash` join `dash` and
`bash`, all from the Ubuntu archive rather than built from source -
`apt` is the right tool when the packages exist, and they all do.

The payoff is immediate on the one case that was already
inconclusive. With two references it read "sh disagrees with bash";
with seven it reads **"sh disagrees with bash mksh"** - so on
tilde-after-`=` in a non-assignment word, five of seven shells agree
with `shell.4` and bash and mksh are the outliers. `GOALS.md` recorded
that divergence in Iteration 98 on the strength of dash alone. It now
has a majority behind it, which is a stronger claim than the one that
was written down.

The other four cases held their verdicts under five extra opinions,
which is the more important result: adding references did not shake
anything loose, so the three passes are three passes and the failure
is a real failure.

### A harness bug, surfaced as four false disagreements

The first full run reported busybox disagreeing with every other shell
on every case. That is not a finding, it is a defect, and the shape
says so: **a disagreement that lands on exactly one shell and every
single case is the harness, not the shell.**

`busybox` is a multi-call binary invoked as `busybox sh`, so a
reference's label and its command line are not the same string - and
the space-separated lists in `run.sh` can only carry one word. The
label `busybox-sh` was being exec'd verbatim, returning 127 with no
output every time. A `ref_cmd` mapping fixes it, and the reasoning is
now a comment there.

Worth noting what went right: the harness reported its own defect as
INCONCLUSIVE rather than as a silent wrong answer or four spurious
failures. Consensus scoring degrades safely when a reference is
broken, which is a property it was not explicitly designed for.

### `zsh` excluded, deliberately

Installed, then left out of the default candidate list. Invoked as
`zsh script.sh` it runs in its native mode rather than sh emulation
and differs from POSIX on word splitting and much else, so it would
produce INCONCLUSIVE verdicts about zsh rather than about the
specification. A fine shell and the wrong oracle.
`POSIX_REF_SHELLS` can add it back.

The general rule, now written into `tests/posix/README.md`: a
reference must be *attempting* POSIX `sh` semantics when run as a
script interpreter. Otherwise it does not contribute an opinion about
POSIX, it contributes noise that suppresses scoring.

### Recorded in GOALS.md

The build-environment section now lists the extra shells and the
`apt` line, alongside the `gcc-multilib` warning Iteration 121 wrote.
That section exists precisely so the next fresh machine does not spend
this time again.

532 assertions across 63 files, 19 differential cases, 1991 core OK
markers **on both cell widths**, mrsh 20 of 21, posix 3 passed /
1 failed / 1 inconclusive against seven references.
## Iteration 128: the size axis of the comparison, as a script

`tests/sizes` — `shell.4` against every other shell installed, on one
table. The size axis of the implementation comparison; `tests/bench`
is the speed axis and `tests/posix` the conformance one.

A script rather than a number pasted into `GOALS.md`, for the reason
Iteration 121 found the hard way: the size table there was Iteration
41's and eighty iterations stale. A measurement that cannot be re-run
in one command will be quoted long after it stopped being true.

    implementation         binary      image       libs        TOTAL
    shell.4 (x86-64)        22744     251104          0       273848
    shell.4 (i386)          17808     134500          0       152308
    dash                   129784          0          0       129784
    posh                   149352          0          0       149352
    mksh                   310312          0          0       310312
    yash                   445352          0     208328       653680
    zsh                    976304          0     259864      1236168
    ksh93                 1432848          0          0      1432848
    bash                  1446024          0     208328      1654352
    busybox (all 272)     2124608          0          0      2124608

### Three columns, because one number would be dishonest

**`image` is not optional.** `relf` is an engine plus a saved Forth
image and both files are needed to run a shell. Reporting the 22,744
engine alone would flatter this project by an order of magnitude and
put it ahead of everything on the list; the image is where `shell.4`
actually lives. This is the number most likely to be quoted wrongly,
which is why it has its own column rather than being folded in.

**`libs` counts only what is not universal.** libc, libm, the loader
and the vDSO are free in any honest comparison because nothing avoids
them. `libtinfo` and `libcap` are not: they are a dependency the shell
pulls in, and a system without them cannot run it. That is a 208KB
difference for bash and yash and a 260KB one for zsh — larger than
several whole shells on this list, and invisible if you only `ls -l`
the binary.

**Stripped, to match.** Distro binaries arrive stripped; an
unstripped `relf` carries ~3KB of symbols the others do not (25,872
against 22,744). Comparing one to the other would have been a free
~12% penalty on the only build where this project is competitive.

### busybox is reported apart

It is a multi-call binary: its `ash` applet is one of **272**
programs in that file. 2.1MB is not a shell size and ranking it
alongside the others would be meaningless in both directions. A
shell-only build would be a fraction of it. Static, too, so it carries
its own libc where every other row borrows the system's — the two link
types are not comparable on this axis at all, and the column says
which each is.

### What the table actually says

The i386 build is **third smallest**, behind `dash` and `posh` and
ahead of `mksh`, and it passes the mrsh suite. That is a real claim
and a narrow one.

It is not a claim to be a smaller bash. bash implements a language
several times larger than this one, and the gaps under GOALS.md's
"Still open" are real. **Size without conformance is half a
comparison**, which is the whole reason `tests/posix` was built first
and why the two numbers are now recorded next to each other rather
than in separate sections.

The x86-64 build at 273,848 sits between mksh and yash, and that is
structural rather than sloppy: RelF dereferences a cell as a real host
pointer, so cell width must equal pointer width and a 64-bit host pays
double for an image that is mostly small values. The measured
zero-rate by byte position is already recorded in GOALS.md. The
genuinely small build is the i386 one.

### Also updated

`GOALS.md`'s size table was still Iteration 121's and its "for
context" line quoted a `dash` of 121,520 from a different machine
against this machine's 129,784. Both replaced by the table above, with
a pointer to `tests/sizes` so the next reader re-runs it instead of
believing it.

532 assertions across 63 files, 19 differential cases, 1991 core OK
markers on both cell widths, mrsh 20 of 21, posix 3/1/1.
## Iteration 129: where the image bytes actually go, and why Forth
## being "compact" does not make this the smallest shell

The question was why `shell.4` is bigger than `dash` when Forth is
supposed to produce compact code. Measured rather than argued.
`tools/dict-report.4` walks the dictionary and prints header bytes,
body bytes and name for every word; the numbers below are the i386
build, whose 134,500-byte image accounts for 133,772 bytes of
dictionary plus the magic header.

### The Forth system is compact. The application is not.

| | bytes | of image |
|---|---|---|
| Forth kernel (interpreter, compiler, 265 core words) | 13,336 | 10% |
| shell layer: compiled colon-word bodies (353 words) | 77,604 | 58% |
| shell layer: `CREATE ... ALLOT` buffers (55) | 25,968 | 19% |
| dictionary headers - names and link fields (1,069) | 16,400 | 12% |
| `VARIABLE` bodies (365) | 2,920 | 2% |
| `BUFFER:` descriptors (31) | 476 | <1% |

**The compactness reputation holds for the system and fails for the
code.** A complete Forth - outer interpreter, compiler, 265 words - is
13KB against dash's ~120KB of text. That part is real and remarkable.
Everything above it is not compact at all.

### Why the compiled code is not dense: one full cell per token

RelF's threading spends **one cell per operation**: 4 bytes on i386, 8
on x86-64. Against real machine code:

- 77,604 bytes of compiled body = **19,401 cells** = 19,401 tokens.
- `dash` is 21,348 x86 instructions in 115,394 bytes of text =
  **5.41 bytes per instruction** (`objdump -d`, counted, not
  estimated).

So per operation RelF is **4 bytes against x86's 5.41** - a 1.35x
density advantage on i386, and on **x86-64 it is 8 bytes against 5.41,
a 1.5x disadvantage.** That single fact is most of the answer to the
original question, and it explains the 8-byte image being 1.85x the
4-byte one better than any statement about buffers does.

Two things make it worse than the raw ratio suggests:

1. **A Forth token often buys less work than a machine instruction.**
   `DUP`, `SWAP`, `>R`, `DROP` are pure stack shuffling that a
   register-allocating C compiler never emits at all. RelF pays a full
   cell for each.
2. **There is no compression between source and image.** 18,357
   whitespace-separated source tokens produce 19,401 compiled cells -
   almost exactly 1:1. `cross.4` is a transliterator, not an
   optimizer. Nothing is inlined, folded or deduplicated.

Where the "Forth is compact" reputation comes from is 16-bit
threading, where a token is 2 bytes and genuinely halves x86, and from
factoring reducing the *number* of operations. Neither applies here.
GOALS.md's phase 5 already records byte-granular opcodes being
considered and rejected on `CALL`-encoding grounds; this measurement
is the size half of the case that was being weighed there.

### The one piece of pure waste: 16KB for an empty stack

`locals.4` declares `CREATE LSAVE-STACK LSAVE-MAX CELLS ALLOT` with
`LSAVE-MAX` at 4096. That is **16,388 bytes - 12% of the entire i386
image - for a save stack that is empty at save time by construction.**
It is the single largest object in the dictionary by a factor of six.

GOALS.md's memory policy says precisely this: *"Don't hardcode limits,
and don't preallocate. `CREATE name n ALLOT` ... takes dictionary at
compile time, so the space lands in every saved image whether or not
it is ever used."* Iteration 90 raised the limit from 256 cells to
4096 to fix a recursion depth bug, sixteen-fold, and nobody costed it.
The policy was written in Iteration 41 and the violation went in at
90.

### Converting it to `BUFFER:` was measured, and reverted

The obvious fix is `pool.4`'s `BUFFER:`, which puts three cells in the
dictionary and allocates on first use. It works, and it needed one
more change - `pool.4` must load before `locals.4`, and
`tests/locals.fth` includes `locals.4` alone, so that file needed
`pool.4` too. Without it the suite **segfaults** rather than reporting
an undefined word: the failed declaration leaves `LSAVE-STACK`
undefined and every later use compiles a garbage reference.

Then the benchmark, three runs each way, alternating:

| | loop-ms | start-ms | i386 image | x86-64 image |
|---|---|---|---|---|
| `CREATE ... ALLOT` | 862-928 | 394-419 | 134,500 | 251,104 |
| `BUFFER:` | 982-1075 | 487-518 | **118,128** | **218,360** |

**-10.7% image, +13% loop, +22% startup.** i386 total would have gone
152,308 -> 135,936, within 1.05x of dash instead of 1.17x.

GOALS.md predicted exactly this question - *"the ~11K of small hot
buffers still declared with `CREATE`, once it is measured whether
`BUFFER:`'s extra indirection matters on the tokenizer's hot path"* -
and the answer is that it does. `BUFFER:` replaces a constant push
with a `DOES>` body that tests a pointer and branches, on a path taken
on entry to and exit from every locals-using word.

**Reverted, deliberately, and the decision left open.** Landing a 13%
loop regression immediately before Stage 2 of
`PARSE-EXPAND-PLAN.md` - whose entire justification is loop time, and
which needs a clean before/after - would muddy the one measurement
that stage has. Iteration 116 makes the same argument in the other
direction about Stage 1's cost. The size win is real and still
available; it should be taken as its own decision, not smuggled in
under a question about why the image is big.

**The design that gets both**, not attempted here: allocate the stack
once at boot rather than lazily on each access, so the hot path is a
single `VARIABLE` fetch instead of a `DOES>` with an initialization
branch. It cannot be a plain pointer stored in the image - heap
addresses are meaningless after a reload, which is why `BUFFER:`
pointers are scrubbed by `save-system.4` - so it needs boot-time
wiring through `BOOT`. That is an iteration of its own.

### A tracked number that is not what it says

Adding seven lines to `tests/locals.fth` moved "core OK markers" from
1991 to 1998. The suite counts lines beginning `OK`, and the
interpreter prints one per line of stdin it consumes - so the figure
is **lines of test input interpreted without error**, not assertions
passed. It moved by exactly the number of lines added. Still a real
regression signal, since an error breaks the run; not a count of
anything. GOALS.md quotes it as though it were.

### Kept

`tools/dict-report.4`, documented, including the trap that the walk
must terminate on the link *value* being zero rather than the computed
address - the last word's link cell holds 0, so a naive loop walks off
the end of the dictionary into garbage, which is what the first
version did.

No behaviour changed. 532 assertions across 63 files, 19 differential
cases, 1991 core OK markers on both cell widths, mrsh 20 of 21,
posix 3/1/1.
## Iteration 130: what the compiled code is actually made of

`DENSITY-PLAN.md` — three ways to make the image smaller that should
each make it *faster* too, and two large ones that should not be
taken. No code; the options differ in risk by an order of magnitude
and starting with an edit would be the wrong move, same reasoning as
`PARSE-EXPAND-PLAN.md`.

Iteration 129 established that compiled code is 58% of the image and
that RelF spends one cell per operation. This classifies every one of
those cells, using `tools/dict-report.4` extended to dump bodies.

### The 19,506 code cells

| | cells | share |
|---|---|---|
| primitive tokens | 9,122 | 46.8% |
| literal operands | 2,178 | 11.2% |
| call offsets | 8,206 | 42.1% |

**`LIT` is the most frequent primitive in the image**, 2,178 sites and
23.9% of all primitive tokens — and each costs *two* cells, so
literals are 4,356 cells, **22.3% of all compiled code**. 513 of them
push zero. That was the surprise; nothing in the file's shape suggests
that pushing constants is the single largest thing the compiled code
does.

### The rule that separates a good scheme from SOD32's

Worth stating plainly, because it is the answer to "is there anything
left" and it explains a result this project already has:

> **A density scheme is safe when it removes work, and unsafe when it
> adds a decoding step.**

SOD32 packed several opcodes per cell and paid shift/mask/counter work
on every instruction; RelF beat it anyway. `GOALS.md` rejected
byte-granular opcodes here for the same reason from the other
direction — that scheme adds a marker byte and realignment to `CALL`,
the one instruction with zero overhead in the current format.

So the question is not "can the encoding be tighter" but "can it be
tighter *by doing less*". Three answers, all measured:

- **Immediate literals in the token.** The token space is nearly
  empty: primitive tokens are `n*CELL+1`, so `1 mod 4`; call offsets
  are cell-aligned, so `0 mod 4`. **`3 mod 4` is free**, giving a
  three-way discriminator at no cost and a 30-bit payload on i386 —
  four orders of magnitude more than the largest literal in the image
  needs. Saves 2,178 cells, **8,712 bytes on i386**, 17,424 on
  x86-64, and should be *faster*: an immediate is a shift of a
  register already loaded, where `LIT` is a dispatch plus a second
  memory fetch plus an `ip` bump.
- **Superinstructions.** 1,857 adjacent pairs where neither token
  carries an operand; the top 32 cover 1,588 of them. `! BRANCH`
  (163), `@ <` (157), `@ +` (150), `= ?BRANCH` (140). **6,352 bytes**,
  one fewer dispatch per fused pair. Additive: each is one label and
  one table entry appended to `relf.c` and `kernel.4`, the same
  discipline Iterations 120 and 125 used.
- **Headerless words.** 16,400 bytes, **12.3% of the image, at exactly
  zero runtime cost** — headers are read only by `FIND`, at compile
  time. `cross.4` already carries the alternative `"HEADER`, commented
  out. The cost is that `FIND` stops working for those names, so the
  `forth` builtin and interactive use break; it need not be
  all-or-nothing.

All three: **31,464 bytes off i386**, 152,308 -> roughly 121,000,
**below `dash`'s 129,784**, with the speed prediction pointing the
right way.

### Two large options recorded as not-recommended

**A 32-bit code stream on 64-bit hosts** is the biggest lever by far —
code is 62% of the x86-64 image, so halving token width takes ~31% off
it, and it is the direct fix for the 8-byte build being 1.85x the
4-byte one. It also breaks the property `GOALS.md` calls load-bearing,
that a cell is dereferenced directly as a real host pointer, and
complicates `,`/`HERE`/`ALIGN` and every access into a definition
body. Recorded rather than pursued: it is a large change to the
system's identity for the build that is not the small one anyway.

**Variable-length call offsets** would reclaim thousands of cells —
74.7% of offsets fit in 16 bits, 20.5% in 8 — but need assembler
relaxation, iterating to a fixed point because shortening one call
moves every later target. `GOALS.md` already refused that complexity
once when rejecting byte-granular opcodes. Same verdict for the same
reason, now with the numbers that would have tempted it.

### Where the risk actually is

Options 1 and 2 both change what `cross.4` emits, which is where this
project's worst failure mode lives: `cross.4` hand-embeds the
dispatch token numbers for `LIT`, `EXIT`, `BRANCH`, `0BRANCH` and
`R>`, and a stale one segfaults the *next* engine at whatever
primitive lands on the wrong value. Iteration 4's account is the
warning. Both options touch exactly that code, and the mitigation is
`tools/dict-report.4` — check the emitted cells before running
anything.

The predictions here are **predictions**. Nothing in this iteration
was benchmarked; the speed claims follow from counting memory accesses
and dispatches, not from measurement, and are labelled as such in the
plan. Iteration 129's method applies: `tests/sizes` before and after,
`tests/bench` three runs alternating, because a single run on this
hardware proves nothing.

No behaviour changed. 532 assertions across 63 files, 19 differential
cases, 1991 core OK markers on both cell widths, mrsh 20 of 21,
posix 3/1/1.
## Iteration 131: correcting the density numbers, and what longer
## superinstructions are actually worth

`DENSITY-PLAN.md` rewritten. Two options withdrawn on direction, one
replaced by a safer design, and Iteration 130's superinstruction
figures corrected because the decoder was wrong.

### The decoder was wrong, and everything after a branch was noise

130 treated `LIT` as the only primitive consuming an inline operand
cell. `BRANCH` and `?BRANCH` do too, and `S" ..."` compiles to a call
to `(S")` followed by an **inline counted string** which is not tokens
at all. So the cell after every branch was being read as a token
(usually classified as a call offset, since offsets are even), and
every string body was read as a few dozen garbage tokens.

`tools/classify-code.py` now handles all four and accounts for 19,518
of 19,506 body cells. The corrected mix:

| | cells |
|---|---|
| call offsets | 6,986 |
| operand-carrying tokens and their operands | 6,812 |
| plain primitive tokens | 5,445 |
| unclassified (`DOES>`/`CONSTANT` bodies) | 275 |

130's headline - that `LIT` is the most frequent primitive and
literals are ~22% of compiled code - survives. Its *pair table* did
not: entries like `?BRANCH CALL` were `?BRANCH` followed by its own
offset.

### Withdrawn: headerless words

12.3% of the image, and it is not available. Extending the shell in
Forth needs `FIND`, and `FIND` needs headers. That is a requirement,
not a preference, and the 16,400 bytes are what it costs.

### Replaced: tagged immediate literals -> constant-pushing primitives

The objection to tagging is usually "it limits the literal values you
can store". **That is not true**, and it is worth recording as a wrong
reason for a right conclusion: `LIT` would remain as a fallback, so
the compiler emits an immediate only when the value fits and nothing
becomes unrepresentable. The payload would have been 30 bits on i386
against a largest literal in this image of ~127,000.

The two real reasons to drop it: it puts a second test on **every**
primitive dispatch to serve the 24% that are literals, and it changes
`cross.4`'s literal emission - the code holding the hand-embedded
token numbers that segfault the *next* engine when stale.

The replacement gets most of the win with neither cost. **Not one
primitive per hand-picked constant** - that would overfit this image -
but a contiguous block of dispatch-table entries all pointing at one
label that derives the value from the token index. The token stays an
ordinary `n * CELL + 1` primitive, the discriminator is untouched, no
test is added anywhere, `LIT` is the fallback.

Measured, the range matters and the answer is small:

| range | tokens | sites | saves i386 | table |
|---|---|---|---|---|
| `0..15` | 16 | 758 (34.8%) | 3,032 | 64 |
| **`-1..63`** | 65 | **1,140 (52.3%)** | **4,560** | **260** |
| `-16..255` | 272 | 1,219 (56.0%) | 4,876 | 1,088 |
| `-128..1023` | 1,152 | 1,228 (56.4%) | 4,912 | 4,608 |

`-16..255` buys 316 more bytes of image for 828 more of table - a net
loss. Four values (`0`, `-1`, `1`, `2`) are already 40.2% of all
literal sites. Hand-picking the top 128 *individual* values would
reach 84%, because offsets like `44264` recur 51 times, but those
change whenever `shell.4` does; that is a benchmark-specific hack, not
a compiler improvement.

### Longer superinstructions: measured, and worth 1.3%

The interesting result, and it went against expectation. Greedy
selection, patterns cut at branch targets:

| max length | K=16 | K=32 | K=64 | K=128 |
|---|---|---|---|---|
| 2 | 1,855 | 2,336 | 2,656 | 2,927 |
| 3 | 1,879 | 2,345 | 2,687 | 2,951 |
| 4 | 1,879 | 2,349 | 2,689 | 2,951 |
| 6 | 1,879 | 2,362 | 2,700 | **2,965** |

*(cells saved)*

**Searching up to six tokens beats pairs-only by 1.3%**, because
iterated pair fusion *composes*. Once `LIT = ?BRANCH` is a token,
`DUP` + that + `DROP` is a pair again and fuses next round - the
greedy output contains `DUP <LIT+=+?BRANCH> DROP` at 59 sites,
discovered as a pair of pairs.

So the implementation needs to recognise **two adjacent tokens only**,
run to a fixed point. Triples and longer arrive with no n-gram
machinery. That is a large simplification bought by measuring
something that looked like it needed a general answer.

At K=128, 2,927 cells is 11,708 bytes on i386 and 23,416 on x86-64.

### The counterweight nobody had counted

Each superinstruction is a table entry **and a body in the engine**.
The table is K*CELL; the bodies are plausibly 30-80 bytes each, so
K=128 is perhaps 4-10KB of engine growth against 11,708 saved. Still
positive, and the margin narrows fast enough that it must be measured
per K rather than assumed. **Size and speed diverge**: more
superinstructions always removes more dispatches, so speed keeps
improving while net size peaks and turns.

### Order

A then B, and they are not additive: `LIT 0 =` is three cells now, two
after A, one after B. A changes the stream B selects over, so the K
table must be regenerated between them.

Combined, before engine growth: ~15KB off i386, 152,308 toward
~137,000. That does not reach `dash` at 129,784, which is the honest
position - `FIND` costs 16,400 bytes and is worth more than the
ranking.

### Kept

`tools/classify-code.py` and `tools/superinstr-search.py`, both
documented, including the four not-token cases that made 130 wrong.

No behaviour changed. 532 assertions across 63 files, 19 differential
cases, 1991 core OK markers on both cell widths, mrsh 20 of 21,
posix 3/1/1.
## Iteration 132: two tag bits, and where `LIT` goes

A better use of the tag space than Iteration 131 proposed, and it
came from outside: use the low **two** bits to select four classes -
`CALL`, `PRIMITIVE`, `BRANCH`, `0BRANCH` - instead of one bit
selecting two.

    t & 3 == 0   CALL       ip += t                (unchanged, free)
    t & 3 == 1   PRIMITIVE  goto *dispatch[t >> 2]
    t & 3 == 2   BRANCH     ip += (t & ~3)
    t & 3 == 3   0BRANCH    if (TOS) ip += CELL else ip += (t & ~3)

**The branch offset moves into the branch cell.** `BRANCH`/`?BRANCH`
are ordinary primitives today, each followed by an offset cell.
Measured: **1,228 branch sites, 4,912 bytes on i386, 9,824 on
x86-64** - the largest single density win found so far, and it needs
no new primitives and no engine growth at all.

Verified against the image rather than assumed: every branch offset is
4-aligned as the scheme requires, and the largest is 2,216 against a
30-bit payload reaching ±536,870,912.

**Two bits is the right width, not three.** More tag bits are
available if payloads are shifted - offsets are cell-aligned and
primitive indices are tiny - but a shift on `CALL`, the most common
class at 6,986 cells, is exactly the "adds a decoding step" mistake
this whole line of work is organised around. Two bits keeps `CALL`
free.

Side benefit worth recording: primitive tokens become `idx * 4 + 1` on
every host instead of `idx * sizeof(void*) + 1`, decoupling the token
stride from pointer width. `GOALS.md` flags that coupling as a hazard,
since `cross.4`'s hand-embedded token numbers must change whenever the
stride does.

### Where `LIT` goes: nowhere, and that is fine

All four tags are spent, so the question was what to do with `LIT`.
Three options, measured:

1. **Leave it a primitive, and shrink its frequency with a constant
   block inside the primitive index space.** The payload is 30 bits
   and real primitives need seven, so indices above the last one are
   free; a contiguous run of them all point at one shared label, so
   **no test is added to any path**. Block width is a real
   optimisation - each entry costs `CELL` of table and buys `CELL` per
   site covered - and scanning every contiguous range gives an optimum
   at **`-1..96`: 1,189 of 2,178 sites (54.6%), 4,756 bytes gross, 392
   of table, 4,364 net.** The curve is flat from about `-1..48` to
   `-1..128`.
2. **Widen past the table with a bounds test.** Reaches every literal,
   but puts a test on the hot path to serve the tail. Rejected.
3. **Merge the two branch classes to free a tag for a full 30-bit
   immediate.** Covers *every* literal: 2,178 cells, 8,712 bytes on
   i386, nearly double option 1. The price is that `BRANCH` and
   `0BRANCH` must then be distinguished by a bit taken from the
   payload, so branch offsets need a shift on decode.

Option 3 is +4,348 bytes on i386 for one shift on the branch path.
**Rejected anyway**: branches are hot in exactly the loops
`tests/bench` measures at 236x `dash`, and the principle is that
density must not buy itself with decoding work. Recorded with its
number so it can be revisited if the loop benchmark stops being the
constraint.

### The schemes are not additive, and this was the surprise

Folding branches **removes most of what superinstructions had to
offer**. Greedy pair fusion to a fixed point:

| stream | K=32 | K=128 |
|---|---|---|
| today | 2,336 | 2,927 |
| branches folded (branch patterns excluded) | 1,774 | 2,161 |
| branches folded + constant block | 1,691 | **2,116** |

Once a branch carries its own offset, fusing `X BRANCH` gains nothing:
`X` + `BRANCH|off` is two cells and `<X+BRANCH>` + `off` is also two.
**Seven of the ten best fusions in Iteration 131's table ended in a
branch.** Had these been implemented in the other order, the second
one would have looked like a failure.

### Total, and the honest shortfall

| | cells | i386 | x86-64 |
|---|---|---|---|
| branch folding | 1,228 | 4,912 | 9,824 |
| constant block `-1..96`, net of table | 1,091 | 4,364 | 8,728 |
| superinstructions K=128 | 2,116 | 8,464 | 16,928 |
| **total** | **4,435** | **17,740** | **35,480** |

i386 image 134,500 -> ~116,760, total 152,308 -> **~134,568 against
`dash`'s 129,784**. Short by about 4,800, and the 16,400 bytes that
would have closed it are the dictionary headers `FIND` needs. That
trade was made deliberately and this is what it costs.

Order: **encoding, then constant block, then re-run the fusion search
and pick K against measured engine growth.** The encoding is largest,
needs no new primitives, and moves the stream everything else is
measured against.

No behaviour changed. 532 assertions across 63 files, 19 differential
cases, 1991 core OK markers on both cell widths, mrsh 20 of 21,
posix 3/1/1.
## Iteration 133: how the branch merge would work, and why not to do it

Iteration 132 rejected "merge `BRANCH`/`0BRANCH` to free a tag for
literals" in one sentence. Written out properly, the mechanics point
at a better scheme, so the rejection was right and the reasoning was
not.

### The merge, in full

Two branch kinds need one bit to separate them, and under a 2-bit tag
there is no spare: bits 0-1 are the tag and bit 2 already belongs to
the offset. The bit must be manufactured by storing the offset shifted
left one place. An offset is a multiple of `CELL`, so `offset << 1`
has three clear low bits and bit 2 becomes available:

    t      = (offset << 1) | (kind << 2) | 2
    kind   = (t >> 2) & 1
    offset = (t & ~7) >> 1          \\ arithmetic, to keep the sign

Tag `11` is then a 30-bit signed immediate covering every literal in
the image. The cost is `(t & ~7) >> 1` instead of `t & ~3` on the
branch path.

### The better move: don't merge, drop `BRANCH` from the tag space

Nothing requires the four tags to be spent on the four things that
look symmetric. `0BRANCH` is 863 sites and `BRANCH` only 365 - and
`BRANCH` is the one superinstructions can still fuse, because keeping
it a primitive keeps its operand cell:

    t & 3 == 0   CALL       ip += t
    t & 3 == 1   PRIMITIVE  goto *dispatch[t >> 2]     \\ BRANCH lives here
    t & 3 == 2   0BRANCH    if (!pop()) ip += (t & ~3)
    t & 3 == 3   LITERAL    push((INT)t >> 2)

No shift on any branch path, no constant-block table, no bounds test,
and `LIT` survives in primitive space as the fallback for a literal
wider than 30 bits, so nothing becomes unrepresentable.

Measured, each with its own K=128 fusion pass re-run on its own stream:

| | folding | literals | fusion | total | i386 |
|---|---|---|---|---|---|
| both branches tagged + constant block `-1..96` | 1,228 | 1,091 | 2,130 | 4,449 | 17,796 |
| **`0BRANCH` tagged, `BRANCH` primitive, full immediates** | 863 | **2,178** | **2,331** | **5,372** | **21,488** |

**+923 cells, +3,692 bytes on i386, +7,384 on x86-64.** Surrendering
365 cells of `BRANCH` folding buys 1,087 more of literal and 201 more
of fusion - the second of those because full immediates delete every
literal operand cell that was interrupting a fusable run.

This also retires the constant block entirely. Iteration 132 spent an
optimisation scan finding `-1..96`; with a whole tag for literals the
question does not arise.

### What it gives up, stated plainly

An unconditional `BRANCH` closes every loop. Under this scheme it
stays two cells with a memory load, exactly as today - no regression,
but no gain, where tagging both branches would have removed one load
per iteration. `?BRANCH` is folded either way, so the difference is
one load per loop iteration, on the benchmark this project is 236x
`dash` on.

Small, real, and not decidable from a table: **build both and run
`tests/bench` three times alternating.** The size difference is
certain and the speed difference is not, which is the opposite of how
this normally goes here.

### The pattern worth keeping

Three iterations running, an encoding question has been answered
better by rearranging what occupies the tag space than by finding
more bits: 131 wanted a fifth class, 132 got four by using two bits,
133 gets more out of four by not spending them symmetrically. The
scarce resource is not bits, it is decoding steps.

No behaviour changed. 532 assertions across 63 files, 19 differential
cases, 1991 core OK markers on both cell widths, mrsh 20 of 21,
posix 3/1/1.
## Iteration 134: keep the dispatch loop, put the payload above the index

Iterations 132 and 133 both spent the low bits on a tag, and both add
a **second data-dependent test** to the two hottest paths. That is a
real cost against a dispatch loop whose entire virtue is having one
test, and the objection came from outside before it came from here.

The observation that removes it: **the primitive index field is nearly
empty.** There are 68 primitives and room for billions. So put the
payload *above* the index instead of beside the tag, and let the
existing dispatch table do the work.

    bits [31..12]  payload (signed)   -524,288 .. 524,287
    bits [11..2]   primitive index    1024 slots
    bits [1..0]    01 primitive, 00 call

Three reserved indices carry a payload; every other primitive leaves
it zero. `LIT` carries the value, `BRANCH` and `0BRANCH` the byte
offset.

### The loop, which is the point

```c
#define NEXT() do { \
        t = CELL(ip); ip += CELL_BYTES; \
        if (t & 1) goto *dispatch[(t >> 2) & IDX_MASK]; \
        RPUSH(ip); ip += t; \
        goto next; \
    } while (0)
```

against today's

```c
        if (t & 1) goto *dispatch[(t - 1) >> CELL_SHIFT];
```

**One test, one indirect branch, exactly as now.** An `and` replaces a
`sub`. Both single-cycle, neither a branch. `CALL` is untouched.

The three handlers get *shorter*, because the operand arrives in a
register instead of a second memory read:

```c
L_lit:     PUSH((UNS64)TOK_PAY(t)); NEXT();        /* was: PUSH(CELL(ip)); ip += CELL_BYTES; */
L_branch:  ip += TOK_PAY(t); NEXT();               /* was: ip += CELL(ip); */
L_0branch: dsp += CELL_BYTES; if (!old) ip += TOK_PAY(t); NEXT();
```

So there is **no case where the interpreter does more work than
today**. That is the test this whole line of work applies, and this is
the first option to pass it outright rather than on balance.

### It is also the biggest

All three operand-carriers fold, not just the ones a tag could reach:

| | cells |
|---|---|
| `LIT` -> immediate | 2,178 |
| `0BRANCH` -> folded | 863 |
| `BRANCH` -> folded | 365 |
| superinstructions K=128 on the resulting stream | 2,161 |
| **total** | **5,567** |

**22,268 bytes on i386, 44,536 on x86-64**, against 17,796 for the
four-tag scheme (132) and 21,488 for the `0BRANCH`-tagged variant
(133) - and with a simpler dispatch loop than either.

It also retires the constant block. Iteration 132 spent a scan over
every contiguous range to find `-1..96`; a 20-bit immediate covers all
2,178 sites with no table, so the question stops existing.

### Ranges checked, not asserted

`IDX_BITS = 10` gives a 20-bit signed payload, -524,288..524,287,
against measured maxima of **127,404** for a literal and **2,216** for
a branch offset. 1,024 primitive slots against 68 today plus K=128
superinstructions = 196.

`tools/encoding-roundtrip.c` encodes and decodes every primitive
index, both payload extremes, and negatives, and is built `-m32` so
the narrow cell is what is tested. It passes. Sign extension through
an arithmetic shift is the part that would have failed silently.

`IDX_BITS` is the one knob: a bit of index costs a bit of payload.
`LIT` stays available as a two-cell primitive for any literal too
wide, so **nothing becomes unrepresentable** - the compiler picks the
short form when it fits, which was the objection to tagging in the
first place and is now answered by construction.

### Where this leaves the total

i386 image 134,500 -> ~112,232; total 152,308 -> **~130,040 against
`dash`'s 129,784.** Level, near enough, and without giving up `FIND` -
which two iterations ago looked like it cost 4,800 bytes of ranking.

### The pattern, four for four

131 wanted a fifth class. 132 got four classes from two bits. 133 got
more from four by not spending them symmetrically. 134 gets more than
all of them by not using a tag at all. Every step came from
rearranging what occupies the encoding rather than finding more room
in it, and the last one came from someone pushing back on complexity
rather than on size.

No behaviour changed. 532 assertions across 63 files, 19 differential
cases, 1991 core OK markers on both cell widths, mrsh 20 of 21,
posix 3/1/1.
## Iteration 135: a review of `shell.4` for size, and a decoder bug it found

Asked to find duplicated logic and non-compact algorithms in
`shell.4` before touching the engine. The short answer is that **there
is no duplicated-logic problem**, and the savings that do exist are in
repeated *idioms* rather than repeated *code*.

### First, a bug in the analysis tooling

The duplication scan printed `CALL:?` for every call target. Call
offsets are relative to the cell **after** the call cell - `relf.c`
does `RPUSH(ip); ip += t` with `ip` already advanced - and
`tools/classify-code.py` was resolving `a + offset` instead of
`a + CELL + offset`. Checked empirically rather than by reading:
`a+off` lands on a known body start 0.2% of the time, `a+CELL+off`
41.9%.

The consequence was not cosmetic. Because no target resolved, the
inline-string skip never fired, so **every `S" ..."` body was read as
tokens.** 644 cells of string text were being counted as 410 calls, 15
primitives and 219 unclassified.

Re-ran everything downstream. **Iterations 131-134 survive**: the
operand-carrier counts come from primitive token values, and `op` is
still 6,812 - `LIT` 2,178, `BRANCH` 365, `0BRANCH` 863 - so the 3,406
cells of folding and the K=128 fusion figure of 2,161 are unchanged.
Third time in this session that a decoder assumption has been wrong
and the numbers happened to survive; the pattern is that
**tokenization bugs are silent**, and the only defence is resolving
something and checking the hit rate.

### There is no duplicated logic

Normalised source clone detection over 4,002 code lines: **95 lines
recoverable across the ten largest clones, 2.4%**, and most of that is
structural `THEN` / `EXIT` / `THEN` noise that is not logic at all.
The largest genuine clone is 11 lines appearing twice. For a
7,000-line file grown over 130 iterations that is a good result, and
it means the premise that `shell.4` might be copy-paste bloated does
not hold.

Compiled-sequence detection agrees: after the decoder fix, the best
factorable repeat is 5 tokens at 44 sites, worth 170 cells. Nothing
structural.

### What is actually there: idioms, not clones

**1. The locals prologue and epilogue are open-coded at every site.**
`LRESTORE` is **the most-called word in the entire shell** (487
sites), `LSAVE` is third (227), and each is always preceded by a
literal address - so a word with three locals emits six cells at
entry and six at each exit. 68 words use locals, 3.3 locals each,
~2.1 exit points each.

    open-coded now             1,428 cells   5,712 B
    one address list per word     723 cells   2,892 B
    saving                        705 cells   2,820 B

The list is stored once per word and `LSAVE-ALL` / `LRESTORE-ALL`
walk it. **This is a change to `locals.4`, not to `shell.4`** - one
file, one mechanism, 68 words improved without editing any of them,
which is the best risk-to-reward on this list by a wide margin.

Caveat: it replaces straight-line code with a loop, on a path taken at
every entry to and exit from a locals-using word. Same shape as
Iteration 129's `BUFFER:` result, which cost 13% on the loop
benchmark. **Measure it.**

**2. `VAR @ 1+ VAR !` appears 232 times over 102 variables.** A `1+!`
word makes each site two cells instead of five: **696 cells, 2,784
bytes.**

Worth noting why superinstructions do not already get this: `1+` is a
colon word here, not a primitive (`kernel.4` line 336), so `@ 1+` is a
primitive followed by a *call* and fusion cannot span it. Checked
rather than assumed - `('@','1+')` is not among the 128 pairs greedy
selection picks. So this saving is real and additive to Option B
rather than overlapping it.

**3. `VAR @ VAR @ <` appears 132 times** over 63 distinct pairs
(`TOK-POS/TOK-END` 24, `AE-POS/AE-END` 17). A two-address comparison
word saves 2 cells each: ~264 cells.

**4. Ten linear `STR=` chains**, e.g. `REDIR-OP-AT` testing seven
operator strings in sequence at ~11 cells per arm. Table-driven with a
counted table and a loop would save perhaps 40 cells each, ~400 total
- the only item here that is genuinely an *algorithm* rather than an
idiom, and the one with the worst complexity-to-saving ratio.

### Totals, and the recommendation

| | cells | i386 |
|---|---|---|
| locals address lists | 705 | 2,820 |
| `1+!` | 696 | 2,784 |
| two-address comparison | 264 | 1,056 |
| `STR=` chains to tables | ~400 | ~1,600 |
| **total** | **~2,065** | **~8,260** |

About **6% of the image**, against the encoding change's 3,406 cells
on its own.

**Recommendation: do the locals change, skip the rest for now, and
proceed to the encoding.** The locals work is one file and improves 68
words without touching them. Items 2-4 are 400-odd edits spread
through working shell code that currently passes the whole mrsh suite,
for 1,360 cells - a poor trade against an encoding change that is
larger, confined to `relf.c` and `cross.4`, and needs no edits to
`shell.4` at all.

The file was asked to be made smaller and the honest finding is that
it is already about as factored as it is going to get by hand. The
remaining density is in the encoding, which is where the next work
should go.

No behaviour changed. 532 assertions across 63 files, 19 differential
cases, 1991 core OK markers on both cell widths, mrsh 20 of 21,
posix 3/1/1.
## Iteration 136: every buffer out of the image

`CREATE name n ALLOT` reserves *dictionary*, so the space lands in the
saved image whether or not it is ever used. 55 of them were left in
`shell.4` and `locals.4`, 25,968 bytes, including `LSAVE-STACK` at
16,388 - the one Iteration 129 measured, converted, and reverted
because `BUFFER:` cost 13% on the loop benchmark.

**All 55 are now `BUFFER:`, and the loop cost is gone.** i386 image
**134,500 -> 109,576**, total 152,308 -> **127,384, below `dash`'s
129,784.** x86-64 251,104 -> 205,976.

### Why it is affordable now and was not in 129

`BUFFER:` allocated lazily and kept its pointer at descriptor offset
+2, so **every reference** ran a store, three fetches, an add and a
branch - about ten threaded operations where a `CREATE`d name costs
one. On the tokenizer's hot path that is what the 13% was.

Two changes make it a fetch:

- **Pointer moved to offset +0**, so the accessor is `DOES> @`.
- **Allocation is eager**, at declaration, so there is no
  initialisation test on the reference path at all. `RESET-BUFFERS`
  already zeroed every pointer before a save; the new `ALLOC-BUFFERS`
  gives them their space again at boot, called first thing in `MAIN`
  because nothing may touch a buffer before it runs.

Measured: loop 939-1,256ms against a 925-1,239 baseline on the same
machine in the same session. Neutral.

### A startup regression, and where it came from

Startup went 440 -> 1,065ms, and the cause was not the buffers
themselves: **`FILL` is a per-byte threaded loop** (`kernel.4` line
589). `CREATE ... ALLOT` space starts zeroed so the pool must match,
and zeroing ~34KB of buffers at every boot was ~34,000 threaded
iterations.

`BUF-ZERO` does it a cell at a time, with the allocation rounded up to
a whole cell so it cannot overrun. 1,065 -> ~490ms. The residue over
440 is the ~80 `ALLOCATE` calls plus what is left of the zeroing, and
the real fix is a `FILL` primitive - a memset one-liner that would
help everything, not just boot. Left for the engine work rather than
smuggled in here.

### The load order changed

`pool.4` must now load before `locals.4`, so `relfsh` and
`tests/locals.fth` both changed. Loading `locals.4` alone **segfaults**
rather than reporting an undefined word: the failed declaration leaves
`LSAVE-STACK` undefined and every later use compiles a garbage
reference. Same trap Iteration 129 hit; written into `tests/locals.fth`
this time so the next person meets a comment instead of a crash.

### Verified

Both cell widths, 1998 core OK markers, 532 assertions across 63
files, 19 differential cases, mrsh 20 of 21, posix 3/1/1.
## Iteration 137: one LENTER and one LEXIT instead of three cells per local

The locals prologue and epilogue were open-coded. `L-EMIT` compiled a
two-cell literal plus a call for **every local at every entry and
every exit** - `LRESTORE` was the most-called word in the whole shell
at 487 sites, `LSAVE` third at 227, plus 129 `LZERO` and 98 `L!`.
941 sites x 3 cells = **2,823 cells, 14.5% of all compiled code**,
saying the same thing over and over.

Now a definition compiles **one** call to `LENTER` followed by an
inline descriptor - count, argument count, one START-relative offset
per name - and **one** call to `LEXIT` at each exit. `LENTER` steps
over its own descriptor with `R>` / `>R`, the trick `(S")` already
uses for an inline string.

`LEXIT` takes no descriptor at all, because `LENTER` pushes each
slot's **offset alongside its saved value** and then the count. An
epilogue is therefore a single cell however many locals a word has,
which is where most of the saving is: exits outnumber entries about
two to one.

    i386 image   109,576 -> 101,104   (-8,472)
    i386 total   127,384 -> 118,912
    x86-64 image 205,976 -> 189,024

### It costs 42% on the loop benchmark

Measured three runs each way, alternating, on the same machine:

| | loop-ms | start-ms | i386 total |
|---|---|---|---|
| Iteration 136 | 939-1,256 | 477-496 | 127,384 |
| with `LENTER`/`LEXIT` | 1,338-1,389 | 491-498 | **118,912** |

**Committed separately from 136 for exactly this reason** - `git
revert` this one commit returns the 42% and keeps every byte of the
buffer work, which is 74% of the combined saving and free.

The first version was worse: **2.1x**, from `LPUSH`/`LPOP` helper
calls and an `LE-OFF` accessor inside the loops. Flattening both words
- one overflow check per frame rather than per local, running pointers
instead of index-times-`CELLS`, no calls inside a loop - took it to
1.42x. The remainder is structural: a frame is now `2n+1` cells rather
than `n`, because carrying offsets is what makes the epilogue one
cell, and `DO`/`LOOP` overhead replaces straight-line code.

`LSAVE-MAX` is unchanged at 4096, so the depth limit halves to 2048
cells of locals - still far past anything `shell.4` reaches.

### The judgement

`GOALS.md` goal 3 puts minimalism above raw performance, which argues
for keeping it. Iteration 129's precedent argues the other way: do not
land a loop regression immediately before Stage 2 of
`PARSE-EXPAND-PLAN.md`, whose whole justification is loop time and
which needs a clean before-and-after.

Landed, because the size win is large and the revert is one commit -
but **re-baseline `tests/bench` before starting Stage 2**, and treat
1,365ms rather than 960ms as the number Stage 2 is measured against.

### Verified

Both cell widths, 1998 core OK markers, 532 assertions across 63
files, 19 differential cases, mrsh 20 of 21, posix 3/1/1.
## Iteration 138: the size comparison was mixing word sizes

`tests/sizes` ranked the **i386** `shell.4` build in one table with
the distro's **x86-64** `dash`, `bash` and the rest, and Iteration 137
concluded from it that `shell.4` was the smallest shell on the list.
That was not a comparison, and the objection came from outside before
it came from here.

### Fixed by building the comparators, not by adding a caveat

Ubuntu ships no i386 shells - general i386 support ended after 19.10 -
so they had to be built. `tools/build-shells-i386.sh` enables
`deb-src`, fetches the Debian sources and builds `dash` and `posh` at
`-m32`, **and builds each for x86-64 from the same source with the
same flags**. A locally built 32-bit binary against a distro-built
64-bit one just swaps one unfair comparison for another.

The check that the build is representative: this machine's x86-64
`dash` comes out at **129,832** against the distro's **129,784**, 48
bytes apart.

(`mksh` is absent. Its build asserts on `-m32` - "Use the documented
way to build this" - and it was not worth fighting for one more row.)

### The honest result, both ways

*x86-64, the word size this machine actually runs:*

    dash        129,784
    posh        149,352
    shell.4     211,768      <- 1.63x dash
    mksh        310,312
    bash      1,654,352

*i386:*

    shell.4     118,912      <- 0.87x dash
    dash        136,936
    posh        163,308

**Both claims are now stated, and the unflattering one first.** On the
architecture that matters for a modern machine this is not the
smallest shell and is not near `dash`. On i386 it is smaller than
either comparator.

### The finding that saves the i386 claim

**Both comparison shells are LARGER at 32 bits than at 64** - `dash`
136,936 against 129,832, `posh` 163,308 against 149,336, same source,
same flags, same compiler. x86-64 code is not much bigger than i386
code, the extra registers cut spills, and i386 position-independent
code pays for GOT setup.

That was worth measuring rather than assuming, and it cuts the
obvious objection: the i386 result is not an artifact of comparing
against a bloated 32-bit build. It holds against the fairest
comparator obtainable.

It also sharpens what `GOALS.md` already says about RelF's own 1.85x
between widths. Real machine code barely grows from 32 to 64 bits;
**a threaded-code image nearly doubles**, because every token is a
cell and a cell must be a host pointer. The gap between those two
facts is the whole of `DENSITY-PLAN.md`'s case, and it is larger than
it looked when the comparison was against a single 64-bit `dash`.

### `tests/sizes` now cannot make this mistake again

Two tables, one per word size, and nothing is ranked across them. The
i386 table prints an explicit note when no comparators are present -
"the 64-bit table above is the honest one" - rather than silently
listing `shell.4` alone and inviting the reader to compare upward.
`build/` is gitignored; the binaries are reproducible from the script
rather than committed.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 3/1/1.
## Iteration 139: reading the field, after designing without it

`VM-RESEARCH.md`. `DENSITY-PLAN.md` reached its design by measuring
this image alone. Reading the published work afterwards confirms three
of its conclusions, **overturns an assumption in `GOALS.md`**, and
turns up one structural option nobody here had considered that is
probably larger than the whole plan.

### Confirmed, with a caution the plan did not have

Proebsting's superoperators (POPL 1995) and Ertl's *Threaded Code
Variations* (EuroForth 2001) are the sources. Ertl measured
superinstructions in Gforth at **up to 2x on large benchmarks**, from
**fewer mispredicted indirect branches** rather than from fetching
less memory - and only 1.38x against 1.86x on a processor without a
branch target buffer.

The caution: **more superinstructions eventually made things slower**,
on a machine with a small direct-mapped instruction cache, from
conflict misses. `DENSITY-PLAN.md` says to measure engine growth per
K; it should also measure *speed* per K, because that curve can turn
first. 800 superinstructions also needed ~100MB to build and 1600
needed ~300MB and 1.5 hours, which is its own argument against the
K=128 end of the range.

### Ertl's negative size result does not apply to us, and the reason matters

Ertl concluded superinstructions did **not** reduce Gforth's code size
overall. That reads as fatal until you see why: to make them widely
applicable, Gforth first had to move from indirect threading to a
**primitive-centric** scheme, and that growth outweighed what
superinstructions recovered.

**RelF has been primitive-centric since Iteration 2** - a call is one
cell of relative offset, there are no code fields in the threaded code
at all. We take the saving without the entry fee. Ertl even names
eliminating code fields and switching to byte code as what might
change the picture; this project did the first years ago.

### Factorization: our 6% is the right number, not a disappointing one

Clausen et al. (TOPLAS 2000) factor repeated JVM sequences into macro
instructions and measure footprint down to **~85% of original**.
Iteration 135 found only ~6% available here. The explanation is in
Ben Hoyt's *nibbleforth* notes, in one line worth stealing:
programmers who factor into small words are running a dictionary
compressor by hand. `shell.4` is written that way; Clausen's 15% is
what you get when the source was not.

### Settled against a direction we might have drifted toward

Shi, Casey, Ertl and Gregg (TACO 2008) measured register VMs at **46%
fewer executed instructions for 26% larger bytecode.** For goal 3 that
is a closed question in the wrong direction. Recorded so nobody spends
an iteration rediscovering it.

### The assumption that was wrong

`GOALS.md` rejected byte-granular opcodes because `CALL` - which has
**zero** encoding overhead today, the offset being the instruction -
would need a marker byte and realignment. `DENSITY-PLAN.md` promoted
that into a principle: safe schemes remove work, unsafe ones add a
decoding step.

The principle stands. The **quantity** was a guess. Latendresse and
Feeley (SCP 2005) decode canonical-Huffman opcodes with custom-sized
operand fields directly during execution, no prior decompression, and
measure **~9% average slowdown for 30-60% compression** - noting that
earlier work had *assumed* this was too slow and that the assumption
did not survive testing.

Nine percent is a fifth of what Iteration 137's locals change cost,
for several times the saving.

### The option nobody here had considered: token threading

The largest finding, and it dissolves the objection above rather than
arguing with it.

RelF spends a **full cell on every call**, because a call *is* an
offset - 6,576 cells, 34% of compiled code, 8 bytes on x86-64 to name
one of about 620 words. In **token threading** a call is an *index*
into a table of addresses. 620 words needs 10 bits. The "a byte scheme
must widen CALL" objection applies to an offset and **not to an
index**.

*nibbleforth* works this out for Forth: nibble-granular variable-length
opcodes, most frequent words in 4 bits and the next tier in 8,
assigned by frequency analysis of the actual program, with token
threading so **user-defined words get short codes too**. Its reported
frequency profile - `exit` dominant, branches next - is close to this
image's own (`EXIT` 647, `LIT` 2,178, `?BRANCH` 863, `BRANCH` 365).
Lefurgy et al. (MICRO-30 1997) is the hardware precedent; Thumb-2,
MIPS16 and RISC-V's C extension are the shipped ones.

Rough estimate on this image's census, one byte for primitives and
small values, two for calls and wider operands: **~26,000 bytes
against 78,024 on i386 and 156,048 on x86-64.** Roughly **3x on i386
and 6x on x86-64** - and the second number is the point, because **a
byte stream does not scale with cell width at all.** Iteration 138
established that the x86-64 build at 1.63x `dash` is this project's
real size problem. This is the only idea found that addresses it.

### A speed lever that could fund the rest

CPython 3.14 replaced computed-goto dispatch with **tail calls**,
reported at ~10% on 64-bit platforms. The mechanism is the
interesting part: one enormous function defeats the compiler's
register allocation, and compilers **merge the identical `DISPATCH`
tails**, destroying exactly the per-opcode indirect branches that give
the predictor context. Separate functions stop the merging, and
CPython's own analysis attributes most of the gain to that alone.

**`relf.c` is precisely that shape** - one function, `NEXT()`
replicated at every primitive, built with GCC. A speed lever
independent of size, which is what makes it worth having: it could pay
for the density work rather than compete with it. The LWN account is
worth reading for the caveats - early measurements were inflated and
part of the apparent gain was a GCC regression rather than a speedup.

### What this says about method

Three of the seven conclusions - reopening variable-length encoding,
token threading, tail-call dispatch - were **not reachable by
measuring this image**, and each is larger than anything currently in
`DENSITY-PLAN.md`. Measuring before proposing is the right rule and
this project has been well served by it; it does not substitute for
finding out whether the question has already been answered. Read the
field earlier next time.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 3/1/1.
## Iteration 140: three experiments from the literature review, two decisive

`VM-RESEARCH.md` ended with seven recommendations. Three of them were
cheap enough to test without touching the system, so they were tested
rather than scheduled.

### 1. Dispatch-site replication: a clean NEGATIVE result

CPython 3.14's tail-call interpreter is reported at ~10%, and its own
analysis attributes most of that to stopping the compiler **merging
the identical `DISPATCH` tails**, which destroys the per-opcode
indirect branches the predictor needs. Ertl's 2001 superinstruction
speedups rest on the same mechanism.

Checked first, because it is one `objdump`:

    $ objdump -d relf | grep -c 'jmp *(%r'
    5

**Five dispatch sites in the binary for 68 primitives.** GCC had
merged almost all of them, exactly as described.

Fixing it needs no restructuring - a unique zero-cost marker makes the
tails textually different so they cannot be merged:

    __asm__ volatile ("# dispatch %c0" :: "i"(__LINE__));

That took the binary from **5 to 66** dispatch sites, at +4KB of
engine. And it bought **nothing**:

| | loop-ms, 5 runs |
|---|---|
| merged (5 sites) | 1351 1347 1355 1352 **1336** |
| unmerged (66 sites) | 1358 1390 1357 1354 **1330** |

A pure dispatch-bound Forth loop agrees: 985-1002ms against
993-1005ms.

**The classic advice does not pay on this hardware.** Ertl's result is
2001 branch target buffers; this is an Intel Xeon at 2.10GHz, whose
indirect predictor evidently handles one branch with history as well
as 66 with context. Recorded because it also **substantially devalues
the tail-call interpreter experiment** - if replicating the dispatch
gains nothing, most of CPython's reported mechanism is not available
here either.

### 2. Byte-granular token threading: measured, and it is the answer

Two measurements, one for each half of the question.

**Size**, by re-encoding the real token stream rather than estimating:
15,420 operations, 1,119 distinct symbols, 817 distinct call targets.
A two-tier byte encoding - one byte for the 128 most frequent symbols,
which cover **77.2%** of the stream, two bytes for the rest - gives:

    23,969 bytes  against  78,024 (i386)  and  156,048 (x86-64)
    = 3.26x on i386, 6.51x on x86-64

For reference the Huffman entropy floor on the operation stream is
13,778 bytes against the two-tier scheme's 18,937, so **two-tier
captures most of what is there** and full Huffman would buy perhaps
20% more for a great deal more decoding machinery. That settles
Latendresse and Feeley's technique as interesting but not necessary.

**Speed**, by `tools/dispatch-bench.c` - both encodings dispatched
through a computed goto, doing identical work, on the measured
operation mix:

| | x86-64 | i386 |
|---|---|---|
| cell + table call | 32.2 / 34.9 ms | 42.2 / 43.2 ms |
| **cell + offset call (RelF today)** | **30.4 / 33.3 ms** | **38.8 / 40.0 ms** |
| **byte stream** | **31.3 / 32.6 ms** | **39.5 / 39.7 ms** |

**byte / cell-with-offset-call = 0.98 to 1.03.** Within noise. The
byte stream fetches about five times less memory, which pays for the
extra byte load on the two-byte forms.

The third row is the one that matters and it was missing from the
first version of this benchmark. Token threading **gives up RelF's
cheapest property** - a call today is `RPUSH(ip); ip += t`, no lookup
at all - so the comparison had to include a variant that keeps it.
It does, and the byte stream still matches it.

**The first version of this benchmark reported the byte stream 5x
slower.** It gave the byte encoding an if/else comparison chain and
the cell encoding a short one - an artifact of the harness, not the
encoding. Kept in the file's comments as a warning: a microbenchmark
that confirms the expected answer is the one to distrust, and this one
confirmed `GOALS.md`'s existing position before it was fixed.

### What this changes

`GOALS.md` rejected byte-granular encoding because `CALL` would need a
marker byte and realignment. That objection is about an **offset**.
Token threading makes a call an **index** - 817 targets, ten bits - and
the objection does not apply. Iteration 139 found the idea; this
iteration measured both halves of it:

- **3.26x smaller on i386, 6.51x on x86-64**, on the real stream.
- **No measurable dispatch cost**, on this hardware, against the
  current offset-call.

Projected: i386 image 101,104 -> ~47,000, total ~65,000. x86-64 image
189,024 -> ~57,000, total ~80,000. Both **well under `dash`** at
129,832, and it is the x86-64 number that matters, because Iteration
138 established that is where this project is actually behind.

That is larger than everything in `DENSITY-PLAN.md` combined, and it
makes the two-bit-tag encoding of Iterations 132-134 a much smaller
change chasing a much smaller prize.

### Caveats, because the numbers are good enough to be suspicious of

- The speed benchmark is a **synthetic mix with trivial handlers**, so
  dispatch dominates by construction. That is the right isolation for
  the question asked, but real handlers do work that dilutes the
  difference in both directions.
- It does not model `cross.4`, `save-system.4`, or position
  independence, and those are where the actual difficulty is: a byte
  stream has no cell alignment, and every assumption about `HERE`,
  `ALIGN` and `,` in a definition body changes.
- Nothing here was run inside RelF. The next experiment is a
  throwaway prototype - encode one real word, execute it - before any
  commitment.

### 3. Not yet run

The superinstruction K-curve including engine growth and instruction-
cache effects, per Ertl's warning that the curve turns. Deferred,
because if token threading lands, the superinstruction question should
be re-asked on the new stream anyway.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 3/1/1.
## Iteration 141: the prototype, and the number it changed

`tools/proto-gen.py` and `tools/proto-bytecode.c`. A throwaway spike:
take **one real word** from `shell.4` - `VALID-NAME? ( c-addr u --- f )`
- and its colon-word closure, encode it two ways from the **actual
token stream of the actual image**, execute both, and check they agree
before timing them.

    VALID-NAME? from shell.4, 4 words, 20 primitives
    cell program 117 cells = 936 bytes   byte program 154 bytes

    ''  x  _  9  9x  x9  PATH  _foo_BAR9  a-b  HOME  1PATH
    __  z  A1  'has space'  'e\xffz'          -- 16 inputs, all agree

**Size confirmed on real code**: 3.04x on i386, 6.08x on x86-64,
against the whole-image estimate of 3.26x and 6.51x. Calls were given
two bytes even though four words need one, because the real image has
817 targets and flattering the encoding would defeat the exercise.

### The speed result contradicts Iteration 140, and 140 was wrong

| | byte / cell |
|---|---|
| Iteration 140, synthetic mix | 0.98 - 1.03 |
| **this prototype, real word, x86-64** | **1.14 - 1.16** |
| **this prototype, real word, i386** | **1.28** |

**The byte encoding is 14-28% slower here, not free.**

The reason is the working set. Iteration 140's synthetic program was
33MB of cells against 6.8MB of bytes, so it measured *cache misses*,
which the byte encoding wins by construction. This word is 936 bytes
against 154 - **both fit in L1 several times over**, so the memory
advantage vanishes entirely and only the decode cost remains:
assembling a two-byte call index, reconstructing a 16-bit branch
offset, reading a 32-bit literal a byte at a time.

Neither number is the answer for the real system, and saying so is the
point:

- The real image's compiled code is **156KB on x86-64** - far past L1
  at 32KB, comfortably inside L2. So it sits between the two
  measurements, and closer to which end is not knowable from either.
- A hot inner loop in `shell.4` behaves like this prototype: small,
  cache-resident, and it would pay the 14-28%.
- The image as a whole behaves more like Iteration 140: mostly cold,
  and the byte encoding would win on fetch.

**The honest position is that the speed effect is unresolved and
depends on locality**, and that the earlier 0.98 was an artifact of
working-set size in exactly the way the first version of that
benchmark was an artifact of its dispatch structure. Two artifacts in
two iterations, both flattering the same conclusion.

### What the prototype found that no measurement would have

Generating the encoding forced every call target to resolve, and one
would not: **`(LOOP)` reads a branch offset from the cell after its own
call site, through the return stack** - `R> DUP @ + >R` - exactly the
trick `(S")` uses for an inline string. It is a **fifth not-a-token
case**, after `LIT`, `BRANCH` and `?BRANCH` operands and inline
strings, and `tools/classify-code.py` had been misreading it since
Iteration 130.

That matters beyond the census. **Every word that reads inline
operands through the return stack has to be rewritten for a byte
stream**, because the operand is no longer a cell at a cell-aligned
address. `(S")`, `(.")` and `(LOOP)` are the ones found so far; a port
would have to hunt the rest. This is the kind of problem that only
surfaces when something has to actually run.

### What the prototype does not do

No `cross.4`, so nothing compiles Forth source to bytes. No
`save-system.4`, no relocation, no position independence. A byte
stream has no cell alignment, so `HERE`, `ALIGN` and `,` inside a
definition body all change meaning - and that, not the dispatch loop,
is where the work actually is.

### Where this leaves token threading

The size case is confirmed on real code and is large. The speed case
is **weaker than Iteration 140 claimed and unresolved**: somewhere
between 0.98 and 1.28 depending on locality, against a plan that
Iteration 137 already spent 42% of the loop benchmark on.

The next measurement that would settle it is a prototype large enough
to exceed L1 - the whole `shell.4` closure rather than one word - which
is a much bigger generator but no new engine work. That is the
experiment to run before committing to `cross.4`.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 3/1/1.
## Iteration 142: the token-threading design, written out

`TOKEN-THREADING.md`. No code. The proposal has been measured
(Iteration 140), prototyped (141) and recommended twice without anyone
writing down what it actually entails, and the cost turns out to be
concentrated somewhere nobody had looked.

### The substitution, and everything that follows from it

A call stops being a **relative byte offset** and becomes a small
**index into a word table**. An offset must reach any word from any
other, so it cannot be narrow without a relaxation pass; an index has
to distinguish **817 words**, which is ten bits. Calls are 34% of
compiled code and eight bytes each on x86-64.

The encoding is written out byte by byte in the document: 64 primitive
slots, 32 hot-call slots, 16 small literals, 12 reserved for
superinstructions, four control forms, and two escape prefixes giving
1,024 words and 256 further primitives. The one-byte tier deliberately
**mixes categories** - a hot call costs the same as a primitive -
because the measured 77.2% coverage of the top 128 symbols assumed
frequency assignment, not partition by kind.

Branch offsets stay **fixed at two bytes**. One byte would fit most of
them and save perhaps 1,200 more, and it would require assembler
relaxation, which `GOALS.md` refused once and should keep refusing.

### The dispatch loop gets simpler, which was not expected

    #define NEXT() do { b = *ip++; goto *dispatch[b]; } while (0)

One byte load, one indirect branch. Today's `NEXT()` tests `t & 1` to
tell a call from a primitive; here the table does it and **calls stop
being a special case in the inner loop**.

### Where the cost actually is: `EXECUTE` and the dictionary

Not the dispatch loop. Three lines of the current system carry the
whole difficulty:

- **`: EXECUTE ( xt --- ) >R ;`** - it pushes the xt and returns, so
  control continues there. That works *only* because an xt is a
  directly executable code address. An xt becomes an index, and
  `EXECUTE` becomes a primitive. Everything downstream follows: `'`,
  `[']`, `COMPILE,`, `DEFER`/`IS` in `locals.4`, the `forth` builtin.
- **`: >BODY ( xt --- a-addr ) CELL+ ;`** - the parameter field is one
  cell past the code start. Under a byte code stream that identity
  simply dissolves.
- **`: , ( x --- ) HERE ! 1 CELLS ALLOT ;`** - there is now more than
  one `HERE`.

Plus every word that reads an inline operand through the return stack:
`(S")`, `(.")`, `(LOOP)`. Iteration 141 found that class by having to
make a prototype run; there may be more than the three known.

### The structural consequence, and the thing worth doing anyway

**Code space and data space must separate.** A byte-granular code
stream cannot host cell-aligned data, so headers, `VARIABLE` bodies,
`CREATE` bodies and the word table go to a cell-granular data space
with its own `HERE`, and compiled code gets a byte-granular one.

That is the largest piece of work in the proposal **and it can be done
first, alone, with cell tokens unchanged.** Ertl's paper notes
separating code and data avoids the cache-consistency penalty x86 pays
when instruction and data accesses share a line - which this project
has never looked for. Stage 1 is worth doing even if stages 2-4 never
happen.

### Staging, four stages, each green

1. Split code and data space. No encoding change.
2. Calls become indices, still one cell each. Size gets slightly
   **worse** - a cell per call plus a 3KB table - and that is the
   point: it isolates the semantic change so a regression has one
   possible cause.
3. Narrow the stream to bytes. This is where the size arrives.
4. Frequency-assign the hot tier; superinstructions in the reserved
   slots.

### The honest position on whether to do it

The size case is strong and confirmed twice: **3.26x on i386, 6.51x on
x86-64** whole-image, **3.04x / 6.08x** on a real word. It would take
x86-64 from 211,768 to about 80,000 against `dash`'s 129,832, and it
is the only proposal that puts the 8-byte build below `dash`. **The
byte stream is the same size on both architectures**, so the 1.85x
penalty the wide build pays today disappears entirely rather than
shrinking.

The speed case is **not settled and both benchmarks so far were
flattering**: 0.98-1.03x synthetic, 1.14-1.28x on a real word, the gap
explained by working-set size. The decisive experiment - the same
prototype scaled to the whole `shell.4` closure so it exceeds L1 - is a
bigger generator and no new engine work, and should be run **before
stage 3**.

And it would arrive on top of Iteration 137's 42%. Two size changes
each costing 15-40% of loop time would leave this shell meaningfully
slower than one already 236x off `dash`. That is a real argument for
reverting 137 if this lands, and for doing Stage 2 of
`PARSE-EXPAND-PLAN.md` first so there is headroom to spend.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 3/1/1.
## Iteration 143: `ONE-LINE-LOOP?` should not exist, and two bugs prove it

Asked why `ONE-LINE-LOOP?` is needed when parsing ought to be
universal. It should not be, the question is right, and checking it
turned up **two real conformance bugs** - one of which is silent.

### What it actually is

Not a second parser. An **adapter**. `while` and `for` capture their
bodies by *reading further lines* into a buffer and replaying them, so
a loop written entirely on one line has nothing further to read.
`CAPTURE-ONE-LINE-LOOP` manufactures the three pieces the multi-line
path would have produced - body text, suffix, header - and its own
comment says so: everything downstream is "unchanged and unaware".

That is the least-bad version of the workaround. It is still a
workaround, and the root cause is architectural: **the line is the unit
of both input and body storage.** In POSIX's grammar a newline is just
a token, largely interchangeable with `;`, and "does this construct
end on this line?" is not a question the grammar can ask. In this
implementation it is the central question.

### The evidence that it is a design smell and not a local choice

Three compound constructs, three *different* strategies:

- **`if`** executes body lines as it reads them, never buffering. Its
  own comment records why `while`/`for` cannot do this: a loop body
  runs many times, so it must be buffered and replayed.
- **`while`/`for`** buffer and replay, plus `SAME-LINE-DO?` and
  `ONE-LINE-LOOP?`/`CAPTURE-ONE-LINE-LOOP` as adapters for the shapes
  that have no further lines.
- **`case`** has no adapter at all, and says so: "Requires each pattern
  arm on its own line... no same-line support yet, matching while/for."

**The two constructs without a working adapter are the two that are
broken.** That is about as clean a demonstration as this project has
produced that the special case is a symptom.

### Bug 1: one-line `case` (loud)

    case x in x) echo matched ;; esac

    sh, bash, mksh, ksh, yash, busybox, posh   ->  matched
    relfsh -> shell: syntax error: unexpected end of input, expected 'esac'

Also fails with the arm split after the `)`:

    case x in x)
    echo M ;;
    esac

    sh -> M        relfsh -> nothing at all, status 0

The second form is worse than the first: no error, no output, no
failure. A script would carry on.

### Bug 2: content after a nested `fi` (silent)

    if true; then if true; then echo A; fi; fi; echo B

    sh -> A B        relfsh -> A

`echo B` is **silently dropped**. `DO-IF`'s comment documents this as a
deliberate scope limit - preserving the remainder would mean
propagating it up the call stack - but it is written as though it
applies only to the outermost `fi`, and the un-nested case
(`if true; then echo A; fi; echo B`) works. It is the *nested* one that
loses the tail, which is not what the comment says.

Both are now `tests/posix` cases, `2.9.4.2-case-on-one-line.sh` and
`2.9.4.1-nested-if-trailing-command.sh`. The suite goes **3 passed, 3
failed, 1 inconclusive**, and all seven reference shells agree on both,
so neither is a matter of interpretation.

That number getting worse is the suite working. It was built in
Iteration 126 to find exactly this, and it found it the first time
somebody asked it a question about a construct rather than about an
expansion.

### The fix, and what it connects to

Make the tokenizer **stream-oriented**: read tokens from a source that
spans lines, with newline as an ordinary token. Then `do ... done`,
`then ... fi` and `in ... esac` parse identically however they are
laid out, and `SAME-LINE-DO?`, `ONE-LINE-LOOP?`,
`CAPTURE-ONE-LINE-LOOP` and the `case` gap all disappear together
rather than needing an adapter each.

Bodies still have to be *stored* for replay, since a loop body runs
many times - but stored as **tokens rather than raw text**, which is
exactly Stage 2 of `PARSE-EXPAND-PLAN.md`. Stage 2 was specified as a
speed change: cache tokenized body lines instead of re-tokenizing them
every iteration, to attack the 236x loop gap.

**It is the same work.** Approached from speed it is Stage 2;
approached from correctness it is the removal of every same-line
special case in the file. That is a much better argument for doing it
than the benchmark alone, and it should be recorded in
`PARSE-EXPAND-PLAN.md` as such.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 3 passed / 3 failed / 1 inconclusive.
## Iteration 144: auditing for the rest of the same-line family

Iteration 143 found `ONE-LINE-LOOP?` was a symptom. Asked to audit
`shell.4` for the rest. Method: mine the file's own comments for
self-declared limits, then **test every one against the seven
reference shells**, because a special case that produces wrong output
is a bug and one that does not is merely structure.

Twenty shapes tested. Five differed, and the file's comments predicted
only three of them.

### `until` is recognised and then silently ignored

The worst of the five, and it was not in any comment or in
`GOALS.md`'s open list.

    i=0; until [ "$i" -ge 3 ]; do echo $i; i=$((i+1)); done

    sh, and six others -> 0 1 2
    relfsh             -> nothing, status 0

`until` **is** in the reserved-word list (line 3155), so it is
correctly refused as a command name - but the compound-command
dispatcher at line 5519 tests only `while` and `for`. So the word is
recognised, falls through every branch, and the whole loop evaporates
without an error. A POSIX compound command that is a silent no-op, in
a shell that passes mrsh's suite.

Recognised-but-unhandled is a worse failure mode than unrecognised:
had `until` not been a reserved word, it would have been a command
lookup failure with a diagnostic.

### `{ ... }` across lines drops all but the last command

    { echo first
      echo second
      echo third; }

    sh     -> first second third
    relfsh -> third

Silent. `SPLIT-GROUP`'s comment says it "only handles a group
contained in one line"; what the comment does not say is that the
other lines are discarded rather than refused.

### `&` is treated as a line terminator, not a list terminator

    true & echo after

    sh     -> after
    relfsh -> nothing; `&`, `echo` and `after` become arguments to `true`

Background execution works when `&` ends the line, which is how every
existing test writes it. POSIX makes `&` a list terminator: a command
may follow it exactly as after `;`.

### Two already known, confirmed

`pwd > file` (redirection not applied to builtins, recorded) and
`case` on one line (Iteration 143) - which also means **`case` cannot
appear in a one-line function body**, the common form:

    f() { case $1 in a) echo A;; *) echo other;; esac; }

### The shape of the whole finding

Four of the five are **the same fault with four faces**: `do`/`done`,
`{`/`}`, `&`, and `case`/`esac` each need to be recognised as
separators or terminators *within* a line, and the parser asks instead
whether the line ends there. `while`/`for` got an adapter
(`ONE-LINE-LOOP?`), `if` got a different mechanism entirely, and `{`,
`&` and `case` got nothing.

Nine `tests/posix` cases now, **3 passed, 6 failed, 1 inconclusive**,
every failure agreed on by all seven reference shells. The number
getting worse three iterations running is the suite doing its job.

### A hollow pass in the new suite, caught immediately

The first `&` case was `sleep 0 & wait`, which **passed** - because a
shell treating `&` as an argument fails on *stderr*, and this harness
ignores stderr. Exactly the `ulimit.sh` shape from Iteration 122, in a
suite built partly to avoid it.

The second version, `echo one & echo two`, went INCONCLUSIVE: the
reference shells disagree with each other on the interleaving, which
is a race and not a conformance question. The third has the background
command produce no output, so the result cannot depend on ordering.

Both wrong versions are recorded in the case file's own comments. The
rule they teach: **a differential case must put the difference on
stdout, and must not depend on scheduling.**

### `GOALS.md` updated

All four same-line faults and `until` added to the open list, with a
note that they are one fault and that `PARSE-EXPAND-PLAN.md` Stage 2
fixes the class rather than the instances.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 3 passed / 6 failed / 1 inconclusive.
## Iteration 145: why `(` and `)` are not reserved words, and what asking found

Asked why `RESERVED-WORD?` omits `(` and `)`. **It is correct to omit
them**, and checking why turned up a real gap somewhere else.

### The list is exactly POSIX's

XCU 2.9 defines the reserved words as

    !  {  }  case  do  done  elif  else  esac  fi  for  if  in
    then  until  while

which is precisely the sixteen in `RESERVED-WORD?`. `(` and `)` are
**control operators** (2.10.2), a different category with different
recognition rules, and they are correctly absent.

### The distinction is observable, and this shell gets it right

A **reserved word** is recognised only as a separate, unquoted token in
command-name position, so it must be delimited. An **operator**
self-delimits and needs no surrounding space. That predicts two
things, and both hold:

    (echo hi)      -> hi          operator: no spaces needed
    {echo hi;}     -> status 127  reserved word: "{echo" is just a word

Tested unspaced parens in ten shapes - `(echo a)&&(echo b)`,
`((echo a))`, `if (true); then`, `(exit 3); echo $?`, a subshell in a
pipeline, one inside a `for` body - and all match `sh`. So although
`NORMALIZE-OPERATORS` deliberately does **not** space out parens, the
tokenizer handles them anyway.

**A correction to my own first reading.** I initially called
`{echo hi;}` a silent divergence, because I compared stdout and
relfsh printed nothing where `sh` printed a diagnostic. It exits
**127** - `{echo` is not a command - which is the correct behaviour;
only the message differs, and messages are implementation-defined.
Recorded as `2.9.4.1-brace-must-be-delimited.fail.sh`, which passes.
Comparing stdout alone is how the `ulimit.sh` hollow pass happened
too.

### The gap the question actually found

    x=$( (echo inner) ); echo "got=$x"

    sh and six others -> got=inner
    relfsh            -> got=

Silent. POSIX 2.6.3 requires that space: a command substitution whose
first token is a subshell must be written `$( (` so it is not read as
`$((` arithmetic expansion. This shell ignores the space and reads
arithmetic either way, which quietly evaluates to nothing.

The same root shows the other way round: `x=$((echo n))` yields **0**
here where `sh` diagnoses an arithmetic syntax error.

`NORMALIZE-OPERATORS`' own comment predicted this. It says parens are
out of scope because blindly spacing them "would break `$(...)`
command substitution outright - EXPAND-VAR's own detection needs
`"$("` with no space in between". That detection is the same code that
cannot tell `$((` from `$( (`. The comment identified the coupling and
stopped one step short of noticing it was already a bug.

### Where this leaves the audit

Eleven `tests/posix` cases: **4 passed, 7 failed, 1 inconclusive**. The
new failure is the only one of the five differences probed here that
is a genuine defect; the rest of the paren behaviour is correct, and
`RESERVED-WORD?` needs no change.

Worth stating plainly because it is the opposite of the last two
iterations: **the design question had a good answer.** The list is
right, the operator/reserved-word distinction is implemented
correctly, and asking about it was still worth it - it found a defect
next door.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 4 passed / 7 failed / 1 inconclusive.
## Iteration 146: a systematic POSIX corpus, and eleven new gaps

Asked to revisit the tests and get real coverage, derived from the
specification and from what the reference shells actually do. Wrote 35
new `tests/posix` cases covering XCU section 2 systematically -
quoting, token recognition, reserved words, all three parameter
sections, every expansion, field splitting, pathname expansion, quote
removal, redirection, exit status, pipelines, functions, pattern
matching and the special built-ins.

**47 cases: 24 passed, 21 failed, 2 inconclusive**, every failure
agreed on by all seven reference shells.

### What the existing suites were and were not covering

`tests/shell` has 63 files and 532 assertions, but they are
hand-written expectations - layer 2 - and they were written alongside
the features they test, so they encode what was built rather than what
the specification requires. `tests/diff` is 19 cases against bash
alone. `tests/mrsh-suite` is 21 files and fully passed. None of them
systematically walks the specification, which is why a corpus written
*from* XCU rather than from the code found this much.

### Eleven gaps not previously recorded

- **Positional parameters stop at 9.** `set -- 1 ... 10` leaves `$#`
  at 9. Verified separately from the corpus: 8 and 9 are fine, 10 and
  11 both report 9.
- **`${#}`** yields 0. `${#var}` works; the bare count does not.
- **`for w; do ... done`** - the implicit `in "$@"` form - iterates
  over nothing.
- **`eval` is not implemented**, status 127. A POSIX special built-in.
- **`"$*"` joins with a space regardless of `IFS`**, where POSIX says
  the first character of `IFS`, and nothing when `IFS` is null.
- **Non-whitespace `IFS` produces no empty fields**: `IFS=:` on
  `a::b:` gives two fields where the specification requires three.
- **Arithmetic division truncates toward negative infinity.**
  `$((-7 / 2))` is -4 here and -3 in every reference shell; XCU 2.6.4
  defers to ISO C, which truncates toward zero.
- **A reserved word cannot be a `for` list value.**
  `for x in do done; do ...` iterates over nothing - a reserved word
  is being recognised somewhere it should be an ordinary word, which
  is the mirror image of Iteration 145's finding that the
  *classification* is correct.
- **Quoted and escaped `case` patterns do not match**, and neither
  does the `*)` arm afterwards, so the whole construct silently
  selects nothing.
- **An empty `case` word does not match an empty pattern.**
- **Pathname expansion differs** on the sorted multi-match and
  no-match forms.

### One known gap, much wider than its recorded description

`GOALS.md` said "redirection does not apply to builtins" and gave
`pwd > file` as the example. The corpus found the same root behind
three more shapes:

    read -r l < file                    reads nothing
    while read -r l; do ...; done < f   produces nothing
    { printf a; printf b >&2; } > f 2>&1 writes nothing

So it is not a builtin curiosity - **any redirection whose target is a
builtin or a compound containing one is silently dropped**, which
covers the single most common idiom for reading a file in a shell
script. The description has been widened.

### On the cases themselves

Every case cites its XCU section, exercises one section, uses `printf`
rather than `echo`, and avoids anything that depends on scheduling,
process ids or locale. The glob case builds and removes its own
directory under `/tmp` so it does not depend on the repository's
contents.

Two are INCONCLUSIVE and left that way deliberately: the
tilde-after-`=` divergence from Iteration 126, and arithmetic with an
unset variable, where the references disagree among themselves. Both
are findings about the shells, not defects here.

### What is still weak

**The core Forth suite's headline number is not an assertion count.**
Iteration 129 established that "1998 core OK markers" counts lines of
input interpreted without error, and it moved by exactly seven when
seven lines were added to a test file. It is a real regression signal -
an error breaks the run - but it is not coverage, and it should not be
quoted as though it were. Replacing it with a genuine count from
`tester.fr` is unfinished business.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 24 passed / 21 failed / 2 inconclusive.
## Iteration 147: triage, not more discovery

Asked whether the project is in stable shape or needs another audit
round. The answer is **stable, not finished, and the next round should
be triage rather than discovery** - and this iteration is the evidence
for that, because triaging what was already there changed it.

### The audit had a defect of its own

`2.6.5-field-splitting-whitespace.sh` and its non-whitespace twin both
iterated with `for w; do`, the implicit form - **which is itself
unimplemented**. So both cases tested two features at once and blamed
the wrong one. Checked directly:

    IFS=' '  v='  a   b  '   sh: n=2 [a][b]   relfsh: n=2 [a][b]
    IFS=':'  v='a::b:'       sh: n=3 [a][][b] relfsh: n=2 [a][b]

**Whitespace field splitting is correct.** Only the non-whitespace
empty-field case is broken. Iteration 146's write-up listed both as
failures and implied splitting was generally wrong; it is not.

Both cases now iterate with an explicit `"$@"`, and the implicit form
has a case of its own. `tests/posix/README.md` already said "keep a
case to one section"; the stronger rule this teaches is **keep a case
to one feature**, because a case that exercises two attributes the
fault to whichever one you were thinking about.

48 cases: **25 passed, 21 failed, 2 inconclusive** - same failure
count, correctly attributed.

### The 21 failures are six faults, not twenty-one

| root cause | cases | fix |
|---|---|---|
| line-oriented parsing (the same-line family) | 4 | `PARSE-EXPAND-PLAN.md` Stage 2 |
| redirection never reaches builtins or compounds | 3 | Ramey's undo list, in `GOALS.md` |
| construct or built-in simply absent | 4 | independent, each small |
| parameter and expansion semantics | 5 | independent, each small |
| pattern matching | 3 | one area |
| tokenizer | 2 | one area |

**Two root causes account for a third of the list**, and both already
have a designed fix recorded. The four "absent" ones - `until`,
`eval`, `for w; do`, the `NAME=value` prefix - are independent and
small. So is most of the parameter group: `${#}`, the `$*` join with
`IFS`, arithmetic division truncating the wrong way, positional
parameters past 9.

### Why stop auditing

Not because the yield has dropped - it has not. Iteration 146 found
eleven gaps in one pass, and whole sections remain untouched: signals
and traps (2.11), the shell execution environment (2.12), here-
documents beyond the simplest form, `getopts`, `exec`, `set -o`, `$0`,
what a subshell inherits. Another round **would** find more.

The reason to stop is the ratio. **Twenty-one verified, specified,
reproducible failures and not one of them fixed.** A backlog that only
grows stops being read, and finding defect twenty-two is worth less
than fixing defects one through seven.

There is also a specific reason to fix some now: **the corpus is
unproven as a driver of work.** It has only ever gone down. A suite
that has never been used to make a number go *up* has not demonstrated
it can be, and the cheap items - `${#}`, `eval`, the `$*` join,
division truncation - would prove it in an iteration or two.

### On "stable"

In the sense of not regressing: **yes, solidly.** Every commit is
green on both cell widths, the mrsh suite is fully passed against the
set upstream actually runs, and the documents describe the system as
it is - Iterations 122, 135, 138, 144, 146 each corrected something
that had drifted.

Two things are open and should not be forgotten in a stable-sounding
summary. **Iteration 137's 42% loop regression is still in `master`**,
landed deliberately and revertable in one commit, with no decision
taken. And `TOKEN-THREADING.md` is a designed but unstarted change
whose speed cost is unresolved, sitting on top of that.

No behaviour changed. Both cell widths, 1998 core OK markers, 532
assertions across 63 files, 19 differential cases, mrsh 20 of 21,
posix 25 passed / 21 failed / 2 inconclusive.
## Iteration 148: freezing - a reproducible build and one command to check it

Asked what to do for maximum stability before the code base is frozen
and engine work begins in a fresh session. The answer turned out to
start with something that had been visible all session and treated as
noise.

### The build was not reproducible, and the images are tracked

`kernel-shell.img` and `kernel32-shell.img` are committed, and every
test run modified them. I had been running `git checkout` on them
repeatedly for dozens of iterations without asking why.

Two causes, both the same shape - **the saved image was capturing
transient runtime state**:

- `SS-SCRUB` did not know about `locals.4`'s scratch variables. `LE-A`
  holds the address of the descriptor `LENTER` last stepped over, and
  `LE-N`, `LE-ARGS`, `LE-P`, `LE-Q`, `LX-N` hold its counts. They
  arrived with `LENTER`/`LEXIT` in Iteration 137 and nobody told
  `SS-SCRUB`. Eleven bytes of difference.
- `SS-SCRUB` blanked `TIB` but not `#TIB`, so the image recorded **how
  long the builder's last command line was**. One byte, and enough:
  `relfsh -c true` and a full test run produced different images.

`SS-SCRUB`'s own comment already stated the principle - these
variables "hold an absolute address, so it differs every run" and
"leaving them would make two saves of the same system differ". The
word was right; its list was incomplete.

Both fixed. Two full test runs on both cell widths now produce
byte-identical images, as does a build doing entirely different work
in between.

**Why this matters more than it looks.** The engine change ahead
touches `relf.c`, `cross.4`, `save-system.4` and every
position-independence assumption in the system. A tracked artifact
that changes on every run is exactly the noise that hides a real
regression - and it would have been at its most dangerous during the
one change most likely to produce one.

### `tests/verify`

One command. Runs every suite, checks that rebuilt images reproduce
the committed ones byte for byte, and compares **eighteen numbers**
against `tests/BASELINE`:

    ok  core:8byte 1        ok  mrsh:passed 20       ok  posix:passed 25
    ok  core:4byte 1        ok  mrsh:failed 1        ok  posix:failed 21
    ok  core:okmarkers 1998 ok  shell:assertions 532 ok  posix:inconclusive 2
    ok  diff:failed 0       ok  shell:files 63       ok  posix:cases 48
    ok  rebuild:kernel-shell.img reproduces          ok  size:i386 118984
    ok  rebuild:kernel32-shell.img reproduces        ok  size:x86_64 211912

Any difference - **better or worse** - is reported and fails the run.
A `CHANGED` line is not automatically a defect: fixing one of the 21
known POSIX failures will change a number, and the right response is
`tests/verify --update` in the same commit as the fix, so the file
always records what the tree does rather than what someone hoped.

Deliberately excluded: `tests/bench`. Minutes to run, and single runs
on this hardware differ by more than most changes do - it needs
Iteration 129's alternating method, not a threshold.

### What is frozen, and the one decision still open

Everything verifies. Both cell widths, reproducible images, mrsh fully
passed against the set upstream runs, 21 POSIX failures that are
documented, reproducible and grouped into six root causes (Iteration
147).

**Iteration 137's 42% loop regression is still in `master` and still
undecided.** It is one `git revert` away. The recommendation, recorded
here so the next session does not have to reconstruct it: **revert it
before starting engine work.** Three reasons - a clean `tests/bench`
baseline is what the engine change will be judged against and it is
currently contaminated by a deliberate regression; token threading may
cost a further 14-28% and two stacked regressions cannot be
attributed; and the 8,712 bytes it buys are dwarfed by the ~54,000
token threading projects, on code it would have to be rewritten
against anyway.

No behaviour changed beyond the scrub. `tests/verify` passes clean.
## Iteration 149: revert 137, and write down what comes next

The code base is being frozen so engine work can start in a fresh
session. Two things left to do: take the one decision still open, and
make sure `GOALS.md` carries the plan rather than leaving it scattered
across six documents and a hundred log entries.

### Iteration 137 reverted

`LENTER`/`LEXIT` bought 8,472 bytes of image and cost **42% of the
loop benchmark**. It was landed as its own commit precisely so this
was one command.

Measured after the revert, four runs: **741, 788, 741, 788 ms**,
against 1,338-1,389 with it and 939-1,256 before it. Fully recovered,
and faster than the pre-137 figure - that baseline was taken while the
machine was under heavier load, which is its own reminder that single
comparisons across sessions are worth little.

Three reasons, recorded in Iteration 148 and acted on here: the engine
change will be judged against `tests/bench` and its baseline was
contaminated by a deliberate regression; token threading may cost a
further 14-28%, and two stacked regressions cannot be attributed to
either; and 8,472 bytes are dwarfed by the ~54,000 token threading
projects, on code that would have to be rewritten against it anyway.

**The revert was not clean and the reason is worth knowing.** It
conflicted in `GOALS.md` and `PROGRESS.md` - the latter is append-only,
so reverting its Iteration 137 entry would have been wrong. Both were
resolved by keeping the current text: the log records what happened,
including changes later undone. And `save-system.4` had to be edited
by hand, because Iteration 148 taught `SS-SCRUB` about six scratch
variables that only existed because of 137. That dependency is now a
comment in `SS-SCRUB`: **if 137 is ever re-applied, those six must go
back, or the image stops reproducing.**

Sizes return to i386 **127,408** and x86-64 **228,768** - 0.93x and
1.76x a same-architecture `dash`.

### `GOALS.md` now carries the whole plan

A new section, replacing one that predated twenty iterations of work
and said only "Stage 2 is the only one left". It has four parts:

**Settled, so nobody re-proposes them.** Headerless words rejected;
register VMs closed; dispatch-site replication measured and gains
nothing here, which also devalues a tail-call interpreter;
byte-granular *offsets* still rejected while byte-granular *indices*
are not; variable-length branch offsets rejected twice; and 137
reverted, with the `SS-SCRUB` warning attached.

**The queue**, seven items in order with the reason for the order.
The four absent POSIX items first - not because they are the largest
but because **the corpus has only ever gone down, so it is unproven as
a driver of work**. Then Stage 2, which is now justified twice over.
Then the redirection undo list. Then the engine, decisive experiment
first. Then superinstructions, re-measured rather than re-quoted. Then
a `FILL` primitive. Then phase 3, the assembler, which is goal 1's
last piece and has never been started in 149 iterations.

**What has not been audited at all** - signals and traps, the
execution environment, here-documents, `getopts`, `exec`, `set -o`,
`$0`, subshell inheritance - so the next session knows the backlog is
incomplete by choice rather than by accident.

**Method that must survive.** Four rules, each with the incident that
produced it: measure the harness and not just the code (124, 135, 140,
141); check *why* a test passes (122); one feature per test case
(147); and a fix ships with `tests/verify --update` (148).

### State at the freeze

`tests/verify` clean against `tests/BASELINE`, from a fresh clone.
Both cell widths, images reproducing byte for byte, mrsh fully passed
against the set upstream runs, 21 POSIX failures that are documented,
reproducible, and grouped into six root causes.

## Iteration 150: the shell image did not build from a long path

A stabilization audit before the engine work, asked for on the
grounds that `TOKEN-THREADING.md` touches `relf.c`, `cross.4`,
`save-system.4` and every position-independence assumption at once,
so anything shaky underneath would surface wearing an engine bug's
clothes. This entry is the first of two fixes; the audit's other
findings are listed at the end.

### The bug

`relfsh`'s `build_shell_img` interpolated `$DIR` into every line of
the Forth bootstrap it feeds the engine. This kernel's `QUERY` reads
a line with `TIB 80 ACCEPT`, and **an over-long line loses its tail
in silence** - no diagnostic, no status, nothing. Confirmed directly:
a bare `999 . CR` sitting at column 81 simply never runs.

The longest generated line was the save:

    S" $DIR/kernel-shell.img.tmp.$$" SAVE-SYSTEM

Its length is `38 + len($DIR) + len($$)`, and the cliff is exact -
measured by generating the line at controlled widths:

| save-line length | result |
|---|---|
| 80 | BUILT |
| 81 | FAILED SILENTLY |

So the build stopped working once the repository sat deeper than
about 36 characters. `/home/claude/relf` is 17 and had room;
`/home/user/projects/forth/relf-shell` would not have.

**The PID's digit count is part of that sum**, which makes the
threshold nondeterministic - the same checkout builds or fails
depending on the PID it happens to get. Measured: a 39-character path
failed on eight consecutive attempts, a 36-character path built on
three.

### Why it would have been so confusing

`build_shell_img` returns nonzero, and `relfsh` falls back to the
source bootstrap. That path is ~128x slower *and* prints "Welcome to
Forth" plus `Redefining:` lines to stdout, so every output-comparing
test breaks at once, none of them anywhere near the cause. A
developer hitting this while debugging a token-threaded image would
have been chasing a path-length bug that looked like an engine bug.

### The fix

`cd` to `$DIR` in a subshell and feed relative filenames, so every
line is a fixed length whatever the path. The `cd` stays inside the
subshell deliberately: the parent must remain in the caller's
directory or a `relfsh script.sh` argument resolves against the wrong
place. `RELF_BIN`/`RELF_IMG` are resolved to absolute first, since a
relative override (`RELF_BIN=./relf32`) would otherwise break across
that `cd`. Verified building cleanly at 39, 60, 90 and 140 characters.

### The check that could not have caught it

`tests/verify`'s reproducibility test built twice **in the same
directory**, which cannot distinguish "the build leaks nothing" from
"both builds leaked the same thing". Leaking the build path is
precisely the failure `save-system.4`'s own header describes, where
the first prebuilt image carried the machine's directory and the
builder's PID - so `SS-SCRUB`'s whole reason for existing was
untested.

`crosspath:kernel-shell.img` now builds under an 84-character path
and compares byte for byte. It passes, which is also the first
positive evidence that `SS-SCRUB` genuinely scrubs the path rather
than both builds having leaked the same one. Confirmed non-hollow the
way 122 says to: reverted `relfsh`, watched the check fail.

## Iteration 151: neither stack was bounded

`relf.c` set `dsp` and `rp` in `main()` and never looked at either
again. There was no overflow check of any kind on either stack.

### What actually happened on overflow

Both stacks grow down. `rp` starts at `base + MEMSIZE`; `dsp` starts
`RSTACK_BYTES` below it. Nothing stopped either from descending
through the free middle of `mem[]` and into the dictionary, quietly
rewriting compiled words from the top down. The SIGSEGV arrived much
later, when the pointer finally walked off the bottom of the array -
so **the corruption came first and the crash came long after**.

That is exactly the symptom `relf.c`'s own `MEMSIZE` comment already
recorded, without naming the cause: "corrupted compilation reported
as 'Undefined word' against an empty name, nowhere near the actual
cause."

Measured before the fix, both cases exit 139 (128 + SIGSEGV) with
nothing on stderr:

    : OVF BEGIN 1 0 UNTIL ;  OVF     -> exit 139, silent
    : DEEP RECURSE ;         DEEP    -> exit 139, silent

### The fix, and why it is at the push sites

A push is the only way either stack can grow, so `PUSH`/`RPUSH` is
the complete set of sites. There is no cheaper subset that still
catches runaway recursion *and* runaway loops: a check only at the
colon-call path in `NEXT()` misses `BEGIN 1 0 UNTIL`, whose body
contains no call at all.

`DSTACK_BYTES` (256KB) puts the data stack's floor at 720,896 bytes
from `base`. The largest image this project builds is the x86-64
prebuilt shell at 206,024, so **the check fires with half a megabyte
still between the stack and the dictionary** - strictly before any
corruption rather than after it. This reserves nothing and moves
nothing: `dsp` and `rp` start exactly where they always did, so
`S0`/`R0` and every saved image are unaffected.

Status 70 (`EX_SOFTWARE`) rather than 1, so a harness can tell an
engine fault from a Forth-level `ABORT`. No attempt is made to
recover into the interpreter: by the time either pointer is out of
bounds the system has been running away for a while, and `ABORT`ing
back into `QUIT` would need a working data stack to do it with.

### Cost, measured

`fib.4`, which is the most call- and push-dense workload in the
repository, eight interleaved pairs to control for machine drift:

| | mean | median | min |
|---|---|---|---|
| unchecked | 398.1ms | 396.5 | 390 |
| checked | 407.6ms | 407.0 | 402 |

**1.024x on the mean, 1.031x on the min** - so roughly 2.4-3.1% on
the workload chosen to make it look worst. Stripped engine size is
unchanged at 22,744 bytes, and both tracked size figures are
untouched.

That cost is accepted deliberately. Goal 3 ranks simplicity and
correctness above raw performance, and this converts silent
dictionary corruption into a named diagnostic on the exact code path
the token-threading work is about to rearrange. For scale: Iteration
137 was reverted for costing 42% of the loop benchmark; this is not
that.

### The test

`tests/shell/run-engine-stacks`, 6 assertions. An engine test living
in the shell suite because that is where the assertion helpers and
the counting are; it drives `$RELF_BIN`/`$RELF_IMG` rather than
`$THIS_SH`, since `relfsh` boots straight into the shell's `MAIN` and
what is under test is the engine underneath. `tests/run_tests.sh`
already sets those per cell width, so it runs against both builds.

It asserts the diagnostic and the status on both stacks, **and that
`fib.4` still completes with the right answer** - the check must not
trade a rare crash for a common false positive. Confirmed non-hollow:
against the old engine 4 of the 6 assertions fail, showing status 139
and empty stderr.

### Also found in the audit, not yet fixed

Recorded so the next session has them without re-deriving:

- **A duplicated block that has already diverged.** The group
  dispatch sequence appears at `shell.4` 4248 and 6936; the second
  has an `ARGC @ 1 =` multi-line preamble the first lacks. That
  predicts a real defect and does produce one: a multi-line `{ }`
  after `&&` gives correct output but **exit status 127**. No case
  covers it, though `tests/diff` does compare status. This is the
  class the duplication convention exists for.
- **The interactive prompt goes to stdout, and prints when stdin is
  not a terminal.** bash, dash, mksh, ksh, yash, posh and busybox all
  suppress it and write prompts to stderr. It survives because
  `tests/shell/lib.sh` uses substring assertions, justified in its
  header by "RelF's own boot banner and CRLF line endings" - **both
  of which Iteration 40 removed.** Verified: the current shell emits
  no banner and no CR. The justification expired; the weakened
  assertions did not. The prompt is now the only thing blocking
  exact-output comparison in that layer.
- **`MAX-ARGS` (64) still fails silently.** 70 arguments truncate to
  62 plus a spurious `0`, and `set --` then reports 9. Iteration 90's
  diagnostics reached `SET-SHVAR`, `SET-FUNC` and the positional
  stack, but not this path. `MAX-ALIASES` does diagnose correctly.
- **Nine dead variables** in `shell.4`, one occurrence each:
  `IN-ASSIGN-CONTEXT?`, `PW-FID`, `WT-PID`, `FDL-I`, `WHILE-BODY-I`,
  `WHILE-BODY-CUR`, `CASE-PATLAST-LEN`, `FD-ADDR`, `FD-LEN`.
- **Two stale claims in `GOALS.md`**, both corrected in this commit.
  All fifteen "Still open" items were re-tested against bash; thirteen
  reproduce exactly.

The duplication finding came from inspecting only the two largest
repeated blocks. A full pass over 7,091 lines would likely surface
more of the same class, and it should be its own iteration rather
than folded into a fix.

## Iteration 152: one duplicated block had drifted

The second of the Iteration 151 audit's findings, and the reason the
duplication convention exists.

`shell.4` carried the group-dispatch sequence twice, verbatim, at
lines 4248 in `RUN-SIMPLE-OR-PIPELINE` and 6936 in `RUN-TOKENIZED`.
They were not equivalent. Only the `RUN-TOKENIZED` copy carried the
arm above it:

    ARGC @ 1 = IF
      S" (" LINE-IS? IF -1 MG-SUB? ! DO-MULTILINE-GROUP EXIT THEN
      S" {" LINE-IS? IF  0 MG-SUB? ! DO-MULTILINE-GROUP EXIT THEN
    THEN

So a group whose opener is alone on its line was recognized when it
*was* the whole line, and not when it arrived as an `&&`/`||`
segment. `true && {` ran its body and printed correctly, but left
**status 127**: the lone `{` segment fell through `DISPATCH-GROUP`'s
predecessor and was executed as a command name. Silently - no "not
found" diagnostic reached the terminal, which is why output-only
inspection never caught it.

Confirmed the shape before fixing, against bash:

    true && { echo a; }      status 0    (single line, fine)
    { \n echo a \n }         status 0    (whole line, fine)
    true && { \n echo a \n } status 127   <- only this
    false || { \n echo a \n } status 127

### The fix

Both copies are now one word, `DISPATCH-GROUP ( --- f )`, returning
true when it handled the line so the caller can `EXIT`. It sits after
`DO-BRACE-GROUP`, which is early - and `DO-MULTILINE-GROUP` and
`MG-SUB?` are defined ~2900 lines later, since they need the
tokenizer. Reached through `DEFER DO-MULTILINE-GROUP-CALL`, patched
to `(DO-MULTILINE-GROUP)` right after that word exists, which is the
same pattern already used for `RUN-TOKENIZED-CALL`,
`TRY-ASSIGNMENT-CALL` and eight others. The wrapper takes the
subshell flag on the stack so `MG-SUB?` stays private to that end of
the file.

All seven forms now match bash, **including `(echo hi) | tr a-z
A-Z`** - the `AT-GROUP-END?` guard inside the merged word is what
keeps a group followed by a pipe falling through to `SPLIT-PIPE`
instead of running alone, the regression Iteration 20 recorded.

### Result

`tests/diff/cases/multiline-group-segment.sh`, 20 differential cases
now, 0 failed. Written for the statuses, not the output: every one of
these printed correctly before the fix, so an output-only case would
have passed against the bug. It includes the whole-line group and the
piped group as controls, so a fix that broke the working paths could
not pass either. Confirmed non-hollow against the old `shell.4`,
where it shows exactly the `st=127` lines.

Both images still reproduce byte for byte, on both cell widths, and
merging the copies made the shell **smaller**:

| | before | after | delta |
|---|---|---|---|
| i386 | 127,408 | 127,296 | -112 |
| x86-64 | 228,768 | 228,480 | -288 |

The POSIX corpus is unchanged at 21 failures - this fault was never
in it, which is worth noting given the corpus is the thing driving
the queue. It was found by inspecting the file's largest duplicated
block, not by any test.

Still open from the 151 audit: the prompt on stdout, `MAX-ARGS`
failing silently at 64, and the nine dead variables. And the
duplication pass itself is still only two blocks deep - this entry is
evidence the rest of that pass is worth doing.

## Iteration 153: the prompt was on stdout

Third of the Iteration 151 audit's findings, and the one that was
being hidden by a test-strength decision whose justification had
expired.

`SH-PROMPT` wrote `." $ "`, and `SH1` followed `ACCEPT` with a bare
`CR`. Both go to stdout. `relfsh`'s own header documents `... |
relfsh` as a supported mode, so:

    printf 'echo hi\n' | relfsh    ->  "$ \nhi\n$ \n"
    printf 'echo hi\n' | bash      ->  "hi\n"

Every reference shell present - bash, dash, mksh, ksh, yash, posh,
busybox - writes its prompt to stderr. A piped script's stdout was
therefore not what the script printed.

### Why nothing caught it

`tests/shell` *does* pipe into the shell; several files build scripts
with `printf ... | "$THIS_SH"`. But its assertions are substring
assertions, and "hi" is a substring of the corrupted output just as
much as of the correct one.

`lib.sh`'s header justified that choice: "RelF's own boot banner and
CRLF line endings would make literal whole-output comparison fragile
for little benefit here." **Both reasons were removed by Iteration
40**, when the prebuilt image began booting straight into `MAIN`.
Verified before touching anything: the current shell emits no banner
and no CR. The justification went stale; the weakened assertions did
not. That is the same rot `GOALS.md` warns about, in a test harness
rather than in prose - and 124/135/140/141's rule, measure the
harness and not just the code, is what it argues for.

### The fix

`S" $ " 2 WRITE-FILE DROP`, and the terminating newline written as a
single byte from `CREATE SH-NL 10 C,` rather than as `CR`. An empty
`S" "` will not compile in this kernel - the definition silently
fails to complete and the word comes back undefined - so the byte
constant is the way to write exactly a newline and nothing else.

stdout is now byte-identical to bash's for piped scripts; the prompt
and its newline are on fd 2, where they were always meant to be.

**Still divergent, deliberately:** this shell prints a prompt even
when stdin is not a terminal, which the others do not. That needs an
`isatty`, the engine has no primitive for it, and adding one means
touching `cross.4`'s hand-embedded dispatch numbers - not something to
do in a stabilization pass, and especially not immediately before the
token-threading work rearranges that area anyway. On stderr the
remaining divergence no longer corrupts stdout, which was the part
that mattered.

### Tests

`tests/shell/run-piped-stdout`, 5 assertions, using a new
`assert_output_equals` rather than the substring form - a substring
assertion here would pass against the exact bug the file exists to
catch. One case asserts a silent script produces **empty** stdout,
which a substring assertion can never express, since "" is a
substring of anything. One asserts the prompt is still written to
stderr, so a "fix" that simply deleted it could not pass. Confirmed
non-hollow: all 5 fail against the old `shell.4`.

`lib.sh`'s header is corrected to say the justification expired, and
to point new tests at the strong form. The 63 existing files are
left alone on purpose: rewriting them all at once is a large untested
change, and this entry is not evidence for doing it blind.

Sizes grew slightly, `WRITE-FILE` costing more than `."`:
i386 127,296 -> 127,356 (+60), x86-64 228,480 -> 228,592 (+112).
Both images still reproduce on both cell widths; mrsh, the POSIX
corpus and the differential suite are all unchanged.

### Also still open from the 151 audit

Unrelated to the prompt, found while checking whether diagnostics
share the problem: **the shell prints nothing at all for an unknown
command.** `relfsh -c nosuchcommand` exits 127 with both streams
empty, where bash reports "command not found" on stderr. This is why
152's status-127 bug was silent rather than merely wrong. Not fixed
here.

Also outstanding: `MAX-ARGS` failing silently at 64, the nine dead
variables, and the rest of the duplication pass.

## Iteration 154: two silent failures, and a third found by fixing them

Continues the theme of 150-153: this project's characteristic bug is
not a wrong answer, it is a wrong answer delivered without a word.

### 1. No "command not found"

`relfsh -c nosuchcommand` exited 127 with **both streams empty**.
`RUN-CHILD` is documented as returning only on total failure, and
every caller follows it with `127 SYS-EXIT`; nothing in between said
anything.

This is why Iteration 152's status-127 bug read as correct output -
the stray `{` segment was being run as a command name and failing
silently. One missing diagnostic hid another bug for an unknown number
of iterations.

Now `shell: <name>: command not found` on fd 2. Placed inside
`RUN-CHILD` so all four call sites get it. On fd 2 specifically
because this runs in the forked child, whose stdout may be the next
stage of a pipeline - verified that `nosuchcommand | cat` still gives
empty stdout, matching bash.

### 2. `MAX-ARGS` truncating in silence

70 arguments came back as 62 plus a spurious empty one, and
`set -- <70 words>; echo $#` printed 9. The command then **ran**,
with an argument list the script did not write. Iteration 90 gave
diagnostics to `SET-SHVAR`, `SET-FUNC` and the positional stack but
never reached this path.

Now `shell: too many arguments` on fd 2, status 1, and the line is
**not run**. Executing a command with quietly different arguments is
worse than refusing it.

**The instructive part** is where the flag had to go. The obvious
site is `TOKENIZE-RAW`, whose loop carries `ARGC @ MAX-ARGS 1- <`.
A check there never fires: `NORM-WORDS` is itself `MAX-ARGS` cells,
so `NORM-WCOUNT` is already capped by the time the tokenizer reads
it, and `TK-I` can never exceed it. The words are lost ~2500 lines
earlier, in the normalizer's word-recording step. The first attempt
was written at the obvious site, produced no diagnostic at all, and
was only caught by running it - 122's rule, check *why* a test
passes, in its negative form.

### 3. A third silence, exposed by the first fix

With "command not found" in place, the 70-argument test printed an
extra `shell: 65: command not found`. That is not the argument limit.
**`LINE-MAX` is 256, and a script line longer than that has its tail
executed as a separate command.**

    linelen=256  ->  runs correctly
    linelen=260  ->  runs, then runs "xxxx..." as a command
    linelen=500  ->  runs, then runs the remainder

Same class as Iteration 150's `TIB 80 ACCEPT`, but worse: there the
tail was discarded, here it is *executed*. A 300-character line runs
a command nobody wrote. Not fixed here - `READ-LINE` returning
exactly `LINE-MAX` cannot be distinguished from a longer line without
a lookahead, so the fix needs a design rather than a patch, and this
entry is already two fixes long. It is the strongest remaining item
in the backlog.

### Stderr, and the older diagnostics

`ERR-TYPE`/`ERR-CSTR`/`ERR-NL` are defined right after `CSTRLEN`,
early enough for `RUN-CHILD`. `shell.4`'s **older** diagnostics -
"cd: no such directory", "shell: syntax error: ...", "alias: too many
aliases" - still use `."` and so still go to **stdout**, which is
wrong for the same reason 153's prompt was wrong. Moving them is a
separate change with its own test churn; recorded here rather than
folded in.

### Tests

`tests/shell/run-diagnostics`, 11 assertions. Every one checks stdout
separately from stderr, since a diagnostic landing on stdout is 153's
bug returning. Includes the pipeline case, a successful command
asserting **empty** stderr, and 50 arguments still running silently so
a fix that moved the limit down could not pass. The 70-argument case
uses one-character words on purpose, keeping the line under
`LINE-MAX` so it tests the argument limit and not finding 3 above.
Confirmed non-hollow: 5 of 11 fail against the old `shell.4`.

Sizes: i386 127,356 -> 127,684, x86-64 228,592 -> 229,160. mrsh, the
POSIX corpus and the differential suite are unchanged; both images
reproduce on both cell widths.

## Iteration 155: preparing the instruments for the engine work

Neither of these is a bug fix. Both are about being able to TELL
whether the engine work went wrong, which is the part that has to
exist before it starts rather than after.

### 1. Both base images are regenerated, and both are checked

`tests/run_tests.sh` regenerated `kernel32.img` from `cross.4` +
`kernel.4` on every run, but `kernel.img` was only ever consumed. So
for the 8-byte width - the one the project develops on - "cross.4
still produces the image we ship" was **unverified**, and the base
images were never compared against their committed forms at all.

That matters more for 8 bytes than for 4, because the 8-byte image is
simultaneously the image the cross-compiler PRODUCES and the image it
RUNS ON. It is the fixpoint the whole bootstrap rests on, and token
threading rewrites primitive encoding in `cross.4`, which is exactly
what would break it.

Both widths now go through one `cross_compile_image` function, both
are regenerated before the suites, and **the Forth core suite runs
against the regenerated images** rather than against committed
binaries that may no longer match the sources. Two new tracked
numbers, `image:8byte-fixpoint` and `image:4byte-fixpoint`. Both
report `reproduces` today - so the cross-compiler does reach its
fixpoint, which had never been demonstrated.

Confirmed non-hollow, eventually. The first probe appended a
`VARIABLE` to the end of `kernel.4` and both checks still said
`reproduces`. That was the probe's fault, not the check's:
`kernel.4` ends with `END-CROSS`, so anything after it is not
cross-compiled at all. Inserting the same line *before* `END-CROSS`
moved the image from 23,384 to 23,424 bytes and both checks reported
`DIFFERS`. Worth recording as a small trap for anyone editing
`kernel.4`: text after `END-CROSS` compiles into the host, not the
target, and changes nothing about the image.

### 2. `tests/bench` now produces a measurement rather than a sample

The old harness took **exactly one timing** per shell per workload and
printed it as a bare number, with no indication of its uncertainty.
It was nevertheless the instrument for `TOKEN-THREADING.md`'s
decision rule:

    "If that experiment says 1.15x or worse, this proposal is a size
     change that costs speed."

Deciding a 15% threshold from single runs was not possible. Measured
before the rewrite: the loop workload's per-run CV is around 3.5%, so
one run carries about +/-7% at 95%, and the DIFFERENCE of two single
runs about +/-10%. A borderline result - 1.12x against 1.18x - was a
coin flip. Iteration 151's stack bounds, at 2.4-3.1%, were entirely
invisible to it.

What it does now, and what each part means:

  - **BENCH_REPS samples per cell** (default 7), with BENCH_WARMUP
    rounds discarded rather than averaged in.
  - **Interleaved rounds**: every shell sampled once, then again, so
    drift over the run is charged equally to all of them. Measuring A
    fully and then B fully is the easiest way to manufacture a
    difference that is not there.
  - **Mean +/- the half-width of a 95% CI on that mean**, as a
    percentage: `t(0.975, n-1) * s / sqrt(n)`. Student-t rather than
    1.96 because the default n is small - at n=7, 1.96 understates by
    about 25%.
  - **min and median alongside**, as a skew check. Timing data is
    right-skewed; a hiccup can only make a run slower. If mean sits
    well above median, the interval is understating the uncertainty
    and should be said so rather than quoted.
  - **A resolution line**: the smallest relative difference the run
    could call at 95%, about sqrt(2) times the half-width since
    uncertainty on a difference compounds.

Two design points found by running it, not by thinking about it:

**The resolution figure is quoted for the shell under test only.**
The first version took the worst half-width across every row, which
let `dash`'s 3ms loop timing set the resolution. At 3ms with
millisecond granularity the clock alone contributes ~+/-33%, and no
number of samples fixes that. The question this instrument serves is
"is build B of this shell slower than build A", to which dash is not
a party. Rows near the timer floor are now marked as such.

**Raising BENCH_REPS does not monotonically improve the interval.**
Measured: n=5 gave +/-3.7% on the loop ratio, n=15 gave +/-7.2%, with
mean above median in the longer run. The variance is not stationary -
a longer run spans more of whatever else the machine is doing - so a
bigger n buys a better estimate of a distribution that is itself
moving. Interleaving protects the comparison; nothing protects the
absolute numbers. Recorded in the header, with the advice to prefer
two runs that agree over one long one.

**Where that leaves the decision.** Loop resolution now lands around
+/-4% on a ratio at n=5, against a 15% threshold. The decisive
experiment is instrumentable, which it was not before. It should
still be run twice.

Neither change touches the shell or the engine; sizes, mrsh, the
POSIX corpus and the differential suite are all unchanged.

## Iteration 156: comparing encodings, with SOD32 in the table

A design conversation about instruction encoding produced a lot that
existed nowhere in the repository, including a proposal that Iteration
132 had already measured and rejected. `ENCODING-COMPARISON.md` and
`tools/encoding-census.py` exist so the next session inherits the
numbers instead of re-deriving them.

### The freeze

`freeze/iter156-encoding-baseline` tags the tree these numbers come
from. RelF is the right baseline for this comparison for a reason SOD32
cannot match: it builds **both cell widths from one image**, so a
scheme that saves cells can be distinguished from one that saves bytes.
That distinction turns out to decide the whole question.

### SOD32's real encoding, from the author's own source

Fetched from `github.com/lennart-benschop/sod32` rather than
reconstructed from memory. `sod32.txt` gives it exactly:

    bit0=0 bit1=0   CALL     target in bits 31-2
    bit0=0 bit1=1   JUMPZ    target in bits 31-2
    bit0=1          six 5-bit subinstructions, bit31 = return flag

Two things stand out against the schemes proposed in conversation.

`5 bits x 6` is a better bit budget than `4 bits x 7`: 32 opcodes
against 16, costing one slot the code does not use, because the mean
run of packable primitives is 1.34 and 75.5% of runs are a single
operation. Slot count is nearly free; opcode width is not.

And **SOD32 has no unconditional branch**. It synthesises one as
`push0` then `JUMPZ`, spending a subinstruction rather than a tag
class. Unconditional branches are 365 sites against `?BRANCH`'s 863,
so a whole tag class is poor value. Under goal 3 that is the more
minimal design, and it is a twenty-year-old one.

### The table

Word bodies only, macros applied per scheme by profitability:

| scheme | cells | i386 | x86-64 | vs today |
|---|---|---|---|---|
| RelF today | 16862 | 67448 | 134896 | 1.00x |
| SOD32 authentic | 14639 | 58556 | 117112 | 0.87x |
| SOD32 fields + inline literals | 12338 | 49352 | 98704 | 0.73x |
| tagged nibble (4-bit x7) | 12692 | 50768 | 101536 | 0.75x |
| tagged byte (8-bit x3/x7) | 12573 | 50292 | 100584 | 0.75x |
| tagged byte + hot-call | 11759 | 47036 | 94072 | 0.70x |
| token-threaded bytes | - | 25639 | 25639 | 0.38x / 0.19x |

SOD32's format with one addition beats the nibble proposal and ties the
byte one. Only token threading breaks the cell-width coupling, and
x86-64 at 1.76x dash is where this project's size problem actually is.

### The finding that outranks the table

**45.7% of call sites are pushing a data address** - 2,557 sites over
432 `VARIABLE`/`BUFFER:`/`CONSTANT` words, each paying a call, a
`DOVAR` dispatch and a return to deliver a compile-time constant. The
distribution is flat, so no small table captures it, but the operation
is uniform and its payload is an address rather than an identity. None
of the schemes above touches it. It is the largest unexploited
regularity found and it has not been designed.

It also settles an open question: variable references *are* compiled as
calls, so the 452 data words consume call indices. Token threading's
1,024-target extended call is therefore already over budget against
1,060 dictionary entries - before any bash or busybox work. A third
call width (one prefix, two index bytes, 65,536 targets) costs one
first-byte value where widening by prefixes costs 256 targets each.

### Two corrections to earlier work in this session

The hot-call index, proposed and measured here, is the weakest idea in
the table despite the best cell count: only 12.9% of call sites can
actually fold, the rest sitting next to another call or branch where
the pack is empty. It needs a two-pass build and a generated offset
table and cannot include runtime-defined words. Recorded so it is not
re-proposed.

And the first version of the census resolved call targets as
`addr + value` rather than `addr + CELL + value`, which is what `NEXT()`
does - 24 of 6,548 calls resolved and the conclusions drawn from it
were worthless. The tool now handles inline strings and `(LOOP)`
operands too, which is why its op count (14,909) is lower and more
trustworthy than the 19,104 quoted mid-conversation.

### Still not measured

Speed. Every number is size. Iteration 134's objection to two-bit tags
- a second data-dependent test on the two hottest paths - is
unanswered, and Iteration 133's stated experiment (build both,
alternate `tests/bench`) is now runnable at about +/-4% on a ratio
thanks to Iteration 155.

## Iteration 157: the speed half of the encoding question

`ENCODING-COMPARISON.md` sized five encodings and could not choose
between them, because every number in it was bytes while the open
objection was about time. Iteration 134 argued that a tag plus a packed
field adds a second data-dependent test to the two hottest paths in the
interpreter, and Iteration 133 left the experiment stated but never
run. `tools/pack-bench.c` runs it.

### Method

Four inner loops doing identical work on the same operation stream,
differing only in fetch and decode: `CELL` (RelF today), `PACK5`
(SOD32 authentic - six 5-bit subinstructions, return flag in bit 31),
`PACK4` (the tagged-nibble proposal), `PACK8` (the tagged-byte
proposal). Nine interleaved rounds, minimum of each, because
run-to-run drift on this machine is larger than the effects.

The operation mix is **dynamic, not static**, and that is the point.
`tools/dispatch-bench.c` uses the static mix because it was answering a
size question. Dispatch cost depends on what executes, and Iteration
155's profiling showed the two differ sharply - calls are 46.3% of the
image but 24.9% of execution, `EXIT` is 3.6% static and 17.3% dynamic.
Using static counts here would overstate calls by nearly 2x, and calls
are exactly the operation packing cannot help with, since they end a
pack. It would have flattered the packed schemes.

### Result

    x86-64:   cell 1.00   pack5 1.21   pack4 1.65   pack8 1.60
    i386:     cell 1.00   pack5 1.68   pack4 2.05   pack8 1.90
    token threading (tools/dispatch-bench.c):     0.985

Packing costs 20-66% on x86-64 and 68-105% on i386. Token threading
costs nothing - it is marginally faster than cell dispatch.

Iteration 134's objection is confirmed. It is worse on i386, where a
32-bit pack holds fewer fields so pack boundaries come round more
often.

SOD32's 5-bit format is again the least bad packed scheme, as it was on
size. Its 1.21x also sits inside `GOALS.md`'s recorded "SOD32 27-51%
slower" from twenty years ago on different hardware, which is some
evidence both numbers are measuring something real.

### Both axes together

    scheme                    size (x86-64)   dispatch
    RelF today                     1.00         1.00
    SOD32 + inline literals        0.73         1.21
    tagged nibble                  0.75         1.65
    tagged byte                    0.75         1.60
    token threading                0.19         0.985

**Token threading dominates every packed scheme on both axes at once.**
The packed designs buy 25-30% of size for 20-65% of dispatch; token
threading buys 81% of size for nothing. Under goal 3 it is also the
simpler object: no shift register, no nibble alphabet, no SPECIAL
escape, no hot-call table, no two-pass build.

That closes the design question this pair of iterations was opened to
answer. The tagged/packed direction, which several sessions and a long
design conversation converged on, is the wrong one, and it took a
measurement rather than an argument to establish that.

### What this deliberately does not measure

**Cache effects.** The streams are sized to run hot, so density gets no
credit for touching less memory - this is the pessimistic case for
packing, and on a real workload the packed schemes would do better than
1.21x, possibly much better. It is the main reason these ratios are a
guide to where to spend effort rather than a verdict.

**A real engine.** This is a synthetic stream, not RelF executing.
Real dispatch is interleaved with the primitives' own work, which
dilutes decode cost as a share of runtime, so 1.21x here does not mean
1.21x on `tests/bench`. The end-to-end experiment is still the one
Iteration 133 specified, and `tests/bench` can now resolve about +/-4%
on a ratio.

## Iteration 158: variable-length tokens, and the table nobody costed

### First, a correction to Iteration 157

157 reported token threading at 0.985 - marginally FASTER than cell
dispatch - and concluded it "costs nothing". That was wrong, and wrong
in a way this repository has a rule about.

The figure came from `tools/dispatch-bench.c` at its single built-in
stream size, 2^22 operations, where the cell stream is 32MB against the
byte stream's 6.8MB. This machine's L2 is 2MB. Both streams miss, but
the cell stream misses 4.9x harder, so the number was measuring memory
traffic and being read as a decode result. Varying the working set:

    stream (cell)      byte/cell-offset
      16 KB (L1)            1.063
     128 KB                 1.064
       1 MB                 1.059
      32 MB                 1.002

Token threading costs about **6% in decode**, repaid only when the
working set is large. `pack-bench.c`'s header claim that its streams
"run hot" was false for the same reason - they are 13-18MB.

The packed schemes' penalty, by contrast, holds at every size (pack5
1.27 at 9KB, 1.23 at 18MB), so 157's central conclusion - packing is
the wrong direction - survives. What does not survive is "threading is
free".

### Variable-length tokens

`tools/varint-bench.c`. A continuation-bit encoding, UTF-8 in shape:

    0xxxxxxx                  opcode 0..127
    1xxxxxxx 0yyyyyyy         14-bit token
    1xxxxxxx 1yyyyyyy 0zzz..  21-bit, and onward without limit

This removes the ceiling that `TOKEN-THREADING.md`'s fixed 2-byte call
has, and that ceiling is not hypothetical: 1,024 targets against 1,060
dictionary entries today, variables included.

Against the fixed 2-byte form, same tool, near-identical loops:

    working set small   varint 1.03   two-byte case peeled 0.84
    working set large   varint 1.12   peeled 1.10

2-3% when cache-resident, 11-12% when not, for under 2% more bytes.
And the comparison flatters the fixed form, which masks its index to 10
bits and so cannot represent the 20,000 targets in the stream at all.

### What the word table costs as the dictionary grows

The question that had not been asked. Every indexed encoding needs a
`wordtab` lookup; RelF needs none, because the offset IS the
instruction. Sweeping the word count at a fixed stream size:

    words      table     varint/cell
      1,000      7 KB       0.735
      8,000     62 KB       0.727
     65,000    507 KB       0.820
    500,000   3906 KB       0.815
  2,000,000   15.6 MB       0.824

**The indexed scheme loses ~12% of its advantage once the table stops
fitting in L2**, with the knee between 8,000 and 65,000 words. RelF
pays none of this, and the cost grows in exactly the regime the project
is aiming at - bash compatibility plus busybox-style applets, where the
definition count is the thing that is supposed to grow without limit.

The `fixed` column appears immune only because its 15-bit index cannot
address beyond 32,767 words, so it keeps touching a smaller footprint.
Not a result.

### Where this leaves the comparison

Density and dispatch pull in opposite directions and both depend on
scale:

  - packing: 1.35x density, 20-66% dispatch cost, at every size. Ruled
    out by 157 and nothing here changes that.
  - indexed byte tokens: ~5-7x density, ~6% decode cost, plus a table
    cost that starts near zero and reaches ~12% at 65,000 words.
  - RelF today: no table, no decode cost, and a cell per operation.

157's claim that token threading "dominates on both axes" does not
survive. It dominates on density; on dispatch it is behind, and falls
further behind as the dictionary grows.

### Unreconciled, and it matters

`varint-bench.c` and `dispatch-bench.c` DISAGREE about the cell
baseline: here cell is slower than byte at every size (0.69-0.83),
there byte is ~6% slower at L1 sizes. Two tools, two answers, not
reconciled - most likely the loops are not doing equivalent work per
iteration. Trust the within-tool comparisons (varint vs fixed, and the
word-count sweep); do not trust either tool's cell baseline until they
agree. Three times in this line of work a dispatch ratio has turned out
to be measuring something other than dispatch, and each time the cause
was a single configuration with no cross-check.

## Iteration 159: token width, and a table that lives outside the image

### Varint cost grows steeply with width

158 measured varint against a fixed 2-byte token on a natural mix and
got 1.03-1.12x. That mix was mostly 2-byte tokens, so it did not answer
the obvious question. Forcing every cold call to a fixed width
(stream 2^14, table resident):

    width   varint/cell   peeled/cell   stream KB
      1        0.44          0.36         17.9
      2        0.98          0.73         21.9
      3        1.16          1.15         26.0
      4        1.31          1.07         30.0

**About 15% per additional byte.** The loop's exit is data-dependent,
so a stream mixing widths mispredicts on every change.

That matters because the scaled-offset scheme of 158 lives at width 3:
the dictionary span is 27,306 slots on i386 and 25,660 on x86-64,
15 bits, before any growth. So the offset variant sits at ~1.16x, not
the 1.03x quoted from the natural mix.

Peeling the two-byte case out of the loop is worth a lot at width 2
(0.73 against 0.98) and nothing beyond it. If a varint scheme is used
at all it should be written that way.

### Fixed width is not automatically cheaper

    fixed2   5.3 ms   1.00     20,588 bytes
    varint   6.2 ms   1.18     20,987
    fixed3   7.8 ms   1.49     22,831

A fixed 3-byte token costs ~49% over a 2-byte one - steeper than "one
more byte" suggests, and worse than varint on the same stream. Note
`fixed2` cannot represent the 20,000 targets in the stream (it masks to
10 bits), so it is a floor rather than a contestant.

Also corrected here: with a one-byte opcode band, an extended token has
only 7 bits in its first byte. So 2 bytes reaches 32K words and 3 bytes
reaches 8M - not the 64K and 16M that a full-width reading suggests.
And an earlier "fixed3" measurement in this session was actually a
4-byte encoding, prefix plus three index bytes, which is why it looked
so bad.

### The uniform 16-bit token

Proposed in conversation and the simplest thing yet measured. Every
operation is one 16-bit token: `v < 256` selects a primitive or inline
form, `v >= 256` is a word number. No tag, no varint, no packing, no
branch on width - one aligned load, one compare, one branch.

    u16   0.97-1.07 x cell time   36,690 bytes   4.0x smaller than cell

Two bytes per operation against a cell's four or eight, so **2x on
i386 and 4x on x86-64**, uniform across widths, which none of the
offset schemes managed. Less dense than variable-width byte tokens
(7.1x here) but far simpler.

It measured at parity with cell dispatch and slower than the
variable-width byte scheme, which is unexplained. Recorded as measured
rather than rationalised.

### The table outside the image

The strongest idea in this exchange, and it is about where the table
lives rather than how tokens are encoded. A word-number table held in
malloc'd memory rather than in the image is **derived data**:

  - rebuilt at startup by walking the dictionary link chain, so word N
    is the Nth entry and the compiler and loader agree for free;
  - never saved, so `SS-SCRUB` has nothing to clean and the image does
    not grow;
  - rebuilt after load, so it can hold ABSOLUTE addresses - dispatch is
    one load with no base add and no shift, cheaper than every
    in-image variant discussed;
  - grown by realloc outside `mem[]`, so it never collides with `HERE`
    and a runtime-defined word just appends.

Load-time cost is a walk over 1,000-20,000 words against a 1.8ms
startup, i.e. noise.

### Confidence, and what to do next

Three dispatch results in this session have come out contrary to
expectation, and `varint-bench.c` and `dispatch-bench.c` still disagree
about their cell baselines. The marginal value of more microbenchmarking
is low. The uniform 16-bit design is simple enough - fewer concepts
than the current cell scheme, not more - that building it and running
`tests/bench` end to end would settle more than another synthetic loop.
That is Iteration 133's stated experiment, now resolvable to about
+/-4% since Iteration 155.

## Iteration 160: the token prototype, and a bug in every number before it

### The bug first

`tools/encoding-census.py` read an inline counted string's length as a
CELL. `(S")` is `R> COUNT 2DUP + ALIGNED >R` - `COUNT`, so the length is
a **byte**. Reading four bytes of string data as a length produced a
nonsense span, `a` jumped past the end of the word, and the decode loop
stopped early. Every word containing an inline string was silently
truncated.

Corrected, the census moves substantially:

    ops    14,909 -> 18,121   (+21.5%)
    cells  16,862 -> 21,075
    calls   6,596 ->  8,120

Every absolute figure quoted from this tool in Iterations 156-159 was
low by about a fifth. The ratios barely moved and no conclusion
changes, but the numbers in `ENCODING-COMPARISON.md` are wrong and the
document should be regenerated rather than read.

The bug surfaced only because `tools/tokenize-image.py` accumulated the
bad span instead of just skipping past it, and reported a word-body
size of 53 GB. A wrong answer large enough to be obviously wrong is a
lucky bug; the census had been quietly wrong for four iterations.

### The prototype

`tools/tokenize-image.py` translates real compiled word bodies into the
uniform 16-bit token stream discussed in Iteration 159. Not an engine -
a measurement of what the image would weigh, on real code rather than
on a synthetic stream, which is what every previous number here rested
on.

Encoding: one 16-bit token per operation, `0..255` a primitive or
inline form, `256..65535` a word number. Operands follow as further
tokens - `LIT16` one, `LIT32` two, branches one signed offset in token
units. No tags, no varint, no packing, no branch on token width.

    word bodies      cell form    token form
    i386              92,616 B     52,942 B     0.57x
    x86-64           182,456 B     60,668 B     0.33x

Two design assumptions checked rather than assumed, and both hold: the
highest word number any call uses is **1,044** against a 65,279
ceiling, and **zero** branch offsets need more than 16 signed bits. The
two widths differ only because more literals need `LIT32` on 64-bit
(952 against 787).

### Where it sits

Against the corrected census, on x86-64:

    packed schemes            0.71 - 0.76x
    uniform 16-bit token           0.33x
    variable-width byte stream     0.19x

The uniform token is worse than variable-width threading and much
better than anything packed, while being the simplest of the three:
one aligned load, one compare, one branch. On dispatch it measured at
parity with cell in Iteration 159's microbenchmark.

### What is still missing

An engine. Everything above is size; the speed figures come from
synthetic loops whose `cell` baselines still disagree between
`varint-bench.c` and `dispatch-bench.c`. A real comparison needs a
`cross.4` variant emitting tokens and an engine decoding them, and then
`tests/bench` end to end. The translator is a step toward that - it
proves the encoding covers the real instruction mix and that the field
widths are adequate - but it does not execute anything.

Also unmodelled: headers, 16,576 bytes this scheme does not touch, and
data-word bodies, which are copied verbatim.

## Iteration 162: branch `token16`, and a translator that proves itself

First commit on branch `token16`, off `c1d14ac`. The plan agreed: build
the uniform 16-bit token engine first, leave varint for later if it is
ever wanted.

### Why the round trip came before the engine

This session found two silent decoder bugs in analysis tools of exactly
this shape, and each invalidated numbers already reported with
confidence: call targets resolved as `addr+value` instead of
`addr+CELL+value`, matching 24 of 6,548 calls; and an inline counted
string's length read as a CELL when `(S")` uses `COUNT`, so every word
containing a string was truncated and the operation count was low by
21.5%.

Both produced plausible output. Neither was caught by reading the code.
An engine built on an unvalidated translator inherits the same class of
fault, and there the symptom is a corrupt image rather than a wrong
number.

So `tools/token16.py` decodes its own output and asserts equality
against the input, per word. That check paid for itself immediately -
it caught two more bugs that size-counting alone would have missed:

  - `(LOOP)`'s operand is emitted as a bare token and was being read
    back as a call, because operands are POSITIONAL: only the operation
    that emitted one knows it is there. `tokenize-image.py` never
    noticed, because it only counted.
  - signed operands were not sign-extended on decode, so `-24` came
    back as `65512`.

### Result

    round trip: 531 words reproduce exactly, 0 differ  (both widths)

    word bodies      cell form    token form
    i386              92,616 B     54,084 B    0.584x
    x86-64           182,456 B     62,626 B    0.343x

Slightly larger than `tokenize-image.py`'s estimate (52,942 / 60,668)
because that tool approximated inline strings while this one encodes
them exactly and can prove it. **The verified numbers are the ones to
use.**

### Scope, stated plainly

This translates a fully built image. It does not make the Forth
compiler emit tokens - `,` and `:` still build cell code - so a
translated image can run but cannot compile new definitions. That is
enough to measure size and dispatch on real code, and not enough to
self-host, which is a later problem and the one that will decide
whether this encoding can actually replace the current one.

Next: the engine. A `NEXT()` that reads one 16-bit token, compares
against 256, and either dispatches a primitive or calls
`wordtab[v-256]`; the table rebuilt at startup from the dictionary link
chain, held outside the image, in absolute addresses.

## Iteration 163: the dispatch core, running real code

`tools/token16-engine.c`. The decode loop and the table rebuild, run
against real translated word bodies rather than a synthetic stream.

    loaded 1082 words, 22492 tokens (44984 bytes of code)
    table: 1082 entries x 8 B = 8656 B, OUTSIDE the image
    executed 6,477,050 operations in 15.1 ms -> 428 Mops/s

`tools/token16.py --emit` now writes a loadable form, deliberately
plain text so it can be checked by eye and by diff. `CELLB`, which is
`: CELLB 1 CELLS ;`, comes out as `2 1 1279 1` - `LIT`, the value 1,
call word 1279 (`CELLS`), `EXIT`. That is the whole encoding, visible.

### What this establishes

**The table is derived, and the image carries none of it.** Word N is
the Nth record in chain order - here the Nth `W` record, in the real
engine the Nth entry walking the dictionary link chain. Same numbering,
same rebuild. The 8,656 bytes it occupies are outside the image
entirely, which is why the size figures never counted them.

**It holds absolute addresses**, fixed up at load, so dispatch is one
load with no base add and no shift:

    ip = wordtab[v - 256];

**Decode is one 16-bit read, one compare against 256, one branch.** The
loop is in the file and is shorter than the cell version it would
replace, which is the goal-3 argument for this design independent of
any measurement.

Operand handling repeats the lesson that cost two bugs in the
translator: `LIT`, `LIT32`, the branches and `(S")` all consume
positionally, because only the operation that emitted an operand knows
it is there.

### What it is not

Primitives are stubs that touch the data stack so dispatch cannot be
optimised away; they do not implement Forth. That is deliberate and
sufficient - the question is what DECODE costs on a real instruction
mix, and a stubbed primitive answers it as well as a real one while
keeping the prototype small. But it means this cannot run the shell,
and the 428 Mops/s figure is a decode rate, not a comparison against
`relf`.

A like-for-like number needs the real primitives, and a self-hosting
image needs the Forth compiler to emit tokens - `,` and `:` still build
cells. Both are larger than this file, and the second is the one that
decides whether this encoding can replace the current one rather than
merely be measured beside it.

## Iteration 164: naming it SOD16, and an honest gap list

The uniform 16-bit token design is now **SOD16**, and the tools are
`tools/sod16.py` and `tools/sod16-engine.c`.

The name is meant as a claim about lineage. SOD32 packed six 5-bit
subinstructions into a 32-bit cell and paid shift/mask/counter work on
every operation. SOD16 spends a whole 16-bit token per operation and
pays none. Measured, that trade is worth taking: the packed form costs
21-68% in dispatch (Iteration 157) to buy density that a plain 16-bit
token gets more of anyway (0.343x against 0.75x on x86-64).

### Is it complete? No. Can it run shell.4? No.

Worth stating precisely, because "the engine runs real translated
words at 428 Mops/s" invites the wrong conclusion.

**64 of 68 primitives are unimplemented.** Every primitive in
`kernel.4` appears in the compiled bodies - all 68 - and the engine
implements exactly five, all of which are decode rather than
semantics: `LIT`, `LIT32`, `BRANCH`, `?BRANCH`, `EXIT`. The rest are
stubs that push a value so the dispatch loop cannot be optimised away.

**Addresses move.** Translated bodies are a different size from cell
bodies, so every address in the image shifts. Dictionary link fields,
`HERE`, anything a `VARIABLE` holds that points into the image - all of
it needs relocating. The translator does not attempt this; it emits
bodies in isolation.

**Execution tokens are unresolved, and this is the deep one.** `'`
returns an xt, which today is an address. There are 182 tick sites, 17
`DEFER` declarations, 12 `IS` patches, 11 `EXECUTE` sites and 2
`SET-BOOT` calls. In SOD16 an xt could be a word number or an address,
and the choice reaches `EXECUTE`, `DEFER`/`IS`, `SET-BOOT`, and every
place the shell stores a word for later. Nothing here decides it.

**The Forth compiler still emits cells.** `,` and `:` build cell code,
so a translated image can run but cannot compile new definitions. Self
-hosting needs `cross.4` to emit tokens, which is where its
hand-embedded dispatch numbers finally have to be touched - the thing
`GOALS.md` has warned about since phase 3 was written.

### What IS established

  - the encoding is lossless: 531 words round-trip exactly, both widths
  - it is dense: 0.584x on i386, 0.343x on x86-64, verified not estimated
  - the field widths are adequate: highest word number 1,044 against a
    65,279 ceiling, zero branch offsets past 16 signed bits
  - the table is derived and lives outside the image: 8,656 bytes that
    the size figures correctly never counted
  - decode is one 16-bit read, one compare, one branch

That is a validated encoding and a demonstrated decode path. It is not
an engine, and the 428 Mops/s figure is a decode rate, not a
comparison against `relf`.

### The order the rest should go in

1. Real primitives, giving a like-for-like `tests/bench` number against
   `freeze/iter156-encoding-baseline`. Largest mechanical job, least
   design risk.
2. Decide what an xt is. Small change, large blast radius - it should
   be decided before the primitives are written, not after.
3. Image relocation, so a translated image loads and runs.
4. `cross.4` emitting tokens, for self-hosting. The one that decides
   whether SOD16 can replace the current encoding or only sit beside it.
