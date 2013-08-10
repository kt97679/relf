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

In order to start playing with RelF you need to compile engine. You can do it
with virtually any C compiler. I tested RelF with TurboC2.0 under DOS,
lcc-win32 under Windows and gcc under FreeBSD, Linux and Solaris. Please note,
that there are 2 .c sources: relf.c and relfgcc.c. The latter uses specific
gcc features that in theory should result in faster virtual machine. To
compile virtual machine with gcc just issue

gcc -O2 -o relf relf.c

or

gcc -O2 -o relfgcc relfgcc.c

Don't forget to #define BIG_ENDIAN in case your platform is big-endian.

For x86 platform you can use assembler versions of virtual machine: vm.asm or
vm_tos.asm. vm_tos.asm has Top Of Stack in dedicated processor register and as
you can see from benchmarks this version is a little bit faster. Those virtual
machines are "proof of concept" and at present moment do not include file I/O.

To use vm.asm or vm_tos.asm you need to comment out or rename
virtual_machine() function in relf.c. After that you should compile assembler
source using NASM. On FreeBSD I used the following command lines:

nasm -O9 -f elf -o vm.o vm.asm

or

nasm -O9 -f elf -o vm.o vm_tos.asm

After that you should link optimized virtual machine with remaining C code. I
did this by the following command:

gcc -o relf relf.c vm.o

In case you would like to compile sources on windows platform you would need
to change external and global names in nasm sources. They should start with
underscore (e.g. you should change line "extern ip" to "extern _ip" and so
on).

Compilation command lines are:

nasmw -O9 -f win32 -o vm.obj vm.asm

or

nasm -O9 -f win32 -o vm.obj vm_tos.asm

Machine-independent kernel can be compiled by RelF itself or by virtually
any ANS forth. I successfuly used gforth.

To compile kernel with RelF you need to do the following:
    a) start RelF with initial kernel: ./relf kernel.img
    b) load extensions: S" extend.4" INCLUDED
    c) load cross-compiler: S" cross.4" INCLUDED

After a couple of moments RelF would exit and you'll get new kernel.img.
Please, backup original kernel.img, since it would be overwritten during 
crosscompilation.

3. Virtual Machine.

Virtual machine uses 3 internal registers: instruction pointer (IP), data
stack pointer (SP) and return stack pointer (RP).

IP can point to the cells of 2 types:
a) containing reference to primitive;
b) containing shift to high-level definition.

Those 2 cases are distinguished in the following way. Since shift to
high-level definition is obtained by subtracting one cell address from another
cell address it should have 2 minor bits set to zeroes. Reference to primitive
is constructed by adding 1 to address of function, implementing primitive, so
it should look like number_of_primitive * 4 + 1 (4 - sizeof address). If ([IP]
& 1) == 1, then IP points to cell, containing reference to primitive. In this
case we call function at address BASE + [IP], where BASE =
pointer_to_the_array_of_functions,_implemeting_primitives - 1. Otherwise, if
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
