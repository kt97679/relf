# relfsh: a POSIX shell written in Forth, on a Forth that assembles its own engine

relfsh is a POSIX shell written in Forth: one static file of 137,612 bytes that takes about 200 kB of memory at rest, and that you can extend from the inside, in Forth, while it runs. Underneath is a small Forth that compiles itself, and whose x86-64 engine is assembled from Forth source by an assembler written in Forth. This is why it exists, how it is built, and how we know it works.

## Why

I have long been a fan of Forth. What fascinates me most is that one person can bring up a working Forth on a new platform in a few days—the whole system, compiler included, small enough for one mind to hold.

In the 1990s I came across SOD32, Lennart Benschop's Forth: a small virtual machine running a machine-independent image. I found it beautiful. It had two weaknesses—the limits built into its design, and its speed—and RelF, Relative Forth, began as my attempt to fix them. It worked, but the gain in speed was modest, and after a while I put it aside.

Meanwhile another thought kept coming back: the shell is an underrated tool. Most of the glue in our systems—the code that connects programs, files and processes—is exactly what the shell is good at. Written in Python instead, glue grows longer, and every extra line is another place for a mistake. But the POSIX shell has two weaknesses of its own: it can be extended only with external programs—bash, ksh93 and zsh can load builtins, but written in C against their own headers—and it offers almost nothing in the way of data structures.

That is where the two ideas met. A shell written in Forth could be small and frugal, because Forth is; and it could be extended from inside, in Forth itself, given the right builtin.

## The shell

A POSIX sh: pipelines, lists, compound commands, functions, here- documents, every expansion, job control, a line editor with history, search and completion, `$'...'` and `set -o pipefail` from POSIX.1-2024. And the `forth` builtin, which reaches the whole Forth system the shell is written in:

    $ ./relfshasm64
    $ forth '2 3 + . CR'
    5
    $ forth 'S" examples/seq.4" INCLUDED'
    $ seq 1 3 | while read n; do echo "line $n"; done
    line 1
    line 2
    line 3

