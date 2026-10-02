# OPTIMIZATIONS.md - potential future optimizations

A catalog, started at Iteration 545 at the user's request: ideas for
speed, memory and size, each with the evidence behind it, what it would
gain, what it would cost, and where it stands. Optimization is stopped
(QUESTIONS.md A13: simplicity first); this is so that when an entry is
taken up, nothing has to be measured again. The measurements themselves
are in FINDINGS.md; the tools that made them are named.

Status: **open** (not tried), **tried** (built and measured, kept),
**removed** (built, measured, taken out for simplicity), **declined**
(measured, not worth it now).

## Speed

**S1. `+LOOP`, `J` and `2/` as primitives** - open.
Evidence (FINDINGS.md 1.1a, 544): gforth is faster than relf because of
which words are primitives, not because of native code - its dynamic
superinstructions are worth ~3%, and its plainest engine still beats
relf 3x on the sieve. Where relf loses, a colon word sits in the inner
loop: `+LOOP` and `J` in the sieve (~25 dispatches an iteration against
gforth's handful), `2/` in collatz (eight operations; relf's RSHIFT is
logical). Gain: the sieve and collatz near gforth-itc (sieve 488 -> ~160
ms, estimated). Cost: three handlers per engine, escaped so the 64 one-
byte opcodes stay 64; one iteration, like 530's loop words.

**S2. Runtime words as opcodes** - tried (528-531), kept.
`+!` `?DUP` `I` `(LOOP)` `(?DO)` `EXECUTE` `@XT`: 15% fewer dispatches,
and simpler Forth (no return-address lifting in the loop words). The
profile names more: the DEFER runtime (~2%), words in the shell's tree
reader (`X@`, `XF@`). tools/profile.py.

**S3. Superinstructions** - removed (536).
`VAR@` fused with `+ < 1+ C@`, and compare-and-branch: ~8% of the
realistic script's dispatches, ~13% of the whole mix. Cost: a peephole
that rewrites compiled code, two operand formats, nine handlers per
engine. tools/superinst.py ranks the pairs: fusing the top 32 would save
~15-21%.

**S4. Folded returns** - removed (538).
A primitive and the EXIT after it as one opcode: 5.4% of dispatches, for
22 handlers per engine and the folding in both compilers.

**S5. Tail calls** - open.
A call followed by EXIT becomes a jump: one dispatch and one return-
stack push and pop saved. Ceiling: EXIT is 5.5% of dispatches (536).
Cost: the compiler's `;`, and excluding words that read their own return
address (`(S")` and its kind, DOES> tails).

**S6. Inlining small colon words** - open.
Calls and returns together are ~20% of dispatches (536): the ceiling for
any threaded-code technique that removes them. Cost: the compiler copies
bodies - re-encoding their self-relative operands (slots), turning an
inner EXIT into a branch, refusing words that touch the return stack -
and the image grows.

**S7. Native code: subroutine threading, dynamic superinstructions,
JIT/AOT** - open; GOALS.md goal 2, to revisit once relf builds its own
engine (A14 d). The large gains (2-5x over threaded code, typically),
built on the self-hosted assembler. Evidence against starting there: in
gforth 0.7.3 on these benchmarks, copying native code was worth ~3%; the
primitive set (S1) matters more. Iteration 608: the user's idea - an
optimizing native compiler, beside CV8 - designed in docs/NATIVE.md
(N0), waiting on QUESTIONS.md Q33.

**S8. The dispatch loop itself** - declined (526).
Both engines dispatch at the CPU's indirect-jump rate, 0.8 ns; better
handler code cannot help, and two tries made it 10% slower by moving
code.

**S9. The shell: hot operations as primitives** - open (Q16 B, 534).
Name hashing, variable lookup, string comparison - where the profile
spends. Perhaps 2-5x on scripts. Cost: engine size in two engines, and
shell logic out of Forth.

