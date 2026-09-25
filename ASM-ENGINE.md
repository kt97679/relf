# ASM-ENGINE.md — an x86-64 engine on raw syscalls

GOALS.md "What comes next", item 5: an assembly engine with no libc,
the project's first end state, deferred since phase 5 traded it for
portability. Decided at 500: x86-64 first, because the debugging loop
has to run where the code is written. Iteration 2 had a no-libc x86-64
engine for the original token-threaded format; none of it carries over
to CV8, but the approach is proven here. This is the design (Iteration
513), before any code.

## The constraint that shapes everything

**Both engines run the same images.** `cv8.c` stays - it is the
portable engine, the one the ARMv7 board runs, the reference - so the
assembly engine implements exactly its primitives, with exactly their
stack effects and results. The test of correctness is the one the
project already has: the kernels' fixpoint (`cross.4` run on the new
engine must write byte-identical `kernel64.img` and `kernel32.img`) and
every suite, run through a `relfsh` built from the new engine with
`tools/embed.sh`. Nothing new has to be invented to check it.

## What libc does for cv8.c today

`nm -u relf64`: 63 functions, behind 138 handlers in 1,706 lines.

| kind | functions | in assembly |
|---|---|---|
| **one system call each** (41) | read write open close lseek stat lstat access unlink chdir getcwd umask dup2 fcntl pipe poll fork execve waitpid kill getpid getppid setpgid getrlimit setrlimit getrusage mprotect socket bind listen accept connect setsockopt time exit, and the terminal: isatty tcgetattr tcsetattr tcgetpgrp tcsetpgrp (ioctl) | a `syscall` and an error mapping each - `sigaction` needs `SA_RESTORER` and a stub that calls `rt_sigreturn`, `waitpid` is `wait4` |
| **small routines** (9) | memchr memcmp memmove memset strchr strlen, sigemptyset sigaddset, sysconf | a few lines each; the page size comes from the auxiliary vector |
| **services with state** (8) | malloc realloc free; getenv setenv unsetenv (and `environ`); opendir readdir closedir | an allocator; an environment; `getdents64` with a buffer |
| **policy** (3) | getpwnam, localtime_r, inet_pton | see Milestone 0 |

The first two rows are mechanical. The third is where the work is:
`ALLOCATE`, `RESIZE` and `FREE` are hot in the shell (every buffer
grows through them), so the allocator must be decent - segregated free
lists over `mmap`, with `realloc` in place when it can.

## Decided (Iteration 514)

- **x86-64 only, for now.** The 32-bit side keeps cv8.c; an engine for
  it is revisited when the 64-bit one is complete.
- **Every primitive keeps its contract**, the environment included:
  the assembly engine keeps an environment as libc does - the one it
  was started with, changed by `SETENV` and `UNSETENV`, passed by
  `EXECVE` - so the two engines stay interchangeable and the shell does
  not change. About 150 lines of assembly; no concern with it.

So the Milestone 0 first proposed here - moving the environment into
the shell, `~user` and the time zone into Forth - is **not** done.
What remains of it is optional groundwork, each item a question in
QUESTIONS.md: one generated source for the opcode numbering, so the
assembly engine's table is not a fifth hand-kept copy (Q3); `LSAVE`
and `LRESTORE` as real primitives (Q4); and, since the format would
change under both engines, a decision on the two-bit call tag before
Milestone 1 (Q2). `~user` reads `/etc/passwd` (Q5), and `LOCAL-TIME`
gives UTC first (Q6), unless the user decides otherwise.

## The engine

- **Registers**: `r14` ip, `r13` data-stack pointer, `r12` the cached top
  of stack, `r15` return-stack pointer, `rbx` the image base. `rax`,
  `rcx`, `rdx` and `r11` are scratch - `syscall` clobbers `rcx` and
  `r11`. The machine stack stays the machine's: the Forth return stack
  lives where it does now, in VM memory with its guard pages, so
  `RP@`/`RP!`, `CATCH` and the stack-overflow reports mean what they do
  in cv8.c.
- **Dispatch**: `movzx eax, byte [r14]` / `inc r14` /
  `jmp [dispatch + rax*8]` - the 256-entry table cv8.c builds, with
  0x80-0xFF going to the call handler. The folded `;EXIT` forms and the
  specialised band are one handler each, as in C.
- **Memory**: the 16 MB block, 64 KB-aligned, guard pages by
  `mprotect`, a `SIGSEGV` handler that tells a guard hit from a crash -
  as cv8.c does, in fewer lines.
- **Build**: GNU `as` through `cc -nostdlib -static` - no NASM, since
  every machine that builds cv8.c has `as`. One `.S` file, `relfasm64`.
  The trailer lookup of Iteration 506 comes along, so `tools/embed.sh`
  makes a shell of it unchanged.

## Milestones after 0

*Done first, at 518*: the opcode map has one source, `opcodes.tab`. The
assembly engine's dispatch tables will be generated from it as cv8.c's
are, rather than typed a fifth time.

1. **The core**: dispatch, calls, branches, the arithmetic, memory and
   stack primitives, `read`/`write`/`exit`. Runs the bare kernel:
   `echo '2 3 + . BYE' | ./relfasm64 kernel64.img`. **Reached at 519**:
   `relfasm64.S`, 28 KB static with no libc, runs the bare kernel and
   the CORE word suite (`tester.fr`, `core-extra.fth`,
   `coreplus-loop.fth`) with output byte-identical to cv8.c's for 2,040
   OK markers - stopping where `shadow.fth` first opens a file, the
   next milestone. Every opcode but the escaped ones is written; the
   escaped ones are stubs generated from `opcodes.tab` that name
   themselves and exit 99, and 54 of them are left.
2. **Files**: the file primitives and `INCLUDED`. Then the strongest
   check there is: `cross.4` run on the assembly engine rebuilds both
   kernels byte-identically.
3. **Processes**: fork, exec, wait, pipes, descriptors, signals. The
   shell starts; the differential suite runs.
4. **The rest**: terminal, directories, time, limits, sockets. Every
   suite, both through `relfsh`.
5. **Measure**: the paired benchmark against cv8.c. The point of an
   assembly engine was never only libc - it is also where the dispatch
   loop can be exactly what it should be.

## Open, for the user

In QUESTIONS.md, where every question to the user is kept: Q2 to Q6.
