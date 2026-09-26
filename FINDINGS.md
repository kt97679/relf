# FINDINGS.md - measured, examined, and kept for later

Results that decided nothing yet, or decided *against* something, kept
with their numbers so they can be revisited without being measured again.
Each names the iteration and the tool that produced it (PROGRESS.md has
the story). Iterations 526-543.

## 1. Speed

### 1.1 relf against other languages and other Forths (543)

`bench/langs/run.py`: seven small programs, each stressing one kind of
work, written the same way in C, Go, Python and Ruby and ONCE in Forth
(`bench/langs/bench.4`, the same text for relf, gforth and pforth). Every
run's checksum is checked against C's; best of three, wall clock,
process start included; x86-64, one machine, nothing else running.

| ms | fib(32) | loop 30M | sieve 5M | bubble 3000 | matrix 150 | fannkuch 9 | collatz 1e5 | geo. mean vs relf |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C (gcc -O2) | 4 | 10 | 23 | 19 | 3 | 33 | 19 | 0.08x |
| Go 1.22 | 13 | 22 | 27 | 7 | 5 | 21 | 24 | 0.09x |
| **relf, assembly engine** | **55** | **92** | **421** | **84** | **130** | **362** | **231** | **1.00x** |
| relf, C engine | 58 | 90 | 490 | 103 | 137 | 330 | 218 | 1.04x |
| gforth-fast 0.7.3 | 59 | 87 | 106 | 72 | 78 | 234 | 146 | 0.66x |
| gforth 0.7.3 | 61 | 77 | 129 | 93 | 82 | 338 | 152 | 0.74x |
| pforth 2.0.1 | 150 | 173 | 393 | 279 | 353 | 1114 | 419 | 2.19x |
| Ruby 3.2 | 228 | 615 | 430 | 364 | 181 | 855 | 427 | 2.57x |
| Python 3.12 | 208 | 844 | 445 | 260 | 163 | 445 | 515 | 2.34x |

- relf is in gforth's class: it beats gforth on calls (fib), ties it on
  the bare loop, and trails it by 1.35-1.5x over all. gforth 0.7.3 is
  from 2008; later versions are faster.
- Where relf loses most, a colon word sits in the inner loop: the
  sieve's `+LOOP` and `J` cost ~15 dispatches an iteration where `LOOP`
  and `I` - opcodes since 530 - cost one. Not pursued (A13, A14).
- relf is 2.2-2.6x faster than pforth, Ruby and Python over all, and
  about 12x slower than C and Go.
- An earlier three-test version (542): fib(30), loop, sieve - relf 4-18x
  faster than Python and Ruby on calls and loops.

### 1.1a Why gforth is faster, and what closing the gap would take (544)

gforth run with its techniques switched off (ms, best of three):

| | fib | sieve | matrix | fannkuch | collatz |
|---|---:|---:|---:|---:|---:|
| gforth-fast | 72 | 117 | 90 | 261 | 169 |
| gforth-fast --no-dynamic | 67 | 120 | 92 | 265 | 172 |
| gforth-itc (indirect threaded) | 70 | 157 | 101 | 403 | 197 |
| relf, assembly engine | 64 | 488 | 149 | 412 | 267 |

- Not native code: gforth's dynamic superinstructions (copying the
  primitives' machine code at run time) are worth ~3% here; its plainest
  engine still beats relf 3x on the sieve.
