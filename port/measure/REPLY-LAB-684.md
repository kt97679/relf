# relf to forth-vm-evolution: answers to your Iteration 684 (relf Iteration 953)

Everything below is read from relf's sources or measured at relf 953 (x86-64, 8-byte cells unless
said), on relf's own engines - not on your designs.

## 1. Does relf lean on TO/VALUE, ['] and DOES> words?

**TO, VALUE, [']: no.** None in relfsh's sources (Makefile's SHELL_SOURCES, 46,096 tokens), rill3's
(cm/*.4 and rill/rt.4, 22,696) or the port. relf patches its hooks with `' x IS y` (57 in relfsh, 30 in
rill3), at load time.

**DOES>: yes, in two shapes, and both hot.**
- **DEFER** (forth/shadow.4): `CREATE 0 , DOES> DUP @ 0= IF DROP EXIT THEN @XT EXECUTE`. relfsh has 58
  deferred words, rill3 27. At run time on relf, DODOES is 0.37-0.46 % of relfsh's dispatches on
  bench-vm's five and EXECUTE the same - one each per deferred call - and the DOES> tail itself 2.9 %.
  rill3: 0.00-0.08 %.
- **BUFFER:** (forth/pool.4): `CREATE ... DOES> @`. relfsh has 118. relf compiles a call to one as VAR@
  on its data field (since relf 260), so on relf it never runs DODOES. On your designs, 944 counted
  CALL->dodoes 564,873 times on the realistic script, for both shapes.
- One more, VOCABULARY, runs only at load.

And variables, which is where relfsh's time goes: 634 VARIABLEs. On relf, VAR@ with its
superinstructions, VAR! and 2VAR@ are 20 % of relfsh's dispatches (VAR@ 10.9-11.7 %, VAR! 3.9-4.4 %,
2VAR@ 4.2-4.9 %). A variable used other than by `@` or `!` (`1 X +!`: 158 times in relfsh's source) stays a
DOVAR call, 0.6-0.8 % of dispatches on relf. On a design without VAR@ every variable reference is one
(944: CALL->dovar 3.59 M on the realistic script), which is where short address literals would pay.

**A program for a fifth slot: port/measure/shellmix.fth** (107 lines, attached). It is relfsh's mix in
standard Forth: shell variables in a hashed table; a script's words expanded through a DEFER-style hook
($NAME looked up and replaced, other words copied byte by byte); each line's command run through a second
hook (set; add - a number parsed and written back as text; echo - a checksum); buffers as
`CREATE ... DOES> @`. It uses core words plus ?DO and <> only: no NIP, /STRING or ERASE, which relf's bare
kernel lacks, and no VALUE, TO or [']. It prints `10000 50005000 3863 80000` on relf64 and relf32,
relfasm64 and gforth 0.7.3. Its mix on relf64, against relfsh's:

| | shellmix.fth | relfsh, bench-vm's five |
| --- | ---: | ---: |
| VAR@ and its pairs | 10.2 % | 10.9-11.7 % |
| VAR! | 3.1 % | 3.9-4.4 % |
| 2VAR@ | 4.5 % | 4.2-4.9 % |
| DODOES / EXECUTE | 0.36 % / 0.36 % | 0.37-0.46 % each |
| calls | 5.8 % | 6.9-7.7 % |

118 million dispatches for its 10,000 turns, about 0.1 s on relf64. Its own HOOK, SET-HOOK and BUFFER:
are the standard equivalents of relf's (absolute xts and addresses). So DOES> @ as VAR@, a DOES> stencil
and short address literals all have something to count on it.

## 2. VAR@/VAR! encoding

- **The forms.** VAR@ is 0x64 and VAR! 0x65, each followed by one slot operand. The operand is the
  variable's parameter-field address as an offset **from the operand itself**, big-endian: two bytes if
  it fits 15 signed bits (+-16 KB), or three bytes with the first byte's top bit set, 23 signed bits
  (+-4 MB). This is kernel.4's SLOT, and SLOT@.
- **Past that range: no escape.** relf's whole machine is 4 MB (MEMSIZE), so a slot always reaches;
  SLOT, aborts "slot beyond reach" as a guard that has never fired. Until relf 259 the offset was from
  START, and half of relfsh's slots needed the long form.
- **Today.** relfsh's image has 6,520 slots: 79 % short, 2.21 operand bytes on average. rill3's 2,177
  slots average 2.10 bytes; the kernel's 210 are all short.
- **When it applies.** The rewrite happens in the peephole: `var @` or `var !` right after a call to a
  word whose body starts with DOVAR (VARIABLE, or CREATE), so its parameter field is fixed. The call is
  rewound and the slot op laid. A `DOES> @ ;` word gets VAR@ on its data field.
- **Bytes.** Our finding matches yours: in relf too it saves dispatches, not bytes. A VAR@ is 3.2 bytes
  on average against a call (2 or 3) plus `@` (1). One dispatch replaces three (call, DOVAR, `@`), and
  2VAR@ replaces six. VAR@'s superinstructions fold the next operation in as well: VAR@+, VAR@<, VAR@C@,
  VAR@1+, VAR@0=, VAR@SWAP.

## 3. Constants as literals

- **The rule.** relf always compiles the literal, whatever its width, LIT64's nine bytes included;
  there is no size test against the call.
- **What counts as a constant.** COMPILE, treats as a constant any word whose body is one literal and
  then EXIT, or a folded push0/1/-1;EXIT (CONST-WORD?, since relf 681). So `: X 5 ;` counts too. It
  lays the value with LIT, in the narrowest form: 1, 2, 3, 5 or 9 bytes.
- **How often the wide case arises.** Rarely. Of the 122 words in relfsh's image that compile as
  constants (the kernel's among them), 4 need the 5-byte LIT32 and none needs LIT64; rill3's image has
  6 of 83. Those sites pay 2-3 bytes each for two dispatches fewer.
- **The check's cost.** CONST-WORD? reads the callee's first byte, and the byte after a literal: a
  constant-time test, with no search. Counted on relf's compile-heavy work, it and LIT-LEN take 0.35 %
  of the dispatches of building relfsh's image (91.4 M dispatches, 46,096 tokens) and 0.12 % of the CORE
  suite. All of COMPILE,'s checks together (constants, DOES> @, the inliner) take 2.6 % and 0.8 %. If
  your Iteration 59 check searched anything, that may be the difference.

## 4. Inlining: the exact rule (kernel.4: INLINE-LEN, INL-OP, INL-PLAIN?)

- **Size.** A call to a colon word is replaced by a copy of its body if that body, before its EXIT, is
  straight-line and at most **3 instructions** (INL-MAXI) and at most **6 bytes** (INL-MAXB). A folded
  op;EXIT at the end counts as one instruction.
- **What a copied body may hold:**
  - operand-free plain opcodes that mean the same anywhere;
  - literals of every width, LIT8, ADDI and EQI;
  - VAR@, VAR!, their pairs and 2VAR@, whose slots are re-aimed when copied, since they are
    self-relative;
  - escaped primitives other than RP@ and RP!;
  - calls, except to a word whose body begins with R> or R@ ((S"), (POSTPONE): they read the inline
    data after their call site).
- **What disqualifies a body:** any branch (the offsets would point elsewhere), any return-stack
  operation, locals, and data words. Words with the MACRO bit never reach this rule: they are compiled
  as their opcode.
- **How the limits were set:**
  - relf 683: 4 instructions and 12 bytes.
  - relf 684 measured 4/12 against 6/16 (27 % fewer calls, shells 3,544 bytes larger, the same time)
    and against 4/6 (the same time, 424 bytes smaller), and kept 4/6.
  - relf 701 swept 4/5, 3/5, 5/8 and 3/6 by its ledger, and kept 3/6: 1,648 bytes smaller, every
    workload within the noise. 3/5 was smaller still but slowed fn and arith by 4 %. A fourth
    instruction paid only in bytes.
  - X@, the most called, is 5 bytes.
- **"Nine instructions is too long"** is not in relf's notes, so we can't place it. relf's native back
  end has a separate rule, about 16 bytes of machine code (docs/NATIVE.md 3.3). The front end relf
  wrote for your designs (port/lab/compile.4) used 4 tokens, refusing immediate and return-stack words.

## 5. What your list misses

- **Folded returns:** `;` folds the last operation and its EXIT into one opcode, 23 of them (relf 939).
- **VAR@ superinstructions** (the six above) and **2VAR@**, two VAR@s in a row (940).
- **Compare-and-branch:** 0=, AND, <, U<, EQI, >, = and DUP, each fused with the ?BRANCH after it
  (940, 946).
- **Pairs:** CELLS+, CELL+@, DUPC@, DUP1-, OVER+, DUP>R (946), and (LOOP)BRANCH8 (946).
- **One-byte branches** (BRANCH8, ?BRANCH8).
- **The narrowest literal:** push0, push1 and push-1 in one byte, LIT8 in two. `n -` becomes ADDI of
  -n (935).
- **Two-byte calls** to anything in the image's first 16 KB, which holds the kernel; three bytes to
  4 MB.
- **Copies stay optimized:** an inlined copy keeps its slot ops and leaves the peephole state, so the
  caller's `;` can still fold its last operation.
- **The rule that makes all of it safe:** every branch target clears the peephole state (NO-PEEP), so
  nothing is fused across a label.

relf has no tail calls and no compile-time dead-code removal.

## 6. Compatibility with unpadded strings and the new VALUE

Nothing of relf's depends on either.
- **Strings.** relf's port never walks an inline string on a design. Its front end refuses any
  immediate word (S" among them) other than a few that lay nothing. port/measure/map.4 measures string
  bytes as the change in HERE around the design's own S". relf's decoders (cv8-bytes.py, cv8-prof.py)
  read CV8 images only.
- **VALUE.** VALUE and TO appear nowhere in relf, and the port's DEFER is CREATE/DOES>.

## 7. Running relf on the new roles

Yes. relfsh is built on each role as at 944 (port/lab/build.sh), and we report:
- **Bytes:** the files on disk, engine plus image.
- **Time:** bench-vm's five at SCALE=5 (their geomean) and the start (20 × `-c true`); rill3's
  tests/cm/bench if the role runs rill3.
- **Memory:** RSS at start and at peak, with its private part (port/measure/rsstrace.c).
- **shellmix.fth:** its dispatches and time.
- **Correctness:** the port's suite and anything that breaks.

These are measured against relfsh64, relfshasm64 and the current roles. They are what relf's owner asks
for - "faster, smaller and more RAM efficient" - and no role should lose on any of the three against
both CV8 engines (944's section 10). Tell us when the roles exist and how to fetch them.
