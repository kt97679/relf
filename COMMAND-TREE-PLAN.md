# COMMAND-TREE-PLAN.md — parse once into a tree, execute the tree

Written at Iteration 261, before any code, as `PARSE-EXPAND-PLAN.md` was:
the change is large enough that starting with an edit would be the wrong
move. It supersedes that plan's Stage 2, which asked for tokenized body
lines to be cached; this goes the rest of the way, to the shape Ramey
describes for bash and dash has always had. Read `GOALS.md`'s notes on
Ramey's chapter first.

## Why

**The line is the unit of everything.** `shell.4` reads a physical line,
normalizes its operators, tokenizes it into one flat `ARGV`, and then cuts
that array apart with a sequence of splitting passes (`SPLIT-SEMI`,
`SPLIT-ANDOR`, `SPLIT-PIPE`, `SPLIT-AT-KEYWORD`, `GRP-TRACK`, ...).
Compound commands then read further lines themselves, each in its own
way: `if` executes as it reads, `while`/`for`/functions store bodies as
raw text and replay them through a third input source, `case` reads
pattern lines, and whatever follows a keyword on the same line is carried
in a "pending" slot. Each construct needs its own same-line adapter
(`SAME-LINE-DO?`, `ONE-LINE-LOOP?`, `CAPTURE-ONE-LINE-LOOP`,
`CASE-SPLIT-IN`, the compound suffix), and the ones that never got one
are broken. Of `tests/posix`'s ten failures at Iteration 260, six are
this class:

- `cmd & more` on one line (2.9.3)
- a brace group across lines (2.9.4.1)
- text after a nested `fi` on the same line (2.9.4.1)
- a brace group as a pipeline stage (2.9.2)
- redirection on a compound command (2.7, two cases)

and so is the infinite loop GOALS.md records (`n=0; while ...` with `do`
on the next line), and `$( (list) )` (2.6.3) is a lexing fault of the
same scanner. Iterations 255 and 257 each found a bug where a saved "rest
of the line" pointed into buffers a function body overwrote; that whole
hazard exists because the rest of a line is carried as pointers between
passes.

**Speed.** Iteration 260's profile of `tests/bench-vm/loop.sh`, 19,000
dispatches per iteration after that iteration's fixes: the top of the
list is the shell re-reading its own lines - `NORM-PEEK` 9.3%,
`NORMALIZE-OPERATORS` 7.7%, `TOKENIZE-RAW` 6.0%, the keyword literals'
`(S")` 4.1%, `NORM-EMIT`, `EMIT-TOK-CHAR`, `OP-CHAR?`, `WS?`, the split
passes - roughly 40% together, every iteration, for text that cannot
have changed. A loop body parsed once and walked as a tree does none of
it. Expansion (`EXPAND-WORDS`, `$((...))`) and execution remain.

**It is the prerequisite for compiling.** Step 3 of the plan agreed
after Iteration 259 - compiling shell to Forth - needs a tree to compile.
Whether that step is worth taking is to be decided by profiling the tree
walker, not now.

## The shape to move to

```
input source ──► LEXER ──► PARSER ──► tree ──► EXECUTOR
(file, stdin,     tokens      one        nodes     walks nodes;
 -c string,       with        complete   in a      expands words
 eval text,       newline     command    tree      (EXPAND-WORDS,
 $(...) text)     as a token  at a time  arena     unchanged) just
                                                   before each
                                                   simple command
```

### 1. Input sources

One reader interface over five sources: a script file, stdin (with
editing and the `$ ` / `> ` prompts), a `-c` string, an `eval` string,
and command-substitution text. The lexer asks for characters; the source
supplies the next line when the current one is used up. A source that is
a string splits on newlines like a file. This is what makes the `-c`
string with newlines work (a gap recorded in Iteration 251): the string
is a source, not a line.

Interactive prompting falls out: the source prints `> ` when the parser
asks for more input in the middle of a command.

### 2. The lexer

One scanner, replacing `JOIN-CONTINUATIONS`, `JOIN-OPEN-QUOTES`,
`NORMALIZE-OPERATORS` and `TOKENIZE-RAW` - PARSE-EXPAND-PLAN.md's rule
that the codebase must not have two answers to "where does a word end"
still holds; the old four are deleted when the switch is made, not kept
beside it.

Tokens, per XCU 2.3 and 2.10.1:

- `WORD`: raw text, quotes and `$`-constructs intact, as today's raw
  words are - `EXPAND-WORDS` consumes exactly that. Flags travel WITH
  the word (Ramey's `WORD_DESC`; GOALS.md's first recommendation): was
  any part quoted, was the name part quoted, does it contain anything to
  expand.
