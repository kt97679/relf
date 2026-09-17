# EXPANSION-PLAN.md — words encoded at parse time, expanded in one pass

Written at Iteration 273, before any code, as COMMAND-TREE-PLAN.md was.
GOALS.md's queue item 8, from DASH-COMPARISON.md: dash's parser rewrites
each word with control bytes, and its expander walks that in one pass;
this shell's parser keeps the word as written, and the expander scans it
again, a character at a time, every time the command runs.

## Why

**Where the time is** (Iteration 273, `tests/bench-vm`, dispatches per
loop iteration and their shares):

| workload | dispatches | expansion core | pattern matching | rest of shell.4 | kernel | tree.4 |
|---|---|---|---|---|---|---|
| loop | 8,272 | 34% | - | 27% | 20% | 17% |
| fn | 15,790 | 35% | - | 28% | 18% | 16% |
| str | 56,917 | 24% | **51%** | 9% | 7% | 6% |
| arith | 29,407 | 43% | - | 25% | 18% | 13% |

and per operation (`tools/op-bench.py`, µs; dash in brackets):
`y=$x$x` 6.3 [0.09], `y=$((i*3+7))` 11.9 [0.21], `y=${PWD#/}` 11.5
[0.15], an empty loop iteration 35.8 [1.3].

**What the expander does that dash's does not.** `EXPAND-WORDS` hands
each word to `SCAN-TOKEN`, which walks it with `SCAN-TOKEN-CHAR` and
decides again, character by character, what is quoted, where a `$`
expansion ends, where a `$(...)` ends (asking the tree lexer, which
parses it and throws the tree away), whether the word is an assignment
(`TOKEN-IS-ASSIGN-PREFIX?`, per pattern character), and whether each
emitted character splits a field (`EMIT-EXPANDED-CHAR`, per character
of every unquoted expansion) or is a pattern character (`GLOB-MARK`).
A command substitution's text is then parsed a THIRD time, in the child.
An arithmetic expansion's text is parsed by `AE-*` at every evaluation.
The lexer in `tree.4` already knows almost all of this when it reads the
word; the expander rediscovers it on every run.

**And one algorithmic cost.** `${s##*/}` (basename) asks `FIND-TRIM-LEN`
to try every prefix length with `GLOB-MATCH`, each attempt O(n) - O(n^2)
per expansion. That is `str`'s 51%.

## The shape to move to

### 1. The encoded word

The lexer writes a word into the tree as a byte string in which every
control sequence starts with one byte, `CTL` (0x81); a literal 0x81 in
the text is `CTL CTL`. So a literal run is found with one `SCAN` - the
engine's memchr - and copied with one `MOVE`. After `CTL` comes a code:

| sequence | meaning |
|---|---|
| `CTL Q c` | the character c is quoted (in `'...'`, `"..."` or after `\`) |
| `CTL D` ... `CTL d` | a double-quoted region begins / ends |
| `CTL V` *flags* *op* *name* `CTL E` | a parameter: `$name`, `${name}`, `$1`, `$@`, `$#`, ... *op* says which form, *flags* whether it is inside double quotes |
| `CTL V` ... *op* *name* `CTL W` *word* `CTL E` | `${name op word}` - default, assign, error, alternate, the four trims, with or without `:`; *word* is itself encoded |
| `CTL L` *flags* *name* `CTL E` | `${#name}` |
| `CTL C` *flags* *n* | command substitution number n of this word: its tree, parsed ONCE, is a field of the word node |
| `CTL A` *flags* *expr* `CTL E` | arithmetic; *expr* encoded (it may hold parameters) |
| `CTL T` *user* `CTL E` | a tilde prefix, decided by the lexer (word start, or after `=`/`:` in an assignment) |

A word node gains a vector of command-substitution subtrees (backquotes
included, with their quoting rules applied when lexed), and its flags
say whether it is an assignment (the parser decides, as now),
whether it contains anything to expand at all (266's literal fast path),
and whether it has unquoted pattern characters.

### 2. The expander

`EXPAND-ENC ( word flags --- )`, one pass over the encoded string into
the output buffer:

- literal runs: `SCAN` for `CTL`, `MOVE` the run;
- `CTL Q c`: the character, and - when the field may still be globbed -
  kept escaped until pathname expansion, as dash keeps `CTLESC`;
- parameters: looked up (the hashed table of 272), and their value
  copied in one `MOVE`, recording its output range as a **split region**
  if it is unquoted;
- `CTL C`: fork, run the subtree in the child (no parse), read the
  output; unquoted, the result is a split region;
- `CTL A`: the expression evaluated (stage D compiles it at parse time);
- then field splitting, only inside the recorded regions (dash's
  `recordregion`/`ifsbreakup`) - never a per-character test;
- then pathname expansion, only for words whose flags say they have an
  unquoted pattern character, using the escapes; then quote removal.

Flags select the context: an assignment (no splitting, no globbing,
tildes after `:`), a case word or pattern (no splitting, no globbing;
a pattern keeps its escapes for matching), a here-document body (quotes
are not special), a redirection target (no globbing).

What it replaces in `shell.4`: `SCAN-TOKEN`, `SCAN-TOKEN-CHAR`,
`COPY-SINGLE-QUOTED`, `COPY-DOUBLE-QUOTED`, `COPY-ESCAPED-CHAR`, the
parsing half of `EXPAND-VAR` and `EXPAND-BRACED-VAR`, `EXPAND-CMDSUB`'s
scanning and the `TREE-CMDSUB-END` detour, `TOKEN-IS-ASSIGN-PREFIX?`,
the per-character splitting in `EMIT-EXPANDED-CHAR`, `GLOB-MARK`, and
tree.4's `PREPARE-HEREDOC` rewrite - most of the 1,800 lines of the
expansion core. What stays: the parameter operations themselves
(lookups, trims, defaults, lengths, `$@`/`$*`), arithmetic evaluation,
IFS's rules, `GLOB-WALK`, `GLOB-MATCH`.

### 3. Trims without the O(n^2)

`FIND-TRIM-LEN` tries every length with `GLOB-MATCH`. The common
patterns are a star and a literal - `${s##*/}`, `${s%/*}`, `${f%.*}`,
`${x#*=}` - and those are one scan for the literal: the last `/` for
`##*/`, the first for `#*/`, and so on. `GLOB-MATCH` stays for the rest.
Independent of the encoding, and the cheapest win in this plan.

## Staging

As COMMAND-TREE-PLAN.md: each stage leaves `tests/verify` green and is
committed separately; the new path is built beside the old one.

**Stage 0 — trims.** The star-and-literal fast path in `FIND-TRIM-LEN`,
checked against bash by a differential case with every trim form, empty
and missing values, patterns with brackets and quoted stars (which must
take the general path).

   **Done in Iteration 273.** `TRIM-FAST` answers `*LIT`, `LIT*`, `LIT`
   and `*` with one substring search; `str`'s dispatches halved (22.8 M
   -> 11.9 M), its time 0.79 of 272's. The differential case found two
   older faults, both fixed: quoted pattern characters were patterns
   (`${x#*\*}`, `${z#\[ab\]}`) - now escaped while a trim's pattern is
   captured, and matched with escapes on - and a trim nested in another
   trim's pattern (`${d%/${d##*/}}`) clobbered the outer one's name and
   flags. Both are the kind of thing Stage A's encoding removes for good;
   until then `EMIT-QUOTED`, `QUOTE-DEPTH` and `SAVE-TRIM-STATE` carry
   them.

**Stage A — the encoding.** *(Iteration 274: the lexer writes it; what
is left of this stage is the here-document bodies, and the subtrees of
Stage D.)* `TOKEN-WORD` writes the encoded form (and
keeps the raw text beside it while the old expander still needs it);
command substitutions keep their subtrees; `tree-dump` prints encoded
words readably. `tests/parse` gains encoded-word cases: every quoting
form, nested `${a:-${b:-"c"}}`, `$(case x in x) ...)`, backquotes with
escaped backquotes, `$((...))` holding parameters, tildes in and out of
assignments, a literal 0x81.

**Stage B — the expander, beside the old one.** *(Iteration 275: begun.
`XE-TRY` in tree.4 takes the words whose encoding holds only literal
runs, quoted runs, quoted characters and plain parameters - the lexer
marks those `WF-ENC-SIMPLE` - and declines the rest, which
`EXPAND-WORDS` scans as before. `RELF_EXP=1` selects it; every suite
passes both ways. Still to do: the operator forms, arithmetic,
substitutions, tildes, and then the point of the exercise - splitting by
recorded regions instead of per character, which is what will make it
faster. As it stands it is about neutral: `str` -2.7% of the dispatches,
the loop +1.5%.)*

   *(Iteration 276: the rest of the constructs - the operator forms,
   the trims, arithmetic, command substitutions and tildes - so the
   encoded path takes every word. `RUN-CMDSUB-TEXT` is split out of
   `EXPAND-CMDSUB` and shared. Iteration 277 fixed the three
   faults left there, and **every suite now passes both ways**, which is
   this stage's acceptance condition. Iteration 278 added the region
   splitting: an unquoted expansion's result is copied whole and its
   output range recorded, and the word is split once over those ranges,
   with the pattern characters in them found by SCAN. Against the
   scanning path, after Iteration 279's walker work (a pointer cursor
   instead of an offset, and the parameter name's end found by SCAN):
   str -16.9%, arith -4.9%, loop +3.1%, fn +2.0%. The two that are worse
   are dominated by very short words, where the per-word entry and the
   item dispatch are not paid for by copying four characters in bulk. Words holding an unquoted
   `$@` or `$*` keep to the scanning path: their field boundaries are
   their own.)* `EXPAND-ENC` producing
the same ARGV the old path produces, chosen by an environment variable
for the duration; the whole of `tests/verify` run both ways, as 264 did.
Acceptance: every suite equal or better, `tests/diff`'s expansion,
IFS, pathname and here-document cases in particular.

**Stage C — switch and delete.** *(Done in Iteration 282. The encoded
path is the only one; `RELF_EXP` is gone. `SCAN-TOKEN` and
`SCAN-TOKEN-CHAR` were removed and `tools/dead-words.py` found the other
64 definitions that died with them - the quote copiers, `EXPAND-VAR`,
`EXPAND-BRACED-VAR` and its word capture, `EXPAND-ARITH`,
`EXPAND-CMDSUB`'s scanning half, the tilde words, the old trim path and
their variables. shell.4 6,073 -> 5,281 lines; the 64-bit image 80,768 ->
76,920 bytes.*

*What it did not buy is speed: against the scanning path the figures are
what Stage B measured - `str` -16.8%, `arith` -4.9%, `loop` +3.1%, `fn`
+1.9%. The overhead on short words is the walker's own structure -
`XE-TRY`'s entry and `XE-ITEM`'s dispatch - not the double bookkeeping,
which is what I expected the deletion to remove.)*

**Stage D — measure, then arithmetic.** *(Iteration 283 did the
substitutions: the lexer's parse of a `$(...)` is kept with the word
instead of being thrown away, and the child runs that subtree rather
than parsing the text again. A loop of 300 two-command substitutions:
419 -> 381 ms. Backquotes still carry text - they are not parsed while
scanned - and so does `$(...)`, for the printer. Arithmetic is still
evaluated from text on every pass.)*

**Stage D — measure, then arithmetic.** Profile again. Compile each
`$((...))` into a small tree at parse time (or Forth code, if the tree
walk shows), and command-substitution children run their subtree.

## Risks

- **Two word forms at once** during stages A-B: the raw text stays in
  the node until C, and alias splicing and `eval` keep producing text
  that is lexed - into both forms.
- **Quoting corners**: backquotes inside double quotes, `\` before
  newline inside quotes, `"$@"` with no parameters, `"${a+"$@"}"`,
  empty quoted words, `$''`-free POSIX only. The matrix, POSIX, mrsh and
  differential suites cover most; Stage A's parse cases add the rest.
- **Here-documents** are expanded as double-quoted text in which `"` is
  plain: they get their own encoding flag rather than 264's rewrite.
- **The command-substitution child** must see the parent's arena at the
  same address - it does, after fork - and must not free it.
- **Error messages** for malformed `${...}` move from run time to parse
  time, which is what POSIX and dash do (a syntax error), and a behaviour
  change the matrix's error cases will show.
