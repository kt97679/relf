# RelF — a self-hosting Forth, and a POSIX shell written in it

RelF, Relative Forth, is Kirill Timofeev's Forth system, derived from
L.C. Benschop's SOD32. This repository refactors it towards full
self-hosting (docs/GOALS.md). What it is today:

- **Two engines** that run the same byte-coded Forth image: `cv8.c`, a
  small virtual machine in portable C (33 KB on x86-64, static, with no
  C library: `engine/rt-linux.c`), and
  `relfasm64`, 18,512 bytes of x86-64 on raw system calls, no libc -
  **assembled by relf itself**, from `engine/relfasm64.4`, with an
  assembler written in Forth (`forth/asm64.4`). It reproduces itself,
  and from it alone - no compiler, assembler or linker, POSIX utilities
  on the PATH - relf rebuilds the engine, both kernels, the shell's and
  rill3's images and the shell, each byte for byte; relfsh can run that
  build itself (`make selfhost`).
- **A Forth system that compiles itself**: `cross.4`, running on
  `kernel64.img`, compiles `kernel.4` into a new `kernel64.img`, byte for
  byte. gforth builds the same bytes from the same source.
- **A POSIX shell written in that Forth** - `shell.4`, `tree.4` and
  `edit.4` - with job control, a line editor with history, and `$'...'`
  and `set -o pipefail` from POSIX.1-2024. On yash's and busybox's test
  suites it passes more cases than dash does (docs/DASH.md). The whole
  shell is one static file of 137,643 bytes on the assembly engine, and
  `forth` drops from it into the live system it is written in: every
  word, compiler included, is there to extend it.
- **A native back end** (docs/NATIVE.md): the same Forth compiled to
  x86-64 code rather than bytecode. `make relfsh-native` builds the
  shell that way, one static file of 409,184 bytes compiled to x86-64,
  which does the shell's own work about nine times as fast as on the
  bytecode engines.
- **A shell language of its own, rill3** (the command model; docs/TUTORIAL.md, then docs/REFERENCE.md) - `bin/cm script.cm`,
  or its prompt (`make rill3-native` builds it as one native x86-64 file): commands whose arguments and pipes carry values (texts,
  numbers, lists, maps, blocks) as well as bytes, words read as Forth reads
  them. docs/REFERENCE.md is the language; `sh tests/cm/run` its suite.

The Forth passes the CORE tests (John Hayes' core.fr, as adapted in
tests/tester.fr) on both engines and both cell widths; beyond CORE it
has what the shell needed, not every standard word set (docs/QUESTIONS.md
A23).

## Quick start

    make                          # the engines, the shell images, the shells
    ./relfsh -c 'echo hello'      # run one command
    ./relfsh                      # interactive
    ./relfsh script.sh            # run a script
    ./relf64 forth/kernel64.img   # the bare Forth system; BYE leaves
    make relfshasm64              # the shell on the assembly engine (x86-64)

`relfsh` is one executable: the engine with the shell image appended
to it, which the engine finds in itself at startup. `make` builds it,
and rebuilds it when a source changes. Everything is named by cell
width: the engines `relf64` and `relf32`, which run an image file given
as their first argument (the kernels are bootstrapped with them); the
kernels `forth/kernel64.img` and `forth/kernel32.img`; the shells
`relfsh64` and `relfsh32`; and `relfsh`, a link to the one native to
this machine. `make verify` runs every suite; `make help` lists
everything else. Install it by copying the one file.

## Building

**Required**: a C compiler as `cc` (GCC or Clang), and its 32-bit
support - `gcc-multilib` on Debian and Ubuntu - because the 4-byte-cell
engine is built and tested on every change. Without it, `cc -m32` fails
and half of every check is silently skipped. **Required for the
tests**: `python3`, `bash`, `dash` and `timeout`.

**Recommended for the tests**: more reference shells - `mksh`, `yash`,
`posh`, `ksh` and `busybox-static`. The POSIX suite scores a case only
when every reference shell present agrees, so each one makes it
stricter. `zsh` is deliberately not one: run as `zsh script.sh` it is
not in POSIX mode. `gforth`, if present, builds the kernels a second
way, and the bytes must match.

**What is committed, and what is built.** The sources, and the two
kernel images, `forth/kernel64.img` (8-byte cells) and
`forth/kernel32.img` (4-byte): they are the bootstrap seed, since only
an image can cross-compile an image. The engines, the shell images and
the shells are build products, at the top of the tree and ignored by
git. `make` does not rebuild the kernel images: `make images
IMAGES_FORCE=1` does, deliberately, for a change to the engine's
primitives or to `kernel.4`, and `make check-images` then confirms they
reproduce themselves.

**Other architectures.** Use that architecture's C compiler; nothing
else changes. The engine's cell width is the process's pointer width,
so a 32-bit host builds the 4-byte engine and runs `kernel32.img`. One
image serves every machine of the same cell width - images are
little-endian, and position-independent. Checked on x86-64, i386, ARMv7
(an NVIDIA Tegra, natively) and, under qemu, AArch64 and RISC-V. The
assembly engine is x86-64 only.

**No C library.** On Linux on x86-64, i386, AArch64 and RISC-V 64 the
engine is linked with `engine/rt-linux.c`, what it needs of a C library
over raw system calls: static, about 280 KB resident at start rather than
the library's 1.9 MB, at the same speed. `make ENGINE_RT=libc` links the
library instead, and is what any other system gets. The one difference:
`~name` comes from `/etc/passwd` alone, not through NSS.

**Time.** The shell keeps time in UTC everywhere (docs/QUESTIONS.md A16),
and has no locale: character classes, ranges and the order of pathname
expansion are byte-based, as in the C locale.

