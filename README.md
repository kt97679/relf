This is README for the Relative Forth (RelF) version 0.2.

It is still very preliminary version, but at least it can crosscompile itself
and passes test suite by John Hayes.

1. Introduction.

The idea of RelF came to me after looking at SOD32 by L.C. Benschop. SOD32 is
a very interesting project with separated engine and machine-independent
forth-system binary image. But SOD32 is pretty slow due to many reasons. I
became interested in speeding up SOD32. At least to some extent I succeeded.
PLease note, that my primary platform was x86. I was pretty much surprised by
benchmarks results, obtained on sparc-solaris, which can be found below.
During this work a lot of changes in system design were introduced. The main
one was organization of threaded code: reference to high-level definition
contains now not address of this definition, but relative offset (thus the
name - Relative Forth).

2. Compilation.

As of phase 5 (see GOALS.md), RelF is portable C targeting every
architecture its libc supports (verified on x86-64 and ARM64 Linux so
far). The engine (relf.c) is plain libc-based C, no special flags, no
custom startup code:

cc -O2 -Wall -o relf relf.c

For a different architecture, use that architecture's C compiler (e.g.
aarch64-linux-gnu-gcc for ARM64); nothing else changes.

Cells are 8 bytes by default, matching the process's own pointer width
on every 64-bit host targeted so far (RelF's real-pointer addressing
model needs the two to match - see PROGRESS.md, Bug 2). Cell width is
parameterized (see GOALS.md, phase 6): relf.c picks 4 or 8 bytes at
compile time from the host's own UINTPTR_MAX, so building with a 32-bit
compiler (e.g. `gcc -m32`) automatically produces a 4-byte-cell engine,
matching a 32-bit host's own pointer width - no source changes needed
for the engine itself. i386 is verified working this way (full CORE
test suite passes on both cell widths from the same cross.4/kernel.4
source). ARM32 should work the same way in principle but hasn't been
verified. There is no separate relfgcc.c/vm.asm/vm_tos.asm engine any
more; relf.c is the only one.

kernel.img is native host endianness (little-endian - see GOALS.md's
non-goals) with an 8-byte magic header (cell width + a fixed tag), so a
mismatched image fails cleanly at load rather than silently
misbehaving. Any two architectures that agree on *both* cell width and
endianness can share one image unmodified - confirmed by running the
identical kernel.img, unchanged, on both x86-64 and ARM64 (both 8-byte
cells). A 4-byte-cell image (e.g. for i386) is a *different* image,
built separately - see below.

Machine-independent kernel can be compiled by RelF itself. gforth is
not currently usable as an alternative host: cross.4/extend.4/kernel.4
rely on RelF-kernel-specific search-order words (CONTEXT, #ORDER,
CURRENT) that gforth doesn't provide.

To compile kernel with RelF you need to do the following:
    a) start RelF with initial kernel: ./relf kernel.img
    b) load extensions: S" extend.4" INCLUDED
    c) load cross-compiler: S" cross.4" INCLUDED

After a couple of moments RelF would exit and you'll get new kernel.img.
Please, backup original kernel.img, since it would be overwritten during 
crosscompilation.

To cross-compile a *32-bit* (4-byte-cell) target image instead of the
8-byte-cell default, edit the "8" in cross.4's own
"VARIABLE TARGET-CELL-BYTES / 8 TARGET-CELL-BYTES !" lines (near the
top of the file) to "4", then follow the same three steps above. This
is a plain, direct source edit rather than something settable before
including cross.4 - see the comment at that exact spot in cross.4 for
why (a top-level IF/THEN silently corrupted the dictionary instead of
erroring; see PROGRESS.md for the full account). Bootstrapping a new
target cell width needs a cross-compile *host* whose own cells are at
least as wide as the new target's - i.e. building a 4-byte-cell image
needs to run on an 8-byte-cell (or wider) host; the reverse doesn't
work. This doesn't apply to building for a *new architecture* at the
*same* cell width (e.g. ARM64) - that needs no image rebuild at all,
per above.

3. Virtual Machine.

Virtual machine uses 3 internal registers: instruction pointer (IP), data
stack pointer (SP) and return stack pointer (RP). Cells are 8 bytes by
default, or 4 bytes when built for a 32-bit host (see above).

IP can point to the cells of 2 types:
a) containing reference to primitive;
b) containing shift to high-level definition.

Those 2 cases are distinguished in the following way. Since shift to
high-level definition is obtained by subtracting one cell address from another
cell address it should have 3 minor bits set to zeroes. Reference to primitive
is constructed by adding 1 to address of function, implementing primitive, so
it should look like number_of_primitive * 8 + 1 (8 - sizeof address). If ([IP]
& 1) == 1, then IP points to cell, containing reference to primitive. In this
case we jump (via computed goto - a GCC/Clang extension, not a
function-pointer call - see GOALS.md phase 5) to the code implementing
that primitive, indexed the same way: number_of_primitive * 8 + 1 is
still the addressing scheme, just used to index a table of label
addresses instead of function pointers. Otherwise, if
([IP] & 1) == 0, IP points to cell, containing shift to high-level definition.
In this case we push current IP to return stack and jump to high-level
definition: IP = IP + [IP].

