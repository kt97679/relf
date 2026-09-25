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

## Milestone 0 — thin primitives, in C first

Before any assembly, make every primitive a thin wrapper over the
kernel, moving policy into Forth where the existing suites test it.
Each step is an ordinary iteration: `cv8.c`, the kernels rebuilt, both
widths verified, the ARMv7 board too.

- **The environment moves into the shell.** It already keeps every
  variable with an export flag; today it mirrors exports into libc's
  `environ` through `SETENV`/`UNSETENV`, and `EXECVE` passes `environ`
  implicitly. Instead: `EXECVE` takes an explicit `envp`, which the
  shell builds from its table when it runs a program, and the engine
  offers only the environment it was started with (`ENV-AT`). `GETENV`,
  `SETENV` and `UNSETENV` go. The largest step, and a shell change, not
  an engine one.
- **`~user`** (`GETPWNAM-HOME`) reads `/etc/passwd` in Forth. A real
  reduction - libc's `getpwnam` also asks NSS (LDAP, systemd-homed) -
  and inherent to having no libc; dash with a static musl has the same
  limit.
- **`LOCAL-TIME`** (prompt escapes `\t`, `\D{...}`) needs the zone:
  `TZ`, or `/etc/localtime` in TZif form. A TZif reader in Forth, the
  engine giving only the clock - or UTC first, with the zone as its own
  step.
- **`TCP-CONNECT`** takes the address as a number; the dotted form is
  parsed in Forth.

After Milestone 0 the contract is: every primitive is at most a
system call and the arithmetic around it, except the allocator,
`getdents64`'s buffering, and the memory routines.

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

1. **The core**: dispatch, calls, branches, the arithmetic, memory and
   stack primitives, `read`/`write`/`exit`. Runs the bare kernel:
   `echo '2 3 + . BYE' | ./relfasm64 kernel64.img`.
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

- **Milestone 0's environment change is the one real design step**, and
  it changes the shell. The alternative - an environment array kept by
  the assembly engine, as libc keeps one - costs ~150 lines of
  assembly and leaves the two engines' contract as it is.
- **`~user` without NSS**, and **the time zone**: accepted reductions,
  or reasons to keep a little policy in the engine?
- **The 32-bit side**: the ARMv7 board keeps cv8.c. An ARM engine would
  be its own project, after x86-64 has shown what one costs.
