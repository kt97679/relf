# One machine for Forth and for the shell? (research, from Iteration 305)

A standing question, with evidence added as it is measured rather than
answered in one go. Three parts:

1. Could one virtual machine run both Forth and the shell *well*?
2. Could Forth use the shell's AST?
3. Is there a representation better than either, that suits both?

## What is known already

**Both are already interpreters over a tree or a token stream.** The
shell parses to an AST and walks it (`EXEC-SIMPLE`, `EXEC-LIST` and the
rest in tree.4); Forth compiles to token-threaded code the engine walks
in `NEXT()`. dash and bash are AST walkers too (PERFORMANCE.md), so the
shape is not the problem.

**The engine's dispatch is cheap; the shell's use of it is not.**
Measured in Iterations 292 and 294:

    a tight Forth loop           0.82 ns per dispatch  (~2.4 cycles)
    the shell's own workload     3.36 ns per dispatch  (4.1x)

The difference is not the instruction cache - the loop benchmark touches
4,383 distinct image offsets, a few kilobytes. It is the indirect
branch: a tight loop alternates two tokens and the predictor never
misses, while the shell's stream is thousands of words in an order
nothing can predict. **Any design that reduces the NUMBER of dispatches
on a hot path is worth four times the raw rate**, and any design that
makes the stream more predictable is worth more than its instruction
count suggests.

**One shell operation costs thousands of dispatches.** A loop iteration
of `while [ $i -lt N ]; do i=$((i+1)); done` was 9,289 dispatches in 292
and is about 8,300 now, against roughly 3,500 cycles in dash. The work
is spread thin: after the builtin index and the expander changes, no
single word is more than about 6% of it.

## The questions this raises, and what would settle them

**Q1. Would fewer, larger primitives close the gap?** `MOVE`, `SCAN` and
`COMPARE` already do whole operations in C. Iteration 293 measured what
happens when a hot loop is replaced by `MOVE`: the dispatch count fell
7% and the clock did not move, because a memcpy call costs what the
cheap dispatches it replaced cost. **Evidence needed**: the same
experiment on a coarser unit - a whole word expansion, or a whole simple
command - where the C code would do far more per call.

**Q2. Is the shell's AST a plausible Forth representation?** The shell's
nodes are variable-arity records in an arena with a type tag and a
vector of children; Forth's threaded code is a flat byte string with no
structure. A Forth AST would be a different thing again - Forth has no
expressions, only a sequence of words, so its "tree" is a list. The
honest question is not whether Forth COULD use it but whether anything
is gained: the shell's tree exists to be walked repeatedly with
different data, while Forth's code is walked once per call with the
stack carrying the data.

**Evidence needed**: how much of the shell's execution time is tree
walking (`X@`, `XF@`, `EXEC-SIMPLE`'s dispatch) against how much is the
work at the leaves. 292's profile says the tree reads are about 5% of a
loop iteration, which suggests the representation is not where the cost
is - but that measurement was made on dispatch counts, and 293 showed
those mislead.

**Q3. Is there a third representation?** The candidates worth measuring:

- **A register or stack bytecode for the shell**, compiled from the AST
  once, so that a loop body is a byte string rather than a tree walk.
  This is what the encoded expander already does for WORDS (Iteration
  274 onwards): the lexer emits a byte encoding and expansion walks it.
  That change was worth -16% of dispatches on string work, which is the
  only direct evidence that the approach pays here.
- **Superinstructions** in the engine: fuse the sequences that actually
  occur. This attacks the branch misprediction directly, which is the
  4.1x above, and it needs no change to either language.
- **Native compilation** (Phase 4), which removes dispatch entirely and
  is the only thing that can reach dash's numbers.

## Evidence log

Entries are added as measurements are taken; each says what was
measured, and on what.

- **305**: nothing yet beyond what is summarised above, which comes from
  Iterations 292 to 294 and is recorded in PERFORMANCE.md.

- **315**: where a realistic script's dispatches go, by phase. The
  script is the one PERFORMANCE.md uses - 400 lines through a `while
  read` loop with trims, `case` matching and arithmetic, plus four
  external commands - and the words are grouped by their prefix:

        49.5%  kernel + other      (MOVE, SCAN, arithmetic on the stack,
                                    the Forth words everything is built from)
        23.9%  expansion
        11.6%  name lookup         (variables, builtins, functions)
         8.3%  tree walk + exec
         3.5%  builtins + redirection
         2.5%  arithmetic
         0.7%  lexing/parsing

  **Two things this says about the questions above.** The tree walk -
  `EXEC-*`, `X@`, `XF@` - is 8%, so *the representation of the program
  is not where the time goes*, and a different one for the shell would
  be fighting for a fraction of that. Half of everything is in the
  general-purpose Forth underneath: the words a shared machine would
  have to make cheaper are not shell-shaped at all, they are `MOVE`,
  `SCAN`, comparisons and stack arithmetic.

  That points away from "a better IR for both" and towards the two
  levers already named: more work per primitive on the paths that are
  hot (expansion is the only shell-shaped block big enough to matter at
  24%), and making dispatch itself cheaper, which is superinstructions
  or native code. Lexing is 0.7%, which also retires the idea that
  parsing once into a shared form would buy anything - it already is
  parsed once.
