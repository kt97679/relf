# Rill's roadmap (Iteration 762)

The order comes from what the three pilots measured
(docs/PILOT-NATIVE-BY-SOURCE.md): the cheapest fixes first, then the cause
behind most of Rill's defects and much of its slowness, then the open
gaps, then speed, then putting Rill to work. Each phase is measured as the
last iterations were: the search's four criteria (docs/RILL-SEARCH.md),
and defect logs on real scripts.

## Phase 1: catch the slips the pilots found - done in 762

- A bare word that names a variable, in an expression, is an error in both
  compilers ("x is a variable - $x, or "x" for the text"); in a command's
  arguments a bare word is its text, as before. It catches the three `$`
  slips of the pilots, and found a fourth no output check had: dead-words'
  `[e for e in ...]`, a list of the text "e", hidden while no IS line was
  dead.
- tools/rill-forth-lint.py reports a name defined again that the kernel
  has, or, in a program (.fth), that the runtime has - the pilots' CURRENT,
  KILL, BASE and PARSE; and it found three in the compiler itself, DEPTH,
  LIT and SRC, now SM-DEPTH, TEXT-LIT and RS-SRC. `[']` in a definition is
  no longer reported in a program loaded when it runs.
- tests/rill/pilots.rill holds each defect the pilots found in Rill;
  tests/rill/errors/ the programs both compilers must reject;
  tests/rill/pilots/is-lines.4 the IS-line case dead-words' three versions
  now agree on.

## Phase 2: kinds for lists and records - designed in 763 (docs/RILL-KINDS.md)

The first attempt, kinds decided binding by binding, broke on reused names
and showed the order of binding was never sound for loops; the design is now
one kind per variable over its whole scope, inferred by a first pass.


Every value taken out of a list or record is a boxed item: four of Rill's
thirteen pilot defects were that, and so is much of its time against the
hand-written Forth (1.4x). A kind inferred for each list and record field
where it can be known - from literals, pushes, a def's result - so a list
of texts holds texts: conversions at compile time, mismatches caught
there, fewer boxes and kind checks at run time. The largest piece of work
here; through the search, so its cost in source and generated Forth is
measured.

Step 3 (766): element kinds for lists, in the Python compiler behind gene
elemkinds - correct on the corpus, 24 of 40 lists typed, and no faster.
Step 4 (767): lists of a known element kind stored unboxed, gene unbox -
correct, and slower (items boxed anew wherever the kind is not known).
Both genes taken out by the search's rule; their code is in the history
(docs/RILL-KINDS.md). Phase 2 ends with `infer`: sound kinds. Phase 4
begins with a profile of where the dispatches go, not with a guess.

## Phase 3: the gaps still open

`continue` in while loops; `return` inside a loop that has a `continue`;
`a[i][j] = v`; defs as commands with arguments, or a clear error; a
built-in `format`, so scripts stop calling printf; runtime errors that name
the Rill line - behind a debug switch if they cost speed.

## Phase 4: speed - begun from a profile in 768 (docs/RILL-PROFILE.md)

tools/rill-profile.py: the matcher was three quarters of native-by-source;
rebuilt one word per instruction, the program linked - 51 % fewer
dispatches there, 37 % less time; dead-words 5.7 % fewer from the arena and
list fixes.


