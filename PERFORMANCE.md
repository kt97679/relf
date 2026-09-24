# PERFORMANCE.md — where the shell's time goes

Measured, not assumed. Figures are best-of-five CPU time on this
container, and dispatch counts come from the counting engine.

This file is the record of what was measured here. The method it
follows - price a change before paying for it, price what cannot be
removed by doing it twice, and convert a proxy like dispatch counts to
time at least once - is `prompts/10-price-before-refactor.md`, and the
optimisations measured and rejected are indexed in GOALS.md's "Tried and
rejected" register so they are not rebuilt.


## Where it stands (Iteration 491)

DASH.md §1 has today's operation-by-operation comparison with dash. In
short: in-process work is 25 to 120 times dash's, builtins are at parity,
and anything that starts a process is within 1.1-1.8x. One thing in that
table is new and unexplained: **an empty loop iteration costs 61 µs,
where Iteration 268 measured 34.5** on a machine where dash measures the
same 1.4 µs as then. Two hundred iterations of correctness work have
made in-process work about 1.8x slower, and it has not been profiled.
The sections below are the measurements made so far, oldest first, and
the last part is the standing research questions about the machine
itself, formerly RESEARCH-VM.md.
## The question

In-process work here costs 18-28x dash and 8-10x bash:

    workload   dash    bash    relf
    loop        2.9     6.2    64.5 ms
    fn          1.7     4.6    39.1
    str         2.1     4.9    37.7
    arith       1.9     5.3    53.3

Process-bound work is already at parity (an external command is 1.2x
dash, 1.0x bash; a command substitution is 0.7x bash). So the gap is
entirely in what the shell itself does between forks.

## Do they compile to a better representation?

**No.** Both are AST walkers, as this shell now is.

- dash (source read here, 0.5.12): `evaltree` in eval.c is a `switch
  (n->type)` over a node tree built by the parser, with a case per node
  kind - `NIF`, `NWHILE`, `NCMD` and so on - calling itself for the
  children. There is no bytecode, no compilation step, no caching of
  expanded words. A loop body is the same node tree on every iteration.
- bash is the same shape (a `COMMAND` tree walked by `execute_command`);
  I could not fetch its source from this container - github's raw host
  is not reachable through the proxy - so that statement rests on prior
  knowledge, not on a reading here, and is marked as such.

So the answer to "do they have a better internal representation" is no,
and the answer to "do they have more efficient code over that
representation" is yes, in two distinct ways, both measurable.

## Where the time actually goes

**The engine's dispatch is not the problem.** A tight Forth loop runs
240 million dispatches in 196 ms: **0.82 ns, about 2.4 cycles, per
dispatch**. That is a fast token-threaded interpreter.

**The problem is how many dispatches a shell operation costs.** One
iteration of `while [ $i -lt 2000 ]; do i=$((i+1)); done` is **9,289
dispatches** here against roughly 3,500 cycles in dash. Two factors
multiply:

1. **Work per operation.** Each of our dispatches does roughly what one
   or two machine instructions do in dash's compiled C. Nothing but
   native code closes this, which is Phase 4's business (JIT/AOT).
2. **Operations per operation.** Several things this shell does in tens
   or hundreds of dispatches, dash does in a handful of instructions.
   These are ordinary algorithmic gaps and they are fixable now.

The profile of one loop iteration, by word:

    840  EXPAND-WORDS      per-word bookkeeping: five arrays copied
    532  FIND-BUILTIN      a linear walk of the builtin list
    396  ARGV-ADD
    262  NAME-CHAR?
    258  (LOOP)  204 (+LOOP)  201 I     Forth's loop words, as definitions
    246  X@   190 XF@        tree field reads
    198  FIND-EQ-OR-END
    174  PARSE-DECIMAL     arithmetic, from text, every iteration
    172  EXEC-SIMPLE  176 EXEC-IMPL
    156  COPY-LITERAL
    144  AE-SKIP-WS

Against dash's equivalents: it finds a builtin with `bsearch` over a
sorted table (six comparisons); it keeps variables in a hash table; it
allocates words from a bump arena; its loop control is a C `for`.

## What was done here

`FIND-BUILTIN` was the clearest of them: a linked-list walk comparing
names, 532 dispatches an iteration, 6% of the whole benchmark, where
dash bsearches. The table is fixed once the shell has loaded, so it is
now hashed once into an open-addressed index, and a builtin registered
later rebuilds it.

    loop -4.2%   fn -5.4%   str -1.5%   arith -1.8%   (dispatches)

