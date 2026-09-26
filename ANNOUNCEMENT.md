# ANNOUNCEMENT.md - facts for the announcement article

The user's plan (Iteration 549): an announcement article for ForthHub
and Habr once the project settles down. This file keeps the facts it
will need - each with where it was measured and how to measure it again
- and the caveats that keep it honest. Kept current: whenever a headline
number changes, it changes here. The fuller record is PROGRESS.md (the
log), FINDINGS.md (measurements), OPTIMIZATIONS.md (what was tried).

**Re-measure every number before publishing**; the commands are below.
All measurements so far: one x86-64 machine (a container), nothing else
running, best of three unless said; plus the user's ARM board and a
second x86-64 machine for correctness runs.

## What relf is, in one paragraph

A Forth system and a POSIX shell written in it. A small engine - in C,
or in x86-64 assembly with no C library - runs a byte-token-threaded
image; the kernel image is cross-compiled from Forth source by Forth,
and the shell is Forth code on top. Since Iteration 548 relf assembles
its own assembly engine from Forth source, byte for byte what GNU as and
ld make, and that engine rebuilds itself.

## Headline facts

**Self-hosting** (548-549; SELF-HOSTING.md). relf assembles its x86-64
engine from its Forth source (relfasm64.4, via asm64.4, a 351-line
x86-64 assembler in Forth). Proven byte-identical to GNU as + ld
building the former assembly source - 15,176 bytes - and that engine,
run on the same program, writes itself again, identical: a fixpoint.
**Since 549 the engine's only source is Forth**: `make relfasm64` is
relf running on the C engine; no assembler or linker is involved.
`make verify` checks the fixpoint on every run (asm:fixpoint).

**Another Forth builds the same kernel** (542). gforth 0.7.3, running
relf's cross-compiler (cross.4) unmodified, produces relf's kernel
images - 64-bit and 32-bit - byte for byte: a diverse double-compile.
`make verify` row ddc:gforth.

**Sizes** (549):

| artefact | bytes | note |
|---|---:|---|
| assembly engine (relfasm64) | 15,176 | static, no C library, x86-64 |
| C engine (relf64), stripped | 39,136 | dynamically linked with libc |
| kernel image, 64-bit cells | 9,359 | the Forth kernel |
| kernel image, 32-bit cells | 8,871 | same source |
| shell image, 64-bit | 118,580 | kernel + extensions + the shell |
| **the whole shell, one file** (relfshasm64) | **133,772** | engine + image, static |

**Source** (549, lines): kernel.4 1,853; the shell 13,300 (shell.4
8,199, tree.4 3,991, edit.4 708, pool.4 193, shadow.4 292); cross.4
699; extend.4 158; save-system.4 211; C engine cv8.c 1,710; assembly
engine 2,416 (relfasm64.4, in Forth; comments included); the assembler
asm64.4 351. About 20,800 in all.

**Speed against other languages and Forths** (543; FINDINGS.md 1.1;
`python3 bench/langs/run.py`). Seven small programs, one Forth text for
every Forth, checksums checked against C's; ms, best of three, process
start included:

| | fib(32) | loop 30M | sieve 5M | bubble 3000 | matrix 150 | fannkuch 9 | collatz 1e5 | geo. mean vs relf |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C (gcc -O2) | 4 | 10 | 23 | 19 | 3 | 33 | 19 | 0.08x |
| Go 1.22 | 13 | 22 | 27 | 7 | 5 | 21 | 24 | 0.09x |
| **relf, assembly engine** | **55** | **92** | **421** | **84** | **130** | **362** | **231** | **1.00x** |
| relf, C engine | 58 | 90 | 490 | 103 | 137 | 330 | 218 | 1.04x |
| gforth-fast 0.7.3 | 59 | 87 | 106 | 72 | 78 | 234 | 146 | 0.66x |
| gforth 0.7.3 | 61 | 77 | 129 | 93 | 82 | 338 | 152 | 0.74x |
| pforth 2.0.1 | 150 | 173 | 393 | 279 | 353 | 1,114 | 419 | 2.19x |
| Ruby 3.2 | 228 | 615 | 430 | 364 | 181 | 855 | 427 | 2.57x |
| Python 3.12 | 208 | 844 | 445 | 260 | 163 | 445 | 515 | 2.34x |

