# relfsh: a POSIX shell written in Forth, on a Forth that assembles its own engine

*Draft for ForthHub. The bracketed notes are for the author to settle;
everything else is measured, and says where. The working copy is a
Claude Doc, edited by the author; this file mirrors it.*

relfsh is a POSIX shell written in Forth: one static file of 136,524
bytes that runs in 196 kB of memory, and that you can extend from the
inside, in Forth, while it runs. Underneath is a small Forth that
compiles itself, and whose x86-64 engine is assembled from Forth
source by an assembler written in Forth. This is why it exists, how it
is built, and how we know it works.

## Why

I have long been a fan of Forth. What fascinates me most is that one
person can bring up a working Forth on a new platform in a few days -
the whole system, compiler included, small enough for one mind to hold.

In the 1990s I came across SOD32, Lennart Benschop's Forth: a small
virtual machine running a machine-independent image. I found it
beautiful. It had two weaknesses - the limits built into its design,
and its speed - and RelF, Relative Forth, began as my attempt to fix
them. It worked, but the gain in speed was modest, and after a while I
put it aside.

Meanwhile another thought kept coming back: the shell is an underrated
tool. Most of the glue in our systems - the code that connects
programs, files and processes - is exactly what the shell is good at.
Written in Python instead, glue grows longer, and every extra line is
another place for a mistake. But the shell has two weaknesses of its
own: it can be extended only with external programs, and it offers
almost nothing in the way of data structures.

That is where the two ideas met. A shell written in Forth could be
small and frugal, because Forth is; and it could be extended from
inside, in Forth itself, given the right builtin.

## The shell

A POSIX sh: pipelines, lists, compound commands, functions, here-
documents, every expansion, job control, a line editor with history,
search and completion, `$'...'` and `set -o pipefail` from POSIX.1-2024.
And the `forth` builtin, which reaches the whole Forth system the shell
is written in:

    $ forth '2 3 + .'
    5
    $ forth 'S" examples/seq.4" INCLUDED'
    $ seq 1 3 | while read n; do echo "line $n"; done
    line 1
    line 2
    line 3

`seq` there is a new builtin, defined in a dozen lines of Forth. The
examples directory also has a prompt hook, a TCP echo server and an
HTTP server, all in Forth, inside the shell. A Forth error in such
code fails that one command, as any builtin's failure does: `$?` is
1, the message goes to standard error, the shell goes on - and so does
a division by zero or a bad address, which the engine turns from the
CPU's trap into a Forth THROW.

## What it is

    ./relfsh - one static file, 136,524 bytes
    +------------------------------------------------+
    | the shell: parser, executor, line editor       |
    |   shell.4  tree.4  edit.4          (Forth)     |
    +------------------------------------------------+
    | the Forth: kernel, compiler, extensions        |
    |   kernel.4  extend.4  ...          (Forth)     |
    +------------------------------------------------+
    | the engine: 15,456 bytes of x86-64, no libc    |
    |   or a C engine, anywhere a C compiler is      |
    +------------------------------------------------+

The shell and the Forth are one byte-coded image; an engine runs it.
There are two engines and they run the same image: a portable one in
C, and one written in x86-64 assembly on raw system calls. Every test
runs on both, and their outputs must agree.

## The Forth underneath

- **Token-threaded.** 64 one-byte opcodes, and further primitives as
  two-byte tokens (RelF calls these "escaped primitives"). Colon
  definitions call each other by *relative* offset - the "Relative" in
  RelF - so an image is position-independent, and its 4 MB region is
  exactly the reach of a call.
- **One image per cell width.** 8-byte cells or 4-byte, little-endian;
  one image runs on every machine of its width.
- **It compiles itself.** `cross.4`, running on the previous kernel
  image, compiles `kernel.4` into the next one - and it comes out byte
  for byte the same. gforth, running the same cross-compiler, produces
  the same bytes too: a diverse double compile.
- **What it claims.** It passes the CORE tests - John Hayes' suite,
  with additions from the Forth 2012 test suite: 2,136 checks - on
  both engines and both cell widths. Beyond CORE it
  has what the shell needed; it does not claim the other word sets,
  and the missing words can be defined with the `forth` builtin.

## Assembling its own engine

    engine/cv8.c --cc--> relf64 (the C engine, once)
                            |
    kernel.4 + cross.4 -----+--> kernel64.img  (reproduces)
                            |
    relfasm64.4 + asm64.4 --+--> relfasm64     (15,456 bytes)
                                |
    relfasm64.4, again ---------+--> relfasm64 (the same bytes)

The x86-64 engine is written in Forth, `engine/relfasm64.4`, with an
x86-64 assembler written in Forth, `forth/asm64.4`, in postfix syntax:

    rax [ rbx 8 ] mov,       \ mov rax, [rbx+8]
    r12 [ r13 ] mov,         \ mov r12, [r13]

The C engine, built once, runs the assembler; the engine that comes out
assembles itself again, to the same 15,456 bytes. The assembler is held
to GNU as's bytes on the 456 instruction shapes the engine uses, and on
random instructions of every form it offers - which is how it was found
to have assembled `push`, `pop` and `xchg` with a memory operand as
register instructions, silently. Fixed; the random check now runs with
every verification. The nearest prior art I know is Lars Brinkhoff's
lbForth, a self-hosting metacompiled Forth bootstrapped from a few
lines of C. [author: other prior art to name?]

