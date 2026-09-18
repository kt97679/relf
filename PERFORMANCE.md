# Why dash and bash are faster (Iteration 292)

Measured, not assumed. Figures are best-of-five CPU time on this
container, and dispatch counts come from the counting engine.

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
