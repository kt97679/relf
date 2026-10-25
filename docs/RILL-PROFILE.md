# Where Rill's time goes - the profile, and what it changed (Iteration 768)

Phase 4 of docs/RILL-ROADMAP.md, begun from a measurement after 766 and 767
each guessed a cost that was not there. tools/rill-profile.py runs a Rill
program (compiled by tools/rillc.py first, so the compiler is not counted)
on the counting engine tools/profile.py builds from engine/cv8.c, decodes
kernel64-rill.img with tools/image-audit.py, and gives each word the
dispatches of its own instructions; `--calls` adds how often each is
called. Dispatch counts are exact and repeatable: a change's effect is a
number, not a median.

## Before

dead-words, the 21-definition case: 141,717,728 dispatches. No one cost:
list access (R-AT 9.5 %, R-ITEMS 4.7 %, R-UNBOX 6.8 %), texts (R-T@ 7.0 %,
R-SPLIT-WS 6.4 %, SP-FIND 4.8 %, /STRING 3.0 %), records (R-HASH 4.0 %,
RH-PROBE 2.6 %, R-FIND-LINEAR 2.5 %), membership by scanning (R-BOX=
4.0 %, R-IN 3.1 % - the script's own `";" in $body`, as Python's), the
arena (R-ALLOT 4.7 %, ALIGNED 2.4 %, and (ABORT") 2.4 % - the arena's
"full" test called on every allocation), PICK 4.0 % (a colon word in this
kernel).

native-by-source: 427,913,143 dispatches, three quarters of them in the
regular-expression matcher: RX-STEP 40.1 %, RX-AT 19.4 %, the DEFER
RX-RUN went through 5.6 %, RX-RUN-IMPL 3.3 %, RX-AT-POS 3.0 %. Each step
of the backtracking program ran a chain of up to nine tests on its op,
turned the instruction's index into an address by multiplying (RX-AT,
up to three times a step), and went through a deferred word.

## The changes

The arena's test is a branch now, its ABORT" reached only when full; the
alignment written out; R-PUSH and R-AT fetch the item array inline.

The matcher: each instruction a word of its own (H-CHAR, H-SPLIT,
H-SAVE, ...). A program, once made, is linked (RX-LINK): its op cells
hold those words' xts - from a table kept as offsets, since the image is
saved - and its jumps hold addresses. A step is `OVER @ EXECUTE`: no
tests on the op, no multiply. Where the matcher recurses (a split, a
group's save) the run is written out, so no deferred call per branch.
Each start position clears only the pattern's own groups, not all
twenty.

Checked: tests/rill, the oracle, tools/rill-regex-diff.py's 1,200 cases
against Python's re (none different), and all three pilots against their
Python originals.

## After

| | dispatches before | after | | time before (median) | after |
|---|---:|---:|---:|---:|---:|
| native-by-source | 427,913,143 | 208,496,315 | -51 % | 486 ms | 304 ms |
| dead-words, 21 dead | 141,717,728 | 133,575,901 | -5.7 % | 158 ms | 152 ms |

The matcher's share of native-by-source is now about a half: H-CHAR,
H-SPLIT, the run loops, the search's start positions. What is left to
look at, by the counts: a first-character test before each start
position (most positions cannot begin a match), dead-words' list and text
words (R-AT, R-T@, R-UNBOX, R-SPLIT-WS), and records' hashing.
