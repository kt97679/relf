# Answers to the grammar prompt, checked (848)

Four answers to `ask-rill-syntax-grammar-847.md` (rules R1-R16): Gemini, DeepSeek, ChatGPT and
Qwen, as the owner named them. They agree on the shape: a recursive-descent parser reading
characters, or a tokenizer that keeps adjacency; one parser for commands and one for expressions,
chosen by the first token; adjacency deciding `name(` against `name (`, `$x[` against `$x [` in a
word, `-b` against `- b`. Their grammars were read against R1-R16; the gaps they found were
measured on today's rill2, whose behaviour the language keeps.

## New holes, checked

| | finding | from | checked | verdict |
|---|---|---|---|---|
| G1 | operator precedence and associativity unspecified | ChatGPT; all assume Python's | rill2 today: `1 + 2 * 3` 7, `10 - 3 - 2` 5, `true or false and false` true, `not 1 == 2` true, `12 / 2 / 3` 2, `-7 % 3` 2; `1 < 2 < 3` refused; no `**` | held - rill2's order is the spec |
| G2 | a statement starting with `{`: record, command or block? | DeepSeek | R2 does not list `{`; rill2 today reads `{a: 1}` as a record | held |
| G3 | `$x [0]` in code: index or not? | DeepSeek (index), ChatGPT (adjacency) | rill2 today: `l [1]` indexes | held - to be said |
| G4 | which errors come before running, which when the line runs | DeepSeek, ChatGPT, Qwen | R12 needs the script's bindings - the whole script is read first; R16, R3's list given to a program, R10's unset name and R14's empty list need values | held |
| G5 | how `@(...)` splits into lines | ChatGPT | R4 says only "a command's lines" | held |
| G6 | `@cmd` with an empty list | DeepSeek | R14 silent | held - an error when run |
| G7 | nested captures and quotes, `$(printf '%s\n' "$(echo x)")` | ChatGPT | A requires it; rill2 today prints `$(echo x)` | held - and a rill2 bug under it (below) |
| G8 | record keys | ChatGPT | rill2 today takes bare and quoted keys | held - to be said |

## A wrong premise, found checking G7

The brief said both languages run `$(cmd)` captures as a shell does. True of Rill; in rill2 only in
code. Inside a command's words, quoted or not, rill2 passes `$(...)` through as text:
`echo "today $(echo x)"` prints `today $(echo x)` (dash and Rill: `today x`), `echo $(echo $(echo x))`
prints itself, so `mkdir backup-$(date +%F)` would make a directory of that name. No answer leaned
on it - they read A, where R3 and R4 define captures in words - but it is a silent wrong result in
rill2 today, worse than the one-line block of 845: to mend, with a test.

## What did not hold

- Gemini: its `OrExpr` chains `and` and its `AndExpr` `or`; `?` and `@` as unary operators, which
  R4 and R15 do not have; `?(test -f $f)` parsed as a capture - it is a success test; `print "..."`
  parsed as a call - R2 makes it a command, only `print(` calls; R13's hint given as `@ls` - it is
  `@(ls)`.
- Qwen: its `Text` excludes `{` and `}`, so `{}` cannot be a word - against R3 and its own parse of
  `find -exec`; its `Spread` takes `@$x`, which R15 refuses; `?(...)` parsed as a capture; `$f.bak`
  parsed as text with no substitution - R3 substitutes `$f`, then `.bak`.
- DeepSeek: `echo a$b` "ambiguous" - R3 decides it: a `$` before a letter substitutes.
- ChatGPT: "R10 does not say when the environment is read" - it says: when read. "R12 contradicts
  a syntax-only policy" - it uses the script's own bindings, text the compiler holds whole; said
  outright in R21 below.

## Ranked

1. DeepSeek - explicit assumptions, a fourteen-row lookahead table, G2, G3, G6, the split between
errors before running and when run. 2. ChatGPT - G1, G4, G5, G7, G8 and sound advice; one misreading
of R10. 3. Qwen - compact, the same split; a grammar against R3 and R15. 4. Gemini - `and` and `or`
swapped, operators the rules lack, misparses.

## Adopted - A.3, nothing built yet

- **R17.** Operators and their order are rill2's today - Python's: `or`, `and`, `not`, comparisons
  (not chained), `in` and `not in`, `+ -`, `* / %` (integer `/` floors; `-7 % 3` is 2), unary `-`;
  no `**`.
- **R18.** A statement starting with `{` is an expression - a record. Inside an expression a space
  before `[` or `(` is allowed (`$l [1]` indexes, as in rill2 today); where R2 decides - a
  statement's start, inside `$(...)`, a header - `name(` must touch to be a call.
- **R19.** Record keys are names or quoted strings.
- **R20.** `@(...)` splits a command's output at newlines, its trailing newlines dropped first;
  empty lines between are kept. `@cmd` with an empty list is an error when it runs.
- **R21.** Before running, from the text - the whole script, defs included: R1, R5, R2's shapes,
  `$name[` in a word (R3), R12, R13, R15. When the line runs: a missing program (R2), a list or
  record given to a program (R3) or put beside text (R16), an unset `$NAME` (R10), an empty `@cmd`
  (R20). Never an empty string, never a silent pass.
- **R22.** Captures nest, and a `"..."` inside a capture holds captures of its own:
  `$(printf '%s\n' "$(echo x)")` is `x`.

The question is answered; no more models need this prompt.