Loops and branches are implemented using BRANCH (unconditional jump) and
0BRANCH (conditional jump) primitives, which are followed by shift, which
should be added to IP.

RelF works in absolute addresses. During system initialization absolute
address of system is pushed to the stack. It is used to adjust all system
addresses, which should be absolute.

4. Shell.

An optional POSIX-flavored shell, shell.4, is layered on top of an
already-bootstrapped kernel.img - it is not part of the base kernel
image, kept separate deliberately so the base image stays minimal (see
GOALS.md, goal 3). The easiest way to use it is via the relfsh wrapper
script at the repo root, which gives it a normal single-executable
interface:

    ./relfsh -c 'echo hello'      run one command, exit with its status
    ./relfsh                      interactive read-eval loop
    printf 'cd /tmp\npwd\nexit\n' | ./relfsh
                                   piped multi-line script

relfsh is a thin POSIX-sh wrapper: it feeds relf the two-line Forth
bootstrap (load shell.4, then call MAIN) ahead of whatever else is on
its own stdin, so relf itself doesn't need to be invoked interactively
just to reach the shell. The same two steps done by hand:

    ./relf kernel.img
    S" shell.4" INCLUDED
    MAIN

(MAIN checks whether relf was invoked with `-c "command"` - exposed to
Forth via the SYS-ARGC/SYS-ARG primitives, which read relf's own argv
beyond the image path - and either runs that one command via SH-C or
falls through to the ordinary interactive SH loop; calling SH directly
skips that check and always goes interactive.)

This loads twelve new process-control primitives' worth of shell logic
(FORK/EXECVE/WAITPID/PIPE/DUP2/GETENV/SETENV/SYS-EXIT/CHDIR/GETCWD/
SYS-ARGC/SYS-ARG are already compiled into kernel.img itself, same as
any other primitive). Current (v0.3) scope: external commands are
resolved via $PATH and run via fork/exec/wait, cd/pwd/export/exit are
supported as builtins, a single pipe per line (cmd1 | cmd2) wires two
external commands together via a real pipe, redirection (<, >, >>) is
supported for external commands, and arguments can be quoted (single
quotes are fully literal; double quotes recognize \" and \\ as
escapes; a lone backslash escapes the next character) so they can
contain spaces or literal shell metacharacters - echo 'a | b' prints
"a | b" rather than starting a pipeline. There is no $VAR expansion
yet, `-c` only ever runs a single command (no ";"/"&&" chaining),
pipes and redirection can't be combined on the same line yet, and only
a single pipe per line is recognized (no a | b | c). See GOALS.md
phase 7 and
PROGRESS.md's Iteration 5 through 8 entries for the current state and
what's planned next. tests/shell/ has a small test suite
(structurally modeled on bash's own tests/ directory) exercising all
of the above; run it directly via `tests/shell/run-all`, or as part of
`tests/run_tests.sh`.

5. Possible usage.

The main advantages of this system is small size of both machine-dependent
engine and of machine-independent binary system image. Due to those features
it can be used:
    * for development of plugins to different applications;
    * as embedded programming language;
    * etc ;).

6. Benchmarks

The numbers below predate phase 2 (32-bit cells, relfgcc/vm.asm/vm_tos.asm
variants that no longer exist - see GOALS.md) and are kept only as a
historical record; they are not representative of the current engine.

Benchmarks results were obtained with the only test, calculating fiboncci
numbers (fib.4). I used gforth-0.5.0 and sod32 from the authors home page
(http://www.xs4all.nl/~lennartb/sod32.tar.gz). Numbers in table are user time,
obtained by the following command:

cat fib.4 | time relf kernel.img

------------------+----------------+-------------------------+
OS                | FreeBSD 4.11-S | SunOS 5.9               |
CPU               | P1, 75 MHz     | UltraSparc III, 900 MHz |
gforth            | 0.6.2          | 0.6.2                   |
gcc               | 2.95.4         | 2.95.2                  |
test              | fib 34         | fib 38                  |
------------------+----------------+-------------------------+
C                 |  4.73          | 2.9                     |
relf              | 47.60          | 51.2                    |
relfgcc           | 33.03          | 37.4                    |
relf + vm.asm     | 16.53          |                         |
relf + vm_tos.asm | 15.74          |                         |
gforth            | 16.51          | 15.9                    |
gforth-fast       | 13.21          | 12.4                    |
sod32             | 72.73          | 43.1                    |
------------------+----------------+-------------------------+

------------------+--------------------------------+
OS                | SuSe 9.2 (kernel 2.6.4-52-smp) |
CPU               | Xeon 2.40GHz                   |
gforth            | 0.6.2                          |
gcc               | 3.3.3                          |
test              | fib 40                         |
------------------+--------------------------------+
C                 |  3.89                          |
relf              | 87.81                          |
relfgcc           | 58.05                          |
relf + vm.asm     |                                |
relf + vm_tos.asm |                                |
gforth            | 14.37                          |
gforth-fast       |  7.70                          |
sod32             | 89.66                          |
spf               |  2.53                          |
------------------+--------------------------------+

7. Contact info.

e-mail: kt97679@gmail.com
