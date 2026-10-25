# RILL-SEARCH.md - searching for Rill's best implementation

What forth-vm-evolution's evolution lab does, what of it carries over to
Rill, and the first experiment (Iteration 748). The user asked whether
the genetic programming that lab uses to find the smallest, fastest and
leanest Forth VM could find an optimal Rill implementation, and sent
its repository: the bundle at its Iteration 516, read beside relf in
/home/claude/fve, unmodified.

## The lab, as its code and records show it

`lab/evolve/evolve.py` (2,394 lines) breeds CV8-family designs.

**A design is a parameter genome**, not a program: about forty genes -
the top of stack in a register, the call target scale, byte-granular
headers, the dispatch table, specialisation families, folds,
superinstruction pairs, run-time fusion, the JIT's options - each a
choice among builds the engine and the image converter already know how
to make. A gene is one row, `gene(name, values, show, family, late,
needs, convert)`; `gene-table-test.py` registers a fictional gene and
requires it to work with no code change. `--validate` rebuilds the
hand-made stages from their genomes, and their images must come out
byte-identical, or a genome means something other than it says.

**Life is a gate, not a score.** The engine must compile, the image
convert, the CORE corpus give the cell engine's output byte for byte,
the kernel workload reproduce the reference kernel byte for byte.
Anything else dies, and the cause is kept.

**Fitness is a Pareto front**, NSGA-II, nothing traded: speed - the
geometric mean over the selection workloads (kernel, fib, corpus, loop,
bubble, ackermann) of cycles where the hardware counters can be read,
CPU time otherwise - size (engine plus image), resident memory, and
speed at 4-byte cells. Speed within 2 % and memory within 8 KB are ties
in the ranking. On a machine that is not quiet, every timed run of a
design is paired with one of the hand-made s6, back to back, alternating
order, and the speed is the ratio: drift cancels, and s6 against itself
comes out within 1 %.

**What is never selected on is watched.** The held-out workloads (sieve,
parse) and held-out applications (`appbench.py`) are measured for the
survivors only; `heldout.py` gives the rank correlation and the designs
the selection flatters.

**The operators, and what the records taught about them.** Mutation, a
gene flipped or nudged; crossover gene by gene; borrowing a whole block
from an unrelated design. In seed 40's database mutation-only children
made 73 % of the final front from a quarter of the children, and
crossover, 60 % of the variation, was twelve times less productive per
child - so crossover is now 0.25, genes that travel together on the
front (mutual information 0.67-1.00) are inherited whole, and genes
whose mutants were almost never better are drawn one time in ten.

**What saves measurements.** `build/evolve/db.jsonl` keeps every design
ever evaluated - genome, parents, how it lived or died, its numbers - so
nothing is measured twice and a run resumes. A surrogate screen (one
additive weight per gene value, refitted every ten generations) skips a
child predicted to be beaten by 30 % in speed and 5 % in size, auditing
one skip in ten: a third of the children skipped, 1 of 163 front designs
lost.

**What guards the result.** `--remeasure`: the first Ryzen run's own
leader fell from 0.590 of s6's time to 0.620 when measured again, and
off the front - the winner's curse. `--knockout`: each gene set back to
s6's value, to see what it buys. `gate.py` rebuilds a front with the
current code. Two searches on different machines reached the same front
(0.605-0.609 of s6 at 13,480 bytes).

**Cost**: a design builds and tests in a second or two; 32 designs x 40
generations is about an hour. Runs go out as chains of seeds to other
machines (`chainctl.py`, `next-run.sh`) and come back as packs.

The lab vendors relf at 8ec0e75 (relf Iteration 718); both are GPLv2
only and the owner's, so its generic code - `dominates()`, `fronts()`,
`crowding()`, some sixty lines - can be taken with its origin named.

## What carries over to Rill

The lab's representation is the one this repository's first target
needs: **a parameter genome over choices that are each already correct**
- how Rill's compilers generate code, and the runtime's numbers - not
programs evolved from nothing. What carries over, mapped:

| the lab | for Rill |
|---|---|
| a gene is one row | one table, read by tools/rillc.py, rill/compile.4 and rill/rt.4 alike, so tests/rill/oracle still compares the two compilers word for word under every genome |
| `--validate`: hand-made stages rebuilt byte-identical | the default genome must reproduce today's generated Forth for every test program, byte for byte |
| life: corpus and kernel byte for byte | tests/rill, the oracle, tools/rill-regex-diff.py, tests/rill/real-make-bundle - and a planted broken design that must die (the lab's README rule 1) |
| speed: cycles or paired CPU time | CV8's own dispatch counts - tools/profile.py's counting engine - deterministic, so no pairing and no curse in the search; real time, paired against the default genome as the lab pairs s6, only to confirm the front |
| size: engine plus image | Rill's image, plus the generated Forth of the corpus |
| memory: resident set | the arena's peak |
| held-out workloads | programs kept out of the selection: the regex differential cases, the rewrites as they come to run |
| NSGA-II, db.jsonl, remeasure, knockout | the same, with dominates/fronts/crowding taken from the lab |

What does not carry over: the VM's genes themselves (relf gets them from
the lab, GOALS.md 12 - and Rill gains from them without a search of its
own, since it compiles to Forth), the hardware counters, and the chains
of remote runs - premature while Rill's code changes every iteration.