**S10. The shell: less work per operation** - open (Q16 C, 534).
Resolve variables to slots when a function or loop is parsed, expand
constant words once, compile the parsed tree into threaded Forth instead
of walking it. Perhaps 5-10x on loops and functions - relf's scripts are
~30x dash's time. Where Rill's "text never re-read" already points.

## Memory (FINDINGS.md 8, 545)

The user's goal (A18, 546): minimize relfsh's RAM - revisited once relf
assembles its own engine (GOALS.md, "After self-hosting").

**M1. Do not zero what the system already zeroed** - **done (551)**: the
allocator's memory is zero (calloc in C; a reused block zeroed in the
assembly engine), the pool's fills gone - 40 kB.
The shell allocates its ~140 buffers at startup, and pool.4 fills each
with zeros - but the allocator's memory comes fresh from mmap, already
zero, and the fill makes every page resident, used or not: 152 kB of the
assembly shell's 308 kB at idle. Skipping the fill for fresh memory
would leave unused buffers untouched. Cost: the pool knowing which
memory is fresh.

**M2. Map the image, do not copy it** - declined, measured (551): a
prototype C engine mapped the shell image from a page-aligned offset
(copy-on-write, MAP_PRIVATE) instead of reading it in - and all 116 kB of
it were Private_Dirty at idle: every page of the image is WRITTEN at
startup. ALLOC-BUFFERS stores a pointer into each of 136 buffer
descriptors, spread through the dictionary, and the shell's variables
sit among its code, as a Forth dictionary interleaves them. Mapping pays
only once writable data is gathered apart from code - a restructuring,
not a loader change. What the prototype needed, for when it is: the
dictionary at a page-aligned offset in the file (padding when the shell
is embedded), since mmap wants address and offset congruent. (Kept
below as first written.)
**M2 as first proposed.**
Each relf process copies its image into its own memory region - a
private 118 KB, 132 kB resident with the stacks' pages. Mapped from the
file copy-on-write, the pages no one writes would be shared between
relf processes, as a C program's code is. (Forked children share their
parent's already.) Cost: the engines' loaders; the image's own writes
still copy their pages.

**M3. Allocate rarely used buffers on first use** - declined (551): it
would cost every buffer reference its one-fetch VAR@ form. Done instead:
**the buffers carved from one arena** - one header, not 136 - so a
buffer's pages are touched when it is used: 64 kB.
The line editor's buffers in a script, for instance. Overlaps M1.

## Size

**Z1. Fewer names** - declined (A20, 552): the Forth builtin keeps every
word.
Headers are 21-23% of the image; names pruned to an extension API would
save about a sixth of it. The largest size lever there is.

**Z2. Word order for near calls** - declined (542).
A call is 2 bytes to the first 16 KB, 3 beyond: the most-called words
moved there would save 2.1 KB, 1.8%, at the price of hoisting them and
all they depend on into an early source file. tools/call-layout.py.

**Z3. Calls relative to the call site** - declined; open again (579).
~0.7 KB (image-audit.py's model) was a SIGNED distance, 8 KB either way.
But a Forth word calls only words defined before it - forward only
through DEFER - so the distance back needs no sign: 16 KB behind in a
2-byte call (the user, 579). On the 122,004-byte shell image, 6,166
calls: today 2,498 near, 16,000 B; backward unsigned 3,863 near, 14,635
B - 1,365 B, 1.1%; either form by a bit, 13-bit offsets, 4,283 near,
14,215 B - 1.8 KB. Two calls point forward, both in the kernel: they
would be reordered or take a far form. No speed in it - one addition
either way - and still a format change: both engines, CALL, and
CALL,-T, what reads calls, every image and the double compile.

**Z4. Offsets in full cells** - open (509).
~2 KB at 64-bit, where a cell holds an offset a smaller field could.

**Z5. The two-bit call tag** - declined for now (A6, A15).
A 1 GB call range; no smaller calls. Possible since 539's 64 one-byte
opcodes; its first step would be packing them into 0x00-0x3F.
