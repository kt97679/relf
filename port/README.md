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
| strings.4 | CSTRLEN COMPARE STR-EQ? and relf's SCAN: the design's C SCAN where it means relf's, COMPARE a cell at a time while the strings agree (the lab only; gforth has its own, and CSTRLEN from relfsys.c) |
| alloc.4 | ALLOCATE FREE RESIZE as a C library's: size classes on 64 KB chunks - a design's own are an mmap and a munmap a block (the lab only) |
| os.4 | the primitives over SYSCALL, relf's stack effects and result codes: files, processes, pipes, the terminal, directories, limits, time, the environment table, signals (a signalfd), TCP |
| kernel-io.4 | kernel.4's file and terminal words over those, verbatim, and its ABORT" |
| shadow.4 | shadow.4's SHADOW{ locals: each local's save and restore inline, where relf has one opcode |
| lab/ | a design's kernel (relf's of long ago): its search order, interpreter, JIT headers, the save; and a front end for its compiler (below) |
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

    PROGRAM=rill3 sh port/lab/build.sh DESIGN-DIR OUT.img      # rill3 in place of the shell
    RILL3_PATH=lib DESIGN-DIR/forth OUT.img script.cm          # as bin/cm runs relf64 kernel64-cm.img

The lab build loads the port and the shell on the design's own kernel and writes the design's image
header (lab/header.py) and the body (lab/save.4's SAVE-BODY, START to HERE, the heads made relative);
on a design with the JIT gene (its Makefile's -DX_JIT=1) jit.4 first records each word's JIT header, so
the saved image starts as an unrun one. The gforth build is gforthmi's: a relocatable image, run by
either engine, with the data and return stacks at 256 and 64 KB (gforth's 16 KB default is the forth
command's gap). Both start the shell from a boot word that resets the port's state (PORT-BOOT) and
gives $0 as relf's engine does (RELF_ARGV0).

## rill3

rill3 (cm/, rill/rt.4) builds on a design the same way, from tools/build-cm-image.sh's sources (the shell's
character widths and its line editor less TAB completion cut out of shell/shell.4 and shell/edit.4), its
boot word R-BOOT; tests/cm's 192 checks (the runtime's own tests, the scripts, the prompt's sessions) pass
on every design. What it asks beyond the shell is port/rill.4's, which loads rill/rt.4 itself: safety.4's
TRAPPED (rt.4's trap word hands it the traps it does not take, though no engine here traps), kernel.4's
EXIT, (cm/ir.4 lays a made word's bytecode with COMPILE, LIT, CALL, STRING, and ends it with it), and the
cell at image offset 8 - relf's engine calls the word there when a frame of locals fails, rt.4 puts its
own there, and on a design those bytes are the kernel's start vectors: kept, and rt.4's word given to
shadow.4's LOCALS-FAILED through LF-HOOK. lab/host.4 has a >NAME (the made code shown, IR.): a design's
header has no flag on its count byte, so it tries each length below the xt and takes the name FIND
finds there (944; 943's walked back to a byte with bit 7 and showed garbage).

Not on gforth: cm/ir.4 keeps a word in its tokens as a three-byte offset from START, as relf's CALL, does,
and a gforth primitive's xt is in gforth's binary, not within 16 MB of its dictionary. Nor on relf32:
rill3's numbers are 64-bit (`cm: a number past 64 bits`). A script is compiled when it runs, by the
design's own compiler - the front end is the build's only - and a made word has no JIT header, so a JIT
design interprets a script's own code, its runtime's words native.

## What differs from relfsh

tests/shell, 93 files and 1128 assertions: against the knee's build (portable-knee) 10 fail, against
gforth-fast's 20, every one in the forth command's own Forth or in the layout; the JIT designs' fail
what the knee's does (a forth command's words are interpreted there, so `: X RECURSE ;` overflows as on
the knee - the JIT made it a jump, and run-forth-errors never ended, before Iteration 942):

- A script without `#!` is run as `ENGINE IMAGE script` - the engine and image are two files, as relf's
  were before Iteration 506 (run-noshebang, 1).
- A lab engine ends the process on a fault (`relf: segmentation fault`, status 70) where relf's routes
  it to the innermost CATCH: a bad address, a runaway recursion or push, the guard pages - and the
  kernel's own ABORT"s, ":"'s "name too long" among them, say nothing under a CATCH (run-forth-errors, 9).
- On gforth the forth command is gforth's Forth: its messages ("forth: uncaught exception -13" for
  relf's "Undefined word XYZ"), its search-order words, its [COMPILE]; a fault there fails the command
  only, as in relf (run-forth-errors and run-coverage-gaps, 19).

## Speed on a design: the front end

A design runs the lab's Forth benchmarks faster than relf, and ran relfsh 1.9-3.0 times slower (Iteration
941). Two reasons, both in what compiles the shell, not in the engines:

- **The compiler.** The shell is compiled at build time by the design's kernel compiler, which calls every
  word but its primitives: a variable is a call to DOVAR, a constant a call, CELLS or 2DUP or `-` a call to
  a colon word. The lab's converter (tools/layout.py), which gives the kernel its slot opcodes, folds and
  superinstructions, never sees the shell. loop.sh was 47.0 million dispatches on the knee, 10.4 million
  of them calls, against relf's 15.2 million (944's count: 941's said 57.4, every call taken twice) - the lab's benchmarks are mostly primitives; the shell is
  variables, constants, small words and locals, which relf's compiler and instruction set were made for.
- **The JIT took almost nothing.** A JIT design translates a word only if it can translate every word
  below it. A few words it has no stencil for - the kernel's variables (a NOOP and DOVAR), the system
  call, the kernel's SCAN, HERE and PAD (a variable's slot) - and calls of them left every word above
  interpreted: fastest-x86-64 interpreted 46.3 million dispatches of loop.sh (942's 32.8 was another
  build's).

lab/compile.4 is a front end for the kernel's COMPILE, (interp.4's INTERPRET calls it): variables, the
kernel's too, and constants as literals (every absolute address recorded and moved at boot, as the image
loads elsewhere each run - RELOCATE, PORT-BOOT's first); the kernel's small words inline; words of up to four tokens inline; POSTPONE
through it. On a JIT design with the gene jitexec, a call of a word the JIT refuses goes through
EXECUTE - native code runs a refused word in the interpreter - when that word cannot throw, and so does a
call that would make a word deeper than the JIT's sixteen levels; the primitives its JIT lacks are
found by probes. lab/jitwords.4 has the string words, HERE, PAD and the pictured numbers as the JIT takes
them; lab/again.4 compiles again the words of the files the kernel's interpreter read. build.sh's VARLIT
chooses the variables compiled as literals: 0 none (an interpreted design's default: its LIT64 reads
its bytes one at a time, which costs what the call saved), 1 all, 2 the kernel's (a JIT design's: its
JIT makes a call of our variables a literal itself, not of the kernel's).

The JIT's THROW is a limit to respect: a THROW from interpreted code that native code called unwinds the
return stack but not the machine's, and the catching code goes on in the innermost interpreter - the
native caller's continuation is lost, and a later return through an outer interpreter lands in the
wrong frame (on the bare design: `: T2 ABORT ; : T3 ['] T2 CATCH . ; : T5 ['] T3 EXECUTE 5 . ; T5` prints
`-1` and not `5`). A word that calls THROW is never translated, nor any word that calls it, so the
shell's parser, the interpreter and a forth command stay interpreted from their CATCH to their THROW;
the front end keeps it so - no call through EXECUTE of a word that may throw, a forth command's own
words left to the interpreter, PORT-BOOT too (its callees would be translated before RELOCATE ran).
The port's fatal errors (out of memory, the locals' save stack) still go through it, as a fault does.

Measured (Iteration 942, docs/progress has the table): fastest-x86-64 runs the shell in 0.25-0.28 of
relfsh64's time (941: 2.4-2.7 times it), fastest-x86-32 0.33-0.40, best-all-round 0.48-0.55, small-jit
1.50-1.63; the interpreted designs 1.6-2.7 (941: 1.8-3.3). The JIT designs' images are a quarter larger,
their memory 924-944 KB at peak, their start 1.2-1.5 of relfsh64's.

## Measuring (port/measure/)

port/measure/README.md has every command 941-944 measured with - bench-vm's configurations, sizes and
memory, the dispatch counts, the profiles, the JIT's refusals, where an image's bytes go - and results/
what they gave. build.sh's MAP=1 writes IMAGE.map beside the image: each word's address, kind and name,
under a line for the file it came from, and the bytes of the strings compiled in code. port/measure/REPORT-944.md answers the lab's questions of its Iteration 673.