- It is WHICH WORDS ARE PRIMITIVES. relf wins fib, where the work is
  calls. It loses where a word that is one primitive in gforth is a
  colon word in relf, inside the inner loop: the sieve's `+LOOP` and `J`
  (~25 dispatches an iteration against gforth's handful); collatz's `2/`
  (eight operations, since relf's RSHIFT is logical). gforth has several
  hundred primitives; relf 64 one-byte and 74 escaped.
- The effort: `+LOOP`, `J` and `2/` as primitives - escaped, so the 64
  stay 64 - is one iteration's work, like 530's loop words; it would
  bring the sieve and collatz near gforth-itc. Beyond that, each further
  gain is another word made a primitive, against A13 and A14's line.
  Not done: optimization stopped (A13).

### 1.2 relf's shell against dash and bash (534)

The realistic script, identical output from all four: dash 2.5 ms, bash
7.6 ms, relf 75.7 ms (assembly engine) / 81.9 ms (C engine) - ~30x dash,
~10x bash. Startup the other way round: relf 287 us, dash 748, bash
1,108. The gap is the amount of work (17.5 million Forth operations for
a script dash runs in ~10 million cycles), not the dispatch rate.
QUESTIONS.md Q16/A13: accepted - simplicity first.

### 1.3 The dispatch floor (526)

Both engines run a 100-million-iteration loop in ~320 ms: 0.8 ns a
dispatch, the rate the CPU takes indirect jumps. Better handler code
cannot help; two "improvements" made it 10% slower by moving code.

### 1.4 Where the dispatches go (536, whole workload mix)

Direct primitives 25.7%, specialised 20.4%, superinstructions 15.1%,
tiny words 11.4%, **calls 11.3%, EXIT 5.5%, folded returns 3.2%**,
synthetic 4.6%, escaped 1.4%, short branches 1.3%. Call and return are
about a fifth of all dispatches: the ceiling for any threaded-code
technique that removes them (tail calls, inlining, trace flattening);
removing dispatch itself takes native code (subroutine or context
threading, dynamic superinstructions) - GOALS.md goal 2, JIT/AOT,
revisited once relf self-hosts its engine (A14 d).

### 1.5 Opcodes added and removed (528-539)

Seven runtime words as opcodes (`+!` `?DUP` `I` `(LOOP)` `(?DO)`
`EXECUTE` `@XT`) - kept; nine superinstructions (`VAR@` fusions,
compare-and-branch) - removed at 536, worth ~8% of dispatches on the
realistic script, ~13% on the whole mix; 22 folded returns - removed at
538, 5.4%. The pair analysis that ranked them: tools/superinst.py.

## 2. Size

- **Word order** (542, tools/call-layout.py): a call is 2 bytes to a
  target in the image's first 16 KB, 3 beyond; the kernel fills 9 KB of
  it. The most-called words per byte moved into the other 7 KB would
  make 2,127 more of the 5,976 calls near: **2.1 KB, 1.8% of the image**
  - at the price of hoisting those words (ARGV@, STR0=, ERR-TYPE, XF@,
  NIP...) and all they depend on into an early source file. Not done.
- **Calls relative to the call site** (image-audit.py's model): ~0.7 KB,
  a format change. Not done.
- **Names** are 21-23% of the image (509, Q1) - the larger lever.

## 3. Why 64 one-byte opcodes (537-539)

- Every opcode is a handler written twice today (C and assembly) and
  once more in Forth assembly when the engine self-hosts: 111 -> 64
  removed 47 per engine; the assembly engine 16.5 KB -> 15.1 KB.
- The compilers lost the folding and fusing machinery: a body ends in
  EXIT, and nothing rewrites compiled code.
- The rare cases cost nothing: nine primitives escaped for 0.013% more
  dispatches.
- It keeps the two-bit call tag possible (A6, A15) without paying for
  it now; packing the 64 into 0x00-0x3F would be its first step.
- The price: ~13% more dispatches than at the optimizations' peak; still
  ~11% fewer than before them.

## 4. Another Forth builds the kernels (542)

gforth 0.7.3 runs cross.4 unmodified and lays down kernel64.img and
kernel32.img byte for byte - a diverse double-compile: the seeds owe
nothing to relf's own compiler. `make verify` row `ddc:gforth`.
(pforth was not tried: its default dictionary is small - see 5.)

## 5. Forth assemblers examined (542-543) - for asm64.4

- **SP-Forth** (github.com/rufig/spf, lib/asm/486asm.f, from Win32Forth):
  PREFIX - `MOV [EBP], EAX`, `LEA EBP, -4 [EBP]` - reads like GNU source,
  made to work by assembling each instruction when the next one begins.
  32-bit only. Its look would make translating relfasm64.S nearly
  one-to-one; the price is that deferral and the flushing it needs.
- **gforth** (arch/amd64/asm.fs, 626 lines, Bernd Paysan): postfix;
  families generated by counted loops - one line `$10 jmps jo jno jb
  ...` defines all sixteen conditional jumps, `sets:` all sixteen setcc.
  Control flow STRUCTURED, not labelled: `IF` lays down a short jump
  with a placeholder and leaves its address; `THEN` patches it, with a
  range check (`?brange`) that stops rather than emit a wrong offset.
  One pass.
- **lbForth** (github.com/larsbrinkhoff/lbForth, targets/x86/asm.fth,
  331 lines; small assemblers for ~30 processors): the same structured
  words (`if, then, begin, until, while, repeat, ahead,`) - conditional
  forward jumps short, unconditional ones long; `label` defines BACKWARD
  targets only. One pass.
- What asm64.4 takes (SELF-HOSTING.md M1): one pass; labels referenced
  before they are defined leave a fixup, resolved when the label is -
  like cross.4's FORWARD/RESOLVE, and an unresolved one an error at the
  end; a backward jump sized by its distance, a forward one short unless
  the source says NEAR, and a short one that does not reach an error,
  never a wrong byte; families generated by loops, as gforth does.

## 6. Robustness found on the way (543-544)

- **The memory region and the call reach disagree** (544, the user's
  question): each engine reserves 16 MB - zero-filled BSS, so it costs
  address space, not memory: a running relf is 19 MB of address space
  and 1.4 MB resident. The dictionary grows up from the bottom towards
  the stacks at the top. But a call reaches 4 MB (the three-byte form's
  22 bits), and `CALL,` does not check: for a target past 4 MB,
  `DUP 16 RSHIFT 192 OR` folds the high bits into the tag, and the call
  goes somewhere else - SILENTLY. So code defined past 4 MB (after
  allotting a few megabytes of data, say) would be miscompiled. And
  cv8.c's comment on MEMSIZE says it is "far below the call reach" and
  "overridable at run time with RELF_MEMSIZE" - neither true now (no
  RELF_MEMSIZE is read anywhere). QUESTIONS.md Q19.

- `ALLOT` does not check the dictionary's end: 9 MB allots, 20 MB is a
  segmentation fault ("relf: segmentation fault (not a stack guard)")
  instead of an error. To fix: ALLOT (and , C,) against the limit.
- relf's bare kernel has no `THROW` or `0>` (extend.4 does): bench.4
  uses `ALLOCATE DROP` and `0 >`, to run on the bare kernel.

## 7. Local time (542-543)

The assembly engine's LOCAL-TIME is UTC (A10); outside UTC the prompt's
`\d \t \A` show UTC and run-invocation's check against `date` fails
(fury). /etc/localtime is not everywhere (Windows has none; some small
systems neither), so reading it in Forth is not portable. QUESTIONS.md
Q18: UTC everywhere, both engines, is the simple and portable choice;
its only cost is that the prompt shows UTC.
