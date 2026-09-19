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

## Would a recognizer mechanism help? (assessed Iteration 352)

A recognizer, in the Forth 200x sense, replaces the text interpreter's
hard-wired "look the word up, and if that fails try to read it as a
number" with a list of recognizers, each offered the token in turn and
each answering either "not mine" or "mine, and here is how to interpret,
compile and postpone it". It is how a Forth gains `0x1F`, `'c'`,
`"string"`, floats or typed addresses without anyone editing
`INTERPRET`.

**Where this shell's text interpreter is actually used.** Twice: while
building an image, and behind the `forth` builtin. The whole source -
kernel, extensions, shell, editor, tree - is 82,769 tokens, and
interpreting all of it takes **78 ms**, about 0.9 us a token. At run
time the shell never interprets anything: its own lexer, parser and
expander are compiled Forth, and `EVALUATE` appears at exactly one call
site, the escape hatch.

**So the three things a recognizer could improve, measured:**

1. *Shell speed*: nothing. The interpreter is not on any path a script
   touches. PERFORMANCE.md's profile has no INTERPRET, FIND or NUMBER?
   in it at all.
2. *Build speed*: a recognizer list costs a few comparisons per token
   where there is now one `FIND` and a fallback. On 83,000 tokens at
   0.9 us that is single-digit milliseconds - real, and irrelevant.
3. *Expressiveness*: this is the honest one. The source builds **32
   literals byte by byte** - 125 bytes in all, things like
   `CREATE OA-QUOTED 4 C, 34 C, 36 C, 64 C, 34 C,` - because a double
   quote cannot appear inside `S" "`. That is the only real irritation
   a literal syntax would remove.

**And point 3 does not need a recognizer.** A parsing word - `CSTR," ... "`
with its own escape convention - solves it in a dozen lines and needs no
change to `INTERPRET`, because the token has a prefix. Recognizers earn
their keep when a BARE token must be given meaning, which is not what
any of these 32 cases are.

**Costs, against this project's own measures.** The kernel image is
9,090 bytes and every image inherits it; a recognizer stack with its
token/action tables is perhaps half a kilobyte to a kilobyte of that,
against a shell that advertises 122 KB total versus dash's 130 KB. The
kernel is also the file that must re-converge to a fixpoint through the
cross-compiler, which is the riskiest change in the repository, and the
no-dead-words rule means the mechanism must then be used by something.

**Verdict: no, not for this shell.** It is an elegant answer to a
question this project does not ask. Two things would change that:
adding a family of literal syntaxes to the Forth layer (floats, typed
addresses, string escapes) rather than the one; or making the `forth`
escape hatch a user-facing programming environment where people extend
the syntax themselves. Until then, the cheap and specific fix -
a `CSTR,"` parsing word - buys the only benefit identified, at a
hundredth of the cost.

## Would another language or VM suit this project better? (Iteration 362)

Asked directly: Lisp, Lua, MicroPython, something else. Answered with
this machine's own numbers.

**Size.** The whole system - engine plus kernel image plus shell image -
is 132 KB on x86_64, against dash's 130 KB. The engine's code is 23 KB;
the kernel image is 9 KB; everything else is the shell. On the same
machine: Lua 5.4's core library is **265 KB** with no shell in it,
twice this system entire. Python's runtime is **9 MB**, its binary 8 MB.
Perl is 4 MB. mawk, one of the smallest real interpreters packaged, is
171 KB. A small Lisp (femtolisp and friends) lands around 100-150 KB -
the only candidate in the same order of magnitude, and still five times
the engine here. Forth's threaded model is why: the runtime is tiny
because the program IS data in an image.

**Speed, and what is actually slow.** The engine dispatches in 0.82 ns,
about 2.4 cycles. That is not the bottleneck and a faster VM would not
help it. What costs is how MANY dispatches a shell operation takes: one
iteration of a counting loop is 9,289 dispatches here against roughly
3,500 cycles in dash, and the profile of that iteration is 840
dispatches of per-word bookkeeping (five arrays copied) and 532 of a
linear walk down the builtin list. Those are algorithmic, and they would
still be there after a rewrite in any language.

The phase split says the same thing: 49.5% of dispatches are kernel
words - MOVE, SCAN, stack arithmetic - 23.9% expansion, 11.6% name
lookup. That is byte and memory work. Lua's register VM is genuinely
faster at arithmetic and table code, which is 2.5% of this profile, and
it would do the string work through a garbage-collected immutable string
type: every `${x#pattern}` allocating, in a program that forks for
almost every command. For this workload that is a poor trade.

**What would genuinely be better, by goal.**

- *Fastest shell*: C. That is dash, and it is 130 KB and 6x faster.
  Nothing about this project's shape beats a C shell at being a C shell.
- *This project's shape, but faster*: Forth with native code generation
  for hot words - the standing Phase 4 item - plus the two algorithmic
  fixes named above. Both keep every test and the bootstrap.
- *Easiest for other people to extend*: Lua or a small Lisp, at four to
  ten times the size and with a garbage collector in a process that
  forks constantly.
- *Smallest self-hosting system with an image*: what is here already.

**Verdict: no, and the measurement says why.** The substrate is not what
makes this shell 6x slower than dash; the number of operations per shell
operation is, and that is the same in any language. The cheap
experiments are hashing the builtin lookup (532 dispatches an iteration)
and trimming the per-word bookkeeping (840), which between them touch a
sixth of the loop before any knock-on effects - more than a VM swap
would buy, at a fraction of the cost, and without discarding 360
iterations of tests.
