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
  tests/verify. **Reached at 670:** forth/native-kernel.4 run by the
  native kernel instead of CV8 writes the same native-kernel, byte for
  byte, and the same map - in 0.12 s, where CV8 takes 0.68.
  tools/native-self-build.sh does it; verify's native:self-built row
  says same. The host's own words share names with the target's - 598
  "Redefining" lines that CV8, which has none of kernel-native.4, never
  prints - and change nothing in the output.

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

## 9. N2: the code generator's rules (Iterations 625-630)

The decisions, each with why; the measurements behind them, and the
dead ends, are the log's entries 625-630 (docs/PROGRESS.md). Workloads:
tests/native/bench/*.4 on bare kernels, C twins in tests/native/bench/c/;
tools/native-bench.py times them (the child's CPU, medians) and checks
that every engine prints the same answer.

- **Data written never shares a 64-byte cache line with code** (626).
  A store beside code is self-modifying code to the processor - a
  machine clear, some 750 cycles: 100 million stores to a VARIABLE took
  24.9 s, 0.15 s after. A created word's data begins at the next 64-byte
  boundary after its 24-byte stub, whose mov holds the address (so
  >BODY reads it there); the first definition after data starts on a
  fresh line. Both compilers keep it; it costs some 4 KB of padding.
- **A word that only pushes a constant is pushed inline** (627): a
  CONSTANT, a VARIABLE, a CREATE no DOES> has patched, `: FIVE 5 ;` - by
  its bytes at run time (LIT-WORD?), by a mark in the shadow at cross
  time. A DOES> word has a jump where the ret was and is called.
- **A literal folds into the operation after it** (628): + - AND OR XOR
  as `op rbx,imm32`, = < > as cmp and setcc, @ and C@ as a load from
  the address. Only a literal that is the last thing laid, and only
  where no jump lands inside it (FOLD-BARRIER, set where jumps land).
- **A compare fuses with IF, WHILE, UNTIL; OVER with + - AND OR XOR**
  (629): `DUP SIZE < WHILE` is cmp and jge, no copy and no flag made;
  `OVER +` is `add rbx,[rbp]`. By recorded positions, not by bytes.
- **DO loops in registers** (630): r14 the index, r15 the limit, the
  enclosing pair saved on the return stack; LOOP is inc, cmp, jne. CATCH
  is the kernel's bracketed by routines that keep the pair, so a THROW
  out of a loop leaves the catcher's loop whole. The cross-compiled
  kernel's own loops keep their counters in memory; the two never share
  a register.

Where it stands at 630, medians of 5 (this VM; fury's numbers to come):

    workload     cv8-c   cv8-asm    native         c   native: vs cv8-asm   / c
    fib         0.059s    0.055s    0.011s    0.005s     5.14x faster   2.04x
    interp      0.680s    0.685s    0.208s         -     3.30x faster
    loop        0.574s    0.636s    0.075s    0.064s     8.51x faster   1.17x
    mem         0.037s    0.237s    0.073s         -     3.23x faster
    sieve       0.908s    0.886s    0.102s    0.034s     8.69x faster   2.97x

The three workloads with a C twin are within A33's three times C. The
native kernel: 51,226 bytes - a 4,096-byte ELF header page and a 47,130
byte image.

## 10. N2: the native shell - the operating system's primitives (Iteration 633)

kernel.4 declares 122 primitives; the native kernel has code for 64 -
native.4's templates and native-rt.4's routines - and stubs for 58. The
shell's sources (safety.4, pool.4, shadow.4, save-system.4, shell.4,
edit.4, tree.4) name 43 of the stubs: processes (FORK EXECVE WAITPID
WAIT-NOHANG WAIT-JOB GETPID GETPPID SETPGID TCSETPGRP KILL), descriptors
and files (PIPE DUP2 DUP-FROM FILE-SIZE FILE-KIND FILE-MODE ACCESS UMASK
OPEN-DIR READ-DIR CLOSE-DIR CHDIR GETCWD ISATTY), the environment
(GETENV SETENV UNSETENV ENV-AT SYS-ARGC SYS-ARG GETPWHOME), memory
(ALLOCATE FREE RESIZE), signals (SIGNAL-ACTION SIGNALS-PENDING TRAP-XT!),
the terminal (TERM-RAW TERM-RESTORE), time and limits (LOCAL-TIME
CPU-TIMES GETRLIMIT SETRLIMIT). The other 15 are CV8's own mechanisms
(LIT, BRANCH, (DO)...) or primitives the shell does not name.

**One source for them, as for the kernel.** engine/relfasm64.4, the
assembly engine, implements every one as raw system calls in asm64 - the
assembler the native back end uses - and its conventions are the native
ones renamed: its top of stack in r12 where native has rbx, its data
stack pointer r13 (at the second item) where native has rbp, `NEXT,`
where a native routine returns. So the native routines are not written
again: a generator takes each handler's text from relfasm64.4 and emits
an NCODE routine, the registers renamed, PUSHT a native push, NEXT, a
ret - and a fix to a handler reaches both engines (A33 e's principle,
for the primitives). The handlers that keep to their arguments, the
system call and the result go across this way: most of the list.

Those tied to the asm engine's own machinery need native designs:
- **signals and traps** (SIGNAL-ACTION SIGNALS-PENDING TRAP-XT!) - the
  asm engine's handlers set flags and throw into the VM's state, its ip
  (r14) and return stack (r15); native code's return stack is rsp, and
  r14 r15 are its loop registers;
- **the environment** (GETENV SETENV UNSETENV ENV-AT, SYS-ARGC SYS-ARG) -
  from the process's start, which the native start must capture as the
  asm engine's does;
- **memory** (ALLOCATE FREE RESIZE) and the data areas handlers use
  (scratch, the terminal's saved state) - in the native image's free
  memory, off code's cache lines (section 9);
- **EXECVE** and the rest that build argument vectors from the stack.

Then the shell's Forth compiled by the native cross compiler, as kernel.4
was - it names nothing of CV8's encoding - and the shell's suites run on
the native shell, as on both CV8 engines.

**Where it stands (635).** tools/gen-native-os.py ports 42 of the 43:
each handler with its closure - the engine's subroutines it calls,
thirteen of them (the heap allocator and its lazy reservation, the
environment's, the passwd reader, CPU time, a terminal copy), as
labelled code, and the constants it names, its data chain re-rooted
(BSS_BASE is N-RTDATA, 64 KB below the data stack). The native start
captures what the engine's start does - argc, argv, envp, argbase 1 (no
image file), no raw terminal. A label the code uses as an address - in
[ ], or an immediate - becomes `label ORG @ - N-START @ +`, as 616's
OPEN-FILE. Left: SIGNAL-ACTION, whose trap handler is the asm engine's
VM's - the one native design to make. tests/native/kernel-os.4: native,
CV8's asm engine and CV8's C engine print the same.

**All 43 (636).** SIGNAL-ACTION came last: the asm engine's handler,
generated, with its sig_catch and sig_restorer, and one piece written
natively - forth/native-sig.4, which the generator inlines after the
allocator's code: int_throw, action 4's handler (^C into Forth), as the
engine's - no trap word registered, or the signal inside the allocator
(alloc_block to alloc_end): SIGINT's flag only, so a throw never leaves
the heap half updated; else the saved rip becomes trap_entry and the
saved rax -28, and trap_entry pushes the code and goes to the trap word.
The engine resumes its VM in the trap word; native code goes there.
tests/native/kernel-sig.4 - the throw route through a CATCH, a caught
signal taken once, SIGSEGV refused: the three engines the same.


## 11. N2's result, and N3 (Iterations 641-642)

**N2's shell is complete (641).** relfsh-native passes every suite CV8's
shells pass - the main shell suite, the differential suite, run-forth-
errors, the pseudo-terminal suite, mrsh, posix, forthfuzz, intrfuzz -
from the one source: kernel.4 and the shell's Forth unchanged, the back
end kernel-native.4's, the operating system's primitives the asm
engine's handlers (tools/gen-native-os.py), and four short files written
natively: native-sig.4, native-locals.4, save-system-native.4, the start
in native-kernel.4. tests/verify runs every suite on it.

**What it was for (642).** tools/bench-vm.py, SCALE=10, 3 rounds, this
VM - time relative to dash, the median and its 95% interval:

    config         loop                 fn                   str                  arith                start
    dash           26.0ms               12.1ms               13.5ms               14.7ms               31.5ms
    cv8-asm        38.830 [38.70-39.88] 45.616 [40.66-48.02] 38.277 [36.67-39.81] 55.610 [47.00-56.02] 0.670 [0.665-0.670]
    cv8-c          41.751 [39.81-42.14] 46.435 [41.43-52.24] 40.114 [38.49-41.77] 55.689 [50.67-56.09] 1.152 [1.075-1.167]
    native          4.499 [4.49-4.54]    5.182 [4.82-5.59]    4.488 [4.48-4.58]    6.318 [5.97-6.43]   0.744 [0.675-0.764]

The native shell is 8.5 to 8.8 times CV8's on every shell workload, the
same shell's source; to dash, 4.5 to 6.3 times its time, where CV8 is 38
to 56. A33's exit target for N3, five times dash: loop and str are in
it, fn just over (5.2), arith over (6.3). It starts faster than dash
(0.74), a little slower than CV8's asm engine - its file is 3.9 times
larger. To be confirmed on fury (tools/bench-report.sh has the native
shell since 642), with more rounds; this VM drifted within sessions.

**N3: from here.** fn and arith are the shell's interpreter: variable
lookup, function calls, arithmetic expansion - the shell's Forth, which
the native compiler compiles at the native kernel's prompt. Its levers,
each to be measured alone against this table: inlining small colon
words; keeping the stack's second cell in a register; and what a
profile of fn and arith shows - nothing is to be guessed (section 9).

Done since, each chosen by the profile and an A/B against the build
before it (PROGRESS.md has each): CSTRLEN and SCAN without repne scasb
(644); a VARIABLE's stores folded (645); small words inlined (646), with
internal jumps too (651); COMPARE's tail and short MOVEs as byte loops
(647); SIGNALS-PENDING eight flags at a time (648); an assignment's
environment search once (650); CSTRLEN's short strings in one load
(652); the locals' saves and restores inline, a run as one group (655); a
compare of two cells, or of one with 0, fused with its branch (661); a
VARIABLE's fetch folded into the operation after it (662); S" laid
inline, its string jumped over and its address by a rip-relative lea -
(S")'s return, to the byte after the string, missed the predictor every
time (666: 4-10 % faster here, the shell 2 % bigger). COMPILE, knows
an inlinable body by its first bytes, EB 01 and a length - so no other
code may begin a body with jmp +1 (666 did, for a one-byte string).
Built and reverted: SCAN's one-load path (654).

The profile at 655 (tools/native-prof.py, this VM, the workloads x100) -
shares are ceilings, not prizes (prompts/10): MOVE 3.2-5.3 %, CSTRLEN
3.4-5.1, FIND-SHVAR-SCAN 3.0-5.3, (S") 2.9-3.8 (fn's 3.8), AE-SKIP-WS
5.0 of arith, SCAN 2.6-3.2; (L-SAVE) and (L-RESTORE) are gone. On fury,
the reference (658, the pack's profile at 657, 279-476 samples a
workload): FIND-SHVAR-SCAN 9.0-9.6 % of str and arith - twice its share
here - then EXPAND-WORDS, DEFER, MOVE, CSTRLEN and SCAN, 2.5-4.9 %.

The scan priced (660, done twice, A/B here): native loop 5.5 %, fn 4.7
%, arith 14.5 %; asm 3-6 %. Walking its entries - no slot computed, no
call - left its time where it was. tools/native-prof.py's
NATIVE_PROF_WORD lists a word's instructions with the samples on each:
the time is in reloading VARIABLEs stored the iteration before, and in
compares of two stack cells that make a flag with setcc and neg and then
test it (629 fused only a compare with a literal). The compiler's, then,
everywhere: the next levers are such a compare fused with its branch,
and the stack's second cell in a register.

The first is done (661): = < > U< <> 0= 0< before IF, WHILE or UNTIL
lay cmp or test, two pops by mov and lea, and the jump - 5 instructions
where there were 11. A/B against 660 here: str 0.955, arith 0.953,
realistic 0.960, loop 0.990, fn 0.995; the shell 2 % smaller (536,392
bytes). The second is next.

Priced at 662 with the work it would remove: one more push-and-pop round
trip at every pushing primitive copied - 2,570 sites - cost 11-15 % on
every workload. What pushes most, counted in one instrumented build: a
VARIABLE's fetch, 3,185 of 10,951 compiled pushes, its pushed cell read
back at once by + < - OR = AND > or >R at 831 places. Those now take
[X] as their operand (662): A/B against 661, loop 0.966, fn 0.970,
realistic 0.977, str and arith within 2 %; the shell 522,504 bytes. The
rest of the traffic is the stack model's (3.2), not yet built.

### 11.1 Measured on fury

tools/bench-report.sh on fury (AMD Ryzen 7 PRO 8840HS, governor
powersave), SCALE=25, 7 rounds - CPU time as a ratio to dash's, the
median; arith's 95% interval beside it. The reports are in
bench/reports/ - 648's and 649's too since 658, from fury's first pack,
and their rows, passed on in a message before, match them:

| | loop | fn | str | arith | realistic | start |
|---|---:|---:|---:|---:|---:|---:|
| relfsh, native, 648 (70c2d65) | 4.08 | 4.57 | 3.82 | 5.72 | 5.38 | 0.94 |
| relfsh, native, 649 (the same binary) | 4.17 | 4.59 | 3.88 | 5.79 | 5.18 | 1.00 |
| relfsh, native, 652 (87a5157) | 3.80 | 4.56 | 3.49 | 4.93 [4.81-5.14] | 4.76 | 0.94 |
| relfsh, native, 657 (8ad19f8) | 3.58 | 4.21 | 3.18 | 4.87 [4.59-5.08] | 4.36 | 0.98 |
| relfsh, native, 662 (0ee4740) | 3.34 | 3.74 | 2.99 | 4.30 [4.23-4.45] | 4.20 | 0.90 |
| relfsh, native, 664 (the same code) | 3.22 | 3.91 | 2.98 | 4.48 [4.23-4.54] | 4.01 | 0.92 |
| relfsh, native, 666 (7350a38) | 3.05 | 3.55 | 3.00 | 4.25 [4.14-4.38] | 3.98 | 0.95 |
| relfsh, native, 672 (bacbf45) | 3.01 | 3.51 | 2.82 | 4.15 [4.09-4.23] | 3.91 | 0.80 |
| relfsh, native, 676 (7e8c745) | 2.88 | 3.50 | 2.89 | 3.67 [3.39-3.93] | 3.83 | 0.83 |
| relfsh, native, 691 (c6aaf26) | 2.84 | 3.41 | 2.79 | 3.67 | 3.79 | 0.80 |
| relfsh, native, 702 (1bb2428) | 2.95 | 3.25 | 2.88 | 3.83 [3.66-3.90] | 3.96 | 0.85 |
| relfsh, asm engine, 648 | 31.7 | 34.0 | 29.2 | 40.3 | 41.0 | 0.91 |
| relfsh, asm engine, 652 | 29.3 | 37.9 | 29.9 | 42.1 | 42.1 | 1.01 |
| relfsh, asm engine, 657 | 29.4 | 36.6 | 28.6 | 40.3 | 40.2 | 1.10 |
| relfsh, asm engine, 662 | 30.1 | 35.5 | 30.1 | 39.7 | 41.5 | 0.96 |
| relfsh, asm engine, 672 | 29.3 | 36.6 | 30.2 | 38.7 | 41.9 | 0.86 |
| relfsh, asm engine, 676 | 27.8 | 34.6 | 30.0 | 35.1 | 41.6 | 1.01 |

**After 652, N3's five times dash holds on every workload by the
median** - arith only just: its interval reaches 5.14. The rows for 648
and 649 are one binary measured twice: 2 to 4 % is fury's own noise
between runs. From 649 to 652 fury gave loop 0.91, fn 0.99, str 0.90,
arith 0.85, realistic 0.92; 650-652's A/B ratios on the Intel VM,
compounded, say arith 0.87-0.91 and realistic 0.85-0.91 (the range is
650's, with 19 or 80 environment variables) - a step's A/B chooses the
change, and the report is the claim (649). About 8 times faster than
the asm engine throughout.

**After 655's locals (657's run, 658).** Against 652: loop 0.94, fn
0.92, str 0.91, arith 0.99, realistic 0.92 - five times dash still on
every workload, arith's interval now reaching 5.08. Decomposed: dash's
own medians moved between the two runs, realistic's by 9 % (26.7 to
29.1 ms, the range of its four runs since 648), and the native's times -
ratio times dash's - by 0 to -6 %: fn -6, loop -4, str -3, arith -3,
realistic 0. The paired ratio is the method; but realistic's 0.92 is
mostly dash's run, and fn's gain is the one both measures show.

**After 661 and 662 (662's run, 663).** Against 657: loop 0.94, fn 0.89,
str 0.94, arith 0.88, realistic 0.97 - and here both measures agree: the
native's own times, ratio times dash's, moved by 0.92, 0.93, 0.91, 0.90,
0.89, dash's medians by -8 to +4 %. Fury gained 7-11 % where the VM's A/B
of the two, multiplied, said 4-6.5 %. Every workload now inside 4.3 times
dash, arith's interval to 4.45: N3's five times holds with a margin.
664's run is 662's code again (665): -4 to +4 % on each workload - fury's
noise between two runs, as 648 and 649 showed. A difference smaller than
that, between two of its reports, is not a claim.
666's S" inline, against 664 (667): loop 0.95, fn 0.91, str 1.01, arith
0.95, realistic 0.99; the native's own implied times 0.95, 0.91, 0.96,
0.97, 0.95. fn's 9 % is past the noise; the rest are at its edge, where
the VM's A/B said 4-10 %.
672's run (673), with 669's folds and 672's data region since 666: the
ratios 0.99, 0.99, 0.94, 0.98, 0.98, the implied times 0.99-1.06 - inside
fury's noise, where the VM's A/B said 3-5 % together; no claim. Start-up
0.95 -> 0.80: the smaller image starts faster. Memory there: idle 352 kB
resident (488 at 666), 64 kB written (344). The language benchmarks:
native 0.14 of the asm engine's time (0.17), the loop 48 -> 8 ms - 669's
I + fold.
676's CTABLE-FIND (677): native arith 0.88 against 672's run, its implied
time 0.87 - past the noise; loop 0.96 and 0.93; fn, str and realistic
inside it. And the asm engine's shell, CV8's own, which no native change
had moved: loop 0.95, fn 0.94, arith 0.91 - implied 0.92, 0.88, 0.89 - the
first fury figures in a while to speed up the shell people run.

**Memory.** tools/mem-profile.py, idle: on fury after 652, 484 kB
resident, 412 of it the executable; here, the same binary (539,724
bytes), 592 and 528 - all of the image mapped. This section said after
649 that COLD writes every page; it does not. kernel.4's COLD relocates
only DP and the word lists' thread heads. smaps splits the executable's
528 kB here into 324 kB written (Private_Dirty) and 204 kB only read
(Private_Clean) - private in smaps only because no other process maps
the file: page cache, shared by a second shell. What writes the 324 kB
is the data: a VARIABLE's or CREATE's cell sits on the code's next
64-byte line (626), so the data is spread through the code, and each
cell written at start dirties its page. tools/native-written.py
(Iteration 653): 74 of the image's 132 pages differ from the file once a
shell has started, holding 210 words' data - 23 of those pages for one
word alone (R0 S0 START on one, DP HLD SRC on another, ARGC ARGV on a
third). Fury maps fewer of the unread pages (412 against 528): the read
part is the machine's, the written part is the code's. Measured on fury
at last (658, the pack's native-written.log): of 536 kB mapped, 456
resident - 328 written (Anonymous) and 128 the file's, where here it is
328 and 208. The written part is the code's. At 662, smaller code: 512
kB mapped, 432 resident, 308 written, 124 the file's (663).

So the lever on N3's list is not relocation at start-up: it is where the
data lives. Cells gathered in a region of their own, away from the code,
would leave the code's pages clean, and shared between shells; the cost
is an absolute address per data word, where the stub's mov has one
already. With code size (539 KB, 3.8 times CV8's shell), on N3's list.

The language benchmarks (bench/langs/run.py) have a native row since 649:
the native kernel runs bench.4 with the same input; all seven answers are
CV8's.

### 11.3 dash's functions against relfsh's (Iteration 668)

N3's last exit item. dash 0.5.12 built here with symbols - -O2, not PIE,
from the Ubuntu pool's source, as tools/bench-report.sh fetches it -
and both shells sampled by tools/native-prof.py (NATIVE_PROF_NM=1 for
dash) on the bench-vm workloads x100, on the VM; a sample is about a
millisecond of CPU. Each job's time sums the words that do it, from the
top 25 of each profile, so every sum is a floor:

| arith x100 | dash | relfsh-native | times dash |
|---|---:|---:|---:|
| variables: findvar lookupvar - FIND-SHVAR(-SCAN) NAME-HASH SET-SHVAR CSTR= | 2.9 ms | 36.8 ms | 12.5 |
| expansion: argstr expandarg evalvar ... - EXPAND-WORDS EW-ENTRY XE-* ARGV-ADD ... | 23.9 | 77.0 | 3.2 |
| execution: evaltree evalcommand ... - EXEC-* SPECIAL-BUILTIN? TP-* DEFER | 20.1 | 65.2 | 3.2 |
| the whole run | 128 | 694 | 5.4 |

On realistic: variables 8.0 against 43.4 ms (5.4 times), expansion 32.1
against 93.5 (2.9), execution 10.0 against 62.1 (6.2), the whole run 167
against 668 (4.0). dash spends 38-48 % of its samples in libc - strlen,
memcpy and the like - which its rows leave out; relfsh has no libc, and
its MOVE, CSTRLEN and COMPARE are its own.

The listings, the lookup: dash's lookupvar is 73 instructions in 239
bytes, findvar 46 in 128 - a hash of the name, then a bucket's list;
relfsh's FIND-SHVAR 117, FIND-SHVAR-SCAN 76, NAME-HASH 69, CSTR= 16
(each to the next word, its header and data lines included). Setting:
dash's setvar 71 and setvareq 143, relfsh's SET-SHVAR 557.

So variables are relfsh's furthest-behind job - 12.5 times dash on
arith, where the whole run is 5.4. The index for every lookup, tried
natively (668): arith 0.964, the rest 0.99-1.00, and the asm shell 2-5 %
slower - not taken. The scan's time is the compiler's code (660), which
is the stack model's to fix (3.2).

## 12. The stack model, measured (Iteration 669)

Section 3.2's model - the top items in registers through a run of code,
written back at calls, branches and labels - was priced at 662: one more
push-and-pop at every push costs 11-15 %. But a push is the compiler's
to remove only where an inline word takes the cell straight back; where
a call takes it, it is the calling convention's. So, before building:
what follows each push? One build with the compiler instrumented (not
kept), every pair it compiled, the shell's sources (40,185 pairs):

- DUP 1,556: a literal 564 (DUP lit = is folded, 629), a call 464,
  CSTRLEN 164 (a call), C@ 82, 0= 41, 0< 40, 1+ 38, a branch 36, >R 29;
- OVER 380: a literal 162, a call 50, + 38 and - 13 (folded, 629), = 31;
- R> 227: a call 87, DROP 46, + 11; R@ 75: a call 42, + 9;
- a literal not folded, 3,154: a call 2,021, EXIT 332, another literal 249;
- and in the source, which the count did not see: I + 47, ?DUP IF 103,
  DUP IF 22, DUP WHILE 12, DUP 0= IF 35, DUP 0< IF 24.

Most pushes feed a call. The stages, then:

1. **Peepholes for the frequent pairs** - done: a literal and its
   operation (628, 645), OVER and its operation (629), a compare and its
   branch (629, 661), a VARIABLE's fetch and its operation (662), and at
   669 R> DROP (add rsp,8), DUP >R (push rbx), R@ + (add rbx,[rsp]), I +
   (add rbx,r14), and ?DUP, DUP, DUP 0= and DUP 0< before IF, WHILE or
   UNTIL (test rbx,rbx and the jump). 669's A/B: loop 0.982, fn 0.988,
   str 0.986, arith 0.979, realistic 1.005.
2. **A deferred push** - the second cell in a spare register through a
   run, the general form of stage 1, catching chains as well as pairs.
   What it adds after stage 1 is the pairs the count shows left - small -
   and it would have to be woven through every fold above. Not now.
3. **Arguments in registers across calls** - where most pushes go. A
   change of the native calling convention: every primitive, every
   runtime routine, the routines generated from the asm engine. The
   biggest prize left in the stack, and a back end rewritten; to be
   decided before it is begun.

## 13. What is left, priced (Iteration 671)

Neither has a milestone; each was priced before either is begun.

**Arguments in registers across calls** (12's stage 3). Priced with the
work it removes: one more push-and-pop round trip before every call the
compiler lays - 5,433 in the shell - cost, A/B on the VM, loop 7.6 %, fn
9.7 %, str 7.0 %, arith 3.0 %, realistic 8.6 %. A convention keeping the
second cell in a register as well would take back part of that - not
all: what a call's arguments no longer store, the deeper cells spill -
so 3-6 % is the honest guess. Its cost: every primitive, every runtime
routine, the routines generated from the asm engine, the compiler's
every laid sequence, and SP@ SP! DEPTH PICK CATCH THROW, rewritten.

**Looked at again before beginning (675), and not begun.** A second cell
held in a register does not take a round trip away - it moves one: every
push spills the register to memory and every pop refills it from there,
one instruction more each time. Counted over 669's instrumented build of
the shell, primitive by primitive: instructions +22 %, memory operations
-4 % (SWAP and OVER's). What it would remove is the second cell's
store-to-load latency where a callee reads it soon - priced by storing
the second cell again before every call (behaviour unchanged): loop 2.3
%, fn 2.5, str 4.0, arith 5.0, realistic 5.3. So the prize is at most
that, before the extra instructions take their share - against the whole
back end rewritten. 671's 3-6 % priced a round trip of the top cell,
which this convention leaves where it is: the wrong work. Not begun.

**Data in a region of its own.** 762 CREATE words keep their data in the
image, each on the code's next 64-byte line (626), and 119 more are
BUFFER:s, outside it. From each stub to the next word they take 106,672
bytes: 18,288 of stubs, 22,713 of padding before the data, and 65,671
of data, its padding after, and the next header - 651 of them a cell or
two. Gathered in one region, the image would lose most of the padding,
about 45 kB, 9 %; and a started shell's written pages - 77 of 130 here,
308 kB, every one of them for some word's data (653) - would fall to the
handful the data fills: about 270 kB less private memory a shell. Its
cost: two pointers where there is one - the compiler lays code at one,
CREATE ALLOT , and HERE work at the other - in kernel-native.4, in the
cross compiler for the kernel's own data, and in the native image's
save; N4's byte-for-byte check keeps it honest.

**Done for the shell's data (672).** DP and a second pointer, DDP, trade
places: CREATE lays its stub in the code and points it at DDP's region,
512 KB below the runtime's data, then HERE ALLOT , and C, lay data until
the next definition - :, CONSTANT, another CREATE - swaps them back.
DICT-LIMIT reads a cell the swaps set, so each region has its own limit.
The image is two PT_LOAD segments, the code's and the data's; the native
SAVE-SYSTEM writes the code, a page's padding, and the data. The shell:
530,088 -> 459,232 bytes (-13 %: 440 KB of code, 16.9 KB of data); a
started shell's written pages 77 -> 10, its copied memory 344 -> 64 kB;
A/B, 1.5-3.5 % faster too. The kernel's own variables - DP, R0, POCKET
and the rest, cross-compiled - are still in the code, on the 10 pages
left: the cross compiler's half, next.

**And the kernel's (674).** The cross compiler's DP-T and N-DDP-T trade
places the same way: a VARIABLE's stub in the code, its cell - and the
ALLOT-T after it, TIB POCKET CONTEXT and the rest - in data's region;
N>A and N-HEAD swap back. N-ELF's data segment holds the kernel's 1,880
bytes, WRITE-ELF writes them after the code, the run-time DDP starts past
them, and the native SAVE-SYSTEM copies from START to data's end, so the
scrub and the unrelocation (save-system.4's, START-relative) find the
kernel's variables where they live now. The shell: 452,920 bytes, 18.7
KB of it data; a started shell writes 6 pages, 44 kB - from 77 and 344
at 671. The native kernel still builds itself, byte for byte.


## 14. Where the native shell's bytes go (686)

GOALS.md 9, the user's: why the native shell is as big as it is, and
what can shrink it at no cost in speed. tools/native-budget.py splits the
image - the dictionary walked for each header's start, the code
disassembled by objdump and each instruction classed, S" strings laid
inline found by their bytes (SLIT,'s jmp, then sub rbp,16, mov
[rbp+8],rbx and a lea back to them) and masked before objdump sees them:

```
relfsh-native: 452912 bytes - the code segment 432728 (from N_BASE: the runtime 7077, headers 28203 in 2381 words, code 393352), the data segment 18736

the words' code by class (391524 bytes classed of 393352):
  stack      164911   42.1 %
  other      116241   29.7 %
  literal     45557   11.6 %
  call        30741    7.9 %
  branch      26346    6.7 %
  data         4428    1.1 %
  return       3300    0.8 %

encodings:
  jcc 2 bytes               599
  jcc 6 bytes              2913
  jmp 2 bytes               462
  jmp 5 bytes              1422
  literal 5 bytes          1155
  literal 7 bytes          5691
saved if:
  [rbp+0] as a register needing none   20117 bytes
  literals at their shortest           16609 bytes
  forward branches that fit rel8, as rel8   10725 bytes
  backward branches that fit rel8, as rel8     594 bytes
```

The data stack in memory is 42 % of the words' code: every push and pop
a cell in rbx costs, 8 bytes a pair. Four ways the bytes could shrink
with the same instructions executed, each priced in bytes by the tool:

1. **Literals at their shortest - 16.6 KB.** 5,691 loads use mov rbx,
   imm32 (7 bytes) where most values are positive and under 2^32 - mov
   ebx, imm32 is 5 and zero-extends - and 0 could be 2 (xor, which sets
   flags: to be checked against the compare-branch fusion). The cheapest:
   one word, LIT,.
2. **Forward branches that fit in rel8 - 10.7 KB.** 2,913 jcc and 1,422
   jmp use rel32; most land within 127 bytes. A forward branch's distance
   is known only at THEN, after the code between is laid: shrinking it
   moves that code, and the relative calls and pending branches in it.
   Medium-hard.
3. **The data stack's register - 20.1 KB.** 20,117 instructions address
   [rbp+0]: rbp as a base always needs a displacement byte; r15, or rsi,
   would need none. Every runtime routine, the compiler and the generated
   OS routines name rbp: a large change for 4.6 %.
4. Backward branches that fit in rel8 - 0.6 KB: most already do.

Not shrinkable without slowing: calls (7.9 %, rel32), the strings' own
bytes (1.1 %), the headers (28 KB, which the forth builtin's interpreter
needs).

**687: literals at their shortest, built and held back.** LIT, laid
mov ebx,imm32 (5 bytes, zero-extended) for 0 to 2^32-1 and kept the
7-byte form for negatives; FRESH-LIT? learned the literal's end
(LIT-END) instead of assuming 15 bytes; LIT-WORD? learned the 5-byte
form, so constants stay inlined. Every native test the same, the
self-build the same. The code segment 432,728 -> 426,706 bytes (the file
-4,088, by whole pages); 2,005 zeros at 5 bytes and 566 negatives at 7
remain, and 1,711 CREATE stubs keep their 7-byte form by design.
Speed, four A/Bs against 686: realistic 1.082, 1.004, 1.034, 0.994;
arith 1.012, 1.036, 1.030, 1.028; fn 1.021, 1.007, 1.015. The
diagnostic: the 5-byte load padded back to 7 with a 2-byte NOP - the old
layout, one more instruction - was 1.058-1.096 slower: so the load itself
is not slow, an executed NOP per literal is, and what moves the others
by a few percent is where the code lands. Arith's +1-4 % in all four
runs fails the user's condition - not slower - so it is not committed.
What it shows for every size change after it: shrinking the code moves
the hot loops, and the VM's A/B cannot tell a 3 % layout effect from a 3
% cost. The next step is a measurement that can - the same change built
over several paddings of the code's start, so layout averages out.

**688: an A/B over layouts.** tools/native-ab-layouts.py BASE builds each
side four times - the native kernel with 0, 16, 32 or 48 bytes of target
space before its runtime, so the routines and every word after them
move, and the shell with as many before its first source
(tools/build-native-shell.sh's NATIVE_LAYOUT_PAD) - and times all eight
together. Per workload: the spread of each side's layouts, and the ratio
of their geometric means. Against itself, 9 rounds: layouts alone moved
a workload up to 4.9 %, and the averaged ratios came out 0.989-1.016 -
the method resolves about 2 %. A first version padded only the shell's
words: the null came out 0.987-1.020, but the change it was for moves the
kernel's words, which that padding left in place - and it was those.

**689: literals at their shortest, kept.** 687's change through 688's
A/B, 13 rounds: loop 0.994, fn 0.998, str 0.985, arith 1.012, realistic
0.998 - inside the method's 2 %; arith's 1-4 % of 687 was where the
kernel's words had landed, 8 bytes further on. The shell 452,912 ->
448,824 bytes (code 432,728 -> 426,706); the kernel +8 bytes (LIT,'s own
growth); the shell's data +8 (LIT-END). Left for later: zeros by xor
ebx,ebx (2,005 loads, 3 bytes each, if the flags allow), -1 by or (566).

**690: 0 by xor and -1 by or, built and held back.** LIT, laid 0 as
xor ebx,ebx (2 bytes; it sets flags, which no fold reads across a
literal - FRESH-CMP? and its kin want the compare laid last) and -1 as
or rbx,-1 (4); LIT-WORD? learned both. Every native test the same, the
self-build the same, the suites passed. Over layouts against 689, 13
rounds, both: fn 1.028, the rest 0.994-1.018 - or reads rbx, so a TRUE
waits on the cell under it, where mov did not: -1 left out. Zero alone,
-3,470 bytes of code: realistic 1.015 and 1.031 (17 rounds), arith
1.009 and 1.008, the rest 0.995-1.029. Realistic slower in every run, by
1-3 %, at the edge of what the method resolves - and the pads move code
by at most 48 bytes, so a change of a page's worth (this one shrinks the
code by most of a page) can still move things the pads do not. Under
"not slower": held back. Those bytes stay.

**691: the method's floor, and the branches priced.** The layout A/B's
null run again, with pads that also move the code by up to 3 KB
(0, 1040, 2080, 3120 - the four 16-byte phases, a page's worth of
shifts): the two sides byte for byte the same, layout by layout (cmp),
and yet 0.979, 1.021, 1.023, 1.019, 1.011 - layouts alone 0.98-1.08.
At 13 rounds over four layouts the VM resolves about 2.3 %, so 690's
zero (realistic 1.015 and 1.031) cannot be called slower or not; the
nulls' realistic came out 1.003, 1.009, 1.011.

Forward branches priced from the disassembly: 2,933 rel32 branches
would fit in rel8 once shrunk - 10,993 bytes. Shrinking one moves the
code it skips back by 3 or 4 bytes, so whatever in that code points out
of it, or is pointed at from outside, must be fixed: of the 2,933, 1,409
skip a call (its rel32 then off by the shrink), 429 a branch that leaves
(the same), 39 something rip-relative. 1,056 skip nothing to fix - 3,851
bytes. The whole needs the compiler to keep, per definition, every
rel32 field and every code address it holds (LIT-AT, CMP-AT, LAST-AT,
the control-flow stack's origins) and move them all; the safe part needs
only to know that the skipped code holds none of them.

**692: the user's ruling, and what it kept.** Inside the layout A/B's
floor counts as not slower (the user, 692). Kept under it: 0 by xor
ebx,ebx (690's half) - the shell 448,824 -> 444,728 bytes, code -3,470.
Then the safe forward branches, built: >RESOLVE laid a branch short when
nothing since its own field needed fixing - REL,, >MARK, LEAVE's link
and S"'s lea recording where the last relative field ended (LAST-REL),
MARK-TARGET where the last jump landed (LAST-LAND) - moved the skipped
code back and rewrote E9 as EB, 0F 8x as 7x. The first shell built
crashed at start: ?DUP IF (669) lays test and a jnz +13 over a drop and
its jmp, landing where the moved code begins, and nothing recorded that
landing; bisected to LOOKUP-VAR by definition, fixed by shrinking the
jnz with the jmp (QDUP-JMP). Then every test passed - and the shell's
code was 180 bytes smaller: 605 branches shrunk, about 2.4 KB, and
SHORTEN and SHORT-OK?, written in Forth and compiled by the native
compiler, 1,780 bytes of the kernel with their variables and headers,
2.2 KB in all. Set aside: the code that saves the bytes costs them.
What would pay: the ELSE case (the IF's branch into the moved code
fixed too), calls inside the skipped code (their rel32s +3 or +4), the
kernel's own branches through the cross compiler - and the shrinker
small, in assembly, not Forth.

**693: forward branches laid short - kept.** Every relative field a
definition lays (calls and backward branches through REL,, resolved
forward branches, ?DUP IF's jnz) goes in a table - field, target, width
- allocated for the definition and freed at `;`. >RESOLVE shortens a
branch whose target is within a signed byte: E9 to EB, 0F 8x to 7x, the
skipped code moved back 3 or 4 bytes, and REL-FIX (native-rt.4, in
assembly) walks the table: a field in the moved code aimed out of it
gains the shrink, one before it aimed into it - the IF of IF ELSE THEN,
?DUP IF's jnz - loses it, and the entries follow the code. Not when a
LEAVE's link is pending in the skipped code (LAST-LEAVE), nor once the
table is full. ELSE lays its jmp before resolving the IF, so a shortened
IF carries ELSE's pending field back with it: ELSE takes SH-MOVED off its
address - found by the new test, whose IF ELSE THEN gave 22 for 20 and
then ran wild. tests/native/kernel-short.4 (native:short): calls in
skipped code, IF ELSE THEN, nesting, ?DUP IF, ?DO and LEAVE, WHILE,
UNTIL, S", EXIT, RECURSE, a body too long for a byte - CV8 the oracle.

Shrunk: 1,951 jcc and 685 jmp, about 9.9 KB; 1,238 bytes of fitting
branches left (LEAVE's, a full table). The shrinker in the kernel
+3.4 KB, so the shell's code 423,236 -> 417,816 (-5,420), the file
444,728 -> 440,696. Over layouts against 692, 13 rounds, pads to 3 KB:
loop 1.002, fn 0.989, str 0.954, arith 0.982, realistic 0.969 - not
slower; denser code may be the faster for it. Next for the bytes: the
kernel's own branches through the cross compiler, whose code is not in
the image, and the shrinker itself in assembly.

**694: the kernel's own literals at their shortest.** The kernel's code
is laid by the cross compiler, and native.4's N-LIT laid every literal
as mov rbx,imm32: the budget of native-kernel showed 1,308 seven-byte
loads, 3.5 KB to save at no cost in the image - the cross compiler's own
code is not in it. N-LIT now lays them as LIT, does at run time: 0 by
xor ebx,ebx, 1 to 2^31-1 by mov ebx,imm32; LIT-WORD? already knows both.
The kernel's code -2,767 bytes, the shell's -2,760 (the file 440,696 ->
436,600). Over layouts against 693: 13 rounds 0.963-1.065 (str 1.065 on
a noisy run, the spreads 0.87-1.15); str, realistic and loop again at 21
rounds, 0.961, 1.018, 0.999 - not slower.

**695: the shrinker in assembly.** SHORTEN's work - the opcode rewritten,
the table's fields fixed, the code moved, the rel8 written - is
SHORT-MOVE now, one routine in native-rt.4 (REL-FIX folded into it), and
SHORT-OK?'s tests SHORT-FITS?, RT+'s store RT-PUT; the Forth words that
remain are wrappers. Two faults on the way: rep movsb advances rsi, which
still held B for the rel8 after it - every IF crashed the kernel - and
imul's third operand wants `#` (24 # imul,), without which it laid a
two-operand imul and RT-PUT stored nowhere sane: IF ELSE THEN's else path
hit an illegal instruction. kernel-short.4 caught both. The kernel's
code 64,491 -> 63,533 (-958), the shell's 415,056 -> 414,096. The
shell's compiled code is what it was, moved by the kernel's shrinking:
over layouts 0.955-1.026, the floor.

**697: the data stack in r15.** rbp as a base always takes a
displacement byte - [rbp+0] is four bytes - where r15 takes none: mov
[r15],rbx is 49 89 1F. 696 moved the counted loop's limit off r15 to
r13 (r12 is gen-native-os.py's scratch); now the data stack is r15:
the assembler sources renamed (native-rt.4, native-locals.4,
native-sig.4, native.4, native-kernel.4), gen-native-os.py's map (the
asm engine's r13 to r15), and kernel-native.4's raw sequences re-encoded
- a push is 7 bytes now, so LIT-WORD? reads a 56-bit pattern and its
offsets move by one, the inline DUP and OVER are 7 and 11, ?DUP IF's
jnz is +12, a CREATE stub's address is at +10 (>BODY, N>BODY,
native-prof.py, native-budget.py) and its ret at +14 ((;CODE)); the
signal path resets the interrupted r15 at the ucontext's offset 96,
where rbp's was 120. Every native test, the self-build, the suites: as
before.

The shell 436,584 -> 424,296 bytes (code 414,096 -> 403,193, -10.9 KB),
the kernel 67,472 -> 63,376. Over layouts against 696, 13 rounds: loop
1.053 - one layout at 1.165 - fn 1.002, str 1.010, arith 1.024,
realistic 1.015; loop, arith, realistic again at 21: 1.008, 1.010,
1.017. Inside the floor. The native shell since 686: 452,912 ->
424,296 bytes, -28.6 KB, -6.3 %.

**698: a CREATE stub in 17 bytes.** 697's budget left 1,547 seven-byte
loads, most of them the stubs of created words - 967 in the shell (769
plain, 198 patched by DOES>), 23 bytes each: push, mov rbx,imm32, ret,
eight nops. Data's region is below 2^31, so the address fits mov
ebx,imm32 (5 bytes); DOES> needs only five bytes from the ret for its
jmp, so four nops. Now push, mov ebx,data, ret, four nops: >BODY reads
+8, (;CODE) patches +12, and LIT-WORD? already took the mov ebx form, so
a VARIABLE's push is still inlined. CREATE, N-STUB24 (the cross
compiler's), N>BODY, native-prof.py and native-budget.py moved together.
The shell's code 403,193 -> 397,347 (-5,846), the file 424,296 ->
420,200. Over layouts against 697: 0.972-1.006.

**699: backward branches short - built, set aside.** BACK, knows its
distance as it lays the branch, so UNTIL, AGAIN, LOOP and +LOOP could
take rel8 at once (not after ?DUP's fused test, whose jnz lands past the
field - the table's last entry shows it). It worked - loops, the
short-branch test, every native test - and shortened all but 37 bytes'
worth; but those branches were only 611 bytes, and the new BACK,, Forth
through the native compiler, cost more: the shell's code came out 232
bytes larger. The same lesson as 692's first shrinker, at a smaller
scale: a saving smaller than the code that makes it is not one.

**Idea 9's account (686-698).** The native shell 452,912 -> 420,200
bytes (-32.7 KB, -7.2 %), its code 432,728 -> 397,347 (-35.4 KB, -8.2 %):
literals at their shortest (689, 692, 694), forward branches short
(693, 695), the data stack in r15 (696, 697), CREATE stubs in 17 bytes
(698). Every step kept under the user's ruling - the layout A/B inside
its floor, which several of them beat. Left: what is not cheap - the
stack traffic itself (41 % of the code; a deferred push would cut it and
might be faster, a compiler change), and the headers (28 KB, which the
forth builtin needs).

## 15. Searching the compilers' choices (GOALS.md 10, from 700)

The user's idea 10: a genetic or randomized search over the compilers'
choices - CV8 faster without a larger image, the native shell smaller
without being slower. What bounds it here is the measurement: each
candidate is a build and an A/B over layouts, 1-2.5 minutes, resolving
about 2.3 %; a search over many knobs at once could not tell its
candidates apart. So one knob at a time, swept, the winners re-measured.

**700: the native inliner's limit.** INLINE-MARK copied bodies of 1 to
64 bytes into their callers (646, 651); the limit is INL-LIMIT now. Each
value against HEAD (64) over four layouts, 9 rounds, the candidates again
at 21 (the second figure):

| limit | code bytes | loop | fn | str | arith | realistic |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 386,403 | 1.092 | 1.061 | 1.073 | 1.064 | 1.080 |
| 16 | 387,923 | 1.034, 1.051 | 0.978, 1.067 | 1.007, 1.010 | 1.037, 0.994 | 0.976, 1.052 |
| 24 | 389,859 | 1.036 | 1.011 | 0.994 | 1.096 | 1.033 |
| **32** | **394,075** | 1.025, 0.988 | 1.010, 1.033 | 0.938, 1.023 | 0.986, 1.040 | 0.957, 1.010 |
| 64, the control | 397,379 | 0.975 | 0.980 | 1.033 | 0.998 | 0.995 |
| 128 | 403,243 | 1.093 | 0.968 | 1.074 | 0.995 | 1.014 |

128 is larger and slower: copies past 64 bytes cost more in the cache
than the calls they save. 8 is clearly slower, 16 and 24 too by the
longer runs. 32 saves 3,272 bytes and its two runs average 0.980-1.021 -
inside the floor: kept. The control's own 0.975-1.033 is the floor at 9
rounds.

**703: fury on the size work (686-702).** Native against dash at 702:
loop 2.95, fn 3.25, str 2.88, arith 3.83, realistic 3.96; against 681's
run 1.02, 0.95, 1.01, 1.06, 1.06 by the ratios, and by the implied times
1.023, 0.952, 0.970, 1.021, 1.007 - inside fury's noise: the native shell
32.7 KB smaller and as fast. Idle 328 kB resident (340 at 681), the
executable 260 of it, 44 kB written as before; its file's code segment
384 kB.