A bug on the way, worth recording: builtin names are stored without a
terminator, so hashing to the NUL ran into the next entry whenever a
name exactly filled a cell. `continue` - eight characters - was the only
one affected, and it vanished from the shell. The index now hashes by
explicit length.

## What is left, in measured order

1. **`EXPAND-WORDS`'s per-word bookkeeping** (840/iteration). Five
   parallel arrays are copied per word before expansion. Most words are
   literals that need none of it.
2. **`I`, `(LOOP)`, `(+LOOP)` as engine opcodes** (663/iteration, 7%).
   They are colon definitions; dash's loop control is a C `for`. This is
   already on the queue and is the cheapest large win left.
3. **Tree field reads** `X@`/`XF@` (436/iteration) - candidates for
   primitives.
4. **Arithmetic from text on every pass** (`PARSE-DECIMAL`,
   `AE-SKIP-WS`, 318/iteration) - Stage D's remaining item, and 287
   measured the whole evaluator at 10% of the arithmetic benchmark.

None of these changes the shape: this shell will stay an AST walker,
like both references. The difference that remains after all of them is
the cost of interpreting rather than compiling, and that is Phase 4.

## Iteration 293: the per-word bookkeeping, and what measuring it taught

Two changes to `EXPAND-WORDS`:

- **The save loop is six `MOVE`s.** It copied six parallel arrays a cell
  at a time before the expansion pass overwrites `ARGV`; the arrays are
  contiguous, so one memcpy each does it whatever the word count.
- **A command whose words are all literal skips the pass entirely.**
  `ARGV` already points at the lexer's text in the tree with the flags
  set, and the pass would copy all of it into the output buffer to
  arrive at the same thing. Whether any word needs expanding is counted
  as the words are added (`ARGV-NONLITERAL`), so the test is one read -
  scanning the words cost a command with any expansion in it about ten
  dispatches a word to learn nothing.

**Dispatches** (against Iteration 291): loop -6.8%, fn -7.2%, str -2.7%,
arith -3.1%, and a literal-heavy script -17.8%.

**Wall clock, interleaving the builds and taking minima over 21 rounds:**

    loop      +0.3%      str   -0.2%
    fn        +3.5%      literal-heavy  -5.8%

So the only workload that actually got faster is the one the fast path
is for. **The dispatch count overstated every other figure**, and `fn`
went the wrong way while its dispatches fell 7%. Two reasons, both worth
remembering before the next round of this work:

- A `MOVE` is one dispatch but a call into memcpy; the cell-at-a-time
  copies it replaced were about the cheapest dispatches there are,
  predicted perfectly by the branch predictor.
- Dispatch counts say nothing about cache behaviour or branch
  prediction, and the shell image is now big enough for both to matter.

The changes are kept: the literal path is a real gain on the kind of
script that runs many short fixed commands, and nothing regressed beyond
measurement noise. But the ranking in the section above was built from
dispatch counts, and items 2 to 4 of it should be re-measured on the
clock before anyone spends an iteration on them.

## Iteration 294: is there more in the shell's own logic?

Asked directly, and answered with measurements rather than opinion.

