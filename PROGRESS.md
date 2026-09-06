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
