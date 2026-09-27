# TESTING-IDEAS.md - new ways to find what relf gets wrong

The user (Iteration 552): more tests - specs we missed, other POSIX
implementations, fuzzing - "unleash your imagination, think outside the
box, don't follow standard patterns". What we have: CORE (2,136 checks,
both engines identical), a differential suite (131), a matrix against
bash and dash (421), POSIX cases (48), mrsh (21), a pty suite (23), 83
shell test files (874 assertions), a crash fuzzer (tools/crashfuzz.py),
reproducible images, a double-compile with gforth. Every one of them
compares relf with an answer somebody wrote down, or with one or two
other shells. The ideas below mostly do not; each is aimed at a class
of bug the present suites cannot see. Marked **first** are the ones to
build first - cheap, and likely to find something.

## Oracles that need no expected answer

1. **Built, 557: tools/metamorph.py.** The differential suite's 131
   scripts, nine rewritings each, relf against itself, dash as the judge
   of neutrality: 1,170 rewritings, 0 findings on both engines. Scripts
   reading $LINENO are set aside - every rewriting moves it. First written:
   **Metamorphic testing** (**first**). A shell program and a rewriting of
   it that means the same must print the same. Rewrite every test script
   by transformations that preserve meaning, and compare relf with
   ITSELF: the body wrapped in `{ ...; }`, in `( ... )`, in `eval '...'`,
   in `if :; then ... fi`, in a function called once, fed through a here-
   document, sourced with `.`; `$(...)` and backquotes exchanged; `[` and
   `test` exchanged; a redirection moved from after a command to before
   it; comments, blank lines, `:` and backslash-newlines added; variables
   renamed consistently. No reference shell, no expected output: any
   disagreement is a relf bug, in the parser or the executor.
2. **Built, 563: tests/shell/run-round-trips.** set, export -p, trap and
   alias listings, read back in by a fresh shell, list the same, with
   every awkward value; both engines and 32-bit. First written:
   **Round trips** - POSIX says `set` prints variables, and functions
   print, in a form the shell can read back. Print every function the
   test scripts define, re-read the text, and require the same behaviour;
   print again, and require the same text (a fixpoint, like the images).
   A strong test of the parser and the printer together.
3. **Built, 555: tools/twin-fuzz.py.** 3,000 random programs - 50 words
   and guarded phrases, values leaning to the edges - on the C engine and
   the assembly engine: 0 differences. Its probes of what Forth leaves
   undefined agree too (MIN -1 / gives MIN without a trap; shifts of 64
   or more take the count mod 64, as x86 does), and found that a zero
   divisor kills the process with SIGFPE on both - inside the shell,
   `forth '1 0 /'` ends the shell (QUESTIONS.md Q21). First written:
   **The engines as each other's oracle** (**first**): random, well-
   typed Forth programs - a generator that knows each opcode's stack
   effect, so every program is valid - run on the C engine and on the
   assembly engine; any difference in the final stack or the output is
   a bug in one of them. Stack effects become a column of opcodes.tab,
   which documents them too. And the width-independent words the same
   way across 64- and 32-bit cells.
4. **Built, 566: tools/asm-fuzz.py** (and the verify row asm:fuzz-mismatches).
   First run: memory push/pop/xchg silently mis-assembled - fixed; now 0
   mismatches, the rest exact or refused loudly. First written:
   **The assembler against GNU as, at random**: the corpus tests the 456
   instruction shapes the engine uses; generate random instructions -
   every register, displacement size, immediate - in asm64.4's syntax
   and GNU as's, and compare the bytes. Finds what the engine does not
   use yet, before it does.

## A parliament of shells

5. **Built, 558: tools/parliament.py.** The 131 differential scripts to
   seven shells - dash, bash --posix, yash, posh, mksh, ksh93, busybox
   ash (all installed here already; the POSIX suite uses them too, but
   only where they are unanimous). 112 scripts have a majority of 5 or
   more, and relf is with it in all 112; bash, the differential suite's
   oracle, is never outvoted. 19 split - $'...', job status, arithmetic
   extensions, builtins-269 with seven answers from seven shells - where
   the suite's choice of bash decides relf's answer. First written:
   **The consensus oracle** (**first**): install every POSIX-ish shell
   the system offers - dash, bash --posix, busybox ash and hush, mksh,
   yash (the strictest reading of POSIX), posh, ksh93, zsh in sh
   emulation, oksh - and run every case through all of them. Where relf
   differs from the MAJORITY, it is probably wrong; where the majority
   itself splits, the spec is ambiguous there, and the case belongs in
   DASH.md's list of choices, decided on purpose.
6. **Built, 559: tools/shfuzz.py.** 1,000 programs over two seeds, 0
   findings; calibrated with yash in relf's seat (9 findings in 150,
   each shrunk to one line). First written:
   **Grammar-based differential fuzzing**: generate random programs from
   POSIX's shell grammar (a safe vocabulary: echo, printf, :, test,
   arithmetic, case, bounded loops, functions, redirections to temporary
   files), run them through the parliament, and shrink each disagreement
   automatically (delta debugging) to its smallest form before a human
   reads it.

## Tests that measure the tests

