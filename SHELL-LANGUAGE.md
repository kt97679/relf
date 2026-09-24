# SHELL-LANGUAGE.md — a shell language of our own

GOALS.md "What comes next", item 4: a shell language designed from its
own principles - convenient and expressive, but more testable, simpler
to implement and better formalized than the POSIX one this project has
spent five hundred iterations implementing. Part 1 measures where that
language's cost lives, so the design can refuse the right things; Part 2
is the design.

## Part 1 — where the POSIX language's cost lives (Iteration 502)

`tools/feature-cost.py` assigns each of the 821 colon definitions in
`shell.4`, `tree.4` and `edit.4` to a feature by its name - the
per-feature prefixes FORTH-STYLE.md 5 asks for make that possible - and
counts two things per feature: **code**, lines that are neither comment
nor blank; and **trouble**, how many of the 445 iteration titles in
PROGRESS.md name the feature, a proxy for how hard it was to get right
rather than merely to have. The rules are written out in the tool, to be
read and argued with; 2.8% of the code, 91 small helpers, is claimed by
none of them.

| feature | lines | % | trouble | per 100 lines |
|---|---|---|---|---|
| lexer and parser | 1,045 | 12.6 | 21 | 2.0 |
| execution and control flow | 927 | 11.1 | 61 | 6.6 |
| the expander, in general | 778 | 9.4 | 48 | 6.2 |
| line editor, history, completion (not POSIX) | 495 | 6.0 | 17 | 3.4 |
| arithmetic | 467 | 5.6 | 5 | 1.1 |
| pathname expansion and patterns | 380 | 4.6 | 13 | 3.4 |
| variables and the environment | 379 | 4.6 | 22 | 5.8 |
| job control | 328 | 3.9 | 9 | 2.7 |
| quoting, `$'...'`, word encoding | 284 | 3.4 | 25 | 8.8 |
| parameter expansion | 250 | 3.0 | 12 | 4.8 |
| traps and signals | 240 | 2.9 | 9 | 3.8 |
| read | 210 | 2.5 | 5 | 2.4 |
| redirections | 207 | 2.5 | 20 | 9.7 |
| ulimit, umask, kill, times | 200 | 2.4 | 3 | 1.5 |
| prompt escapes (not POSIX) | 196 | 2.4 | 5 | 2.6 |
| echo, printf, backslash escapes | 183 | 2.2 | 3 | 1.6 |
| field splitting (IFS) | 180 | 2.2 | 17 | 9.4 |
| cd and pwd | 170 | 2.0 | 3 | 1.8 |
| aliases | 168 | 2.0 | 10 | 6.0 |
| test and `[` | 156 | 1.9 | 10 | 6.4 |
| here-documents | 137 | 1.6 | 5 | 3.6 |
| command substitution | 134 | 1.6 | 11 | 8.2 |
| options and tracing (`set`) | 130 | 1.6 | 10 | 7.7 |
| getopts | 114 | 1.4 | 2 | 1.8 |
| functions | 87 | 1.0 | 10 | 11.5 |

The rest - plumbing, startup, `forth`, the unclaimed - is under 6%.

### What the numbers say

**No feature can be dropped to halve the source.** The largest single
one is the parser, at 12.6%. Dropping every extra POSIX does not ask for
(the line editor, prompt escapes, `forth`: 8.7%) and every builtin that
could as well be a program of its own (`test`, `echo`, `printf`,
`getopts`, `ulimit` and its kin: another 7.9%) comes to about 17%.

**The cost is the language model, and the trouble is concentrated
there.** The features that needed a fix every ten or so lines are
quoting (8.8 per 100), field splitting (9.4), redirections (9.7),
command substitution (8.2), `set`'s options (7.7) and functions (11.5);
the builtins needed one every fifty or more - arithmetic, the largest
builtin, 1.1 per 100. Trouble lives where features *meet*: one word
passes through tilde, parameter, command and arithmetic expansion, then
field splitting, pathname expansion and quote removal, and every stage
has rules that depend on what the stages before it did - whether text
came from a quote, from an expansion, from an assignment, from a
redirection target. The expander carries flags for exactly those
contexts (`XE-NOSPLIT?`, `WORD-IS-ASSIGN?`, `REDIR-TARGET-WORD?`,
`TOK-WAS-QUOTED?`), and a good part of the log is the story of those
flags leaking into each other: Iteration 471's three fuzzer bugs were
all of that one kind.

**The parser is big but was not where the trouble was** - 2.0 per 100
lines. Its difficulty is the language's: here-documents that begin on
one line and whose bodies come after it, aliases that rewrite the input
as it is read, line continuations inside every construct, reserved
words that are reserved only in some positions, `$(...)` whose end can
only be found by parsing what is inside. The lexer and parser are large
because the grammar is context-dependent at the level of characters.

So the design input is: **a language in which text is never re-read.**
Every one of the troublesome stages exists because POSIX sh turns
values back into text and parses that text again - splitting it,
globbing it, removing quotes from it. Part 2 starts there.

## Part 2 — the design

(Iteration 503.)
