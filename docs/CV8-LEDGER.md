# CV8-LEDGER.md - what each change to CV8 gained, and what it cost

Since Iteration 679, at the user's asking: CV8 - the bytecode engine and
its two engines, C and assembly, and the shell they run - takes back what
the native back end learned, item by item, and each item is entered here
with its gain and its cost, so the whole is visible: what we are getting,
and what it costs us. The native shell is the baseline: CV8's distance
from relf's fastest is the last row of every measurement.

## How a row is measured

`tools/cv8-ledger.py BASE` builds BASE in a scratch worktree and measures
the checkout against it on this VM, interleaved: the asm engine's shell
and the C engine's on tools/bench-vm.py's five workloads (SCALE=5; a
ratio under 1 is faster), each engine on bench/langs/bench.4's seven
kernels (best of 3 a round, alternated; their geometric mean), the
engines', shells' and images' bytes, and the asm engine's shell as times
the native shell. A fury pack confirms a batch, as for the native back
end (prompts/19): VM ratios choose, fury's report claims.

**The noise floor (679):** the unchanged tree against itself, 5 rounds -
the asm shell 0.997-1.046, the C shell 0.939-1.075, bench.4 0.97-1.06. A
difference under 5 % on the shell, or 4 % on bench.4, is not a gain at 5
rounds; rows that claim less use more rounds.

## The baseline (Iteration 678)

CV8 as it stands, against the native shell. Fury at 676 (times dash):

| | loop | fn | str | arith | realistic |
|---|---:|---:|---:|---:|---:|
| asm engine's shell | 27.8 | 34.6 | 30.0 | 35.1 | 41.6 |
| C engine's shell | 28.7 | 35.4 | 30.5 | 37.3 | 41.9 |
| native shell | 2.88 | 3.50 | 2.89 | 3.67 | 3.83 |
| asm shell, times native | 9.7 | 9.9 | 10.4 | 9.6 | 10.9 |

On the VM (679's run): the asm shell 13.7, 11.9, 11.8, 12.3, 12.0 times
native. bench.4 on fury: native 0.13 of the asm engine's time, 0.13 of
the C engine's. Bytes: relfasm64 15,856, relf64 45,360, relfshasm64
141,844, relfsh64 171,348, kernel64.img 9,840, kernel64-shell.img 125,972.

## The items (from 678's reply, in order)

1. The asm engine's string primitives - CSTRLEN, SCAN, MOVE, COMPARE,
   FILL - without the microcoded rep and repne instructions for short
   strings, as native-rt.4's since 644, 647 and 652. The asm engine only:
   the C engine calls the C library's.
2. `(S")` as an engine instruction: a string literal in one dispatch,
   where the colon word took a call, five instructions and a return.
3. Grouped saves and restores of locals: one instruction a run, where
   each local took one.
4. Inlining small colon words (OPTIMIZATIONS.md S6).

## Entries

(one per item, newest last: what was built, the ledger's block, the cost
in bytes and source, and fury's figures when a pack has them)

### 679, item 1: the asm engine's string primitives - built, measured, reverted

Built: native-rt.4's MOVE (a byte loop under 16), COMPARE (eight bytes at
a time, then a byte loop), SCAN (a byte loop) and CSTRLEN (one load where
the first eight bytes lie in one page, else aligned eight at a time)
ported into relfasm64.4's handlers - native's rbx and rbp are the asm
engine's r12 and r13 - in place of repne scasb, rep movsb and repe cmpsb.
FILL was native's already. The engines' outputs the same on
tests/native/kernel-str.4 and the other string tests.

| shell, SCALE=5, 7 rounds | loop | fn | str | arith | realistic |
|---|---:|---:|---:|---:|---:|
| asm engine, against 678 | 1.020 | 1.015 | 1.029 | 1.006 | 1.058 |
| C engine, unchanged: the noise | 1.025 | 0.989 | 0.907 | 1.028 | 0.962 |

bench.4: the asm engine's geomean 1.001. Cost: relfasm64 +216 bytes.

**Got nothing; reverted.** Natively the same routines were 6-14 % of the
profile because everything around them had become fast; in CV8 a dozen
dispatches surround each call, and the microcoded instructions' slow
start is lost among them. The lesson for the items after it: the native
back end's profile prices native code, not CV8 - each item is priced on
CV8 itself, by doing its work twice, before it is built.

### 680, items 2-4 priced on CV8 - by doing each one's work twice

Each priced before building, on CV8 itself (679's lesson), the work done
twice with behaviour unchanged, A/B against 679's shells, 9 rounds:

| shell, SCALE=5 | loop | fn | str | arith | realistic |
|---|---:|---:|---:|---:|---:|
| 2: every string literal twice - asm | 1.038 | 1.026 | 0.981 | 1.031 | 1.019 |
| 2: the same - C | 0.969 | 1.005 | 0.979 | 0.955 | 0.968 |
| 3: every local saved and restored twice - asm | 0.990 | 0.997 | 1.025 | 1.032 | 1.037 |
| 3: the same - C | 0.997 | 1.003 | 0.992 | 1.015 | 1.044 |
| 4: an extra call and return at every call - asm | 1.337 | 1.391 | 1.317 | 1.373 | 1.368 |
| 4: the same - C | 1.375 | 1.332 | 1.413 | 1.390 | 1.334 |

**Item 2, `(S")` as an instruction: not built.** All of a string
literal's runtime, done twice, is inside the noise: an instruction that
saved part of it could not be seen.
**Item 3, grouped locals: not built,** for the same reason.
**Item 4, inlining small colon words: next.** One more call and return
at every call site costs a third of CV8's time on every workload, on both
engines: calls and returns are where CV8 spends, and inlining the small
words removes some of them outright. How many depends on how many of the
calls executed go to words small enough to copy - the first thing to
count before it is built. (Item 4's first pricing build used ['] in
kernel.4, which the cross compiler refuses; the images were not rebuilt,
and its A/B compared two copies of one shell - noise, caught by their
equal sizes and the failed build's status. Rebuilt with POSTPONE, guarded
against its own recursion.)

### 681, item 4 stage a: a constant's use compiled as its literal

First, how many calls are there to inline? tools/profile.py's
PROFILE_CALLS=1, new: every call site's dispatches summed by the word it
calls, on the realistic script. 1,849,354 calls, a call and an EXIT each:
18.2 % of 20.3 million dispatches. Calls to words of at most 2
instructions, EXIT included: 16.7 %; 3: 39.3 %; 4: 52.4 %; 6: 69.1 %.
The most called: X@ 9.2 % (4 instructions), * 5.1 (3), NIP 4.8 (3), XF@
4.6 (5); and among the 2-instruction words, constants - SHVAR-NAME-MAX,
ENC-CTL, WF-QUOTED, T-SIMPLE: CV8's CONSTANT is HEADER REVEAL LIT, EXIT,
a call each time it is used.

Built: kernel.4's COMPILE, compiles a word whose body is one literal and
EXIT - LIT-LEN knows the five literal forms - as that literal: the word
EXECUTEd at compile time, its value LIT,'d. The word stays for ' and
EXECUTE; nothing patches a constant's body later (checked). The native
cross compiler skips the two new helpers, as the other CV8 back-end
words: the native kernel is byte for byte the same, and builds itself.

Calls on the realistic script 1,849,354 -> 1,545,820 (-16.4 %), calls to
2-instruction words 308,387 -> 4,850, dispatches 20.3 -> 19.6 million.

| 7 rounds, against 680 | loop | fn | str | arith | realistic |
|---|---:|---:|---:|---:|---:|
| asm engine's shell | 0.998 | 0.949 | 0.957 | 1.005 | 0.936 |
| C engine's shell | 0.957 | 0.943 | 0.970 | 0.968 | 0.951 |
| asm shell, times native | 12.3 | 12.2 | 12.1 | 11.7 | 12.0 |

bench.4: the asm engine's geomean 0.936 (matrix 0.791, bubble 0.864,
sieve 0.919), the C engine's 0.958 - its kernels' constants are laid as
literals now too. **Cost:** the kernel image +104 bytes (the two
helpers); the shells -272 bytes - a literal is shorter than a call.
**Got:** 3-6 % on the shells (at the noise floor's edge, both engines
agreeing), 4-6 % on bench.4.

