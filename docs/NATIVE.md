# NATIVE.md — a Forth that compiles to native code

Iteration 608 (N0). The user's idea, after the ForthHub announcement:
a Forth design, most likely different from CV8, that compiles into
machine code close to what gcc makes of dash - small words inlined,
bigger words as native functions. dash is the yardstick, not the
target: the question is how close a Forth compiler can come to an
optimizing C compiler's code for the same work.

This document is the design. OPTIMIZATIONS.md S7 ("Native code") points
here.

**Decided (A33, Iteration 609):**

- **Beside CV8, never instead of it.** "cv8 stays as is. We may improve
  it but we are definitely not replacing it." CV8 and the C engine stay
  for every machine.
- **x86-64 only** - an experiment.
- **Speed first, size watched.** The code may grow, but every growth is
  measured, weighed against the speed it buys, and discussed before it
  stays: "+50% in code size and +5% performance probably not worth it."
  Each milestone reports both.
- **The exit targets** (section 5): Forth benchmarks within 3 times of C
  at N2, scripts within 5 times of dash at N3.
- **One source.** Both back ends run the same shell sources and all the
  tests.

## 1. Where things stand

CV8 is a bytecode: one-byte opcodes for 64 primitives, calls by offset
in two or three bytes, interpreted by an engine - relfasm64 (15,768
bytes, assembled by relf itself) or the portable C engine. Both
dispatch at the CPU's rate for one indirect jump after another, about
0.8 ns a dispatch (OPTIMIZATIONS S8): better handler code cannot help.