Typed lists (phase 2); regular expressions compiled to Forth rather than
interpreted by backtracking (the first pilot's time); temporaries released
(the arena frees nothing); Rill on relf's native kernel rather than the
VM - likely the largest single gain, waiting on forth-vm-evolution
(GOALS.md 12).

## Phase 5: Rill at work

The repository's Python tools and shell scripts rewritten one at a time,
each held to the original's output byte for byte; smallest and most used
first, starting with run-utf8 and gen-opcodes. relfsh running Rill scripts
itself, the shell and the language on one runtime. Once the rewrites are
done, the Python compiler frozen as a regression oracle and only the
Forth compiler grows.

## Phase 6: a reference

One Rill reference - syntax, the kind rules, the library - from
docs/SHELL-LANGUAGE.md's parts; each settled decision in RILL-LEDGER.md.

## Phase 3 progress (Iteration 779): break, continue and return in loops

Two crashes found on the way and fixed: `break` in a while loop compiled to
LEAVE, which only leaves DO loops - ignored on its own, a crash nested in a
for loop; `return` from inside a for loop left the loop's frame on the
return stack - the def returned to a garbage address. Neither was in the
corpus. Now:
- return unwinds the loops of the word it is in: UNLOOP for each DO loop, and
  a counted loop's two cells dropped under the value;
- a while loop whose body holds break or continue (at its own level) makes
  the body a word, as a for loop with continue does (745); its stop flag is
  checked before the condition, so the condition is not evaluated again;
- return inside such a body word sets R-RET with the value in R-RETV and
  leaves the word; each loop around stops and passes it on, and the def
  returns R-RETV.
tests/rill/flow.rill against tests/rill/flow.py (Python): 13 lines, every
combination. Every example compiles to the same Forth as before.

## Phase 3 progress (Iteration 780): a[i][j] = v; items to library calls; defs as commands

- `a[i][j] = v`, `+=`, `-=`, to any depth: the container read down the chain
  (the first index by the variable's kind, each later one R-INDEX-ANY), the
  last index assigned through R-ASSIGN-ANY. The Forth compiler reads each
  index's tokens again where its code goes. tests/rill/chain.rill as Python.
- Found on the way, a crash: join, slice, sum, at and sort-by passed an item
  (a list read out of a list or record) on still boxed. Unboxed now, as
  keys, max, min and the rest have been since 758.
- A def called like a command with arguments: both compilers name it and
  show the call - `greet is a def: call it as greet(...)`
  (tests/rill/errors/def-args.rill).

Still open in phase 3: a built-in format; run-time errors naming the Rill
line. Phase 5's three waiting rewrites (gen-opcodes, pack-results,
run-utf8) need abs() and more of the library first.

## Phase 3 done (Iteration 781): format, and errors that name the line

- `format(f, a, ...)`: Python's % formatting - s d i f x X %%, the flags
  - 0 + and space, width and precision; too few or too many values are
  errors, as in Python. One difference, on purpose: f rounds Rill's exact
  decimals half away from zero, where Python rounds the binary float - they
  differ only on an exact tie (1.005, 2.25). tests/rill/format.rill as
  Python.
- A run-time error names the line of the statement running, innermost first:
  `rill: index 5 past a list of 3 (line 4)`. Nothing is paid at run time:
  each statement marks, as it is compiled (`[ n R-MARK ]`), where its code
  starts; an error looks down the return stack for the innermost address in
  the script's own code. Gene lines (on). Every example compiles to the same
  code as before once the marks are taken out. The driver no longer adds
  `rill: error -40xx` after a message Rill has printed itself; the kernel's
  own errors (a crash, a division by zero) still print only their number -
  the return stack is unwound by the time they are caught.

## Phase 5 (Iteration 782): gen-opcodes in Rill, as the shell script

examples/rill/gen-opcodes.rill now runs, and in all four of its modes
(generate, --forth-ops, --forth-consts, --check) says what
tools/gen-opcodes.sh says, byte for byte, with the same status; tests/rill/run
checks --check. Rill took ~29 ms where the shell took 5-7 (most of it
compiling the script); --check 141 ms against 113. What it needed:
- abs(): a number's or decimal's absolute value; a path's absolute form, as
  Python's abspath. dir(): as dirname.
- == and != compare lists and records by what they hold, as Python (records
  in any order; 1 == 1.0, inside lists too).
- at() on a list (the item, negative from the end, or the default) and on an
  item, besides a record. It crashed on a list.
- a comprehension's `if` takes a value's truth, as an if does: a match() or
  a text filtered nothing before - every item passed.
- a newline inside [ ] does not end the statement, as Python's.
- number() reads 0x hex, as the shell's $((...)), in either case.
The draft itself: bare names in comprehensions, its own def called as a
command, byname by a loop that returns, the top three directories up, a
diff on two process substitutions made a loop, a blank-tolerant pattern.
tests/rill/library2.rill as Python. Still waiting: pack-results (setenv,
a case statement), run-utf8 (load).

## Phase 5 (Iteration 783): setenv, and a case statement

- `setenv(name, value)`: env(name) sees it, and so does every command run
  after it - Rill starts commands through env, so NAME=value goes right after
  env in the vector; the strings live in the C heap. tests/rill/setenv.rill.
- `case subject { pat pat { block } ... }`, as the shell's case: patterns
  with * ? [...] (! or ^ to negate, ranges) and \, several to an arm, the
  first arm that matches runs. A quoted pattern is the text itself, as in
  the shell; $x and unquoted patterns are globs. The subject is held on the
  stack only while the patterns are tried and dropped before a block runs,
  so return, loops and the collector never see it. tests/rill/case.rill
  against the same cases in sh.
pack-results now stops at line 19: a def reads $stage, set further down -
which Python allows and Rill (772) does not.
