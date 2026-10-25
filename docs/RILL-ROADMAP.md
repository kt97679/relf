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
