# PROGRESS.md — RelF self-hosting project log

Append-only. Newest entries at the bottom. This log exists so future work
(including future Claude sessions, which have no memory of prior ones)
doesn't silently retry a path already found to be wrong.

**For project context, priorities, and phase plan, read `GOALS.md`
first** — that's the stable reference. This file is only the log of what
was actually done, in order, and shouldn't repeat what's already stated
there.

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
