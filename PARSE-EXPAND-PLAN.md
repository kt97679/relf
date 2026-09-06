# PARSE-EXPAND-PLAN.md — separating parsing from expansion

A design for the one remaining architectural change in `shell.4`,
written before any code because it is large enough that starting with
an edit would be the wrong move. Read `GOALS.md`'s notes on Ramey's
bash chapter and `FORTH-STYLE.md` first.

## Why

Three separate problems have the same root, and one change addresses
all of them. That is unusual enough to be worth doing deliberately
rather than incrementally.

1. **Correctness.** `$VAR` is expanded *during* tokenization, once per
   raw line, before any command on that line has run. So
   `FOO=bar; echo $FOO` does not see the new value (Iteration 18) and
   `set a b c; echo $#` reports 0 (45). Both are recorded as
   architectural limitations, not bugs, precisely because of this.
2. **A whole bug class. Done in Iteration 108.** Expansion used to
   write *in place* into the input buffer, which is why `ENSURE-ROOM`
   existed and why a too-long expansion smeared over the rest of the
   line — Iteration 26 for `$VAR`, 46 for `$?`/`$$`/`$#`/`$((...))`,
   99 for `$*`'s separator and 103 for `$@`'s field break, each one a
   missing call. Expansion now writes into its own buffer, so there is
   no shared buffer to overrun and `ENSURE-ROOM` is deleted.
3. **Performance.** `tests/bench`: 568ms against dash's 3ms on a pure
   loop: 236x dash as re-measured in Iteration 116, up from ~172x
   before Stage 1, which added a copy per line. Every iteration
   re-normalizes and re-tokenizes body
   lines that cannot have changed, and re-tokenizes the `while`
   condition. dash parses once and re-executes.

## The shape to move to

Today: `RUN-LINE` → `NORMALIZE-OPERATORS` → `TOKENIZE` **(expands
inline, 24 call sites)** → `RUN-TOKENIZED` → splitters → dispatch.

Target: `NORMALIZE-OPERATORS` → `TOKENIZE` (**no expansion** — records
word boundaries and per-word flags only) → `EXPAND-WORDS` (produces the
argument list, per command, immediately before it runs) → dispatch.

The key move is that `EXPAND-WORDS` runs **per command**, after
everything earlier on the line has executed, rather than once per raw
line. That is what makes `FOO=bar; echo $FOO` work.

## Staging

Each stage must leave the full suite green — as of Iteration 108, 524
assertions, 16 differential cases, 1991 core OK markers, both cell
widths, and mrsh at 18 — and be committed separately. Do not begin a stage before the previous one is committed
green.

**Stage 1 — split tokenize from expand.**
`TOKENIZE` stops calling the `EXPAND-*` words and instead records, per
word: its text, whether it was quoted, and whether it *contains*
anything needing expansion (a `$`, a backquote, a leading `~`). A new
`EXPAND-WORDS` runs the existing expansion words over that list into a
fresh output buffer. Call it from `RUN-SIMPLE-OR-PIPELINE` and the
other execution paths, not from `TOKENIZE`.

**Stage 1a is done (Iteration 108).** The expansion sites no longer
write back over the input: `TOKENIZE` emits into `TOK-BUF`, a separate
buffer, and `ENSURE-ROOM` is gone along with all twenty of its call
sites. That was half of what this stage's difficulty was made of, it
removed the four-instance bug class on its own, and it left `LINE-BUF`
intact after tokenizing — which the rest of the stage needs, since
re-expanding a line per command means the line has to still be there.
It went green first time on both cell widths with no test changes.

**Stage 1b is the rest, and is where the care goes.** Two pieces:

*Producing raw words.* Do NOT write a second scanner for "where does a
word end". `NORMALIZE-OPERATORS` already walks the raw line tracking
single quotes, double quotes, `$(...)`, backquotes and `$((...))`, and
already emits into a buffer of its own. Word boundaries are exactly
the whitespace it emits while at depth zero in all of those, so it can
record `RAW-ARGV`/`RAW-ARGC` as it goes, for free and by construction
in agreement with itself. Any other approach gives this codebase two
answers to the same question, which FORTH-STYLE.md §11 is entirely
about.

  **That obstacle is cleared (Iteration 110).** `DO-WHILE` used to
  re-tokenize its stored condition with no `NORMALIZE-OPERATORS` in
  between, so `TOKENIZE` could not have consumed spans the normalizer
  produced. All five call sites now go through one `NORM-TOKENIZE`,
  which normalizes and then tokenizes, so every path into `TOKENIZE`
  has normalized first.

