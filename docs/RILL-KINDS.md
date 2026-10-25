# Kinds for lists, records and variables - the design (Iteration 763)

Phase 2 of docs/RILL-ROADMAP.md. Its first attempt, kept out of the tree,
taught what the design must be.

## The attempt

Element kinds as the compilers now keep kinds: as they go, binding by
binding. A list literal of texts, `words()`, `lines()`, `split()`,
`all()`, `keys()` made a list of texts; `range()` one of numbers; a
comprehension a list of its expression's kind. Reading `$l[i]`, `first`,
`shift`, `min`, `max` of such a list gave a text or a number, not an item;
a for loop's variable took the element kind; `push` and `l[i] = v` of a
known other kind were errors. In the Python compiler it took 70 lines.

Run over the corpus it stopped at once, in dead-words.rill:

    for a in $args { ... }           # $a: now a text, an argument
    ...
    a = $nd.first                    # an item: converted to a text (758)
    while ($a > 0 and ...) { ... }   # "a number is needed here, not a text"

The same short name, bound twice in one script for two things. While loop
variables were items, the second binding was free; with kinds decided at
the first binding, it is not. Scripts reuse `a`, `i`, `t`, `x`, `line`
all the time - Python's rewrites more than most.

And the order of binding was never safe, only lucky. A variable's kind
changes from the point of a binding on, in the order of the source; but a
loop runs its body again from the top:

    while (...) {
        echo $x              # compiled with $x's kind before the for: a text
        for x in $items { }  # $x an item from here on - a box in R.x
    }

the second time round, `echo $x` reads a box as a text. Kinds that follow
the source's order cannot be made sound for loops; the per-binding
element kinds only made the hole wider.

## The design: one kind per variable, inferred over its whole scope

Each variable - the script's, or a def's own - gets one kind for its
whole scope: the join of every binding's kind. The same kind joins to
itself; two different kinds to an item (number and decimal to a
decimal). A list's element kind is the join of every item put in it:
literals, pushes, `l[i] = v`, extends, a comprehension's expression -
so `out = []` followed by `push($out, $t)` is a list of texts, which
binding by binding it could never be. A record's field kinds the same way,
field by field.

Both compilers already compile a whole script in one go, so the
inference is a first pass of the same compiler: compile, collecting every
binding's kind and every push's, join them per variable, list and field;
then compile again with those kinds fixed from the first line. The
second pass's code is the only code. In the Python compiler a second run
of the parser; in the Forth one a second run over the same tokens, with a
table of the inferred kinds kept between the runs.

What it gives:

- Sound kinds: a variable has the same kind wherever it is read, so no
  back edge can find a box where a text was compiled, or the other way.
- Typed items without declarations: `$l[i]`, a for loop's variable,
  `first`, `shift` of a list of texts are texts; conversions at compile
  time; the pilots' four kind defects caught there or not possible.
- Reused names keep working: `a` bound to a text and to an item is an
  item, as now.
- The ground for phase 4's unboxed lists: storage can follow a list's
  element kind only once that kind holds for the list's whole life.

Measured as everything is: tests, the oracle (both compilers alike), the
corpus, and the search's four criteria - generated Forth and dispatches.

## Steps

1. The Python compiler: two passes, joins for variables; nothing else
   changes - the corpus must compile to the same code wherever a variable
   had one kind already.
2. The Forth compiler the same, the oracle word for word.
3. Element kinds for lists, then field kinds for records, on top.
4. Measure; then phase 4's unboxed storage, as a gene.

## Step 1 - the Python compiler (Iteration 764)

Gene `infer` (rill/genes.tsv), off by default until the Forth compiler has
it too. With it on, tools/rillc.py compiles a script twice. The first
pass binds as it goes - an assignment of another kind rebinds, no
conversion, no error - and records every binding's kind per variable: the
script's, or a def's own (its parameters bound as items). Their join is
each variable's one kind. The second pass starts the script, and each
def, with those kinds, so every binding finds its variable's kind
already there: the same kind is stored as it is, an item takes the value
boxed, a text or number variable given an item converts it - the rules
the compiler had, now applied to the variable's kind for its whole scope.
Where a loop's index, count or key lands in a variable that is an item,
it is boxed (`I K-NUM R-BOX`), or the key's box kept.

Every binding goes through one word now, `bind`, at the sites the Forth
compiler has as BIND and SET-KIND: assignments; range loops (both forms);
a record's key and value; a list's index and item; a comprehension's
names; a def's parameters.

Measured on the corpus (tests/rill and examples/rill, 22 scripts):

- the gene off, all 22 compile to exactly what the compiler made before;
- the gene on, 20 compile to the same code, word for word: their
  variables had one kind already. The other two differ where a variable
  was bound to two kinds - dead-words.rill's `$why`, a text and then an
  argument (7 words), native-by-source.rill's likewise (3) - and both
  still print what the Python originals print; dead-words' IS-line case
  too;
- tests/rill all pass compiled this way; and the program that showed the
  hole, now tests/rill/infer/backedge.rill, prints `x is hello`, `x is 2`
  - as Python does - where without the gene it prints a box as a text.

Step 2, the Forth compiler's half, is next: the same two passes, then the
gene on by default and tests/rill/infer/ among the tests.
