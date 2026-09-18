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
