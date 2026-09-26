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
  **The list exists** (Iterations 537, 540): `tools/asm-corpus.py`
  reads GNU `as`'s own listing of relfasm64.S, macros expanded - each
  line's address, bytes and source - and takes the bytes from the linked
  engine: **2,577 instructions, 10,302 bytes, 453 distinct shapes, 56
  mnemonics**, each shape with one real instance, its bytes and its
  source text, in `tests/asm-corpus.txt`. (537's version disassembled
  instead, and took the data inside the code for instructions.) One choice already
  visible: an absolute address is encoded with a SIB byte and no base
  (`48 89 04 25 disp32`), not RIP-relative.
  **The encoder** (541-542): `asm64.4`, 255 lines - **all 452 shapes
  assemble to GNU `as`'s bytes**, tested by `tools/asm-test.py`, which
  translates each corpus line into asm64.4's syntax and assembles it on
  relf at its own address. On the way the engine lost its ten RIP-
  relative addresses (every other address in it is absolute; nine more
  bytes, one less form for the assembler to know).
  *SP-Forth's assembler* (the user's pointer; github.com/rufig/spf,
  lib/asm/486asm.f, from Win32Forth): a PREFIX assembler - `MOV [EBP],
  EAX`, `LEA EBP, -4 [EBP]` - that reads like GNU source, made to work
  in Forth by assembling each instruction when the next one begins. For
  x86 only, 32-bit (no RAX anywhere), so not reusable here. Its look
  would make M2's translation nearly one-to-one; the price is that
  deferral, and the order its end (a label, END-CODE) must flush.
  asm64.4 stays postfix - each mnemonic finishes itself - as the simpler
  of the two.
- **M1 - one pass, and a program.** The user's requirement (543): the
  assembler works in ONE pass, forward references resolved as cross.4
  resolves its FORWARD words. The design, from that and the assemblers
  examined (FINDINGS.md 5):
  - *Labels*: `L: name` defines one at the current address. A jump to a
    label not yet defined lays down its displacement as a placeholder and
    leaves a fixup - where, and how wide; defining the label patches
    every fixup waiting for it. Numeric local labels for the translated
    source's `1f`/`2b`: `1 L:` defines, `1 F` and `1 B` refer forward and
    back, as GNU as's do. At the end, a label still waited for is an
    error, as cross.4's RESOLVE makes one of an unresolved FORWARD.
  - *Sizes, in one pass*: a jump BACK knows its distance and takes the
    short form where it fits - which is GNU as's choice too. A jump
    FORWARD cannot know it: short unless the source says `NEAR` before
    it. A short forward jump its label turns out too far for is an
    error at the label - never a wrong byte. The translation (M2) writes
    `NEAR` wherever GNU as chose the long form, so the output stays
    identical to its.
  - *Structured control flow* (`IF, THEN, BEGIN, UNTIL, WHILE, REPEAT`
    with condition codes, as gforth and lbForth have): optional sugar for
    code written by hand, on the same fixups; not needed by M2.
  - *Families by loops*: the sixteen conditional jumps, setcc, cmovcc
    defined by one counted loop each, as gforth does.
  **Working** (544-545): a program with every kind of jump - back to a
  local label, forward to one, forward to a named one, a NEAR one over
  200 bytes - assembles in one pass to GNU as's 237 bytes exactly
  (tests/asm-labels.4 and .S; tools/asm-test.py runs it after the
  corpus, which it now regenerates first).
  Then the program: an ELF file that exits with status 42, written
  entirely from Forth. An ELF file that exits with status 42, written
  entirely from Forth.
  **The program, done** (546): tests/asm-exit42.4 lays down every byte of
  an ELF executable - header, program header, code - its entry point and
  size forward references (absolute fixups, `Q,+`), writes it, and makes
  it executable with CHMOD, a new primitive (both engines create files
  0644); it runs and exits 42. tools/asm-test.py runs it with the corpus
  and the labels.