What that costs, measured (fury; the articles' numbers):

- Forth benchmarks (bench/langs): RelF on its own engine is about 16-17
  times slower than C and Go, 1.2 times slower than gforth 0.7.3, 1.75
  times slower than gforth-fast.
- Shell scripts (tools/bench-vm.py): relfsh is 29-42 times slower than
  dash.

A13 accepted that gap for CV8: no more opcodes or fusions, CV8 stays as
simple as it is. This design does not change CV8. It adds a second way
to compile the same Forth.

What S7 already knew: copying primitives' native code end to end, with
no optimization, was worth about 3% in gforth on these benchmarks. The
gain is not in being native; it is in compiling well - the stack in
registers, inlining, constants folded. So this is an optimizing
compiler, or it is not worth building.

## 2. The yardstick: dash's machine code

dash 0.5.12 built with -Os and symbols (Iteration 608, this container):
268 functions, 56,261 bytes of machine code; its text segment, with
tables and strings, 91,686 bytes; libc on top. By module, code and
data: parser 9.4 KB, jobs 8.2, expand 7.8, eval 6.4, exec 4.6, var 3.7,
options 3.5, miscbltin 3.0, output 2.3, arith 2.1, redir 2.1, trap 2.0,
input 2.0, main 1.6.

relfsh's shell image, for comparison: 125,308 bytes - code 75,324,
headers about 28 KB (kept: the user's decision, 608), data about 21 KB.
By source file: shell.4 69 KB, tree.4 35 KB, edit.4 7 KB, the Forth
extensions about 4 KB, the kernel about 9.5 KB.

The yardstick is used two ways (section 6): whole workloads against
dash, and function against function - a hot dash function and the
relfsh word that does the same job, compiled by this compiler, side by
side: instructions, bytes, time on the same input.

## 3. The design

### 3.1 Words are native functions

A colon definition compiles to a native function. The Forth return
stack is the machine stack: a call is `call rel32`, `EXIT` is `ret`.
x86-64's calls are encoded relative to the call site, and data is
reached rip-relative, so the code is position-independent - "Relative
Forth" keeps its meaning, and the image needs no relocation.

Registers (a first assignment, to be confirmed in N1):

| register | holds |
|---|---|
| `rsp` | the return stack (the machine stack) |
| `rbp` | the data stack pointer |
| `rbx` | the top of the data stack, cached |
| `r14`, `r15` | the innermost DO loop's index and limit |
| the rest | the compiler's to allocate, within a word |

There is no C ABI to honour: the engine's system calls are its own, as
relfasm64's are.

### 3.2 The stack in registers

The compiler keeps a model of the data stack while it compiles a run
of code with no branch into it: which items are in registers, which are
constants, which are still in memory. `DUP @ 1+ SWAP !` becomes register
moves and two memory operations, with no stack traffic at all. At a
call, a branch or a label the model is written back to a fixed state -
the top in `rbx`, the rest in memory - so code on both sides agrees.
This is where most of the speed is, as in VFX Forth and iForth.

### 3.3 Inlining, folding, fusing

- A word whose code is small - a threshold in bytes, about 16 to start
  - with no control flow of its own is inlined at each use; `INLINE`
  and `NOINLINE` override. Recursion and DEFER are never inlined.
- Constants fold: `3 CELLS +` is one `add`.
- A literal becomes an instruction's operand: `5 +` is `add rbx, 5`.
- A comparison followed by `IF`, `WHILE` or `UNTIL` is one compare and a
  conditional jump.

Bigger words stay calls, which keeps the code small: inlining only
tiny words is the lever on size (section 4).

### 3.4 Control flow and the rest of Forth

`IF ELSE THEN`, `BEGIN UNTIL WHILE REPEAT AGAIN`: native jumps. `DO
LOOP`: index and limit in `r14`/`r15`, saved on the machine stack around
a nested loop or a call that needs them. `CATCH`/`THROW`: a frame on the
machine stack with `rsp`, `rbp` and the previous handler, as the kernel's
CATCH keeps them now. `CREATE`, `VARIABLE`, `HERE`, `ALLOT`: data in the
dictionary as now, reached rip-relative.

### 3.5 Compiling at run time

The `forth` builtin defines words while the shell runs, so the compiler
is resident, as now, and writes native code into the dictionary. The
dictionary is mapped readable, writable and executable to start; a W^X
discipline - writing and executing separated - can follow if it is
wanted.

### 3.6 Errors and safety carry over

Everything 582-606 established for CV8 must hold for native code, and
tools/forthfuzz.py and tools/intrfuzz.py check it:

- guard pages below the data stack and the machine stack, and traps -
  a bad address, a zero divisor, a guard - become THROWs (A26), the
  signal handler resuming at the innermost CATCH;
- a forth command's own stack base and the gap below the executor's
  cells (589, 595, 602);
- ^C thrown into Forth from the start, nothing lost in the switch (606).

### 3.7 The image and the engine

The image holds native code; its header names the back end, so a CV8
engine refuses a native image and the other way round. The "engine"
becomes a loader, the system-call layer and the trap handler - most of
relfasm64 without its interpreter. The shell's source stays the same
for both back ends: anything in it that depends on CV8 - the `!XT`
offsets, for one - goes behind a word both back ends define.

### 3.8 Built by relf, then by itself

The native compiler is written in Forth (new files, forth/native*.4),
emitting through forth/asm64.4 - the assembler that already builds
relfasm64, held to GNU as on 456 instruction shapes and random
instructions. It first runs on the CV8 system and compiles a native
image; then the native image compiles itself, and the two builds must be
byte for byte the same - the discipline the kernel's builds already
keep.

## 4. What to expect

From compilers built this way: VFX Forth and iForth come within about
one to two times of C on benchmarks; simpler native compilers that
inline - SwiftForth, SP-Forth - within about two to four. For relf's
Forth benchmarks, a reasonable aim is within 2-3 times of C, against
16-17 now. For scripts, the shell's own algorithms then matter as much
as the code: name hashing, variable lookup, string comparison
(OPTIMIZATIONS S9, S10) - perhaps within a few times of dash, against
29-42 now.

Size: x86-64's calls are 5 bytes against CV8's 2-3, and inlined code is
bigger than one-byte opcodes. The 75 KB of code may grow toward 150 KB;
headers and data do not change. The C engine and CV8 stay for every
other machine.

## 5. Milestones

Each is an iteration or several, with what must be true at its end.

- **N0** (608): this document; the decisions as Q33, answered at 609
  (A33).
- **N1a, the pipeline** (610, done): forth/native.4, the code
  generator, and forth/native-n1a.4, an ELF file of its own with a small
  program - `N: SQUARE DUP * N;`, a recursive `U.` with `/MOD` and `IF`,
  a `MAIN` - that prints 169. `make native-n1a`; tests/verify's
  native:n1a row. The listing is what N1 is - each primitive its fixed
  sequence, `6 7 +` two pushes and an add - and what N2 is for: that is
  one `mov rbx, 13`.
- **N1b-1, the computational core** (611, done): CV8's primitives that
  compute - stack, arithmetic, comparisons, shifts, UM* UM/MOD D+,
  memory, the return stack, DO ?DO LOOP +LOOP I J LEAVE UNLOOP, EXECUTE -
  as fixed native sequences, and the string primitives (MOVE FILL
  COMPARE SCAN CSTRLEN TYPE) as NCODE routines, called. tests/native/
  prims.4, written once in a T: dialect, is compiled by CV8 and by
  native.4; the two print the same, byte for byte - tests/verify's
  native:prims row.
- **N1b-2, what the kernel calls** (612, done): SP@ SP! RP@ RP! and @XT,
  inlined; forth/native-rt.4, the runtime's routines - the string
  primitives, and READ WRITE POLL OPEN-FILE CLOSE-FILE REPOSITION-FILE
  FILE-POSITION SYS-EXIT BYE as raw system calls, with CV8's results
  (ior 200, fid -1). prims.4 grew to 45 lines - an SP@/SP! round trip,
  RP! unwinding a word's pushes, !XT/@XT through EXECUTE, the Makefile
  read back with a seek - and prints the same in both. CV8's locals
  are used by neither the kernel nor the shell; the operating system's
  other primitives - processes, signals, the terminal, directories,
  the environment, the heap - are the shell's, and come with N1d.
- **N1, plain native code.** Primitives inlined as fixed instruction
  sequences, words as native functions, the top of the stack in `rbx`,
  no optimizer. Exit: the CORE tests pass, both cell widths' kernels
  still build on CV8, bench/langs measured - what native calls alone
  buy.
- **N2, the optimizer.** The stack model, inlining, folding, fused
  compare-and-branch. Exit: bench/langs against C, gforth-fast and N1;
  the code of a few chosen words read against dash's.
- **N3, the shell, native.** Exit: the shell suite, the pty suite, both
  fuzzers, the comparison with bash - all as on CV8; scripts against
  dash in tools/bench-vm.py; the function-against-function table.
- **N4, built by itself.** Exit: the native image built by the
  CV8-hosted compiler and by itself, byte for byte the same; in
  tests/verify.

## 6. How it is measured

- bench/langs (Forth: fib, sieve and the rest) - against C, Go, gforth,
  gforth-fast, and CV8.
- tools/bench-vm.py (scripts) - against dash, bash, busybox ash.
- Function against function: dash's lexer (readtoken1 and its syntax
  tables), variable lookup (lookupvar), its allocator (stalloc) and the
  relfsh words that do those jobs - instructions and bytes from the two
  listings, time on the same input.
- tools/image-audit.py, extended for native code: bytes per word, how
  much was inlined.

## 7. Costs and risks

- A third engine to keep green on every change, and a compiler far more
  complex than cross.4 - the opposite of A13's minimalism, by design and
  beside it, not instead of it.
- Debugging generated machine code: SEE has to become a disassembler,
  or the compiler has to explain itself.
- x86-64 only: ARM, for rage, needs an ARMv7 assembler in Forth first.
- The time: N1 alone is several iterations; N2 is the hard part.

## 8. N1c: the kernel, mapped (Iteration 613)

What in forth/kernel.4 depends on CV8's encoding - so what the native
kernel needs written again, and what it takes as it is. A script split
kernel.4 into its definitions and flagged each whose body uses CV8's
encoding words (OP, and the opcodes, the literal and branch forms, the
peephole, DOVAR and DODOES, @XT and START, the call's encoding).

**180 colon definitions; 40 flagged; 140 untouched.** Beside them, 123
primitive declarations: 103 PRIMITIVE lines and 20 OPCODE lines. The 40
fall into five groups:

| group | words | for the native kernel |
|---|---|---|
| A. the cell's width as a token | CELL- J FIND ALIGN | `CELLBYTES-TOK` is cross.4's way of building both widths from one source; natively it is 8 - the source unchanged |
| B. xts as offsets from START | !XT DOES-FETCH? (POSTPONE) POSTPONE (;CODE) COMPILE-ONLY-XT CO? RELOCATE-WORDLIST | the native image keeps START and the offsets (N1b's @XT already does): unchanged, or close |
| C. the compiler proper | NO-PEEP LIT, EXIT, CALL, PEEP-IMM PEEP-VAR COMPILE, CREATE >MARK >RESOLVE BACK, BEGIN UNTIL AGAIN IF THEN ELSE REPEAT DO LEAVE-LINK, ?DO LEAVE RESOLVE-LEAVE LOOP +LOOP RECURSE DOES> | written again: they lay down native code, at run time too - the forth builtin compiles |
| D. the primitives (123) | the PRIMITIVE and OPCODE lines | native.4's sequences and native-rt.4's routines, as dictionary words: an inline word's code copied by COMPILE, up to its `ret`; a routine called |
| E. the start | COLD (with RELOCATE-WORDLIST) | the native runtime's: stacks, guard pages, the trap handler, then the kernel |

So the native kernel is kernel.4's 140 untouched definitions, group B
nearly so, and about 30 words of group C written for native code - not a
second kernel. CREATE and DOES> take the classic native form: a created
word's code is a short fixed stub - push the address of the data that
follows it - so >BODY is the xt plus the stub's length, and DOES>
rewrites the stub's tail into a jump to the DOES> code.

**How N1c goes, then - revised at Iteration 614.** The plan above had
N1c-1 move the compiler words into a file of their own, CV8's images
unchanged to the byte. A look at the range said no: between NO-PEEP and
INTERPRET the back-end words are interleaved with common ones - STATE
[ ], CSP ?CSP ?COMP, ' ['] CHAR [CHAR], S" ." ABORT ABORT", IMMEDIATE,
.( ( \, >BODY, ?STACK. Moving the range would make the native side carry
copies of all of them; moving only the back-end words reorders kernel.4,
and CV8's images change - the bytes could no longer prove the move. So
kernel.4 is not split:

- **The native cross compiler compiles kernel.4 itself**, the one source
  (A33 e). When it meets a definition of one of the back-end words, it
  skips CV8's and compiles the native one from forth/kernel-native.4 in
  its place; a call that reaches a back-end word before its native
  definition is a forward reference, resolved when it comes - as cross.4
  resolves COLD and WARM. CV8's images are untouched by construction:
  "cv8 stays as is" (A33 a).
- **N1c-1a, the shared core** (615, done): cross.4's parts 1-3 - the
  vocabularies, the target dictionary space, creating definitions and
  their headers - moved, as they stood, into forth/cross-core.4, which
  cross.4 includes where they were. The kernels cross.4 builds are the
  same to the byte: both cell widths, built by relf and by gforth, and
  tests/verify's rebuilds and fixpoints. The target space is a buffer
  of offsets from the image's start - what position-independent native
  code wants too.
- **N1c-1b, headers over native code** (616, done): forth/native-cross.4
  - cross-core.4, asm64 pointed at its image (ORG 0, so the code is
  offsets and rel32), `NH: name ... N;` for a native definition with a
  target header, and the ELF writer: a header page, then the image at
  N-BASE, its START. forth/native-n1c.4 defines words so, publishes
  the thread table into the image, and runs a walker - itself such words
  - that decodes the backward links: it prints exactly the six names
  defined. tests/verify's native:headers row.
- **N1c-1c, kernel.4's parts 0-3, native** (618, done): native.4's
  compile-time words moved to NCTRL, searched first, and target shadows
  that lay themselves - so kernel.4's own /MOD and * win over native.4's
  templates, as the newest definition does in Forth. native-cross.4
  reads kernel.4 itself: CROSS-COMPILE runs N-CROSS; PRIMITIVE gives a
  header whose body is the template (flagged inline), a jump to the
  runtime's routine, or a stub that names itself; VARIABLE a 16-byte
  stub and its cell; `:` resolves the calls laid before it to (.") and
  (ABORT"). The first 569 lines of kernel.4, unchanged, compile;
  tests/native/kernel-cut.4 prints the same natively as on CV8's kernel -
  floored and symmetric division, */MOD, M*, FM/MOD, SM/REM, ." through a
  forward call. tests/verify's native:kernel-cut row.
- **N1c-2a, parts 0-8** (619, done): kernel.4 through part 8 - number
  output, memory, files, source input, the interpreter's helpers - 1,267
  lines, compile natively. Two things stood in the way: cross-core.4's
  40,000-byte image buffer, now 512 KB on the heap (CV8's kernels the same
  to the byte, by relf and gforth); and PRIMITIVE storing a shadow's
  second cell after laying ?DUP's template, whose forward local label
  allots a record in the host's dictionary - the cell landed after the
  record, and N-SHADOW executed what it read. The test of parts 4-8's
  words (620-621): three more faults found by it and fixed - see
  PROGRESS - and then 14 lines the same as CV8's kernel: number output
  signed, unsigned, HEX and double, pictured output, SPACES, ROLL 2OVER
  2SWAP, overlapping CMOVE and CMOVE>, NUMBER? good and bad.
- **N1c-2b, part 9 with the back end skipped** (622, done): forty
  back-end names - CV8's helpers, the compiling words, the defining
  words, every control and loop word - are skipped where kernel.4 defines
  them, an IMMEDIATE after one with them; a common word's call to one is
  a forward call; POSTPONE works at cross time - a call for an immediate
  word, else the xt and a call to the target's COMPILE, - by a third
  shadow cell, the header's name field. kernel.4 through part 9 compiles;
  six forward calls wait: COMPILE, (three), CREATE, LIT, and WARM -
  part 10's. kernel-native.4 is to define the back end and resolve them.
- **N1c-2c, the native back end** (623, done): forth/kernel-native.4,
  the target's own compiler for x86-64, in Forth that lays the bytes
  with C, - LIT, CALL, EXIT, COMPILE, (an inline primitive's body begins
  EB 01 len, a jump over its length, and is copied), the control and
  loop words with LEAVE's chain threaded through the jumps' own fields,
  : ; RECURSE, CREATE with a 24-byte body (the ret at 15, where DOES>
  puts a jump; >BODY is 24 +), CONSTANT, (;CODE) DOES> POSTPONE.
  kernel.4 through part 9 with it: only WARM, part 10's, still a forward
  call. tests/native/kernel-rc.4 lays code fragments at HERE with these
  words at run time and EXECUTEs them; the same on CV8's kernel -
  native:compiler, same.
- **N1c-3, the native kernel boots** (624, done - N1c's end): kernel.4's
  part 10 compiles as it is, COLD included - it relocates the thread heads
  and DP by START, offsets in the native image as in CV8's - and the
  build finishes as cross.4's does: the word list published into
  FORTH-WORDLIST, DP at the image's end. The start sets the data stack,
  START as its one cell, and calls COLD. forth/native-kernel.4, `make
  native-kernel`: 39,087 bytes, kernel.4 entire and no forward call
  waiting; it says "Welcome to Forth", interprets, compiles - : ; IF
  RECURSE DO LOOP LEAVE VARIABLE CREATE DOES> ." - at its own prompt.
  Hayes' CORE suite (tests/tester.fr) on it and on CV8's bare kernel:
  the same output, 2,073 lines, byte for byte. native:core, same.
- **N1c-1, the native cross compiler** (forth/native-cross.4): cross.4's
  pattern - TARGET's shadow words compile calls, TRANSIENT's compile-time
  words are native.4's - with the header and dictionary format CV8's, the
  bodies native; the skip-and-substitute; the start.
- **N1c-2, the native back end** (forth/kernel-native.4): the ~30 words
  of group C for native code, CREATE and DOES> as above.
- **N1c-3, the CORE tests,** at the native kernel's prompt, as on CV8.

## 9. N2's first measurement, and a layout rule (Iterations 625-626)

tests/native/bench/*.4 - five workloads on bare kernels, so the native
kernel and CV8's run the same source - and tools/native-bench.py, which
times them (the child's CPU, median of rounds) and checks that every
engine prints the same answer. The first measurement, medians of 3:

    workload     cv8-c   cv8-asm    native   native vs cv8-asm
    fib          0.06s     0.06s     0.01s    3.97x
    interp       0.70s     0.69s     4.95s    0.14x
    loop         0.59s     0.64s     0.13s    4.78x
    mem          0.04s     0.24s     1.41s    0.17x
    sieve        0.91s     0.87s     0.28s    3.17x

Compiled code is 3-5 times CV8's speed. interp - EVALUATE, the kernel's
own interpreter - is 7 times slower, and an empty EVALUATE alone costs
1.3 us against CV8's 0.1. The cause, measured: 100 million stores to a
VARIABLE take 24.9 s natively, 0.29 on CV8; 100 million to a cell 500
bytes into a buffer, 0.19; fetches, 0.07. A variable's cell is in the
same 64-byte cache line as its code stub, and a store there is, to the
processor, self-modifying code: a machine clear, some 750 cycles, each
time. EVALUATE stores five variables per call. CV8 cannot have this -
its code is the engine's data.

So a rule for the native image: **data that is written never shares a
cache line with code.** A created word's data begins at the next 64-byte
boundary after its stub, whose mov holds the address - so >BODY reads it
there, not xt + 24 - and the definition after data begins on a line of
its own. The cross compiler's VARIABLE and kernel-native.4's CREATE and
: keep it (626). mem is the other slow one: COMPARE is `repe cmpsb`,
microcoded, a byte a cycle - eight bytes at a time is the cure.

The rule, kept (626): the cross compiler's VARIABLE and kernel-native.4's
CREATE put the data at the next 64-byte boundary, int3 between, the mov
holding its address and >BODY reading it there; the first definition
after data - the cross compiler's N-HEAD, kernel-native.4's : CREATE
CONSTANT - starts on a fresh line. And COMPARE compares eight bytes at a
time, leaving `repe cmpsb` the last few. The kernel grew 39,087 ->
42,959 bytes, the padding. Medians of 3:

    workload     cv8-c   cv8-asm    native   native vs cv8-asm
    fib          0.06s     0.06s     0.01s    4.12x
    interp       0.68s     0.67s     0.26s    2.56x
    loop         0.57s     0.63s     0.13s    4.77x
    mem          0.03s     0.25s     0.07s    3.59x
    sieve        0.88s     0.88s     0.27s    3.28x

100 million stores to a variable: 24.86 s -> 0.15. interp 19 times
faster, mem 20; the native kernel is faster than CV8 on all five. The C
engine's libc memmove and memcmp still win mem (0.03).

Against C (627). tests/native/bench/c/ has fib, loop and sieve in C, the
harness builds them with cc -O2 - the loop's sum kept a real loop with an
empty asm, which gcc would otherwise turn into the closed form - and
prints native's time over C's. First: fib 2.48, loop 1.96, sieve 7.07.
The sieve's inner loop calls SIZE, a CONSTANT, and FLAGS, a CREATEd
buffer, every turn. Now a word whose code only pushes a constant and
returns - a CONSTANT, a VARIABLE, a CREATE no DOES> has patched, `: FIVE
5 ;` - has its push laid inline: by kernel-native.4's COMPILE, at run
time, which knows the bytes, and by the cross compiler for the kernel's
own, marked in the shadow. The kernel: 45,595 bytes. Medians of 5:

    workload     cv8-c   cv8-asm    native         c   native: vs cv8-asm   / c
    fib         0.060s    0.056s    0.013s    0.005s     4.17x faster   2.51x
    interp      0.681s    0.701s    0.252s         -     2.79x faster
    loop        0.614s    0.635s    0.131s    0.064s     4.83x faster   2.06x
    mem         0.037s    0.243s    0.072s         -     3.39x faster
    sieve       0.920s    0.879s    0.175s    0.039s     5.02x faster   4.46x

fib and loop within A33's 3 times C; sieve not yet - what is left is the
stack in memory, every DUP OVER + through [rbp]. Folding a literal into
the operation after it (`SIZE <` a compare with an immediate, `FLAGS +`
an add) is next.

Literal folding (628), in kernel-native.4's compiler: LIT, remembers
where a short literal's push began and its value; COMPILE, of + - AND OR
XOR = < > right after it unlays the push and lays one instruction with
the literal as its operand (add rbx,imm32; cmp and setcc for the
comparisons), and of @ or C@ a load from the literal address. Only a
literal that is the last thing laid, and only where no jump lands inside
it: BEGIN, THEN (through >RESOLVE), DO and ?DO mark the places jumps
land, and nothing before the last mark is unlaid. The pushes 627 inlines
are literals too, so `SIZE <` and `FLAGS +` fold. Medians of 3: fib 2.17,
loop 2.10, sieve 3.81 times C (from 4.46); CORE and the compiler test
the same as CV8's.
