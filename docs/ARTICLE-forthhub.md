# relfsh: a POSIX shell written in Forth, on a Forth that assembles its own engine

relfsh is a POSIX shell written in Forth: on x86-64, one static file of 141,212 bytes that takes about 210 kB of memory at rest, and that you can extend from the inside, in Forth, while it runs. Underneath is a small Forth that compiles itself, and whose x86-64 engine is assembled from Forth source by an assembler written in Forth.

## Why

I have long been a fan of Forth. What fascinates me most is that one person can bring up a working Forth on a new platform in a few days—the whole system, compiler included, small enough for one mind to hold.

In the 1990s I came across [SOD32](https://github.com/lennart-benschop/sod32), [Lennart Benschop](https://github.com/lennart-benschop)'s Forth: a small virtual machine running a machine-independent image. I found it beautiful. It had two weaknesses—the limits built into its design, and its speed—and RelF, Relative Forth, began as my attempt to fix them. It worked, but the gain in speed was modest, and after a while I put it aside.

Meanwhile another thought kept coming back: the shell is an underrated tool. Most of the glue in our systems—the code that connects programs, files and processes—is exactly what the shell is good at. Written in Python instead, glue grows longer, and every extra line is another place for a mistake. But the POSIX shell has two weaknesses of its own: it can be extended only with external programs—bash, ksh93 and zsh can load builtins, but written in C against their own headers—and it offers almost nothing in the way of data structures.

That is where the two ideas met. A shell written in Forth could be small and frugal, because Forth is; and it could be extended from inside, in Forth itself, given the right builtin.

## The shell

A POSIX sh: pipelines, lists, compound commands, functions, here-documents, every expansion, job control, a line editor with history, search and completion, `$'...'` and `set -o pipefail` from POSIX.1-2024. And the `forth` builtin, which reaches the whole Forth system the shell is written in:

```
$ ./relfshasm64
$ forth '2 3 + . CR'
5
$ forth 'S" examples/seq.4" INCLUDED'
$ type seq
seq is a shell builtin
$ seq 1 3 | while read n; do echo "line $n"; done
line 1
line 2
line 3
```

`seq` there is a new builtin: eight lines of Forth in `examples/seq.4`, not part of the binary, loaded while the shell runs. The [examples directory](https://github.com/kt97679/relf/tree/article-2026/examples) also has a prompt hook, a TCP echo server and an HTTP server, all in Forth, inside the shell. Put the `forth` line, with the full path to `seq.4`, in the file `$ENV` names, and the builtin is there every time an interactive shell starts.

Here is `seq` itself, less the two lines of `SEQ-NUM` that read a decimal number: the whole interface a builtin has—its arguments through `ARGC` and `ARGV@`, its status through `LAST-STATUS`, and `BUILTIN` to give it a name.

```
: DO-SEQ ( --- )
  ARGC @ 3 < IF S" usage: seq FIRST LAST" ERR-TYPE ERR-NL 2 LAST-STATUS ! EXIT THEN
  2 ARGV@ SEQ-NUM 1+  1 ARGV@ SEQ-NUM
  2DUP > IF ?DO I N>STR DUP CSTRLEN TYPE CR LOOP ELSE 2DROP THEN
  0 LAST-STATUS ! ;
' DO-SEQ S" seq" BUILTIN
```

Errors the Forth system itself detects fail only that command, as a regular builtin's failure does: `$?` is 1, the message goes to standard error, and the shell goes on. They are an undefined word or a THROW; cells left over or missing on the stack, which the shell puts back; a stack overflow, a runaway recursion say; a division by zero or an address outside the shell's memory, which the engine turns from the CPU's trap into a Forth THROW; and a file that fails to include. But there is no isolation: anything else a Forth word does happens inside the shell, and a store in the wrong place in its memory can bring it down, as a faulty loadable builtin can bring down bash.

## Who it is for

Beyond people who like Forth, I see three uses. Minimal environments: on x86-64, a static shell without libc, near a static dash in memory but extensible in place, could serve in an initramfs—the utilities would still have to come from somewhere, busybox for one—or in a container with no base image. Scripts that lack data structures: what is missing can be written in Forth as builtins and called without starting a process—[examples/map.4](https://github.com/kt97679/relf/blob/article-2026/examples/map.4) is an associative array, `map set KEY VALUE`, `map get KEY` and `map keys`, in 33 lines of Forth, not counting comments. And teaching: on x86-64 the whole chain, from the assembler to the shell, is written in Forth and reproduces itself.

## What it is

```
./relfshasm64 - one static file, 141,212 bytes
+------------------------------------------------+
| the shell: parser, executor, line editor       |
|   shell.4  tree.4  edit.4          (Forth)     |
+------------------------------------------------+
| the Forth: kernel, compiler, extensions        |
|   kernel.4  extend.4  ...          (Forth)     |
+------------------------------------------------+
| the engine: 15,760 bytes of x86-64, no libc    |
|   or a C engine, anywhere a C compiler is      |
+------------------------------------------------+
```

The shell and the Forth are one byte-coded image; an engine runs it. There are two engines and they run the same image: a portable one in C, and one written in x86-64 assembly on raw system calls. On x86-64 both pass the same CORE tests, with byte-identical output, the shell suite, the comparison with bash and the pseudo-terminal sessions, and the images they build are the same.

## The Forth underneath

- **Token-threaded.** 64 one-byte opcodes, and further primitives as two-byte tokens, an escape byte followed by a selector. Colon definitions are called by their offset from the start of the image—the "Relative" in RelF—so an image runs wherever it is loaded. A call to a word in the image's first 16 KB takes two bytes, from anywhere; any other takes three and reaches 4 MB, which is why an image lives in a 4 MB region. The kernel is the image's first 9,544 bytes, so every call into it is two bytes.
- **One image per cell width.** 8-byte cells or 4-byte, little-endian; one image runs on every supported machine of its width.
- **It compiles itself.** `cross.4`, running on the previous kernel image, compiles `kernel.4` into the next one—and it comes out byte for byte the same. Self-compilation alone guarantees little, though. In "Reflections on Trusting Trust", Ken Thompson showed that a compiler can be taught to plant a backdoor in the programs it compiles, new versions of itself included; the backdoor then survives any reading of the source—the source is clean, the binary is not. The defence is [diverse double-compiling](https://arxiv.org/abs/1004.5534): compile the same source with a different, independent compiler and compare the results. David A. Wheeler formalised it; the idea goes back to Henry Spencer. Here gforth 0.7.3 plays the independent compiler: running the same cross-compiler, it produces the same bytes. So the kernel holds nothing beyond what its source says, unless gforth itself carries the same backdoor. The rest of the image and the assembly engine are built by RelF itself, and the C engine by a C compiler, so the check covers the kernel only.
- **What it claims.** It passes the CORE tests—John Hayes' suite ([tests/tester.fr](https://github.com/kt97679/relf/blob/article-2026/tests/tester.fr)), with additions from the Forth 2012 test suite: 2,136 checks—on both engines and both cell widths. Beyond CORE it has what the shell needed, and the missing words can be defined with the `forth` builtin.

## Assembling its own engine

```
engine/cv8.c --cc--> relf64 (the C engine, once)
                        |
kernel.4 + cross.4 -----+--> kernel64.img  (reproduces)
                        |
relfasm64.4 + asm64.4 --+--> relfasm64     (15,760 bytes)
                            |
relfasm64.4, again ---------+--> relfasm64 (the same bytes)
```

The x86-64 engine is written in Forth, [`engine/relfasm64.4`](https://github.com/kt97679/relf/blob/article-2026/engine/relfasm64.4), with an x86-64 assembler written in Forth, [`forth/asm64.4`](https://github.com/kt97679/relf/blob/article-2026/forth/asm64.4), in postfix syntax:

```
rax [ rbx 8 ] mov,       \ mov rax, [rbx+8]
r12 [ r13 ] mov,         \ mov r12, [r13]
```

The C engine, built once, runs the assembler; the engine that comes out assembles itself again, to the same 15,760 bytes. The assembler is held to GNU as's bytes on the 456 instruction shapes the engine uses, and, on random instructions of every form it offers, to the same bytes or an equivalent encoding. The assembler is small: it knows only what the engine needs, and refuses the rest.

The nearest prior art I know is Lars Brinkhoff's [lbForth](https://github.com/larsbrinkhoff/lbForth), a self-hosting metacompiled Forth bootstrapped from a few lines of C. SP-Forth also builds itself from its own sources, with an assembler written in Forth, but it compiles to x86 machine code, where RelF compiles to a portable bytecode with a separate engine.

## Numbers

All measured on September 28, 2026, on an AMD Ryzen 7 PRO 8840HS (Ubuntu 24.04, the powersave governor), with dash 0.5.12, bash 5.2.21 and BusyBox 1.36.1 (its static build) as Ubuntu ships them, and for comparison dash 0.5.12 built statically against musl (musl-gcc -Os -static). `sh tools/bench-report.sh` repeats it on your machine; what it needs is listed at the top of the script, and whatever is missing is skipped.

Memory at rest, in kB, measured with [tools/mem-profile.py](https://github.com/kt97679/relf/blob/article-2026/tools/mem-profile.py):

```
                       resident    private
relfsh, asm engine          212        212
dash, static (musl)         176        176
busybox ash, static         812        148
dash                       1564        120
relfsh, C engine           1564        400
bash                       2808        292
```

Each shell reads its own /proc/PID/smaps: resident is the sum of Rss, which also counts pages shared with other processes, chiefly the C library; private is the sum of Private\_Clean and Private\_Dirty. A static binary maps no C library, so relfsh on its own engine takes 7 to 13 times less resident memory than the dynamically linked dash and bash, almost 4 times less than the static busybox, and is close to a static dash, which is smaller still. Private memory is what each copy adds: there dash is the smallest, and relfsh on its own engine has almost twice as much. relfsh's file is 141,212 bytes against the static dash's 169,720, with a Forth compiler and a line editor in it.

First the shell's speed: CPU time (user+sys) as a ratio to dash, the median of the ratios over seven rounds in which every shell ran every workload ([tools/bench-vm.py](https://github.com/kt97679/relf/blob/article-2026/tools/bench-vm.py)). The workloads are sized so that dash's own start (1.7 ms) is at most a tenth of dash's time on each: loop is 50,000 rounds of test and increment; fn, 15,000 function calls; str, 10,000 rounds of `${s##*/}`, `${s%/*}` and `case`; arith, 17,500 steps of a modular Fibonacci; realistic, option parsing, trims, `case`, arithmetic and `set --`, 7,500 rounds; start, one `sh -c true`. The first row is dash's own time.

| CPU time relative to dash | loop | fn | str | arith | realistic | start |
| --- | --: | --: | --: | --: | --: | --: |
| dash, in ms | 37.5 | 18.1 | 22.0 | 23.0 | 26.9 | 1.7 |
| dash, static (musl) | 1.7× | 1.8× | 1.2× | 1.4× | 1.6× | 0.80× |
| busybox ash, static | 1.2× | 1.4× | 1.2× | 1.5× | 1.2× | 0.88× |
| bash | 2.5× | 3.6× | 2.9× | 3.2× | 4.0× | 1.2× |
| relfsh, asm engine | 31× | 37× | 29× | 41× | 40× | 0.98× |
| relfsh, C engine | 32× | 39× | 30× | 41× | 42× | 1.2× |

relfsh runs scripts 29 to 42 times slower than dash—relfsh is an interpreter that itself runs on a bytecode VM, and dash is an interpreter in C—and starts in about the same time. A static dash starts faster still, but runs scripts slower than the usual one: it is built with -Os and musl, and it is here for memory and start. The assembly engine is barely faster at scripts than the C one, by 0 to 5%: both are held to the rate at which the CPU takes one indirect jump after another, and the point of the assembly engine is having no C library. On the Forth programs below the difference is larger, about 15%, though matrix and fannkuch run faster on the C engine.

Then RelF as a Forth: seven small programs, the same Forth text for all three Forths, the same algorithms in C, Go, Python and Ruby ([bench/langs/run.py](https://github.com/kt97679/relf/blob/article-2026/bench/langs/run.py)). Milliseconds, best of three, the process's start included; every result checked against C's. The last column is the geometric mean of the ratios to RelF, from the unrounded times.

| ms | fib | loop | sieve | bubble | matrix | fannkuch | collatz | vs RelF |
| --- | --: | --: | --: | --: | --: | --: | --: | --: |
| C (gcc -O2) | 4 | 8 | 11 | 15 | 2 | 15 | 9 | 0.06 |
| Go 1.22.1 | 10 | 7 | 11 | 4 | 3 | 13 | 13 | 0.06 |
| gforth-fast 0.7.3 | 45 | 53 | 65 | 39 | 66 | 254 | 103 | 0.57 |
| gforth 0.7.3 | 79 | 63 | 82 | 70 | 74 | 409 | 161 | 0.83 |
| RelF, asm engine | 39 | 72 | 359 | 55 | 155 | 371 | 164 | 1.00 |
| RelF, C engine | 52 | 122 | 416 | 59 | 146 | 340 | 205 | 1.18 |
| pforth 2.0.0 | 99 | 99 | 273 | 195 | 233 | 754 | 284 | 1.75 |
| Ruby 3.2.3 | 182 | 347 | 314 | 264 | 146 | 654 | 370 | 2.32 |
| Python 3.12.7 | 189 | 945 | 462 | 295 | 200 | 455 | 488 | 2.98 |

gforth here is 0.7.3, as Ubuntu ships it, released in 2014. RelF's weakest case is byte memory, the sieve.

## How it is tested

- CORE: 2,136 checks, the same output from both engines.
- The shell:
  - 1,087 assertions in 91 files;
  - 132 cases compared with bash;
  - 422 cases of small constructs, each run in every context—after `;` and `&&`, inside a function, a loop, an `if`, a subshell or a command substitution, piped, redirected, in the background—and compared with bash and dash;
  - 48 POSIX cases, scored only where every reference shell agrees;
  - the test suite of [mrsh](https://github.com/emersion/mrsh), another small POSIX shell;
  - 45 sessions through a pseudo-terminal, for the line editor and job control;
  - the POSIX standard's own examples, 64 of them, with the results its text states.
- Beyond the suites:
  - 131 comparison scripts were run through seven other shells—dash, bash, yash and mksh in POSIX mode, posh, ksh93 and busybox ash: where at least five agree (112 scripts), relfsh is always with the majority; the other 19 split, over extensions, POSIX.1-2024 additions such as `$'...'`, and what the standard leaves to the implementation;
  - the same 131 scripts, each rewritten in up to nine ways that must not change its output—1,170 variants;
  - 1,000 random programs from a grammar-based generator, [tools/shfuzz.py](https://github.com/kt97679/relf/blob/article-2026/tools/shfuzz.py): on 827 of them dash and bash agree, and so does relfsh; the other 173 are set aside. That the generator can find differences shows with yash: on 150 programs it finds nine, all legitimate (yash's `echo` and arithmetic);
  - mutation testing on the compiled image: of 30 random opcode swaps, out of 3,699 sites, the tests catch 20, and the other 10 change nothing visible;
  - the project's own test scripts, every tests/shell/run-\*, run by relfsh instead of /bin/sh;
  - signal storms, a signal every 2 ms through pipelines and command substitutions: the traps ran, and every result came out exact;
  - real scripts: zlib's configure runs as it does under dash, and ncurses's—32,301 lines of Autoconf—writes 1,041 files, 1,040 of them identical to dash's; in the last one, config.status, only the two lines differ where Autoconf recorded how each shell's `echo` omits a newline.

## What it is not

- A certified POSIX shell: its conformance is what the tests above show, no more.
- A complete Forth 2012 system: it is CORE, and what the shell needs.
- Floating point: `printf '%.2f'` is refused, as POSIX allows—printf may leave the floating conversions out.
- Fast at scripts: see above.
- Everywhere native: the assembly engine is x86-64 only. The C engine runs on x86-64, i386 and ARMv7, and under qemu on AArch64 and RISC-V.
- Localised: no locales, and the shell keeps its time in UTC wherever it runs.

## How it was built

Since the end of August 2026, almost all of the code, tests and documents—some 650 commits—have been written by Claude, an AI model, in several hundred numbered iterations under my direction. I set the goals, made the decisions—thirty-two of them recorded in [docs/QUESTIONS.md](https://github.com/kt97679/relf/blob/article-2026/docs/QUESTIONS.md)—and checked every iteration: before each commit Claude ran the full check in its own x86-64 Linux environment, and then I ran it on a ThinkPad P14s Gen 5 (AMD Ryzen 7 PRO 8840HS) and on an ARMv7 board with an NVIDIA Tegra. A model makes mistakes like anyone else, which is why the project leans so hard on tests. The log of every iteration, mistakes included, is [docs/PROGRESS.md](https://github.com/kt97679/relf/blob/article-2026/docs/PROGRESS.md).

## Try it

```
git clone -b article-2026 https://github.com/kt97679/relf
cd relf
make relfshasm64 && ./relfshasm64   # x86-64 Linux, static
make relfsh && ./relfsh             # other CPUs: the C engine
```

The `article-2026` branch is the version this article describes, and it receives only fixes; `master` goes on. `make test` runs the main tests—CORE and the shell suite at both cell widths, and the comparison with bash—and `make verify` runs every suite, the assembly engine's included, and checks the results against `tests/BASELINE`. Like a plain `make`, both also build the 4-byte-cell engine, which on x86-64 Debian or Ubuntu needs gcc-multilib. The [README](https://github.com/kt97679/relf/blob/article-2026/README.md) has the full build details.

GPL version 2. Questions I would like answered by people who know Forth better than I do: RelF's 64 one-byte opcodes are single primitives, chosen by how often they execute on real workloads—the way Gforth picks its superinstructions and Proebsting his superoperators; RelF had superinstructions once and dropped them. Is there a better criterion for a shell, whose time goes to processes and system calls as much as to Forth? And what would you build with a shell you can extend in Forth?
