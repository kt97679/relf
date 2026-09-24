# RelF — a self-hosting Forth, and a POSIX shell written in it

RelF, Relative Forth, is Kirill Timofeev's Forth system, derived from
L.C. Benschop's SOD32. This repository refactors it towards full
self-hosting (GOALS.md). What it is today:

- **An engine**, `cv8.c`: a small virtual machine in portable C that
  runs a byte-coded Forth image (CV8.md). 39 KB stripped on x86-64.
- **A Forth system that compiles itself**: `cross.4`, running on
  `kernel64.img`, compiles `kernel.4` into a new `kernel64.img`, byte for
  byte - no other language involved beyond the engine's C.
- **A POSIX shell written in that Forth** - `shell.4`, `tree.4` and
  `edit.4` - with job control, a line editor with history, and `$'...'`
  and `set -o pipefail` from POSIX.1-2024. On yash's and busybox's test
  suites it passes more cases than dash does (DASH.md), and `forth`
  drops from it into the live system it is written in.

## Quick start

    make                          # both engines, both shell images
    ./relfsh -c 'echo hello'      # run one command
    ./relfsh                      # interactive
    ./relfsh script.sh            # run a script
    ./relf64 kernel64.img           # the bare Forth system; BYE leaves

`relfsh` is one executable: the engine with the shell image appended
to it, which the engine finds in itself at startup. `make` builds it,
and rebuilds it when a source changes. Everything is named by cell
width: the engines `relf64` and `relf32`, which run an image file given
as their first argument (the kernels are bootstrapped with them); the
kernels `kernel64.img` and `kernel32.img`; the shells `relfsh64` and
`relfsh32`; and `relfsh`, a link to the one native to this machine. `make verify` runs every suite; `make help` lists
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
not in POSIX mode.

**What is committed, and what is built.** The sources, and the two
kernel images, `kernel64.img` (8-byte cells) and `kernel32.img` (4-byte):
they are the bootstrap seed, since only an image can cross-compile an
image. The engines (`relf`, `relf32`) and the shell images are build
products, ignored by git. `make` does not rebuild the kernel images:
`make images IMAGES_FORCE=1` does, deliberately, for a change to the
engine's primitives or to `kernel.4`, and `make check-images` then
confirms they reproduce themselves.

**Other architectures.** Use that architecture's C compiler; nothing
else changes. The engine's cell width is the process's pointer width,
so a 32-bit host builds the 4-byte engine and runs `kernel32.img`. One
image serves every machine of the same cell width - images are
little-endian, and position-independent. Checked on x86-64, i386, ARMv7
(an NVIDIA Tegra, natively) and, under qemu, AArch64 and RISC-V.

**Locale.** The shell has none: character classes, ranges and the order
of pathname expansion are byte-based, as in the C locale. The test
suites pin `LC_ALL=C` for that reason.

## The repository

| file | what it is |
|---|---|
| `cv8.c` | the engine |
| `kernel.4` | the Forth kernel, and the run-time compiler |
| `cross.4` | the cross-compiler that builds `kernel64.img` |
| `extend.4`, `pool.4`, `shadow.4`, `save-system.4` | extensions: search order, heap buffers, locals, saving an image |
| `shell.4`, `tree.4`, `edit.4` | the shell: commands and expansion, the parser and executor, the line editor |
| `tests/`, `tools/` | the suites; the tools that build the shell, measure and fuzz |
| `forth-shell-examples/` | the shell extended from inside, with `forth`: new builtins, a prompt hook, network servers |
| `prompts/` | reusable prompts for this kind of work; `prompts/INDEX.md` dispatches |

## The documents

Each covers one topic; where one needs another, it says which.

| file | topic |
|---|---|
| `README.md` | what this is, how to build and run it |
| `GOALS.md` | the direction: what is open, what was decided and why, what was tried and rejected, the conventions |
| `PROGRESS.md` | the log, one entry per iteration, oldest first - read it through its Index |
| `CHECKING.md` | what to run after pulling, what each suite is for, and what its failures mean |
| `CV8.md` | the engine and its image format: the reference, and the reasons |
| `DASH.md` | this shell against dash, how dash runs a script, and what was taken from it |
| `PERFORMANCE.md` | where the shell's time goes, and the standing questions about the machine |
| `INTERACTIVE.md` | the interactive shell, its line editor, and how it is tested through a pty |
| `FORTH-STYLE.md` | how to write Forth here, each rule with the incident behind it |
| `EXPANSION-ORDER.md` | the order of a simple command's expansions: the design, and where it stopped |
| `SHELL-LANGUAGE.md` | a shell language of our own: where the POSIX one's cost lives, and the design |
| `tests/from-others/CATALOGUE.md` | behaviours learned from other shells' test suites |

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
