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

Cells are 8 bytes, matching the process's own pointer width on every
64-bit host targeted so far (RelF's real-pointer addressing model needs
the two to match - see PROGRESS.md, Bug 2). 32-bit-cell hosts (ARM32,
i386, etc.) aren't currently supported - see GOALS.md's non-goals.
There is no separate relfgcc.c/vm.asm/vm_tos.asm engine any more;
relf.c is the only one.

kernel.img is native host endianness (little-endian - see GOALS.md's
non-goals) with an 8-byte magic header (cell width + a fixed tag), so a
mismatched image fails cleanly at load rather than silently
misbehaving. Any two architectures that agree on cell width and
endianness can share one image unmodified - confirmed by running the
identical kernel.img, unchanged, on both x86-64 and ARM64.

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

Note: bootstrapping a *new* target cell width (e.g. a future 32-bit
port) needs a cross-compile host whose own cells are at least as wide
as the new target's - see GOALS.md and PROGRESS.md for the details of
how cross.4's @-T/!-T and the hand-numbered primitive tokens in
kernel.4 (LIT/EXIT/BRANCH/0BRANCH/R>) account for this. This doesn't
apply to building for a *new architecture* at the *same* cell width
(e.g. ARM64) - that needs no image rebuild at all, per above.

3. Virtual Machine.

Virtual machine uses 3 internal registers: instruction pointer (IP), data
stack pointer (SP) and return stack pointer (RP). Cells are 8 bytes.

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

4. Possible usage.

The main advantages of this system is small size of both machine-dependent
engine and of machine-independent binary system image. Due to those features
it can be used:
    * for development of plugins to different applications;
    * as embedded programming language;
    * etc ;).

5. Benchmarks

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

6. Contact info.

e-mail: kt97679@gmail.com