relf: in gforth's class (faster on calls, level on the loop, 1.35-1.5x
behind over all); 2.2-2.6x faster than pforth, Ruby and Python; ~12x
slower than C and Go. Why gforth is ahead - not native code, but which
words are primitives - is FINDINGS.md 1.1a.

**The shell against dash and bash** (534; FINDINGS.md 1.2). The same
script, identical output: dash 2.5 ms, bash 7.6 ms, relf 75.7 ms
(assembly engine). **Startup the other way round: relf 287 us, dash 748,
bash 1,108.** Scripts are relf's weak side (~30x dash): the shell's work
is fine-grained Forth; accepted for simplicity (QUESTIONS.md A13).

**Memory** (545; FINDINGS.md 8; `python3 tools/mem-profile.py`), kB,
idle -> after a workload:

| shell | resident | private |
|---|---|---|
| **relf, assembly engine** | **308 -> 356** | **308 -> 356** |
| dash | 1,968 -> 1,984 | 100 -> 116 |
| busybox ash | 1,604 -> 1,808 | 248 -> 388 |
| bash | 3,612 -> 3,644 | 1,648 -> 1,692 |

Smallest resident footprint (no C library); in private memory ~3x dash,
near ash, a fifth of bash. Minimizing it is planned (GOALS.md, A18).

**Correctness, checked on every `make verify`** (BASELINE): the CORE
test suite, 2,136 checks, output identical on both engines; a
differential suite of 131 cases; 421 cases in a matrix against bash and
dash as references; 48 POSIX cases; 21 from the mrsh suite; 23 through
a pseudo-terminal (line editor, job control); 83 shell test files, 874
assertions; reproducible images, both cell widths, rebuilt and compared
byte for byte - about seventy rows in all.

**Platforms**: x86-64 (C and assembly engines), i386 (32-bit cells, C),
ARMv7 (an NVIDIA Tegra board running Gentoo; C engine, 32-bit cells) -
one Forth source for 64- and 32-bit images.

**The engine's design, briefly**: byte-token threading (CV8 format, 10
versions); 64 one-byte opcodes and 74 escaped primitives; calls of 2 or
3 bytes to a 4 MB region, which is the whole dictionary (A17); images
position-independent; the dispatch loop at the CPU's indirect-jump rate
(0.8 ns, FINDINGS.md 1.3).

**The process**: 549 iterations, each logged in PROGRESS.md with the
number that decided it; every change checked against a recorded
baseline before it is committed; the measured and the rejected kept
(FINDINGS.md, OPTIMIZATIONS.md, GOALS.md's "Tried and rejected").

## Milestones (the recent ones; PROGRESS.md for all)

- 506: the shell as one executable (engine + image appended).
- 523: the assembly engine complete - no libc, 134 KB shell in one file.
- 528-539: opcodes measured; runtime words kept; superinstructions and
  folded returns removed for simplicity; 64 one-byte opcodes.
- 542: gforth builds relf's kernels byte for byte.
- 544: UTC everywhere; verification in a non-UTC zone.
- 545: the dictionary checked (4 MB, the call reach).
- 548: **self-hosted** - relf assembles its own engine, identical to GNU
  as's, and the engine rebuilds itself.
- 549: the engine's only source is Forth; GNU as leaves the build.

## How to re-measure

    make verify                          # every correctness row, ~15 min
    python3 bench/langs/run.py           # speed against languages, Forths
    python3 tools/mem-profile.py         # memory against dash, ash, bash
    python3 tools/asm-test.py            # the assembler against GNU as
    python3 tools/bench-vm.py 10 CONFIG  # the shell's own benchmarks

Needs: gcc, Go, Python 3, Ruby, gforth, pforth, dash, bash, busybox.

## Caveats to state in the article

- One machine for speed and memory; say which, and re-measure there.
- gforth 0.7.3 is from 2008; newer gforth is faster - compare with it.
- "relf beats Python and Ruby" is on these seven small programs; the
  shell's scripts, by contrast, are ~30x slower than dash.
- Resident memory counts shared C-library pages in every process; the
  private column is the fair one per process.
- The self-hosting claim is for the x86-64 assembly engine; the C engine
  (for other platforms, and the bootstrap) is built by a C compiler.