## The repository

    engine/     the engines
      cv8.c             the C engine
      rt-linux.c        what it needs of a C library, on raw system calls
      relfasm64.4       the x86-64 engine, as Forth source relf assembles
      engine-macros.4   its macros
      opcodes.tab       the opcode map's one source: the engines' tables
                        are generated from it, the Forth checked against it
    forth/      the Forth system
      kernel.4          the kernel, and the run-time compiler
      cross.4           the cross-compiler that builds the kernel images
      kernel64.img      the bootstrap seeds, 8- and 4-byte cells
      kernel32.img
      extend.4          the search order, and other extensions
      pool.4, shadow.4  heap buffers; locals
      save-system.4     saving an image
      asm64.4           an x86-64 assembler, in Forth
      safety.4          the shell's guards: stack traps, include depth
      native*.4         the native back end: Forth to x86-64 code
    shell/      the shell
      shell.4           commands, expansion, builtins
      tree.4            the parser and the executor
      edit.4            the line editor
    tests/      the suites; tester.fr is the CORE test harness
    tools/      building the shell, measuring, fuzzing, checking
    bench/      speed against C, Go, Python, Ruby, gforth, pforth
    examples/   the shell extended from inside, with `forth`: builtins,
                a prompt hook, network servers; fib.4
    cm/         the command model: its front end (cmc.4), runtime and prompt (docs/REFERENCE.md)
    rill/       rt.4, the runtime the command model is built on
    lib/        rill3's script library (args.cm, json.cm)
    bin/        cm, which runs a rill3 script or its prompt
    port/       relfsh on Forths that are not relf (gforth, the lab's
                designs), and the measurements made with them
    docs/       every document but this one
    prompts/    reusable prompts for this kind of work (INDEX.md)

## The documents

Each covers one topic; where one needs another, it says which. All but
this README are in `docs/`.

| file | topic |
|---|---|
| `GOALS.md` | the direction: what is open, what was decided and why, what was tried and rejected, the conventions |
| `PROGRESS.md` | the log's entry point: how it is kept, its Index, and its volumes - `docs/progress/`, a hundred iterations each, oldest first; read an entry through the Index |
| `asks/` | prompts for other models, one per question (prompts/28), and what came back, checked |
| `REFERENCE.md` | the command model's language, for writing scripts: words, values, control, captures, pipes, every builtin - each example run by its suite |
| `COMMAND-MODEL.md` | how that language came to be (850-): the idea, its rules, what each iteration changed and why |
| `QUESTIONS.md` | every question waiting on the user, with options and a recommendation; answered ones kept |
| `CHECKING.md` | what to run after pulling, what each suite is for, and what its failures mean |
| `CV8.md` | the engine and its image format: the reference, and the reasons |
| `ASM-ENGINE.md` | the x86-64 engine on raw syscalls |
| `CV8-LEDGER.md` | what each change to CV8 gained and what it cost, measured |
| `NATIVE.md` | the native back end: Forth compiled to x86-64, the native shell, and the hybrid tried and stopped (18) |
| `SELF-HOSTING.md` | how relf came to assemble its own engine: the plan, milestones M0-M5 |
| `DASH.md` | this shell against dash, how dash runs a script, and what was taken from it |
| `PERFORMANCE.md` | where the shell's time goes, and the standing questions about the machine |
| `FINDINGS.md` | measured results, kept for later |
| `OPTIMIZATIONS.md` | optimizations considered: done, declined, open |
| `INTERACTIVE.md` | the interactive shell, its line editor, and how it is tested through a pty |
| `FORTH-STYLE.md` | how to write Forth here, each rule with the incident behind it |
| `EXPANSION-ORDER.md` | the order of a simple command's expansions: the design, and where it stopped |
| `SHELL-LANGUAGE.md` | a shell language of our own: where the POSIX one's cost lives, and the design |
| `TESTING-IDEAS.md` | kinds of tests beyond the present suites |
| `ANNOUNCEMENT.md` | the facts for an announcement, and research on its audience |
| `ARTICLE-forthhub.md`, `ARTICLE-habr.md` | the two published articles, in English and Russian |
| `RELFSH-MEMORY.md` | whether relfsh gives back the memory it no longer needs, measured |
| `TUTORIAL.md` | rill3 in an hour, for a first script |
| `BYTECODE.md` | rill3 compiled to bytecode directly (923-926) |
| `SIMILAR-PROJECTS.md` | projects like kbool, and what rill3 may take from them |
| `SYNTAX-STUDY.md`, `SYNTAX-GENES.md` | how rill3's syntax was chosen: a study, and syntax as genes searched |
| `FORTH-SCRIPTING.md`, `PILOT-NATIVE-BY-SOURCE.md` | records of the languages before rill3 (Rill, Rill 2, retired at 871); the files they name are in git's history |

`tests/from-others/CATALOGUE.md` lists behaviours learned from other
shells' test suites.

## Where it came from

From the original README, by Kirill Timofeev (2013):

> The idea of RelF came to me after looking at SOD32 by L.C. Benschop.
> SOD32 is a very interesting project with separated engine and
> machine-independent forth-system binary image. But SOD32 is pretty
> slow due to many reasons. I became interested in speeding up SOD32.
> At least to some extent I succeeded. [...] The main [change] was
> organization of threaded code: reference to high-level definition
> contains now not address of this definition, but relative offset
> (thus the name - Relative Forth).

The engine has since changed completely - CV8.md tells how - but that
idea, a relative offset where other systems keep an address, is still
the one it is built on. Upstream is https://github.com/kt97679/relf.

## Licence

GPLv2 only, as the RelF and SOD32 sources it derives from are
("version 2", with no "or any later version"). Relicensing would need
the permission of Kirill Timofeev and L.C. Benschop.
