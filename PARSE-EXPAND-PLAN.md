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
2. **A whole bug class.** Expansion writes *in place* into the input
   buffer, which is why `ENSURE-ROOM` exists and why a too-long
   expansion smeared over the rest of the line — found in Iteration 26
   for `$VAR`, and again in 46 for `$?`/`$$`/`$#`/`$((...))`, which had
   never called it. With expansion producing a *new* word list, the
   hazard cannot occur: there is no shared buffer to overrun.
3. **Performance.** `tests/bench`: 568ms against dash's 3ms on a pure
   loop, ~190x. Every iteration re-normalizes and re-tokenizes body
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

Each stage must leave the full suite green — 502 assertions, 4
differential cases, both cell widths, mrsh at 17 — and be committed
separately. Do not begin a stage before the previous one is committed
green.

**Stage 1 — split tokenize from expand.**
`TOKENIZE` stops calling the `EXPAND-*` words and instead records, per
word: its text, whether it was quoted, and whether it *contains*
anything needing expansion (a `$`, a backquote, a leading `~`). A new
`EXPAND-WORDS` runs the existing expansion words over that list into a
fresh output buffer. Call it from `RUN-SIMPLE-OR-PIPELINE` and the
other execution paths, not from `TOKENIZE`.

Expect this stage to be the whole of the difficulty. The 24 expansion
call sites all currently write via `EMIT-TOK-CHAR`/`EMIT-EXPANDED-CHAR`
into the token being built; they need to write into the output word
instead. The field-splitting logic (`IFS-SPLIT-PENDING?`,
`TOKEN-IS-ASSIGN-PREFIX?`, the empty-field rule from Iteration 86)
moves with them and gets *simpler*, because "which word am I in" stops
being implicit in a buffer position.

**Stage 2 — cache tokenized body lines.**
Loop and function bodies are stored as raw text and re-tokenized every
iteration. Once tokenizing is separate from expanding, the token list
for a body line can be built once and only `EXPAND-WORDS` re-run per
iteration. This is where the loop benchmark improves; measure with
`tests/bench` and record the number.

**Stage 3 — nested `$(...)`.**
With expansion a separate pass, a command substitution can invoke the
real tokenizer recursively with `)` as a context-dependent terminator,
saving and restoring parser state — Ramey's recommendation, and the
thing `CMDSUB-TOKENIZE` should be *replaced* by rather than extended a
fourth time (Iterations 71, 73). This closes
`2.2-quoted-characters.sh`.

**Stage 4 — retire the recorded limitations.**
`FOO=bar; echo $FOO` and `set a b c; echo $#` should now work. Add
differential cases for both, and delete the limitation notes in
`GOALS.md` rather than leaving them to mislead.

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