*Deciding where `EXPAND-WORDS` runs.* This is the real work, and it is
an audit rather than a design problem. Every reader of `ARGV` has to
be classified as wanting raw words or expanded ones, because with
expansion deferred it will get raw ones by default:

- **Raw is correct, leave alone.** `LINE-IS?`'s keyword checks;
  `SPLIT-SEMI`/`SPLIT-ANDOR`/`SPLIT-PIPE`/`GRP-TRACK`/`SPLIT-GROUP`
  and the `AT-*?` predicates; `FUNCDEF-NAME?` and `DO-FUNCDEF`'s name;
  `TRY-ALIAS` (POSIX looks up the alias on the unexpanded word);
  `PARSE-REDIRECTIONS`' recognition of the operators themselves.
- **Needs expanded words, and does not pass through
  `RUN-SIMPLE-OR-PIPELINE`.** These are the ones that will break
  silently if missed: `DO-CASE`'s case word *and* each arm's patterns
  (the patterns are expanded but must not then be re-split);
  `DO-FOR`'s word list, expanded once at the `for` line per POSIX;
  `PARSE-REDIRECTIONS`' filename operand; `TRY-ASSIGNMENT`'s value.
- **Gets it from `RUN-SIMPLE-OR-PIPELINE`.** Every builtin, every
  external command, every pipeline stage, and both loop conditions —
  a `while` condition is run through `RUN-TOKENIZED`, so it is covered
  by whatever covers an ordinary command.

Write a differential case for each of the second group *before*
touching it, since that is the group whose failures are quiet.

The field-splitting logic (`IFS-SPLIT-PENDING?`,
`TOKEN-IS-ASSIGN-PREFIX?`, the empty-field rule from Iteration 86)
moves with the expansion sites and gets *simpler*, because "which word
am I in" stops being implicit in a buffer position.

**Stage 2 — cache tokenized body lines.**
Loop and function bodies are stored as raw text and re-tokenized every
iteration. Once tokenizing is separate from expanding, the token list
for a body line can be built once and only `EXPAND-WORDS` re-run per
iteration. This is where the loop benchmark improves; measure with
`tests/bench` and record the number.

**Stage 3 — nested `$(...)`. Done in Iteration 105, ahead of this
plan and without needing it.** Not by saving and restoring parser
state: the substituted text became a replay input source read through
the real tokenizer in the forked child, which has its own copy of
every buffer, so there was no state to save. `CMDSUB-TOKENIZE` is
deleted. `2.2-quoted-characters.sh` passes. Original text follows.


With expansion a separate pass, a command substitution can invoke the
real tokenizer recursively with `)` as a context-dependent terminator,
saving and restoring parser state — Ramey's recommendation, and the
thing `CMDSUB-TOKENIZE` should be *replaced* by rather than extended a
fourth time (Iterations 71, 73). This closes
`2.2-quoted-characters.sh`.

**Stage 4 — retire the recorded limitations. Done in Iteration 115.**
Both work. `tests/diff/cases/same-line-expansion.sh` covers them, and
the notes in `GOALS.md` are gone rather than left to mislead.

## Risks, and how to keep them small

- **This is the tokenizer.** Iteration 48 changed how one character
  tokenizes and the consequences surfaced in four separate places over
  fourteen iterations. Expect the same shape here and budget for it.
- **Buffer lifetime is where this codebase's bugs live** — four
  iterations went on it for one 60-line feature (76–80). Before
  writing, list which buffers each stage reads and writes, and which
  words in between can overwrite them.
- **Build each piece as an isolated diagnostic first.** Both failed
  attempts at compound pipeline stages skipped that step; the isolated
  test in Iteration 79 found the real cause in minutes.
- **The differential suite is the safety net.** `tests/diff/` compares
  against bash with no hand-written expectations, and has already
  caught a bug of mine that no hand-written test would have. Add cases
  *before* each stage, not after.

## What this does not change

Not a rewrite of the shell. `RUN-TOKENIZED`, the splitters, `DISPATCH`,
the builtins, replay-as-input-source and the arena all stay as they
are. The change is confined to the boundary between tokenizing and
expanding — which is precisely why it is worth doing as one deliberate
piece rather than drifting into it.
