# relfsh on the lab's designs: answers for forth-vm-evolution (relf Iteration 944)

From relf, for the lab's Iteration 673 questions. Everything below was measured on one machine (A3), with
the lab at **f248f3e** (Iteration 665: the public master; c38483b and Iteration 673 are not on it, so
the THROW fix was not taken - see 8). The files are in relf's bundle (A1): `port/` is the port,
`port/measure/` the scripts, `port/measure/results/` the raw outputs this report quotes.

**One correction first.** relf's earlier numbers for the designs' dispatches (941-943, and what the
owner carried to the lab) counted every call twice: a design's PROFILE=1 dump (DISPATCH256) records a
call's first byte (0x80-0xFF) and then the pseudo-op 256. Counted once (port/measure/count-dispatch.py),
portable-knee against relf's CV8:

| program | relf64 | portable-knee | its calls | ratio | before (calls twice) |
| --- | ---: | ---: | ---: | ---: | ---: |
| fib | 97,019,850 | 102,330,868 | 10,772,508 | 1.05 | 1.17 |
| loop | 96,284,634 | 64,107,979 | 17,934 | 0.67 | 0.67 |
| bubble | 54,263,924 | 28,994,623 | 2,899,916 | 0.53 | 0.59 |
| ackermann | 32,338,316 | 39,023,614 | 8,463,442 | 1.21 | 1.47 |
| sieve | 100,718,083 | 114,917,983 | 16,460,412 | 1.14 | 1.30 |
| parse | 28,284,628 | 4,250,557 | 588,406 | 0.15 | 0.17 |
| loop.sh, 941's build | 15,217,587 | 46,954,831 | 10,447,080 | 3.09 | 3.77 |
| realistic.sh, 941's | 15,202,654 | 48,002,746 | 10,664,712 | 3.16 | 3.86 |
| loop.sh, 942's (front end) | 15,216,878 | 35,918,736 | 5,728,941 | 2.36 | 2.74 |
| fn / str / arith / realistic.sh, 942's | | | | 2.39 / 2.39 / 2.48 / 2.33 | |

The conclusion stands - 0.15-1.21 of relf's dispatches on the lab's benchmarks, 3.1-3.4 on the shell's
scripts as the design's compiler compiles them, 2.3-2.5 with relf's front end - but the factor is 3.1-3.4,
not 3.8-4.2. fastest-x86-64's profile (TAG2) counts a call once, so its figures stand: 46.3 million of
loop.sh's dispatches interpreted with 941's build (10.2 million calls), 3.2 million with 942's. The 32.8
million that relf's 942 also gave was another build's.

## A. Reproducing it

**1. relf's master.** The bundle `relf-claude-iter944-*.bundle` (`git clone` it), master at the commit
of Iteration 944, which holds this report as `port/measure/REPORT-944.md`. It is not pushed to GitHub
(the owner pushes); relf's public master is older. 941 is e3678ae, 942 1e46db3, 943 41399d1.

**2. The port.** All of it is `port/` (port/README.md is the overview):

