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

## Step 2 - the Forth compiler; the gene on by default (Iteration 765)

rill/compile.4 the same, in [gene infer] blocks: a table of inferred kinds
(scope, name, kind) kept between the passes; BIND-K, the Forth for
rillc.py's bind, at every binding SET-KIND made before; the assignment
binding freely in the first pass; a def's parameters recorded as items,
and its locals preloaded in the second pass in the first pass's order -
the order its SHADOW{ } lists them in, which the oracle compares; the
script's variables preloaded at the start; RILL>FORTH two RILL-PASSes. Two
orders changed to rillc.py's, with the gene off as on: a list loop binds
its item before its index, a comprehension binds its first name once.

Checked: the gene off, tests/rill and the oracle as before. On: tests/rill
all pass compiled in the image; both compilers make the same Forth for
all 20 scripts of the corpus that compile (the oracle's 14 and the
examples); every pilot prints what its Python original prints -
dead-words' three cases and its IS lines, native-by-source,
native-ab-layouts in the stand-in tree; and tests/rill/backedge.rill
prints `x is hello`, `x is 2` compiled by the image itself.

So the gene is on by default, and backedge.rill is among the tests.
Costs: the image 1,149 bytes larger (51,143); a compile two passes, which
on the corpus's largest script is lost in the noise of starting Python.
The search counts both; no score can buy back an unsound kind.

Next, step 3: element kinds for lists, joined the same way.

## Step 3 - element kinds for lists, the Python compiler (Iteration 766)

Gene `elemkinds` (off by default; it needs `infer`). A list variable's
element kind is the join of everything put in it over its scope's life:
the items of a new list it is given - a literal's, a comprehension's
expression's, `words`, `lines`, `split`, `all`, `match`, `keys` (texts),
`range` (numbers), `sort` and `slice` (their list's) - every `push`,
`l[i] = v`, and `extend`. A list that goes out of sight takes `any`:
given to a def, stored in a record or another list, returned, or bound
to a second name (`x = $y`) - two names for one list, either could fill
it. Since a loop's item variable takes its list's element kind, and what
is pushed may be such a variable, the kinds depend on each other: the
compiler runs rounds - each with the last round's kinds, each joining
afresh - until two agree, and the code of that round is the program
(two or three rounds on the corpus; eight without agreeing is an error).

Reads use it: `$l[i]`, `first`, `shift`, `min`, `max`, a for loop's and a
comprehension's item - a text out of a list of texts, checked as every
item is (R-ANY>TEXT), so a kind wrong at run time still stops cleanly.

Measured:

- the gene off, the 23 scripts compile exactly as before;
- on, all compile; 24 of the corpus's 40 list variables get a known
  element kind; tests/rill all pass, and all three pilots print what
  their Python originals print, dead-words' IS lines too;
- speed: no change past the noise. native-by-source, nine runs each,
  interleaved: off best 448 ms, median 489; on best 460, median 489.
  dead-words 155 ms and 153. The generated Forth 0.5 % shorter. Its
  conversions counted: R-ANY>TEXT 26 and 26, R-BOX 47 and 48.

That is what the design predicted, now measured: over boxed storage a
known element kind moves a conversion from each use to the loop's head -
and back to a box when the item is pushed or passed on - but removes
none. The boxes are the cost. So the gene stays off, and its Forth half
waits for the step that needs it: lists of a known element kind storing
their items as they are, unboxed - phase 4's storage, brought forward,
measured through the search like the rest.

## Step 4 - unboxed lists, measured; both genes taken out (Iteration 767)

Gene `unbox` in the runtime: a fourth cell on every list, its tag - 0,
its items boxes; a kind, every item a value of that kind kept as it is.
A list takes a tag at its first R-PUSH-K; anything of another kind put in
boxes all its items first (R-DEMOTE). The generic words box and unbox at
the edge, so all code stays correct whatever it knows; the library's text
lists (words, lines, split, all, match, $args) are built tagged. Typed
code from the Python compiler: R-AT-K for an item of a list whose element
kind is known (as it is when the tag agrees, converted when not),
R-PUSH-K into one, typed pushes in literals and comprehensions.

Correct: with unbox off both compilers compile everything as before; on,
every test and all three pilots print what they should.

Measured, three ways, interleaved, seven runs each (best / median ms):

| | all off | elemkinds | elemkinds + unbox |
|---|---:|---:|---:|
| dead-words, 21 dead | 134 / 165 | 135 / 170 | 145 / 186 |
| native-by-source | 454 / 508 | 442 / 480 | 466 / 521 |
| tests/rill/library (each word 3,000 times) | 19 / 20 | 20 / 20 | 21 / 22 |

Unboxed lists are slower, not faster. Where a list's element kind is
known the read is a little cheaper; everywhere it is not - a def's
parameter, R-JOIN, R-IN, sort, a record's field - a tagged list's item
is boxed anew on every read, and every push and read pays the tag's test.
In this runtime, interpreted on the VM, the boxes were not the cost they
looked.

By the search's rule - a gene that buys nothing goes (752: boxsmall,
rxanchor) - elemkinds and unbox are both taken out. Their code is in the
history: commit "Iteration 767: ... measured" holds both. `infer` stays:
it buys soundness, which is not on the scale.

What phase 4 should start from instead: a profile - which runtime words
the dispatches go to, on the pilots - before any more guessing. Twice now
(766, 767) a cost that looked certain was not there.