- **M2 - the engine source in Forth syntax.** What the survey of
  relfasm64.S (546) says the translation has to carry, beyond the 454
  instruction shapes:
  - *Eight macros* become colon words that assemble, parameters from
    the stack: `PUSHT rax` -> `rax PUSHT,`; `FLAG l` pastes a condition
    into a mnemonic (`set\cc`) -> the condition's number, `12 FLAG,`;
    `SYSCALL1 SYS_close` -> `SYS_close SYSCALL1,`. Written by hand - they
    are eight - and the translator maps their uses.
  - *Local labels in macros* (SLOT's `1f`): `1 F` and `1 L:` resolve as
    each expansion runs, as GNU as resolves them per expansion.
  - *A forward label inside a memory operand*: NEXT jumps through
    `[dispatch256 + rax*8]`, and the tables come after the code - an
    absolute 32-bit fixup, beside the relative ones and 546's absolute
    64-bit one.
  - *89 `.equ`s*, infix expressions (`MEMSIZE - RSTACK_BYTES - ...`),
    some referring to labels (sizes): constants in postfix, or `Q,+`
    fixups where a label is in them.
  - *Data*: the ELF header, the tables, the OPEN-FILE modes, strings;
    `.balign`'s two bytes of padding, in GNU as's own fill.
  - *The generated includes* (relfasm-ops.S, relfasm-consts.S) are
    translated with the rest at first; M5 has Forth read opcodes.tab.
  **Begun** (546): tools/asm-translate.py, first version - the source in
  order, #includes expanded; `.equ` to CONSTANT with the expression in
  postfix and the names kept; labels, instructions (symbols by name, a
  forward jump GNU as made long to get NEAR - next), macro uses mapped,
  data, strings; multi-line comments and the macro definitions (to be
  written by hand) skipped. Of 2,631 lines, 9 are left, all directives:
  two `.balign` (an ALIGN, with GNU as's own NOP fill is needed), two
  `.rept` blocks in the generated tables (to unroll), one `.if/.error`
  layout assertion (to become a check in a colon word). Then: the macros
  by hand, the header and footer (LABEL declarations, END-ASM, the file
  written and CHMODed) - and M3, the first comparison with the engine. A one-time, mechanical
  translation of relfasm64.S (a converter script, kept only until done),
  then read over by hand.
- **M3 - identical.** The Forth build equals the GNU `as` build.
  **Done at 548**: relfasm64.4, translated from relfasm64.S, assembled by
  relf on the C engine, is relfasm64 byte for byte - 15,176 bytes.
- **M4 - the fixpoint.** The engine it built builds itself, identical.
  **Done at 548**: that engine, run on the same program, writes itself
  again, identical, executable. The x86-64 engine rebuilds itself with
  nothing but relf, its kernel and its Forth sources. `make verify` rows
  asm:translation, asm:self-assembled, asm:fixpoint check it every run.
- **M5 - one source. Done at 549** (A19): relfasm64.4 is the engine's only
  source, its comments carried over from relfasm64.S (419 lines of them);
  the tables are relfasm-ops.4, which gen-opcodes.sh writes from
  opcodes.tab; `make relfasm64` runs relf on the C engine over it - no
  assembler, no linker - and the result is the last GNU as build byte for
  byte. relfasm64.S, the translator and the corpus generator are retired
  (git keeps them); the corpus is frozen, with its symbols, so the encoder
  stays held to GNU as's bytes. What 548 found M5 needed:
  the translation keeps no comments (relfasm64.S is heavily commented -
  the translator must carry them over); the dispatch tables still come
  from gen-opcodes.sh's GNU-syntax output (Forth should read opcodes.tab);
  the translation takes NEAR from GNU as's listing (the Forth source then
  keeps its NEARs, written in it); and the build must bootstrap without GNU
  as - from the C engine (gcc), or from a committed engine binary, as the
  kernels are seeds. QUESTIONS.md Q20.
- **M5 (the plan as proposed).** relfasm64.S retired; the Forth source is the
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