- `port/relf.4` extend.4's and safety.4's words a host lacks; `strings.4` CSTRLEN COMPARE STR-EQ? SCAN;
  `alloc.4` ALLOCATE FREE RESIZE as size classes on 64 KB chunks; `os.4` relf's ~80 OS primitives over
  one word, `SYSCALL ( block num --- r )` (the design's own); `kernel-io.4` kernel.4's file and terminal
  words over them; `shadow.4` SHADOW{ locals; `rill.4` what rill3 adds (943).
- `port/lab/`: `build.sh` (the build), `header.py` (the design's image header), `nojit.4` / `jit.4` (JIT
  headers recorded and saved as unrun), `compile.4` (a front end for the design's COMPILE,), `interp.4`
  (relf's INTERPRET EVALUATE INCLUDED), `again.4`, `jitwords.4`, `host.4` (the search order, DICT-LIMIT,
  the stacks), `after.4`, `save.4` (PORT-BOOT, SAVE-BODY).
- `port/gforth/` the same for gforth 0.7.3.

How relfsh gets into an image: **loaded at start and saved by the design's own system.** build.sh pipes
`S" file" INCLUDED` lines for the port and relfsh's unchanged sources (forth/pool.4, shell/shell.4,
shell/edit.4, shell/tree.4) into `DESIGN/forth DESIGN/image.img`. The design's interpreter and its
run-time compiler compile them - port/lab/compile.4 in front of its COMPILE, from again.4 on - and
save.4's SAVE-BODY writes START to HERE (heads made relative, absolute literals listed for RELOCATE)
behind header.py's header. Neither relf's cross.4 nor the lab's tools are used, and the design's kernel
is its own image.img as shipped.

**3. Measuring** (port/measure/README.md has every command):

    WL="start loop fn str arith realistic" SCALE=5 python3 tools/bench-vm.py 12 CFG

CFG from `port/measure/mk-cfg.sh relfsh LAB WORK`; 12 rounds, configurations interleaved, relfsh64 the
base; medians with 95 % intervals of the ratio; CPU time by wait4, children included; start = 20 runs
of `-c true`. Size and memory: `port/measure/measure.py` (rsstrace: Rss, Anonymous, VmHWM at exit) on
the five at SCALE=5 and on `true`. The machine: Intel Xeon @ 2.30 GHz, 2 vCPUs, 4 MB L2, 8 GB, a
Firecracker VM, Linux 6.18.44, Ubuntu 24.04.5, gcc 13.3.0 for relf, clang 18.1.3 for the designs (their
Makefiles' `forth` target), Python 3.13.

## B. The numbers

**4.** Every design with 8-byte cells only (each Makefile's `forth`; its `forth32` and image32.img were
not tried - fastest-x86-32's `forth` is an x86-64 engine with 8-byte cells too). Relf's four as one file
each. Times as ratios to relfsh64 (lower is faster), 942's builds, `[95 % interval]`:

| shell | engine | image | total | RSS start | peak KB | start | loop | fn | str | arith | realistic |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| relfsh64 (CV8, C) | 175,794 | - | 175,794 | 1900 | 1920 | 1 (47.3 ms/20) | 1 (422.9 ms) | 1 (218.9) | 1 (219.3) | 1 (305.4) | 1 (365.4) |
| relfsh32 (CV8, C) | 153,026 | - | 153,026 | 1628 | 1708 | 1.120 [0.918-1.339] | 1.194 [1.136-1.264] | 1.254 [1.154-1.276] | 1.278 [1.178-1.316] | 1.246 [1.151-1.330] | 1.267 [1.232-1.342] |
| relfshasm64 (CV8, asm) | 144,250 | - | 144,250 | 232 | 268 | 0.619 [0.509-0.758] | 0.926 [0.905-0.995] | 0.978 [0.887-1.023] | 0.968 [0.935-1.008] | 0.967 [0.938-0.997] | 0.945 [0.904-1.040] |
| relfsh-native | 417,144 | - | 417,144 | 496 | 532 | 0.616 [0.591-0.741] | 0.097 [0.087-0.112] | 0.105 [0.097-0.126] | 0.107 [0.099-0.110] | 0.111 [0.106-0.116] | 0.109 [0.105-0.112] |
| fastest-x86-64 | 29,124 | 215,260 | 244,384 | 716 | 924 | 1.532 [1.238-1.779] | 0.251 [0.236-0.259] | 0.274 [0.263-0.463] | 0.265 [0.257-0.271] | 0.264 [0.258-0.304] | 0.277 [0.272-0.291] |
| fastest-x86-32 | 33,188 | 213,271 | 246,459 | 728 | 944 | 1.188 [0.984-1.217] | 0.345 [0.290-0.382] | 0.328 [0.287-0.335] | 0.356 [0.318-0.373] | 0.353 [0.337-0.386] | 0.395 [0.361-0.438] |
| best-all-round | 29,748 | 212,381 | 242,129 | 720 | 924 | 1.532 [1.423-1.778] | 0.477 [0.421-0.517] | 0.523 [0.483-0.588] | 0.545 [0.497-0.574] | 0.554 [0.528-0.587] | 0.550 [0.519-0.630] |
| small-jit | 20,588 | 197,177 | 217,765 | 488 | 588 | 0.885 [0.841-0.966] | 1.495 [1.450-1.580] | 1.626 [1.460-1.721] | 1.618 [1.544-1.749] | 1.581 [1.509-1.784] | 1.603 [1.533-1.653] |
| portable-fastest | 16,536 | 172,400 | 188,936 | 304 | 320 | 0.677 [0.618-0.717] | 1.885 [1.797-1.913] | 1.943 [1.790-2.026] | 1.928 [1.876-2.096] | 2.093 [1.964-2.163] | 1.977 [1.924-2.080] |
| portable-arm | 13,320 | 169,920 | 183,240 | 284 | 308 | 0.709 [0.622-0.773] | 1.611 [1.558-1.706] | 1.611 [1.542-1.729] | 1.720 [1.584-1.820] | 1.609 [1.560-1.659] | 1.697 [1.643-1.732] |
| portable-knee | 10,712 | 170,016 | 180,728 | 292 | 312 | 0.689 [0.641-0.731] | 1.937 [1.869-2.010] | 2.052 [1.846-2.095] | 2.109 [1.927-2.213] | 2.143 [2.039-2.230] | 2.100 [2.074-2.215] |
| portable-small | 9,416 | 171,720 | 181,136 | 280 | 300 | 0.714 [0.633-0.759] | 1.675 [1.554-1.722] | 1.747 [1.642-1.819] | 1.765 [1.666-1.871] | 1.721 [1.665-1.843] | 1.803 [1.753-1.871] |
| least-memory | 8,192 | 173,369 | 181,561 | 276 | 296 | 0.746 [0.648-0.772] | 1.978 [1.858-2.057] | 1.960 [1.834-2.029] | 2.020 [1.894-2.092] | 2.052 [1.987-2.167] | 2.070 [1.980-2.221] |
| smallest | 4,912 | 176,489 | 181,401 | 280 | 300 | 0.810 [0.778-0.842] | 2.207 [2.115-2.355] | 2.413 [2.053-2.554] | 2.548 [2.323-2.694] | 2.483 [2.365-2.612] | 2.651 [2.533-2.693] |
| gforth-fast 0.7.3 | 241,296 | 1,041,706 | 1,283,002 | 4036 | 4052 | 6.834 | 1.218 | 1.280 | 1.267 | 1.340 | 1.211 |

**Closest, and where each lost.** No design is both smaller and faster than CV8.
- **Time:** fastest-x86-64 is the closest, and beats it: 0.25-0.28 of relfsh64's, 3.8 times faster. It
  still loses to relfsh-native (0.10-0.11).
- **Size:** portable-knee is the closest at 180,728 bytes, 2.8 % over relfsh64 and 25 % over
  relfshasm64.
- **Every JIT design** loses on size (217-246 KB against 176 and 144 KB) and on start against
  relfshasm64. fastest-x86-64 and best-all-round also start slower than relfsh64 (1.53), fastest-x86-32
  too (1.19); small-jit starts faster (0.89).
- **Peak RSS:** the jitexec three (924-944 KB) beat relfsh64's 1,920 KB, which is its libc, but not
  relfshasm64's 268.
- **small-jit** loses on time (1.50-1.63), since without jitexec its JIT takes little (9).
- **The portable designs** lose on time (1.61-2.65) and size (+2.8 % to +7.5 % over relfsh64). They win
  start (0.68-0.81) and RSS (296-320 KB) against relfsh64, and lose both to relfshasm64.

## C. Where the bytes and the time go

**5. relfsh's image on portable-knee, against CV8's.** port/measure/design-bytes.py and cv8-bytes.py.
The knee's is a MAP=1 build of 944's sources, 560 bytes over the measured 170,016: map.4's own words and
943's >NAME fix. Bytes:

| part | CV8 kernel64-shell.img | portable-knee | fastest-x86-64 |
| --- | ---: | ---: | ---: |
| kernel words | 10,512 (kernel64.img's) | 8,969 (the design's image.img) | 9,694 |
| code (colon bodies less strings) | 64,104 | 99,569 | 141,596 |
| ... of it the port's code | (extend/safety in the 64,104) | 12,176 | 19,466 |
| names and headers | 24,426 | 28,123 (port 4,491) | 28,874 |
| strings (S" ." ABORT" in code) | 6,838 | 8,756 | 8,825 |
| data and buffers | 20,146 | 23,204 (port 3,364) + constants 428 | 24,146 + 428 |
| nojit.4 / jit.4 and map.4 | - | 1,447 | 2,234 |
| total | 126,026 of 126,042 | 170,496 | 215,797 |

The design's run-time header is CV8's (a tagged link of 1-3 bytes, the count byte, the name). So
relfsh's names and headers are the same size on both: 23,632 bytes on the knee, 24,426 with extend's and
safety's on CV8.

By file, the knee's image:

| file | bytes |
| --- | ---: |
| shell/shell.4 | 87,723 |
| shell/tree.4 | 42,250 |
| shell/edit.4 | 8,872 |
| forth/pool.4 | 1,204 |
| port/os.4 | 6,757 |
| port/lab/compile.4 | 5,035 (the front end: run at the build only, dead after boot) |
| port/kernel-io.4 | 1,892 |
| port/shadow.4 | 1,771 |
| the rest of the port | about 4,600 |

The gap of about 44 KB over CV8 is mostly code:
- relfsh's colon code is about 1.37 times CV8's (~88 KB less strings against 64 KB).
- 941's build, without the front end, was 150,532 bytes. The front end added 19.5 KB: its own 5 KB,
  and its inlining and literals. The port's other words are about 15 KB.

The 20 largest words, bytes with header:

| CV8 | | portable-knee | |
| --- | ---: | --- | ---: |
| ZERO-WIDTH | 1965 | ZERO-WIDTH (a CREATE table) | 1963 |
| PRINT-NODE-IMPL | 1051 | TEST-UNARY? | 1537 |
| APPLY-REDIRECTIONS | 581 | PRINT-NODE-IMPL | 1477 |
| TEST-UNARY? | 572 | SET-SHVAR | 945 |
| LIST-VARIABLES | 563 | APPLY-REDIRECTIONS | 902 |
| PD-SPEC | 552 | GLOB-WALK | 826 |
| EXPAND-WORDS | 551 | TEST-BINARY? | 819 |
| TRAPS | 535 | EXPAND-WORDS | 716 |
| DO-KILL | 531 | PF-CONVERSION | 699 |
| DO-ULIMIT | 502 | DO-KILL | 691 |
| (DO-GETOPTS) | 502 | (DO-GETOPTS) | 686 |
| SET-SHVAR | 499 | XE-PARAM-OP | 682 |
| PF-CONVERSION | 498 | PD-SPEC | 673 |
| XE-PARAM-OP | 489 | BRACKET-MATCHES? | 605 |
| SCAN-BRACE | 445 | PRINT-ENC | 604 |
| PRINT-ENC | 438 | GLOB-MATCH | 584 |
| WIDE-CHARS | 414 | LIST-VARIABLES | 577 |
| GLOB-WALK | 409 | SCAN-BRACE | 571 |
| CMD-REST | 403 | DO-ULIMIT | 566 |
| DO-CD | 400 | CMD-REST | 550 |

TEST-UNARY? (2.7 times) and SET-SHVAR (1.9 times) show the front end's inlining at its worst.

**6. The realistic script, on portable-knee and on CV8.** The script at bench-vm's own size (SCALE=1).
On the knee, the MAP=1 build of 5, PROFILE=1, calls taken once (port/measure/design-prof.py). On CV8, a counting
engine, every dispatch per address (relf-count.py, cv8-prof.py). The full lists are in
results/realistic-*.txt.

| | CV8 | portable-knee |
| --- | ---: | ---: |
| dispatches | 15,200,612 | 35,401,119 |
| calls | 1,004,237 (6.6 %) | 5,346,569 (15.1 %) |
| returns | 940,942 (EXIT and the folded) | 1,704,499 (EXIT and folds), plus 3,699,483 DOVAR and 564,873 DODOES |
| user time at SCALE=5 | 250 ms | 549 ms |
| per dispatch | 3.3 ns | 3.1 ns |
| system calls | 0 ms of system time; ~80 calls | 0 ms; ~45 calls |

The share of time in system calls is nil: the script runs no commands.

Hottest operations:
- **CV8:** CALL 6.6 %, DUP 6.5, ?BRANCH 5.8, VAR@ 5.5, 2VAR@ 4.0, + 3.9, VAR! 3.8, push0 3.4, EXIT 2.6,
  LIT8 2.6, VAR@+ 2.5, C@ 2.4, 0=?BRANCH 2.3.
- **The knee:** CALL 15.1 %, dovar 10.5, @ 9.1, lit8 8.3, 0branch 6.5, dup 5.5, exit 4.1, = 4.1, ! 3.3,
  swap 2.6, addi 2.6, r> 2.5, + 2.2.

Hottest adjacent pairs:
- **The knee (exact):** CALL→dovar 10.1 %, dovar→@ 6.0, lit8→= 3.5, dovar→! 2.5, =→0branch 2.4,
  dodoes→r> 1.6, CALL→dodoes 1.6, @→exit 1.6.
- **CV8 (a static estimate):** CELLS→+ 1.4 %, push0→VAR! 1.4, 2VAR@→+ 1.2, +→C@ 1.0, VAR@→?BRANCH 0.9.

Hottest words, by entries:
- **The knee:** ARGC 277,225, EXEC-BASE 184,317, XE-P 181,430, LSAVE-PTR 145,361, TOK-OUT 136,847,
  EW-I, CSTRLEN, START, ARGV, MOVE. Variables, mostly: called, as its compiler compiles them.
- **CV8:** XF@ 84,418, XE-P 46,888, XV@ 44,240, NAME-CHAR-TABLE, (S"), STR0=, SHVAR-NAME-SLOT. Its
  variables are slot operands, not calls.

On fastest-x86-64 most of the script is native; what stays interpreted, and why, is in 9.

**7. What relfsh's hot sequences compile to on portable-knee** (disassembled from the image, and from
the dump's pairs):

- **VAR@** (`X @`) is a call of X, which executes DOVAR, then `@`: three dispatches where CV8 has one.
  That is the realistic script's CALL→dovar 3.59 M and dovar→@ 2.12 M.
  - The knee has vf and vs (0x63, 0x64) with a 16-bit offset (VARSLOT=0). Only the converter emits them
    (vf ran 14,553 times, from the kernel's HERE), and 16 bits reach only the image's first 64 KB:
    relfsh's variables lie up to 170 KB in.
  - With VARLIT=1 the front end makes a variable `LIT64 addr @`: two dispatches, but LIT64 reads its
    eight bytes one at a time, so it is no faster.
- **XF@** (`1+ CELLS + X@`, X@ = `EXEC-BASE @ + @`) compiles to
  `addi 1 | lit8 3 | lshift | + | call EXEC-BASE(dovar) | "@ +" | @ | exit`: eight dispatches inlined.
  XV@ the same with addi 2. CV8 calls XF@ and runs about four inside: 1+, CELLS, +, VAR@+, @.
- **DEFER** (port/shadow.4: CREATE 0 , DOES> ... @XT EXECUTE) is a call, DODOES, R> and some ten more
  ops before EXECUTE (CALL→dodoes 564,873).
- **PICK**, from the front end's macro: `lit8 n | addi 1 | lit8 3 | lshift | sp@ | + | @`, seven ops;
  CV8 has one.
- **(+LOOP)** is one op (x_ploop), as in CV8.
- **Fused tests:**
  - `= IF` is `= | 0branch`, and `0= IF` is `lit8 0 | = | 0branch`. The front end's 0= is `0 =`, where
    x_zeq (0x34) exists.
  - CV8's 0=?BRANCH, EQI?BRANCH, <?BRANCH, U<?BRANCH and AND?BRANCH have no counterpart. eqi (0x7A)
    exists but only the converter emits it. The run-time compiler does fold `n +` into addi, and each
    word's last op into op;EXIT.
- **The SPEC band** (sub 2dup cells zeq ne zlt aligned count lsave lrest ...) is in the engine but
  hardly reached: 2dup 30,085, sub 1,201, cells 52 against 3.7 M DOVAR. The kernel's own `-` is still
  `negate + exit`, and its 2DUP is `over over;EXIT`.
- **The escape band:** relfsh's code reached it 32 times on the script (fork). The OS words are the
  port's Forth over SYSCALL, itself escaped (`system`).
- **Calls where CV8 has an op:** none that the front end left as calls among the hot ones. Variables are
  calls by construction (VARLIT=0), and so are DEFER's and BUFFER:'s children (DODOES).

## D. What the port needed

**8.** What relfsh uses that a design lacks or does differently, and the workaround each took
(port/README.md and the files' own comments have the detail):

- **Primitives.** relf's engines implement some eighty OS primitives (forth/kernel.4's ESCAPED list); a
  design has one, SYSCALL. port/os.4 builds them over it with relf's stack effects and result codes:
  - files: READ WRITE POLL OPEN-FILE CLOSE-FILE DELETE-FILE CHMOD REPOSITION-FILE FILE-POSITION FILE-SIZE
    FILE-MODE FILE-KIND ACCESS OPEN-DIR READ-DIR CLOSE-DIR;
  - processes: SYSTEM FORK EXECVE WAITPID WAIT-NOHANG GETPID GETPPID PIPE DUP2 KILL UMASK SETPGID CHDIR
    GETCWD;
  - the terminal: TCGETS TCSETS ISATTY TERM-RAW TCGETPGRP TCSETPGRP;
  - limits and time: GETRLIMIT SETRLIMIT CPU-TIMES LOCAL-TIME;
  - the environment table: GETENV SETENV UNSETENV;
  - signals: SIGNAL-ACTION SIGNALS-PENDING;
  - TCP: TCP-LISTEN TCP-ACCEPT TCP-CONNECT.

  kernel-io.4 has kernel.4's file words over those, verbatim. alloc.4 has an allocator: a design's
  ALLOCATE is an mmap a block (4,017 munmaps on loop.sh), now size classes on 64 KB chunks.
- **Kernel words added or redefined.**
  - From extend.4 and safety.4 (relf.4): NIP TUCK 0<> 0> U> WITHIN ERASE [COMPILE] CASE..ENDCASE
    ENVIRONMENT? AGAIN @XT !XT TRAP-ENTRY TRAP-XT! (THROW) ABORT".
  - relf's INTERPRET, EVALUATE and INCLUDED: a design throws -13 silently under a CATCH.
  - A search order with relf's link cell; >NAME (rill3).
  - CSTRLEN COMPARE SCAN: the design's SCAN stops at any control character for a blank.
  - MOVE: the kernel's copies backwards whenever the source is lower.
- **Signals.** A Forth word cannot be a handler, so a caught signal is blocked and read from a signalfd:
  - WAITPID polls the signalfd and a pidfd, so a trapped signal ends `wait` with 128+n.
  - A forked child makes its own signalfd: a shared one's mask is the parent's.
  - Lost: a blocked signal interrupts no read (relf's action 3, ^C at an interactive prompt).
- **Sizes.**
  - relfsh needs a 256 KB data stack and the forth command a 16 KB gap below it (host.4's DICT-LIMIT,
    from the design's DSTACK_BYTES). gforth needed its stacks raised to 256 and 64 KB.
  - The include buffer is the design's (nesting checked by interp.4).
  - The JIT designs hold 8,192 JIT headers in jit.4's table (relfsh uses about 2,300).
- **The image moves every run** (mmap, ASLR). Absolute literals are recorded as sites, written as varints
  and relocated by RELOCATE at boot; PORT-BOOT must stay interpreted (9).
- **rill3** (943): TRAPPED, EXIT,, and relf's cell at image offset 8 - on a design those bytes are the
  kernel's start vectors, so they are kept and the word goes to LOCALS-FAILED through LF-HOOK.
- **THROW.** Your fix (673) was not taken: c38483b is not on the lab's public master (f248f3e), so the
  port keeps its THROW rules. With the fix, three could go:
  - the forth command's words left to the interpreter;
  - PORT-BOOT saved as refused (that one is about RELOCATE, not THROW: it stays);
  - may-throw words never called through EXECUTE. That rule keeps EXEC-SIMPLE, EXEC-IMPL and
    EXPAND-AND-RUN interpreted (9).

  A bundle of 673 would let relf retest.

**9. What cost relfsh by construction.**

- **The run-time compiler:** everything in 7 - variables as calls, no SPEC band, no fused tests, LIT64 a
  byte loop - and no whole-image work. relfsh's code gets neither the converter's ranking, folds and hot
  calls nor cross-cv8.4's, since it is not built by them.
- **JIT refusals** (fastest-x86-64, JITLOG's R lines, followed to their roots).
  - Before 942's front end, these roots refused every word above them, up to MAIN, and the JIT
    interpreted 46.3 M of loop.sh's dispatches:
    - kernel variables: NOOPs then DOVAR, which has no stencil, so START, BASE and STATE were refused;
    - SYSCALL (op 140) and the kernel's SCAN (op 38), which have no stencils;
    - HERE and PAD: vf, and stencil why 3;
    - the C CMOVE on best-all-round (op 53);
    - the linear return-stack check: an R> in each arm of an IF, in MOVE, STR-EQ?, COMPARE,
      TEST-PARSE-INT, EXPAND-AND-RUN, EXEC-LOOP;
    - SP! (op 33) in RUN-CAUGHT; RP@ (op 34) in CATCH;
    - JIT_DEPTH 16: `$(( ))` is 21 calls deep, and the top word is refused for good;
    - the cold list's THROW at 4120 while `' THROW` is 4115 (NOOP padding), so direct THROW callers
      were refused. That accidentally kept THROW paths interpreted - the only thing that made them safe
      before 673.
  - After it, the realistic script translates 401 words and refuses 58. The roots are THROW (38 words
    above it), CATCH, RUN-CAUGHT (SP!), EXPAND-AND-RUN, TEST-PARSE-INT, EXEC-LOOP and the I/O words.
  - Interpreted dispatches on the script, by word: EXEC-SIMPLE > EXPAND-AND-RUN 23 %, EXEC-IMPL 23 %,
    EXPAND-AND-RUN 13 %, RUN-CAUGHT 7 %, TEST-PARSE-INT 6 %. results/realistic-fastest-x86-64-jit-*.txt
    has both lists.
  - On rill3, its runtime raises errors from nearly every word: R-FAIL reads the return stack (RP@,
    R-WHERE) and THROWs, so the JIT designs run rill3 at 1.04-1.59 of relf64's time. A script's own words
    are laid headerless (HERE ]), so they are never translated.
- **Limits met:**
  - 16-bit variable slots (VARSLOT=0): 64 KB.
  - The JIT's 1 MB of code: relfsh's native code takes about 300 KB, 924 KB peak RSS.
  - No JIT header on code compiled without `:`.
  - The kernel's name length of 31 ("name too long" under a CATCH is silent).
  - rill3's 3-byte tokens are START-relative, so gforth is out.
  - Start: the JIT translates what a start runs, 1.2-1.5 times relfsh64's start.

## E. What would count

**10. Relf's criteria as recorded, and my reading of them.** The owner sets these, and has not set new
ones for the lab.

- **Recorded in relf:**
  - docs/QUESTIONS.md A33 (Iteration 609, for native code): "cv8 stays as is. We may improve it but we are definitely not
    replacing it". New engines go beside CV8, and size is weighed against speed: "+50% in code size and
    +5% performance probably not worth it".
  - docs/GOALS.md: no libc in the engine's runtime (deferred for portability); self-hosting (cross.4 builds
    the image byte for byte); the same kernel64.img on x86-64 and ARM64, and i386 for 4-byte cells.
  - Your copy from 356 agrees: bench-vm.py; an image cross.4 can produce; both widths; AArch64 and
    RISC-V; nothing x86-only for CV8.
  - The owner this month: relfsh and rill3 "faster, smaller and more RAM efficient".
- **My reading:**
  - Bytes are the file or files on disk (engine and image), with peak RSS over bench-vm's five and RSS
    at start beside them.
  - Times are bench-vm's five at SCALE=5 (their geomean) and start (20 × `-c true`); rill3's are
    tests/cm/bench. Interactive latency has never been measured, by either side.
  - No weights are recorded. A candidate should not lose on any of the three against both CV8 engines,
    relfsh64 and relfshasm64, on x86-64 and AArch64, in both widths.
  - A JIT or an x86-only engine is acceptable only beside CV8, as relfsh-native is (x86-64 only, an
    experiment), not as CV8.
  - So what relf can adopt from the lab is mechanisms, into CV8, cross.4 and the asm engine, as 938-940
    took VAR@'s pairs. A design is a test bed, not a replacement.

**11. My reading.**

Why they don't transfer:
- **The designs' speed is in their images.** The converter's and cross-cv8.4's whole-image work and
  the profile-trained choices are applied to the lab's kernel, trained on the lab's benchmarks.
- **relfsh never sees them.** It is compiled by the design's run-time compiler, which emits calls,
  base primitives and literals. The result: 2.3-3.4 times CV8's dispatches, at about the same cost per
  dispatch (3.1 against 3.3 ns).
- **The JIT is all or nothing per word.** It took almost nothing of relfsh until the port routed around
  six roots; it is now 3.8 times faster than CV8, but at 39 % more bytes and a slower start.
- **Size can't come from the kernel.** A design's kernel is 9 KB of a 170 KB image, and relfsh's code
  under the design's compiler is about 1.4 times CV8's.

What I would change first, in order:
1. **Build relfsh, the kernel and its program together, with the designs' own whole-image tools**
   (cross-cv8.4, 672): dead words dropped (the front end alone is 5 KB, dead after boot), opcodes ranked,
   pairs fused, hot calls inlined. Train them on relf's workloads: bench-vm's five and tests/cm/bench.
   relfsh's hot pairs (CALL→DOVAR, DOVAR→@, lit8 =, = 0branch, DODOES→R>) are not the lab's.
2. **Make the run-time compiler emit what the engine already has.**
   - vf and vs with 23-bit slots (VARSLOT), so a variable is one dispatch.
   - The SPEC band: sub 2dup cells zeq ne zlt; eqi and eqi?branch; fused compare-and-branch.
   - A cheap address literal. LIT64's byte loop makes literals no faster than calls.

   The lab is better placed than relf's port, which can only guess encodings.
3. **For the JIT:**
   - Your THROW fix (relf can then route may-throw words).
   - Kernel variables without NOOP padding, or a DOVAR stencil.
   - Stencils for SYSCALL and SCAN, or jitexec everywhere.
   - A return-stack check that follows the branches (JITCFA).
   - A larger JIT_DEPTH, or translation that resumes.
   - The cold list by both THROW addresses.
   - JIT headers for code laid by HERE ] (rill3).
4. **Score on bytes and start, as on time.** The jitexec designs reach 0.25-0.40 but cost 39 % in bytes
   and 1.2-1.5 in start.

**The lab's guesses:**
- **(a) Confirmed, with one correction.** relfsh's code is compiled at the build, not at each start -
  loaded through the design's interpreter and run-time compiler, then saved - so it gets only what that
  compiler does: 0.15-1.21 of CV8's dispatches on the lab's benchmarks, 3.1-3.4 on relfsh's scripts.
  With relf's front end (literals, inlining) 2.3-2.5. The SPEC band is in every SPEC design's engine
  and almost unused by relfsh's code (7).
- **(b) Consistent, not tested directly** (no design was retrained on relfsh).
  - The knee's three superinstructions (OVER C@, + @, @ +) together run 2.4 % of the script's
    dispatches; its folds and ops10 are the kernel's words.
  - relfsh's top pairs are none of these (6).
  - The JIT's cold list is the lab's I/O words: EMIT TYPE CR SPACE SPACES . U. ABORT THROW KEY ACCEPT.
- **(c) Confirmed.**
  - The kernel is 8,969 of the knee's 170,496 bytes (5.3 %) and 9,694 of fastest-x86-64's 215,797.
  - relfsh's own code, data, names and strings are 140 KB (82 %); the port another 20 KB (12 %).
  - Shrinking the kernel further changes little. Shrinking relfsh's code, and dropping the build-only
    words, is where the bytes are.

## Also measured: rill3 (943)

rill3 on the ten designs, relfasm64 and a native build, against relf64 (tests/cm/bench; peak RSS about
17 MB everywhere, its collector's 16 MB threshold):
- rill3-native: 0.22-0.26;
- relfasm64: 0.80-0.92;
- the JIT designs: 1.04-1.59, for 9's reason;
- the interpreted designs: 1.16-3.58.

results/rill3-bench.txt has it all. Not on gforth or relf32.
