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

## The Forth version - next