`seq` there is a new builtin: a dozen lines of Forth in `examples/seq.4`, not part of the binary, loaded while the shell runs. The [examples directory](https://github.com/kt97679/relf/tree/master/examples) also has a prompt hook, a TCP echo server and an HTTP server, all in Forth, inside the shell. Put the `forth` line in the file `$ENV` names, and the builtin is there at every start.

Here is `seq` itself, less the two lines of `SEQ-NUM` that read a decimal number: the whole interface a builtin has—its arguments through `ARGC` and `ARGV@`, its status through `LAST-STATUS`, and `BUILTIN` to give it a name.

```
: DO-SEQ ( --- )
  ARGC @ 3 < IF S" usage: seq FIRST LAST" ERR-TYPE ERR-NL 2 LAST-STATUS ! EXIT THEN
  2 ARGV@ SEQ-NUM 1+  1 ARGV@ SEQ-NUM
  2DUP > IF ?DO I N>STR DUP CSTRLEN TYPE CR LOOP ELSE 2DROP THEN
  0 LAST-STATUS ! ;
' DO-SEQ S" seq" BUILTIN
``` A Forth error in such code fails that one command, as any builtin's failure does: `$?` is 1, the message goes to standard error, the shell goes on—and so do a division by zero and an address outside the shell's memory, which the engine turns from the CPU's trap into a Forth THROW. What no check can see still does harm: a store into the shell's own memory can bring it down, as a faulty loadable builtin can bring down bash.

## Who it is for

Beyond people who like Forth, I see three uses. Minimal environments: on x86-64, a static shell without libc, as small as a static dash but extensible in place, could serve in an initramfs—beside the tools busybox would otherwise bring—or in a container with no base image. Scripts that lack data structures: what is missing can be written in Forth as builtins and called without starting a process. And teaching: on x86-64 the whole stack, from the assembler to the shell, is written in Forth and reproduces itself.

## What it is

    ./relfshasm64 - one static file, 137,612 bytes
    +------------------------------------------------+
    | the shell: parser, executor, line editor       |
    |   shell.4  tree.4  edit.4          (Forth)     |
    +------------------------------------------------+
    | the Forth: kernel, compiler, extensions        |
    |   kernel.4  extend.4  ...          (Forth)     |
    +------------------------------------------------+
    | the engine: 15,592 bytes of x86-64, no libc    |
    |   or a C engine, anywhere a C compiler is      |
    +------------------------------------------------+

The shell and the Forth are one byte-coded image; an engine runs it. There are two engines and they run the same image: a portable one in C, and one written in x86-64 assembly on raw system calls. On x86-64 every suite runs on both, and their outputs must agree.

## The Forth underneath

- **Token-threaded.** 64 one-byte opcodes, and further primitives as two-byte tokens, an escape byte followed by a selector (RelF calls these "escaped primitives"). Colon definitions are called by their offset from the start of the image—the "Relative" in RelF—so an image runs wherever it is loaded. A call to a word in the image's first 16 KB takes two bytes, from anywhere; any other takes three and reaches 4 MB, which is why an image lives in a 4 MB region. The kernel is the image's first 9,824 bytes, so every call into it is two bytes.
- **One image per cell width.** 8-byte cells or 4-byte, little-endian; one image runs on every supported machine of its width.
- **It compiles itself.** `cross.4`, running on the previous kernel image, compiles `kernel.4` into the next one—and it comes out byte for byte the same. gforth 0.7.3, running the same cross-compiler, produces the same bytes too. That is a check in the spirit of [diverse double-compiling](https://arxiv.org/abs/1004.5534), David A. Wheeler's defence against the attack Ken Thompson described in "Reflections on Trusting Trust".
- **What it claims.** It passes the CORE tests—John Hayes' suite ([tests/tester.fr](https://github.com/kt97679/relf/blob/master/tests/tester.fr)), with additions from the Forth 2012 test suite: 2,136 checks—on both engines and both cell widths. Beyond CORE it has what the shell needed; it does not claim the other word sets, and the missing words can be defined with the `forth` builtin.

## Assembling its own engine

    engine/cv8.c --cc--> relf64 (the C engine, once)
                            |
    kernel.4 + cross.4 -----+--> kernel64.img  (reproduces)
                            |
    relfasm64.4 + asm64.4 --+--> relfasm64     (15,592 bytes)
                                |
    relfasm64.4, again ---------+--> relfasm64 (the same bytes)

The x86-64 engine is written in Forth, [`engine/relfasm64.4`](https://github.com/kt97679/relf/blob/master/engine/relfasm64.4), with an x86-64 assembler written in Forth, [`forth/asm64.4`](https://github.com/kt97679/relf/blob/master/forth/asm64.4), in postfix syntax:

    rax [ rbx 8 ] mov,       \ mov rax, [rbx+8]
    r12 [ r13 ] mov,         \ mov r12, [r13]

The C engine, built once, runs the assembler; the engine that comes out assembles itself again, to the same 15,592 bytes. The assembler is held to GNU as's bytes on the 456 instruction shapes the engine uses, and, on random instructions of every form it offers, to the same bytes or an equivalent encoding.

The random check found a bug on its first run: `push`, `pop` and `xchg` with a memory operand had been assembled as register instructions—silently. Fixed; the random check now runs with every verification. The nearest prior art I know is Lars Brinkhoff's [lbForth](https://github.com/larsbrinkhoff/lbForth), a self-hosting metacompiled Forth bootstrapped from a few lines of C.

## Numbers

Memory at rest, measured with [tools/mem-profile.py](https://github.com/kt97679/relf/blob/master/tools/mem-profile.py) (kB):

                       resident    private
    relfsh, asm engine      196        196
    relfsh, C engine      1,940        384
    dash                  1,968        100
    busybox ash           1,608        252
    bash                  3,704      1,740

Each shell reads its own /proc/PID/smaps: resident is the sum of Rss, which also counts pages shared with other processes, chiefly the C library; private is the sum of Private_Clean and Private_Dirty. By resident memory, relfsh on its own engine is the smallest by far—it maps no C library. Counting only private memory, dash uses half of relfsh's.

Speed, honestly. The shell first: CPU time (user+sys) as a ratio to dash, the median of the ratios over ten rounds in which every shell ran every workload ([tools/bench-vm.py](https://github.com/kt97679/relf/blob/master/tools/bench-vm.py)). The first row is dash's own time.

| CPU time relative to dash | loop | fn | str | arith | realistic | start |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dash, in ms | 4.1 | 2.6 | 2.8 | 3.0 | 3.4 | 1.4 |
| busybox ash | 1.1× | 1.2× | 1.1× | 1.3× | 1.3× | 0.93× |
| bash | 2.1× | 2.4× | 2.2× | 2.4× | 2.8× | 1.3× |
| relfsh, asm engine | 25× | 22× | 20× | 27× | 27× | 0.56× |
| relfsh, C engine | 26× | 23× | 21× | 28× | 28× | 1.1× |

The workloads: loop is 2,000 rounds of test and increment; fn, 600 function calls; str, 400 rounds of `${s##*/}`, `${s%/*}` and `case`; arith, 700 steps of a modular Fibonacci; realistic, option parsing, trims, `case`, arithmetic and `set --`, 300 rounds; start, one `sh -c true`. relfsh starts in just over half of dash's time, but runs scripts 20 to 28 times slower—it is a bytecode interpreter, and dash is C.

Then RelF as a Forth: seven small programs, the same Forth text for all three Forths, the same algorithms in C, Go, Python and Ruby ([bench/langs/run.py](https://github.com/kt97679/relf/blob/master/bench/langs/run.py)). Milliseconds, best of three, the process's start included; every result checked against C's. The last column is the geometric mean of the ratios to RelF.

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

RelF is 2.0 to 2.4 times faster than pforth, Python and Ruby, 1.5 to 1.7 times slower than gforth, and 11 to 14 times slower than C and Go; its weakest case is byte memory, the sieve. Seven small programs are not a ranking of languages: they show what this VM costs, and where. Both tables were measured on September 27, 2026, on one core of an Intel Xeon at 2.1 GHz.

## How it is tested

- CORE: 2,136 checks, the same output from both engines.
- The shell:
  - 1,042 assertions in 91 files;
  - 132 cases compared with bash;
  - 421 constructs in every context, against bash and dash;
  - 48 POSIX cases, scored only where every reference shell agrees;
  - the test suite of [mrsh](https://github.com/emersion/mrsh), another small POSIX shell;
  - 44 sessions through a pseudo-terminal, for the line editor and job control;
  - the POSIX standard's own examples, 64 of them, with the results its text states.
- Beyond the suites:
  - seven shells voting on 131 scripts—relfsh is with every strong majority;
  - 1,000 random programs from a grammar-based generator, [tools/shfuzz.py](https://github.com/kt97679/relf/blob/master/tools/shfuzz.py): where dash and bash agree—827 of them; the other 173 are set aside—relfsh agrees with them too, and with yash in relfsh's place the same generator finds 9 differences in 150 programs, legitimate ones (yash's `echo` and arithmetic), so it can find them;
  - the 131 comparison scripts, each rewritten in up to nine ways that must not change its output (1,170 variants);
  - mutation testing on the compiled image;
  - the test harness run by relfsh itself;
  - signal storms, where each trap ran once for every signal sent;
  - real scripts: zlib's configure runs as it does under dash, and ncurses's—32,301 lines of Autoconf—writes 1,041 files, 1,040 of them identical to dash's; in the last one, config.status, only the two lines differ where Autoconf recorded how each shell's `echo` omits a newline.
- Every change is verified on three machines—two x86-64 and an ARMv7 board—before it goes in.

## What it is not

- A certified POSIX shell: its conformance is what the tests above show, no more.
- A complete Forth 2012 system: it is CORE, and what the shell needs.
- Floating point: `printf '%.2f'` is refused, as POSIX allows—printf may leave the floating conversions out.
- Fast at scripts: see above.
- Everywhere native: the assembly engine is x86-64 only. The C engine runs on x86-64, i386 and ARMv7, and under qemu on AArch64 and RISC-V.
- Localised: no locales, and the shell keeps its time in UTC wherever it runs.

## How it was built

Since the end of August 2026, almost all of the code, tests and documents—some 650 commits—have been written by Claude, an AI model, in several hundred numbered iterations under my direction. I set the goals, made the decisions—thirty-two of them recorded in [docs/QUESTIONS.md](https://github.com/kt97679/relf/blob/master/docs/QUESTIONS.md)—and ran every change on my own machines before it went in. A model makes mistakes like anyone else, which is why the project leans so hard on tests: they are what caught the `push`, `pop` and `xchg` bug in the assembler described above. The log of every iteration, mistakes included, is [docs/PROGRESS.md](https://github.com/kt97679/relf/blob/master/docs/PROGRESS.md).

## Try it

    git clone https://github.com/kt97679/relf
    cd relf
    make relfshasm64 && ./relfshasm64   # x86-64 Linux, static
    make relfsh && ./relfsh             # other CPUs: the C engine

`make test` runs every suite. Like a plain `make`, it also builds the 4-byte-cell engine, which on 64-bit Debian or Ubuntu needs gcc-multilib. The [README](https://github.com/kt97679/relf/blob/master/README.md) has the full build details.

GPL version 2. Questions I would like answered by people who know Forth better than I do: RelF's 64 one-byte opcodes were chosen by how often they execute on real workloads—the practice of Gforth, and of Proebsting's superoperators—so is there a better criterion for a shell, whose time goes to processes and system calls as much as to Forth? And what would you build with a shell you can extend in Forth?
