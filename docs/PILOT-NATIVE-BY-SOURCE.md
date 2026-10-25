# PILOT-NATIVE-BY-SOURCE.md - one script, three languages (Iteration 755 on)

The pilot of the three-way comparison (746, the user's question at 745):
tools/size-research/native-by-source.py written again in Rill
(examples/rill/native-by-source.rill) and in Forth, each run on the same
input (`python3 tools/native-budget.py relfsh-native 3000 >
/tmp/sz/budget-all.txt`) and held to the Python original's output - 40
lines, byte for byte. The protocol: the Forth version may use relf's
Forth libraries and Rill's runtime words, so the comparison weighs the
languages and not a library; every defect from the first run to the
output matching is logged with its class; size in code lines and
characters, as rule 3 counts them.

## The Rill version - matches (Iteration 755)

The same 40 lines as the Python original, compiled by the image's own
compiler and by tools/rillc.py alike. 37 code lines, 2,052 characters
against Python's 43 and 1,951: **+5.2 %**. Time on the development VM:
398 ms against Python's 49 - the regular expressions in Forth, a record
of 2,377 words built and read, and no collector (the arena grows to
some tens of MB).

Its defects, from the first run to the match:

| # | defect | class | found by |
|---|---|---|---|
| 1 | `[k]` for `[$k]` - a variable read without its `$` | Rill's `$` rule (727) | a wrong value, run |
| 2 | a record assigned to a variable holding an item | Rill's kinds | the compiler |
| 3 | `number(x)` for `number($x)` | Rill's `$` rule, again | "not a number", run |
| 4 | relied on `and` not reading its right side | Rill's semantics (and was not short-circuit) | index past the list, run |
| 5 | the header walk without the original's three-line skip | port logic | the output check |

Two of five are the `$` rule - the slip Rill's own design makes possible;
1 and 2 were in the paper rewrite of 735, before Rill ran. 2 and 4
changed Rill rather than the script: a variable holding an item now
takes a value of any kind (754), and `and` and `or` short-circuit (755),
in both compilers - what a reader of Python or sh expects.

Faults the pilot found in Rill's implementation, not the script (each
fixed, each in a test now): DEC-LIT? reading an address as a length
(754); R-STARTS dropping a cell too many when the text is shorter than
the prefix - a data stack underflow after hundreds of lines (755,
tests/rill/library's loop of every library word 3,000 times); the arena's
16 MB filled (755: 128 MB of address space, used as touched).

## The Forth version - matches (Iteration 756)

examples/rill/native-by-source.fth: relf's Forth and Rill's runtime words
(texts, lists, records, regular expressions, R-READ, R-SORT-BY's kind of
sort written out for list entries), loaded with INCLUDED in Rill's image -
R-RUN joins a program's lines into one, which a `\` comment would end.
The same 40 lines as the Python original **on its first run**: no defect
between the first run and the match. rill-forth-lint run on it alone
reported four findings (-ROT and /STRING "not in the kernel") - false:
rill/rt.4 and compile.4 define them; with them loaded beside it, none.

That zero has to be read with the bias the protocol named: the Forth
version was written last, by the author of the runtime words it calls,
knowing every pitfall the Rill run had turned up - the original's skip of
three lines after a header, the short-texts case, the stack effect of
every word. The stack reasoning it took is not in any count here.

## The three, side by side

| | Python | Rill | Forth |
|---|---:|---:|---:|
| code lines | 43 | 37 | 89 |
| code characters | 1,951 | 2,052 | 4,070 |
| against Python | - | +5.2 % | +108.6 % |
| defects, first run to the match | (the reference) | 5 (2 written before Rill ran) | 0 (written last) |
| time, best of three | 48 ms | 415 ms | 292 ms |

Measured alike: code only, comments and blank lines out (a Python
docstring, a Rill `#` line, a Forth `\` line or `( stack comment )`).

**What it says.** In size Rill sits with Python - five per cent over it,
on a script Python is at its best on (re, collections.Counter, %-format)
- and Forth at twice either, with the same library under it: the
difference is the language, not the library. In speed both Rill and
Forth run six to nine times Python's time here - regular expressions and
records in Forth, an arena with no collector - and Rill 1.4 times the
hand-written Forth, the cost of its boxed items and generic words. In
defects nothing can be concluded from one pair written in this order;
what the Rill log does show is where Rill's own design invites slips -
two of its five were the `$` rule.

## The second pilot: tools/dead-words.py - Forth written first (Iteration 757)

To balance the first pilot's order (Forth written last, knowing every
pitfall), the second's Forth version was written **first**:
examples/rill/dead-words.fth, over the same runtime words. The check, three
cases, each against the Python original byte for byte: the shell's three
sources (no dead word, the summary on the err port); the libraries with
them (21 unreachable definitions, sorted as Python sorts the tuples); and
`--delete` run on two copies of those seven files - every rewritten file,
and the output, the same. (`--why` is left out of the check: the chain it
prints depends on the order Python iterates a set of ints.)

Its defects, from the first run to all three matching:

| # | defect | class | found by |
|---|---|---|---|
| 1 | `CURRENT` and `KILL` defined again - names the kernel already has, so "Redefining: ..." in the output | Forth's single namespace | the output check |

(One more stop was the harness's, not the program's: the INCLUDED driver
named the file by a relative path, which the `--delete` case, run in
another directory, could not open.)

| dead-words | Python | Rill | Forth |
|---|---:|---:|---:|
| code lines | 148 | 108 (the paper rewrite) | 172 |
| code characters | 3,299 | 3,576 (+8.4 %, the paper rewrite) | 7,156 (+117 %) |
| defects, first run to the match | (the reference) | next | 1 (written first) |
| time, the 21-definition case | 39 ms | next | 95 ms |

The Rill version is next. To run it needs, in both compilers and the
runtime: `values()`, `sort()` of a list of lists (Python's tuple order),
`split(text, sep)` (Python's: a last empty piece kept - what `--delete`'s
join needs to give back a file's final line end), `push` and `in` and
assignment through an index on a variable that holds an item (a list or
record reached through another).

### dead-words: the Rill version, under way (Iteration 758)

Added for it, in the runtime and both compilers (tests/rill: 13, the
oracle the same): `values`, `sort` (a stable sort in Python's order - texts
by bytes, numbers by value, lists item by item), `split` (Python's: empty
pieces kept, the last one too), commas between a list literal's items, and
items as containers - `push`, `extend`, `shift`, `first`, `keys`, `values`,
`sort` on an item holding a list or record, `in` with an item on the right
(R-IN-ANY), `x[k] = v` with `x` an item (R-ASSIGN-ANY), `==` and `!=`
between two items (R-BOX=), a comprehension over an item, `+=` on an item
holding a number, and a text or number variable given an item converted.

Its defects so far, from the first run:

| # | defect | class | found by |
|---|---|---|---|
| 1 | lines read with `lines()`, which drops a last empty line - `--delete`'s join would lose a file's final line end | port logic (Python's split) | reading the original |
| 2 | `kill[$f][$ln] = true` - two indexes in one assignment, which Rill has not | Rill's syntax | the compiler |
| 3 | a comprehension over a def's parameter, an item | Rill's kinds | the compiler |
| 4 | `a -= 1` on a variable holding an item | Rill's kinds | the compiler |
| 5 | 57 roots where the original finds 77, so 372 words wrongly dead | open | the output check |

1 and 2 changed the script; 3 and 4 changed Rill. 5 is open; the first
suspect is the rewrite's record of string words, whose keys were written
as raw texts with a backslash before the quote (`'.\"'`) - in a raw text
the backslash is itself, so `."` is not among them.