## Numbers

Memory, measured with tools/mem-profile.py (kB):

                       resident    private
    relfsh, asm engine      196        196
    relfsh, C engine      1,940        384
    dash                  1,968        100
    busybox ash           1,608        252
    bash                  3,704      1,740

Resident, relfsh on its own engine is the smallest by far - it maps no C
library. Counting only private memory, dash uses half of relfsh's.

Speed, honestly. The shell first: CPU time as a ratio to dash, the
median of ten rounds in which every shell ran every workload
(tools/bench-vm.py). The first row is dash's own time.

| CPU time, times dash | loop | fn | str | arith | realistic | start |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dash, in ms | 4.1 | 2.6 | 2.8 | 3.0 | 3.4 | 1.4 |
| busybox ash | 1.1 | 1.2 | 1.1 | 1.3 | 1.3 | 0.93 |
| bash | 2.1 | 2.4 | 2.2 | 2.4 | 2.8 | 1.3 |
| relfsh, asm engine | 25 | 22 | 20 | 27 | 27 | 0.56 |
| relfsh, C engine | 26 | 23 | 21 | 28 | 28 | 1.1 |

The workloads: loop is 2,000 rounds of test and increment; fn, 600
function calls; str, 400 rounds of `${s##*/}`, `${s%/*}` and `case`;
arith, 700 steps of a modular Fibonacci; realistic, option parsing,
trims, `case`, arithmetic and `set --`, 300 rounds; start, one `sh -c
true`. relfsh starts in just over half of dash's time, but runs scripts
20 to 28 times slower - it is a bytecode interpreter, and dash is C.

Then RelF as a Forth: seven small programs, the same Forth text for all
three Forths, the same algorithms in C, Go, Python and Ruby
(bench/langs/run.py). Milliseconds, best of three, the process's start
included; every result checked against C's. The last column is the
geometric mean of the ratios to RelF.

| ms | fib | loop | sieve | bubble | matrix | fannkuch | collatz | vs RelF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C (gcc -O2) | 5 | 12 | 27 | 21 | 3 | 35 | 21 | 0.07 |
| Go | 16 | 24 | 30 | 8 | 6 | 25 | 30 | 0.09 |
| gforth-fast 0.7.3 | 67 | 102 | 117 | 81 | 91 | 262 | 168 | 0.60 |
| gforth 0.7.3 | 71 | 90 | 148 | 109 | 93 | 372 | 175 | 0.68 |
| RelF, asm engine | 67 | 123 | 519 | 106 | 165 | 470 | 253 | 1.00 |
| RelF, C engine | 69 | 110 | 620 | 134 | 201 | 420 | 282 | 1.08 |
| pforth 2.0.1 | 174 | 204 | 463 | 326 | 410 | 1,299 | 467 | 2.04 |
| Python 3.12 | 244 | 967 | 558 | 307 | 187 | 506 | 586 | 2.20 |
| Ruby 3.2 | 228 | 736 | 533 | 423 | 198 | 976 | 500 | 2.36 |

RelF is 2.0 to 2.4 times faster than pforth, Python and Ruby, 1.5 to 1.7
times slower than gforth, and 11 to 14 times slower than C and Go; its
weakest case is byte memory, the sieve. Both tables were measured on
September 27, 2026, on one core of an Intel Xeon at 2.1 GHz.

## How it is tested

- CORE: 2,136 checks, the same output from both engines.
- The shell: 1,033 assertions in 91 files; 132 cases compared with
  bash; 421 constructs in every context, against bash and dash; 48
  POSIX cases, scored only where every reference shell agrees; mrsh's
  suite; 32 sessions through a pseudo-terminal, for the line editor
  and job control; the POSIX standard's own examples, 64 of them, with
  the results its text states.
- Beyond the suites: seven shells voting on 131 scripts - relfsh is with
  every strong majority; 1,000 random programs against dash and bash,
  without a difference; each test script rewritten nine ways that must
  not change what it prints; mutation testing on the compiled image;
  the test harness run by relfsh itself; signal storms, where every trap
  ran and every sum came out exact; and real scripts - zlib's configure,
  and ncurses's, 32,301 lines of Autoconf, whose 1,041 generated files
  match dash's run except where autoconf recorded how each shell's
  `echo` omits a newline.
- Every change is verified on three machines - two x86-64 and an
  ARMv7 board - before it goes in.

## What it is not

- A complete Forth 2012 system: it is CORE, and what the shell needs.
- Fast at scripts: see above.
- Everywhere native: the assembly engine is x86-64 only. The C engine
  runs on x86-64, i386 and ARMv7, and under qemu on AArch64 and RISC-V.
- Localised: no locales; the shell keeps time in UTC.

## How it was built

[author: your words here. A draft, to replace or keep: "Most of the
code, tests and documents of the last [period] were written by Claude,
an AI model, in several hundred numbered iterations under my direction.
I set the goals, made the decisions - thirty of them recorded in
docs/QUESTIONS.md - and ran every change on my own machines before it
went in. The log of every iteration, mistakes included, is
docs/PROGRESS.md."]

## Try it

    git clone [author: the repository's URL]
    cd relf && make
    ./relfsh
    make verify            # every suite; takes a few minutes

GPL version 2. Questions I would like answered by people who know
Forth better than I do: is choosing opcodes by dispatch counts a known
practice, and what did it miss? And what would you build with a shell
you can extend in Forth?
