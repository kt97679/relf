# port/ - relfsh on a Forth that is not relf

relfsh is written in Forth against relf's kernel and some eighty operating-system primitives that relf's
engines implement in C or assembly (forth/kernel.4's ESCAPED list). This directory runs the same shell
sources - forth/pool.4, shell/shell.4, shell/edit.4, shell/tree.4, unchanged - on two other kinds of
Forth: the ten designs of the forth-vm-evolution lab (its `designs/<name>/`: an engine `forth` and a
kernel image) and gforth 0.7.3. Iteration 941 built it, to compare the shell on every Forth in the table
of 938-940 (size, speed, memory); docs/progress/0900-0999.md has the numbers.

## What a host gives

One word:

    SYSCALL ( block num --- r )   Linux x86-64 system call num, its six arguments the cells at block,
                                  r its result or -errno; num -1, -2, -3 give argc, argv, environ

A lab design has it as it is (its engine's L_syscall). gforth gets it from port/gforth/relfsys.c, a
shared library called through gforth's call-c (not libcc: a saved image keeps a libcc function's address
from the process that saved it). Everything else is Forth:

| file | what |
| --- | --- |
| relf.4 | extend.4's and safety.4's words a host lacks: NIP TUCK CASE ... ENVIRONMENT?, @XT !XT, the hooks |
| strings.4 | CSTRLEN COMPARE and relf's SCAN: the design's C SCAN where it means relf's, COMPARE a byte loop (the lab only; gforth has its own, and CSTRLEN from relfsys.c) |
| alloc.4 | ALLOCATE FREE RESIZE as a C library's: size classes on 64 KB chunks - a design's own are an mmap and a munmap a block (the lab only) |
| os.4 | the primitives over SYSCALL, relf's stack effects and result codes: files, processes, pipes, the terminal, directories, limits, time, the environment table, signals (a signalfd), TCP |
| kernel-io.4 | kernel.4's file and terminal words over those, verbatim, and its ABORT" |
| shadow.4 | shadow.4's SHADOW{ locals: the variable and a run-time word where relf has one opcode |
| lab/ | a design's kernel (relf's of long ago): its search order, interpreter, JIT headers, the save |
| gforth/ | gforth's differences: a case-sensitive word list, relf's kernel cells, the boot |

Signals are the one real difference in kind. relf catches a signal with a handler in the engine that
sets a flag; a Forth word cannot be a handler. So a caught signal is blocked and read from a signalfd
when the shell asks (SIGNALS-PENDING); WAITPID polls the signalfd and a pidfd for the child, so a
trapped signal still ends `wait` with 128+n; a forked child makes its own signalfd (a shared one's mask
is the parent's too); EXECVE unblocks them for the program it starts. What it loses: a blocked signal
interrupts no read - relf's action 3, which an interactive prompt uses to see ^C at once.

## Building

From relf's top:

    sh port/lab/build.sh DESIGN-DIR OUT.img     # DESIGN-DIR: a lab design, built; prints OUT's size
    DESIGN-DIR/forth OUT.img [shell arguments]

    sh port/gforth/build.sh OUT.fi              # gforth 0.7.3 and its gforthmi; a C compiler
    gforth-fast --appl-image OUT.fi [shell arguments]   # or gforth

The lab build loads the port and the shell on the design's own kernel and writes the design's image
header (lab/header.py) and the body (lab/save.4's SAVE-BODY, START to HERE, the heads made relative);
on a design with the JIT gene (its Makefile's -DX_JIT=1) jit.4 first records each word's JIT header, so
the saved image starts as an unrun one. The gforth build is gforthmi's: a relocatable image, run by
either engine, with the data and return stacks at 256 and 64 KB (gforth's 16 KB default is the forth
command's gap). Both start the shell from a boot word that resets the port's state (PORT-BOOT) and
gives $0 as relf's engine does (RELF_ARGV0).

## What differs from relfsh

tests/shell, 93 files and 1128 assertions: against the knee's build (portable-knee) 10 fail, against
gforth-fast's 20, every one in the forth command's own Forth or in the layout; fastest-x86-64's (a JIT
design) fails what the knee's does, but its run-forth-errors never ends - the JIT makes `: X RECURSE ;`
a jump, so the runaway recursion it tests loops instead of overflowing:

- A script without `#!` is run as `ENGINE IMAGE script` - the engine and image are two files, as relf's
  were before Iteration 506 (run-noshebang, 1).
- A lab engine ends the process on a fault (`relf: segmentation fault`, status 70) where relf's routes
  it to the innermost CATCH: a bad address, a runaway recursion or push, the guard pages - and the
  kernel's own ABORT"s, ":"'s "name too long" among them, say nothing under a CATCH (run-forth-errors, 9).
- On gforth the forth command is gforth's Forth: its messages ("forth: uncaught exception -13" for
  relf's "Undefined word XYZ"), its search-order words, its [COMPILE]; a fault there fails the command
  only, as in relf (run-forth-errors and run-coverage-gaps, 19).

And speed. The shell's sources are compiled by the host's own compiler, which for a lab design is the
kernel's simple one: a variable, a constant and every small word a call, where relf's has VAR@ and its
slots, folded returns, superinstructions and an inliner. loop.sh is 56.9 million dispatches on the
knee's build, 10.4 million of them calls, against relf's 15.1 million - so the designs, faster than relf
on the lab's own benchmarks, run the shell 1.9-3.0 times slower than relfsh64 (docs/progress, Iteration 941).
