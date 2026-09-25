# SELF-HOSTING.md - relf compiling its own engine

A proposal for review (Iteration 535), before any code: GOALS.md item 6,
"the assembly engine, self-hosted - a Forth-hosted assembler that emits
the engine itself, as `cross.4` emits the kernel". The open choices are
QUESTIONS.md Q17; nothing here starts until they are answered.

## 1. What it means

Today Forth already compiles the Forth: `cross.4`, running on an engine,
compiles `kernel.4` into the very image that engine runs, byte for byte
(Iteration 243). What it cannot build is the engine: `cv8.c` needs a C
compiler, `relfasm64.S` needs GNU `as` and `ld`.

Self-hosted means: **a Forth program, running on relf, writes the
assembly engine's executable** - the ELF header, the machine code, the
tables - and the engine it writes can run the same program and write
itself again, identical. Then on x86-64 relf needs nothing outside
itself: the engine rebuilds itself, and the kernels, and the shell.

## 2. Why the assembly engine, and only it

The assembly engine (Iterations 513-524) was built for this. It has no
libc, no C, and it is small - 2,551 lines, 1,938 instructions of 53
distinct mnemonics (`mov` alone is 734), 8 macros, 89 constants:

    mov lea xor add test syscall cmp call jmp inc pop push jz sub movzx
    jne js shl je ret jnz div and or rep dec movsx jns jae ja jle jb neg
    movsxd imul shr sar jge sete not ...

- ordinary two-operand forms (register, memory `[base + index*scale +
  disp]`, immediate) in byte, word, dword and qword sizes;
- shifts, multiply and divide, sign and zero extension;
- calls, jumps and conditional jumps, direct and through a table;
- `rep movsb`/`stosb`, `syscall`.

That is a regular subset of x86-64, and an assembler for exactly it - no
more - is the job. `cv8.c` stays as it is: the portable engine, for the
ARM board and anything else, and the first step of the bootstrap.

## 3. The design proposed

**A Forth-syntax assembler**, in the tradition GOALS.md names (the
classic `ASSEMBLER` wordset, `CODE ... END-CODE`): operands first, then
the mnemonic, each mnemonic a Forth word that lays down its bytes.

    \ relfasm64.S today            \ the same, sketched (syntax: M0)
    L_dup:  sub r13, CELL          L: L_dup   r13 CELL # sub,
            mov [r13], r12                    r12 r13 ) mov,
            NEXT                              NEXT,

- **Macros are Forth words.** `NEXT`, `PUSHT`, `POPT`, `SLOT`, `RPUSH`
  are colon definitions that assemble; `.equ` constants are `CONSTANT`s.
- **Labels and jumps**: forward references resolved when the label is
  defined; a short jump where the distance fits a byte, found as GNU
  `as` finds it - by iterating until nothing changes size.
- **The tables come from `opcodes.tab`**, read by Forth - the dispatch
  tables stay generated from the one source, without the shell script.
- **The ELF file** is what relfasm64.S already writes by hand - a header
  and two program headers laid down as data - so it moves over as data.
- **The output is a file**, written with the primitives `cross.4` uses
  to save a kernel.

## 4. How it is checked

The same way everything here is: **byte for byte**.

1. The Forth assembler, on the C engine, assembles the engine source:
   the result must be **identical to today's relfasm64 built by GNU as**.
   That is the hard test - `as` makes its own choices (the shorter of two
   encodings, `disp8` over `disp32`, which opcode for `mov reg, reg`),
   and the Forth assembler must make the same ones, deliberately.
2. The engine it produced runs the same program and produces **itself**:
   the fixpoint, as the kernels have one.
3. Every suite passes on it - it is the same bytes, so `make verify`'s
   `asm:` rows already say so - and new rows say the two builds agree.

## 5. Milestones

- **M0 - encoder.** The 53 mnemonics and their operand forms, each
  checked against GNU `as` on the same instruction: assemble a list of
  every instruction form the engine uses both ways, compare the bytes.
  **The list exists** (Iteration 537): `tools/asm-corpus.py` disassembles
  the linked engine's code - 2,765 instructions once the macros are
  expanded, 11,024 bytes - into **450 distinct shapes**, each with one
  real instance and the bytes GNU `as` chose, in `tests/asm-corpus.txt`;
  every line's bytes occur whole in the built engine. One choice already
  visible: an absolute address is encoded with a SIB byte and no base
  (`48 89 04 25 disp32`), not RIP-relative.
- **M1 - a program.** An ELF file that exits with status 42, written
  entirely from Forth.
- **M2 - the engine source in Forth syntax.** A one-time, mechanical
  translation of relfasm64.S (a converter script, kept only until done),
  then read over by hand.
- **M3 - identical.** The Forth build equals the GNU `as` build.
- **M4 - the fixpoint.** The engine it built builds itself, identical.
- **M5 - one source.** relfasm64.S retired; the Forth source is the
  engine's only source; `make` builds the assembly engine with relf.

## 6. Risks

- **Matching `as` byte for byte** is where the time goes: every
  encoding choice `as` makes for this subset has to be found and made
  the same way. M0 exists to find them all early, one instruction form
  at a time, before the engine is involved.
- **Two sources during M2-M4**: relfasm64.S and its Forth translation.
  The identity test (M3) holds them together until M5 retires one.
- **The ARM board is not self-hosted by this**: an ARM assembler and an
  ARM engine would be a project of the same size again. Proposed: not
  now (Q17).