**Fury at 681** (its pack, 682; times dash, against 676's run): the C
engine's shell loop 27.2 (28.7), fn 34.1 (35.4), str 28.2 (30.5), arith
34.4 (37.3), realistic 37.4 (41.9) - ratios 0.89-0.96, implied 0.92-0.99;
the asm engine's 27.6, 34.8, 28.4, 35.1, 39.3 - ratios 0.95-1.01, inside
fury's noise. The C engine's gain is claimed there; the asm engine's is
not, yet.

### 683, item 4 stage b: small straight words inlined

Built: kernel.4's COMPILE, decodes the word it is asked to call
(INLINE-LEN): at most four instructions before its EXIT and at most 12
bytes, each one that means the same anywhere - operand-free stack,
arithmetic and memory opcodes, literals, ADDI and EQI, VAR@ and VAR!,
ESC primitives but RP@ and RP!, and calls, unless the called word begins
R> or R@ ((S") and (POSTPONE) take their return address and data follows
the call). No branch, no return-stack word, no locals, no data word. Such
a body is laid in place of the call (INLINE-COPY), each instruction as it
is - calls are offsets from START, the same anywhere - but VAR@ and VAR!,
whose slots are offsets from the operand itself: SLOT@ reads one back,
SLOT, lays it again from its new place. The first build copied slots as
they were: the 4-byte image's cross-compile, run by the new 8-byte image,
crashed, and `VARIABLE V : T5 V @ ; : T6 T5 1+ ;` printed garbage. Then
U> - extend.4's, not the kernel's - stopped the cross compiler.

tests/native/kernel-inl.4 (verify's native:inl): near and far slots (the
three-byte form, past 16 KB), nesting, words that must stay calls - S"
inside, R@, a branch - constants, ESC, EXECUTE; the native kernel, which
does not inline this way, is the oracle, and CV8's engines print what it
prints.

Calls on the realistic script 1,545,820 -> 863,539 (-44 %); dispatches
19.6 -> 18.3 million; calls to words of at most five instructions 4,823.

| 7 rounds, against 682 | loop | fn | str | arith | realistic |
|---|---:|---:|---:|---:|---:|
| asm engine's shell | 0.896 | 0.929 | 0.948 | 0.940 | 0.901 |
| C engine's shell | 0.939 | 0.926 | 0.938 | 0.953 | 0.953 |
| asm shell, times native | 12.3 | 11.5 | 11.6 | 11.2 | 10.4 |

bench.4: asm 0.939 (matrix 0.810, fannkuch 0.807), C 0.944. **Cost:** the
shells +3,600 bytes (+2.5 %), the kernel image +504 (the inliner).
**Got:** 5-10 % on the asm shell, 5-7 % on the C shell, 6 % on bench.4.
A size-neutral variant - only bodies no longer than the call - is a
candidate for GOALS.md 10's search.
