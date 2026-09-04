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