**The search itself may not need to be genetic at first.** A genome of
ten two-valued genes has 1,024 designs; at a few seconds each that is an
hour on one core, minutes on fury - exhaustive, and so free of the
selection's luck. And the lab's own finding, that mutation did the work,
says a search that starts from the hand-made design and mutates is the
next step when the genome outgrows enumeration. NSGA-II with crossover
earns its place only past that.

## The first experiment

1. **The genome table** (`rill/genes.tsv`): the code-generation choices
   that already have two forms, and the runtime's numbers. To begin:
   the one-word short forms (`1+`, `0>`; 737), a pure def's parameters on
   the stack (738), the ` DUP NIP` pairs taken out (741), a list's first
   capacity (4) and growth (twice), the regex cache (32 patterns), the
   arena's alignment of texts. Choices that need a second form written
   first - a record looked up by hash beyond some size, a counted loop's
   variable kept in I instead of stored - join when written, as rows.
2. **`--validate`**: the default genome against today's output, every
   test program, byte for byte.
3. **The gate and the counts**: every design built (both compilers, the
   image), gated as above, then counted on the selection workloads -
   CPU-bound Rill programs written for it (fib, the loop, lists and
   records, regex, text building) - with the image size, the corpus's
   generated size and the arena's peak.
4. **Exhaustive** over the first genome; a database line a design.
5. **The front confirmed**: re-measured in real time, paired against the
   default and alternated; the held-out programs checked; each gene
   knocked out.

What it should answer first is modest: whether any of Rill's current
choices is wrong on its own workloads, and what each buys. The bigger
target named at 747 - superoptimizing the runtime's hot words, where a
genome of instruction sequences would need the genetic search - waits
until rill/rt.4 stops changing.

## The first search's results (Iteration 749)

Seven genes (rill/genes.tsv): `short`, `purestack`, `dupnip`, `rangeloop`
(the compilers'), `listcap` 1-16, `growth` 1.5 or 2, `rxcache` 0, 8 or 32
(the runtime's). 360 expressed designs, every one built, gated and
counted by tools/rill-search.py in about five minutes on one core. Six
CPU-bound selection workloads and two held out, in tests/rill/search.
`--validate`'s part: the default genome made every snapshot program's
Forth byte for byte as before the genes. Both negative controls died -
an image whose compiler is out of step with rillc.py (commands.rill: the
two compilers differ) and one whose R-PUSH drops its item (ending.rill:
not the expected output).

**Each gene alone**, the default with one gene changed (dispatches
against the default, selection and held out; arena summed):

| gene changed | selection | held out | arena |
|---|---:|---:|---:|
| rangeloop=0 | 1.513 | 1.006 | 17.9 MB |
| purestack=0 | 1.329 | 1.446 | 18.1 MB |
| rxcache=0 | 1.069 | 1.002 | 6.8 MB |
| dupnip=0 | 1.012 | 1.000 | 6.8 MB |
| listcap=1 | 1.011 | 1.001 | 6.9 MB |
| short=0 | 1.007 | 1.000 | 6.8 MB |
| listcap=2 | 1.005 | 1.000 | 6.9 MB |
| growth=3 | 1.000 | 1.000 | 7.1 MB |
| rxcache=8, listcap=8, listcap=16 | 1.000 | 1.000 | 6.8-7.4 MB |
| the default | 1.000 | 1.000 | 6.8 MB |

No design beats the default by more than 0.3 % on any one workload, and
none uses less arena: **every choice Rill has made holds on its own
workloads**, and now each has a price - a counted loop without a list,
half again in dispatches and 2.6 times the arena; a pure def's
parameters on the stack, a third in dispatches; the regex cache, 7 %;
the one-word forms and the DUP NIP removal about 1 % each; a list's
first capacity of 4 the knee; doubling better than half again (less
left behind in the arena). rxcache could be 8 for these workloads, as
they hold few patterns - kept at 32, the workloads being small.

**What the gate found** matters more than the front: four faults, in
paths no test had taken - each now in a test (tests/rill/items,
tests/rill/params):

1. The Forth compiler compared an item with a text as numbers - BINOP
   read the right side's kind from the wrong stack place (OVER for
   2 PICK, the class 742 and 746 also met); rillc.py was right, and no
   test had put an item on the left of `==` against a text. Found by the
   workloads in the default design.
2. Both compilers returned a def's value without making it the kind its
   `->` names: with purestack=0, fib's parameter is a box, and fib
   returned the box's address as its number.
3. Both compilers gave a def with locals its parameters the wrong way
   round - SHADOW{ a b } gives a the deeper value, and the header listed
   them reversed (738). Nothing tested it: the two-parameter def tested
   then was symmetric. **It touched 745's claim**: intrfuzz-stress.rill's
   seed(r, j) took r and j crossed, so both jobs of its one round ran
   seed 598 where the sh tool ran 598 and 599; the two reports agreed
   only because neither run failed. The comparison is to be run again.
4. Both compilers passed an item to a pure def without making it a
   number - with rangeloop=0, collatz($k, 0) got $k's box.