- `IO_NUMBER`: digits immediately before `<` or `>`.
- `NEWLINE`: an ordinary token.
- operators: `;` `&` `|` `&&` `||` `;;` `(` `)` `<` `>` `>>` `<&` `>&`
  `<>` `<<` `<<-` `>|`.
- `EOF`.

Rules the scanner owns: backslash-newline is removed (outside single
quotes); single and double quotes may span lines; `$(`...`)` is scanned
by lexing its contents recursively (the only reliable way to find its
closing `)` past a `case` pattern's `)` - dash does this), `` `...` ``
by its own quoting rule, and `$((`...`))` by parenthesis depth; a `#`
at the start of a word starts a comment.

**Reserved words are not the lexer's business.** They are recognised by
the parser, and only where the grammar allows one (command position, and
`in`/`do` in their slots). That is what makes `for x in do done` a list
of two words (2.4).

**Aliases** are substituted by the lexer when the parser asks for a word
in command position: the alias value is pushed as a string source in
front of the rest of the input (XCU 2.3.1), with the usual guard against
recursion and the trailing-blank rule.

**Here-documents.** The parser, on `<<` or `<<-`, records the delimiter
and the redirection node to fill. When the lexer next produces a
`NEWLINE`, it reads the pending bodies line by line from the source, in
order, before the next token. The body is stored in the tree (see §3);
expansion of an unquoted body happens at execution, as with any word -
which also lifts the current "no expansion in here-documents" narrowing.

### 3. The tree

Nodes live in a **tree arena**: a growable heap block, addressed by
OFFSETS from its base, like the body arena (it may move while it grows).
A node is a header cell - its type - followed by fields that are cells:
integers, or offsets to other nodes and to strings. Strings (word text,
here-document bodies) are NUL-terminated, in the same arena.

| node | fields |
|---|---|
| `LIST` | count; items, each (node, separator: `;` or `&`) |
| `AND-OR` | count; items, each (pipeline node, op: `&&` or `\|\|`) |
| `PIPELINE` | bang?; count; stage nodes |
| `SIMPLE` | assignment words; words; redirections |
| `SUBSHELL` | body `LIST`; redirections |
| `GROUP` | body `LIST`; redirections |
| `IF` | condition/body pairs (elif chain); else body or 0; redirections |
| `WHILE` / `UNTIL` | condition `LIST`; body `LIST`; redirections |
| `FOR` | name; word list or 0 (meaning `"$@"`); body; redirections |
| `CASE` | word; items, each (patterns, body or 0, `;;`); redirections |
| `FUNCDEF` | name; body (a compound command node) |
| `REDIR` | fd (or -1 for the default); op; target word or here-doc body; quoted-delimiter? |
| `WORD` | offset of text; flags |

Every compound node carries a redirection list, so redirection on
compound commands is not a special case (2.7).

**Lifetimes.** The tree of a complete command read at top level is
built, executed and then discarded - the arena is reset between top-level
commands, where `BUF-FREE-RETIRED` runs today. A function definition
COPIES its body subtree into a block of its own (one heap block per
function, as Iteration 249 did for body text; retired on redefinition,
because a function may redefine itself while running). A loop body is not
copied: the loop node is in the tree being executed, and it is walked as
many times as the loop runs - that is the whole speed argument. `eval`
and `$(...)` parse into their own arenas, freed when they finish.

### 4. The parser

Recursive descent over XCU 2.10's grammar, one Forth word per rule:

```
PARSE-COMPLETE-COMMAND   list, up to NEWLINE or EOF
PARSE-LIST               and_or { (';' | '&' | NEWLINE) and_or }
PARSE-AND-OR             pipeline { ('&&' | '||') linebreak pipeline }
PARSE-PIPELINE           ['!'] command { '|' linebreak command }
PARSE-COMMAND            compound [redirs] | funcdef | simple
PARSE-SIMPLE             { assignment | redirect } word { word | redirect }
PARSE-IF / -WHILE / -UNTIL / -FOR / -CASE / -GROUP / -SUBSHELL
PARSE-REDIRECT           [IO_NUMBER] op word
```

A syntax error is reported with the token and line number and discards
the rest of the complete command, as `sh` does; a non-interactive shell
then continues with the next command, as this shell does today (dash
exits - a separate decision, recorded, not changed here).

Interactive input: when the parser needs a token and the source is at the
end of a line, the source prompts `> ` and reads another. That replaces
every "read the next line" call in the compound runners.

### 5. The executor

`EXEC ( node --- )` dispatches on the node type. The existing machinery
is reused, not rewritten:

- **Simple command**: copy the node's raw words into `ARGV` (with their
  flags) and call `EXPAND-WORDS`, then the existing assignment handling
  (`TRY-ASSIGNMENT`, `TEMP-ASSIGN`), redirections (the node's redirection
  words expanded into the REDIR tables, then `BEGIN-REDIRECT`/
  `END-REDIRECT` or the child's `APPLY-REDIRECTIONS`), and `DISPATCH` /
  `RUN-EXTERNAL`. `EXPAND-WORDS`, the expansion words, globbing,
  `DISPATCH`, builtins, `RUN-EXTERNAL` and the undo list do not change.
- **Pipeline**: fork per stage; each child `EXEC`s its stage node - so a
  compound command or a brace group as a stage is just a node (2.9.2).
- **And-or, list**: status tests and sequencing; `&` forks.
- **Compound commands**: straightforward walks, with `break`/`continue`
  /`return` as today's pending flags, and the node's redirections wrapped
  around the whole compound with the undo list.
- **Functions**: `RUN-FUNC-BODY` becomes save parameters, `EXEC` the
  body, restore.
- **`eval`, `.`**: parse the string (or file) as a source and execute
  each complete command.
- **Command substitution**: the child parses the text and executes it.

What gets DELETED at the switch: the replay input source and its state
(`REPLAY-*`), the pending-remainder mechanism and its text copies
(`PENDING-*`, `COPY-REST-TEXT`, `RT-*`, `AO-*`), the splitting passes, the
same-line adapters, `DO-IF`'s execute-as-you-read, the body-capture loops
(`CAPTURE-CONTINUE?`, `APPEND-RAW-LINE-TO-BODY`), the compound suffix,
`JOIN-*`, `NORMALIZE-OPERATORS`, `TOKENIZE-RAW`, `LINE-IS?` chains, and
the parallel `ARGV-*` copy arrays that only exist to carry split pieces.
Roughly the middle third of `shell.4`.

## Staging

Every stage leaves `tests/verify` green and is committed separately. The
new path is built BESIDE the old one and only becomes the default when it
passes everything the old one passes; `master` never has a half-working
shell.

**Stage A — lexer, parser, tree, and a tree printer.** No execution. A
builtin-free Forth entry, `PARSE-FILE ( c-addr u --- )`, parses a script
and prints its tree in a fixed text form. Acceptance: every script in
`tests/` (shell cases, differential cases, POSIX cases, mrsh cases, the
benchmarks) parses without error, and for each POSIX-conformance script
the syntax verdict matches `dash -n`. A new `tests/parse/` holds small
inputs with their expected trees, including every same-line shape listed
above and here-documents.

**Stage B — the executor, as a second entry.** `MAIN2` (reached with an
environment variable or a flag, not by default) runs scripts through
lexer → parser → executor. All compound commands, functions, pipelines,
redirections, `eval` and command substitution are in this stage: a
partial executor cannot be compared against the suites. Acceptance: the
whole of `tests/verify`'s shell suite, `tests/diff` and `tests/mrsh`, run
with `MAIN2`, at least as good as with `MAIN`; `tests/posix` better.
`tests/verify` gets a `shell2:` line for the duration of this stage.

**Stage C — switch and delete.** `MAIN` becomes the tree path; the old
machinery listed above is deleted in the same commit, with `tests/verify`
green; `GOALS.md`'s "Still open" list is re-audited, since most of its
parser entries should be gone.

**Stage D — measure.** Profile the four workloads again. Only then decide
on step 3 (compiling trees to Forth), with the tree walker's share of the
dispatches as the number to argue from.

## Risks, and what to watch

- **Two answers to "where does a word end."** Stage A adds the new
  lexer while `NORMALIZE-OPERATORS` still exists; Stage C must delete
  the old one, not keep it for some path. `eval` and command
  substitution in particular must move to the new lexer in Stage B.
- **Alias semantics** are defined in terms of tokens and are easy to get
  subtly wrong; the mrsh alias case is scored and GOALS.md records the
  divergence it tests.
- **Error recovery** in a non-interactive shell: skip to the end of the
  complete command, never to the end of a physical line.
- **Memory**: the tree arena is per complete command; a very long
  script is many complete commands, not one tree. A function's tree is
  copied once, not per call.
- **Interactive editing** stays where it is (`ACCEPT-INTO`); only the
  prompting moves into the source.
- **Speed of Stage B** may at first be slower than the old path for
  one-shot commands (a tree is built and discarded). The benchmarks are
  loops; `start` and the shell suite's wall time are the numbers that
  would show it.
