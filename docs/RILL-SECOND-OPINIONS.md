# Second opinions - what came back, what held up (Iteration 769)

Four prompts (a Claude Doc, "Rill: questions for other models") went to
other models; four sets of answers came back, three to all four prompts and
one to the regex prompt alone, plus one review of the prompts themselves.
Nothing was taken on say-so: the regex idea they all ranked first was built
and measured; every kind counterexample they proposed was run.

## Where they agreed

- Regex: skip start positions that cannot begin a match - a first-character
  set from the program, nullable patterns left unfiltered, ^ handled apart
  (all five ranked it first); then a STRING op for runs of CHAR, a 256-byte
  table for classes, the per-start clearing; keep the backtracker - a Pike VM
  or a bit-state memo would cost more here, or risk Python's results.
- Kinds: the gap is definite assignment - a variable bound on some paths
  only, read where it may be unset (all four).
- Runtime: fuse or write out R-AT, R-UNBOX and R-T@ inside the runtime's own
  hot words; SCAN for splitting by one byte; field names made once.
- Design: keep the $ rule (scripts stay short), keep commands and calls apart,
  give better diagnostics (a def called as a command, for one).

## The counterexamples, run (tests in the image, 769)

| program | Python | Rill now |
|---|---|---|
| `if ($c > 0) { x = hello }` then `echo $x`, c 0 | NameError | segmentation fault |
| `for x in [] { }` then `echo $x` | NameError | segmentation fault |
| `x = 1`, `x += 0.5`, `echo $x` | 1.5 | 1 - wrong |
| `par for x in [1 2 3] { n += 1 }` from n 0 | (no equivalent) | n stays 0: each body a child |
| `for i in range(1, 3)` | 1 2 | 1 2 3 - range includes its end |
| a def reading a script variable bound after it | works | compile error ($x is not set) |
| `on EXIT` reading a variable bound after it | works | compile error |
| `def f -> number { return hello }` | returns the text | compile error |
| comprehension variable after the comprehension | (Python 3: gone) | its last item, as Python 2 |

The first two crash where Python stops cleanly; the third is a wrong answer.
All three are next. The range and par for rows are design questions.

## Claims that did not hold

- "A Pike VM gives leftmost-longest" - not with thread priorities, as RE2's.
- "COMPARE costs a dispatch per character" - one, whatever its length.
- "par for children share the heap and race" - they are forked: writes are
  lost, as the table shows.
- "A def compiled with a global's earlier kind meets its later one" - kinds
  are joined over the whole scope; and the forward read is a compile error.
- One answer was a summary of the prompts, not answers; its one useful point:
  the earlier literal-text measurement was the search's score, not this
  profile - worth measuring again.

## The first idea, built: the start filter

When a pattern is compiled, a walk of its program through SPLIT, JMP, SAVE
and EOL collects the characters a match can take first into a 256-byte table
(a path through BOL stops: it can only start at 0, which is always tried; a
path to MATCH taking nothing means the pattern can match empty, and then
nothing is filtered). The search tries position 0, then only positions whose
character is in the table - with SCAN, one dispatch, when there is just one
such character. A pattern every path of which passes ^ first has an empty
table: only position 0 is tried, which covers the anchored case too.

| native-by-source | dispatches | median time |
|---|---:|---:|
| before 768 | 427,913,143 | 492 ms |
| after 768 (matcher rebuilt) | 208,496,315 | 304 ms |
| after 769 (start filter) | 157,741,195 | 261 ms |

-24 % on 768's count; -63 % on the count before 768. dead-words, little
regex, unchanged. A first slip - the one-character slot kept a character
when there were several - gave 239 wrong results of 1,200 in the regex
differential, which caught it; fixed, 0 different. Tests, the oracle and all
three pilots unchanged.