7. **Built, 558: tools/mutate.py.** One opcode in shell.4 or tree.4
   swapped for one of the same size and stack effect (3,699 sites);
   each mutant a shell of its own, run through the 131 differential
   scripts, its survivors then through the whole shell suite
   (MUTANTS_KEEP). 30 mutants: 15 killed by the scripts, 4 more by the
   suite, 11 survived both. Survivors need reading, not counting: the
   @/C@ and !/C! swaps on values under 256, and OR/XOR on bits that do
   not overlap, cannot change anything (equivalent); + for - in
   LITERAL-FITS? looked like a gap and a test written for it did not
   kill it - the token buffer is sized to the line, so its "no" is
   unreachable (equivalent too). Unread yet: DO-BG, SPLIT-ASSIGN-AT,
   COPY-LITERAL (each + and -) - read at 559: DO-BG a real gap, closed
   by a pty case that kills it; the other two without visible effect. First written:
   **Image mutation testing** (**first**): mutate the compiled shell
   image, not the source - one opcode swapped for another with the same
   stack effect, a literal nudged by one, a branch's sense flipped - and
   run the suites. A mutant that survives marks behaviour no test
   checks; the word it lives in is named. Mutation testing on threaded
   code is cheap - no recompiling - and unusual.
8. **Built, 558: tools/self-harness.sh.** relf interpreting every
   tests/shell file itself: 84 files, 940 assertions, 0 failed - both
   engines. First written: **relf tests itself**: the harness - tests/shell/run-all, lib.sh,
   tests/verify, thousands of lines of real shell - run BY relf instead
   of dash. Every result must be the same; a difference is a relf bug
   found in real-world code nobody wrote as a test.

## The world, not the spec

9. **Begun, 563.** zlib's configure: identical to dash, both engines.
   ncurses's (32,301 lines, Autoconf 2.52): failed at 563 - a here-
   document holding \` in backquotes lost its body - fixed at 565; now
   1,040 of 1,041 generated files identical to dash's. First written:
   **Real scripts**: autoconf `configure` scripts (zlib's, a GNU
   project's) with relf as the shell, their results compared with dash's;
   the Oils project's spec tests (a large, curated corpus that already
   runs against many shells); Rosetta Code's POSIX sh solutions; shell
   quines, which test quoting where it is subtlest.
10. **Built, 563: tools/chaos.py and run-signal-storm.** Signal storms
    (USR1 CHLD WINCH ALRM INT, one every 2 ms) over pipes and command
    substitutions: every trap run, every sum exact, both engines. The
    limits half was done by strange-env.py (560). First written:
    **Chaos**: signals at random instants in pipelines and loops (SIGINT,
    SIGCHLD, SIGWINCH, SIGTSTP storms); input that arrives a byte at a
    time; tight limits (`ulimit -n 8`, `-v`, `-s`), a full disk (a tiny
    tmpfs), no memory - the shell must report and go on, never hang or
    crash. A soak run of hours watching for leaks: memory, descriptors,
    zombies.
11. **Built, 560: tools/strange-env.py.** Ten probes against dash: 0
    crashes now - the first run found the assembly engine's shell dying
    under any `ulimit -v` below 1 GB (fixed); open: PATH unset, and
    `set` with ten thousand imported variables. First written:
    **Strange environments**: `env -i`; ten thousand environment
    variables; a directory deeper than PATH_MAX; HOME unset; arguments
    carrying every byte value; umask 777; each must give dash's answer.

## Specs we have not held relf to

12. **The Forth 2012 test suite** - **begun, 552**: fetched
    (github.com/gerryjackson/forth2012-test-suite) and run on relf with
    extend.4: the preliminary tests pass (57 of 57) and the CORE word set
    runs to its end; the next file stopped at `:NONAME`, and an error
    ends the whole include chain, so no later word set ran. A static
    survey of what each set's tests use - noisy, it counts words from
    comments too - shows about sixty standard words missing: CORE EXT
    `:NONAME 2>R 2R> 2R@` and the number prefixes `$FF #12 %101 'c'`;
    DOUBLE `2LITERAL 2ROT 2VALUE 2VARIABLE D- D.R D0< D0=` ... and
    literals like `12.`; FACILITY's structures `BEGIN-STRUCTURE FIELD:
    CFIELD: +FIELD END-STRUCTURE`; STRING and FILE `/STRING -TRAILING
    FILE-STATUS FLUSH-FILE`; TOOLS `AHEAD CS-PICK CS-ROLL N>R NR>
    NAME>STRING NAME>COMPILE NAME>INTERPRET`; SEARCH `GET-CURRENT
    SET-CURRENT`; LOCALS `(LOCAL)` and `{: :}`; the whole BLOCK set.
    Each is a decision, not a to-do - minimalism first. Next: run each
    word set on its own, so each reports its real failures.
    (First written:) **The Forth 2012 test suite** (**first**; Gerry Jackson's, the
    standard's own): CORE is what we run; CORE EXT, DOUBLE, EXCEPTION,
    FACILITY, FILE, LOCALS, MEMORY, SEARCH, STRING, TOOLS are not. Each
    word set either passes, or its failures become a list of words relf
    lacks or gets wrong - a decision each.
13. **Spec archaeology**: every example in POSIX's Shell Command Language
    and its rationale turned into a test with the behaviour the text
    states; and the Austin Group's interpretations of it, where the
    committee settled what the text left open.
14. **The line editor against bash's**: the same keystroke streams
    through a pty into both; the command lines they produce compared, for
    the keys both claim.
