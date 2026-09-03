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