**Where the cost sits, per operation, against dash** (loop overhead
subtracted, best of seven):

    x=abc                0.02 us dash    0.17 us here     8x
    true                 0.02            ~0
    f (a function call)  0.15            3.16            21x
    [ $i -lt 9 ]         0.28            8.12            29x
    x=$y                 0.05            5.50           104x
    ${#y}                0.10            5.04            51x
    $((i+1))             0.02           10.76          many

The shape is unmistakable: anything with **no** expansion is within an
order of magnitude of dash, and anything **with** one costs 5-11 us
whatever the expansion is. The cost is not in any particular construct;
it is a fixed toll on the expansion path.

**Two things were found in that path and one of them was real.**

- `TOKEN-IS-ASSIGN-PREFIX?` still scanned the word's output for a
  `NAME=` prefix, on every marked character and every split test, to
  confirm what the parser's tag (Iteration 285) already said. It returns
  the tag now: 90 dispatches off every assignment that expands anything.
- Variable lookup uses a linear scan below eight variables. Removing
  that threshold - always hashing - made things **worse** (x=$y +2.1%,
  loop +3.1% dispatches), so the threshold stays.

**And then the number that matters.** The shell's own effective dispatch
cost is **3.36 ns**, against **0.82 ns** for the same engine in a tight
loop: **4.1x**. It is not the instruction cache - the loop benchmark
touches only 4,383 distinct image offsets, a few kilobytes. It is the
indirect branch: a tight loop alternates two tokens and the predictor
gets them every time, while the shell's token stream is thousands of
different words in an order nothing can predict, and each miss costs
what a dozen dispatches would.

That reframes the whole exercise:

1. Every dispatch removed from a hot path is worth 3.36 ns, not 0.82 -
   four times better than the raw rate suggests.
2. But the profile is now flat. After the builtin index and the two
   changes above, no single word is more than about 6% of a loop
   iteration; the rest is a long tail of 1-3% items. Revisiting the
   shell's logic word by word therefore buys 1-3% at a time, which on
   this machine is inside the noise of a single run and has to be
   measured by interleaving builds.
3. The levers that could still matter are the ones that change the
   NUMBER of dispatches by a lot, not by a little: doing whole
   operations in one primitive (as `MOVE`, `SCAN` and `COMPARE` already
   do), superinstructions in the engine - which also cut the
   mispredictions - or native compilation, which is Phase 4.

So: worth revisiting, but not word by word. The remaining shell-level
work should be judged by whether it removes hundreds of dispatches from
a path, not tens.

## Iteration 365: re-profiled, seventy iterations on

The profile above was taken at Iteration 292 and quoted ever since,
including in Iteration 362's assessment of other languages - where one
of the two "cheap experiments" it named, the linear builtin walk, had
already been fixed in 293. A number in a document is not a measurement.

`tools/profile.py` builds a counting engine from cv8.c the way
`tools/coverage.py` builds a marking one, runs a workload, and
attributes every dispatch to a colon definition. On a system-shaped
script - 300 iterations of parameter trims, `case` matching, arithmetic
and `set --` - it found **25.1 million dispatches**, and named three
words worth fixing:

    5.0%  NAME-CHAR?       four range tests per character
    3.6%  FIND-EQ-OR-END   a Forth loop looking for '='
    1.8%  SAFE-COPY-NUL    four saves and restores around one MOVE

All three are now what they should have been: a 256-byte table in the
dictionary, `CSTRLEN` and `SCAN` (both engine primitives), and the
stack.

**Dispatches: 25,124,271 to 23,431,348, down 6.7%.**
**Wall clock, interleaved and paired over 13 rounds: median 0.971**, so
a 2.9% saving - the ratio 293 warned about, dispatch counts overstating
wall clock by about two to one, holding again.

Three things the session taught, all recorded where they bit:

- `BUFFER:` memory is not part of the saved image. The first version of
  the table read as zeros in every session after the one that built it.
- This Forth's `?DO` cannot run outside a definition, so a table filled
  by an interpreted loop is silently wrong rather than an error.
- The profiler must build the image before it starts counting, or half
  the profile is the text interpreter compiling the shell.

What the new profile leaves at the top is `EXPAND-WORDS` at 6.5% and
`ARGV-ADD` at 3.5% - the per-word bookkeeping, which has grown by four
flags and an array since 293 as correctness fixes landed on it. That is
the next piece of work, and it is a restructuring rather than a
substitution.

## Iteration 366: the validator, and the bundle

`VALID-NAME?` walked its word calling `NAME-CHAR?`, which since 365 is a
table read behind a colon definition: five dispatches a character where
two would do. It indexes the table itself now.

**Dispatches 23,431,348 to 23,208,897.** Against the profile before 365
began: **25,124,271 to 23,208,897, down 7.6%**, and wall clock paired
over 13 rounds **median 0.964**. The two-to-one ratio between the two
measures holds for a third time.

## Iteration 367: two things the profiler found that reading had not

**`AND` does not short-circuit.** The test that decides whether an empty
field is dropped read as one expression, and one of its terms was
`WORD-IS-ONLY-AT?` - four string comparisons - so it ran for every word
the shell expanded, not for the empty ones it was written for. Nested
tests instead.

**A `[` is only a pattern when a `]` follows.** Iteration 341 taught the
literal fast path to mark `*`, `?` and `[` so that `case` patterns kept
their quoting. Every `[ ... ]` test command has a `[` in it, so every
test command since then has dragged its word through pathname
expansion - 3.4% of a loop benchmark, and `GLOB-FIELDS` at 1.9% of a
realistic script. The bracket is remembered now and marked only if the
word closes it.

**Dispatches 23,208,897 to 21,607,230.** Over the three optimisation
iterations: **25,124,271 to 21,607,230, down 14.0%.** Wall clock, paired
and interleaved over 13 rounds against the image from before 365:

    realistic script   median 0.891
    a `[ ]` loop       median 0.952

The realistic script gains more than the dispatch count predicts for
once, because what went away - `GLOB-FIELDS` and its mark bookkeeping -
is memory-touching work rather than the cheap stack dispatches the
earlier changes removed.

## Iteration 373: a cache that the clock refused

The profile after 372 put variable lookup at the top of what is left:
`NAME-HASH` 3.9% and `FIND-SHVAR` 2.6%, together 6.5%. `NAME-HASH`
walks a name a character at a time, about eleven dispatches each, and a
script reads the same handful of names over and over.

So: a 64-entry cache in front of the index, keyed on the first
character and the length - two primitives - with a hit confirmed by
`CSTR=`, and a generation counter bumped by anything that could move an
entry.

It worked, and every suite passed. **Dispatches fell 4.9%, from
22,033,160 to 20,956,261.** Wall clock, paired and interleaved over 15
rounds against the build from the hour before: **median 0.9925.**

Three quarters of one per cent, for a cache with an invalidation
obligation on every table mutation, 1.5 KB of buffer, and a correctness
argument that has to be re-checked every time the variable table
changes. Reverted.

**Why the ratio broke.** The three earlier optimisations removed cheap
stack dispatches and gained about half of what the count promised. This
one removed cheap dispatches and ADDED a `CSTR=` - a real memory
comparison - plus a cache line touched per lookup. Dispatch counts
measure dispatches; they are a proxy for time only while the work per
dispatch is constant. That is the caveat to put beside the
two-to-one rule from 365-367: it holds when you remove work, not when
you trade cheap work for expensive work.

The remaining profile is `EXPAND-WORDS` 6.6% and `ARGV-ADD` 3.7%, and
both are bookkeeping made of exactly the kind of cheap dispatch that
the rule applies to. That is where the next attempt should go.

## Iteration 374: what the per-word bookkeeping actually costs

`EXPAND-WORDS` at 6.6% of dispatches and `ARGV-ADD` at 3.7% have been
the standing next target since 365. Before refactoring forty-five call
sites, two measurements.

**The first was invalid, and worth recording as such.** Stripping the
flag clears and five of the seven array copies gave 8.6% fewer
dispatches and a 7% faster run - but with the arrays gone, words took
the literal fast path that the missing data no longer disqualified them
from. The experiment measured a different shell, not the bookkeeping.

**The second adds work instead of removing it**, which keeps behaviour
identical: do each thing TWICE and see what the second copy costs.

    seven flag clears, per word        0.45%
    seven array copies, per command    0.62%

So the whole of the per-word bookkeeping is worth about **1%** of this
script's run - not the 7% the broken experiment suggested, and not the
10.3% its dispatch share implies.

**Why the share misleads here.** These are stores and short `MOVE`s of
a few bytes: cheap per dispatch. The run's time goes on the
memory-touching work inside expansion and on the processes it starts.
Dispatch counts are a good guide to where the interpreter is BUSY and a
poor one to where the time IS, and the gap widens exactly where the
work per dispatch is smallest.

**So the refactor is not worth doing**, and the performance thread ends
here: 365-367 took 14% off the dispatch count and about 11% off the
clock; 373 and 374 established what the rest is not. To go further
would take native compilation of hot words - the standing Phase 4 item -
rather than more bookkeeping.

## Standing questions: one machine for Forth and for the shell? (from Iteration 305)

A standing question, with evidence added as it is measured rather than
answered in one go. Three parts:

1. Could one virtual machine run both Forth and the shell *well*?
2. Could Forth use the shell's AST?
3. Is there a representation better than either, that suits both?

### What is known already

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

### The questions this raises, and what would settle them

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

### Evidence log

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

### Would a recognizer mechanism help? (assessed Iteration 352)

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

### Would another language or VM suit this project better? (Iteration 362)

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
