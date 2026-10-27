# Rill syntax: a grammar for the proposal, and its ambiguities

You are asked for a second opinion on a small scripting language's syntax. Everything you need is below; nothing else is attached.

## Context: Rill and rill2 - one language for a shell and for scripts

### What exists

relf is a one-person research project: a small Forth virtual machine, and a POSIX shell running
on it. On the same VM run two scripting languages, each meant to be both an interactive shell
and a real scripting language in the spirit of Ruby or Python - with real, nested data:

- **rill2**, the one going forward. Values are dynamic: 64-bit integers (overflow is an error,
  not a wrap), decimals, text, true/false, none, lists and records (maps); lists and records nest
  freely, and a garbage collector reclaims them. A script is read whole and compiled to Forth when
  it starts, by one compiler written in Forth. The whole image - VM kernel, libraries, runtime,
  regex engine, line editor and the language - is 68,912 bytes; the language's own part is about
  21 KB. It has an interactive prompt with line editing and history.
- **Rill**, the older one: much the same commands, but kinds inferred at compile time and two
  compilers (a Python reference and one in the image) that must agree; 90,571 bytes.

Both run commands as a shell does: pipelines, redirections (`>`, `>>`, `<`, `2>`, `2>&1`, `&>`),
`$(cmd)` capture (text, its last newline dropped), background `&`, `cd`. A failed command sets
`status` and the script goes on, unless `strict(true)` makes it stop. A value is never
word-split or globbed. Also: defs (callable before their definition), `if/elif/else`, `while`,
`for x in ...`, `break`, `continue`, `case`, list comprehensions, `"""` text blocks,
`on EXIT { }`, `cd dir { }`.

### One program in both, today (both run; same output)

Rill:

    x = 7
    y = $x * 2 + 1
    echo "hello $name, twice {$x * 2}"
    for i in range(3) { if ($i != 1) { echo "i $i" } }
    def sq(n) -> number { return $n * $n }
    dir = /tmp
    ls $dir out> /dev/null
    n = $(printf 'a\nb\n' | wc -l)
    false ?? echo "failed"

rill2:

    x = 7
    y = x * 2 + 1
    print("hello {name}, twice {x * 2}")
    for i in range(3) { if i != 1 { print("i {i}") } }
    def sq(n) { return n * n }
    dir = "/tmp"
    ls $dir > /dev/null
    n = $(printf 'a\nb\n' | wc -l)
    false
    if status != 0 { print("failed") }

### How each tells a command from code, today

- **Rill** decides by syntax: a variable named `ls` does not stop `ls -l` running. Variables
  are read as `$x` everywhere, arithmetic included, and bound bare (`x = 7`, `for i in`,
  `def sq(n)`). A bare word in code is text (`dir = /tmp`). `{expr}` puts an expression into a
  string or a command word; a literal brace is written `\{`.
- **rill2** decides by lookup: a line whose first word is a known variable or def is code;
  otherwise that word must be a program found on PATH when the script is read, or the whole script
  is refused; `!word` forces a command. Variables are bare in code and `$x` in commands. Every
  `"..."` string interpolates `{expr}`.

### Measured on the current builds

| probe | Rill | rill2 |
|---|---|---|
| `ls = 5`, then `ls -l /tmp` | runs ls | error "l is not defined" - read as `ls - l` |
| a branch never taken runs `dnf`, absent on this machine | runs | the whole script refused before it starts |
| JSON-like text in a string, `"JSON-ish: {\"a\": 1}"` | an error unless the braces are escaped (`\{`) | an error |
| `x = dri`, a mistyped variable name | silently the text "dri" | an error |
| `l = [1, "a b", [2, 3]]` given to a program as `$l` | one argument (items joined by blanks) | one argument, `1 a b [2, 3]` |
| the same list given as `@l` | one argument per item | `1`, `a b`, `2 3` - the nested list joined |
| `$n+1` in a command word, n 5 | the text `5+1` | the text `5+1`; `{n + 1}` gives 6 |
| `for f in /tmp/*.log` | error: needs a list | error: needs a value; `for f in glob("/tmp/*.log")` works |
| a def called like a command, `greet bob` | error: call it as `greet(...)` | error: greet is not defined |
| a bare variable name typed at the prompt | - | prints nothing |
| a command inside a one-line block, `if c { echo hi }` | runs | error "} is missing" - the command took the `}` as a word; on separate lines it runs |

### The owner's aim, in his words (lightly edited)

"I want a combination of a shell with a real scripting language similar to Ruby or Python. The
shell is already a reasonable scripting language, with functions, global and local variables,
arrays and hashmaps. Its limit: an array or hashmap can't hold another, so there are no advanced
data structures (the workaround is JSON and jq). And with a shell it is natural to write
`ls $dir`; without `$` it is not obvious how to substitute in the most natural way. Mixing `var`
and `$var` looks inconsistent, can be confusing and may result in errors."

### Already known - no need to repeat

A study of other designs, from their own documentation: one sigil everywhere (fish, Elvish,
PowerShell, Nushell); two modes chosen by syntax (Oils' YSH: `var x = ...`, `if (expr)`,
`$[expr]`, `@x`); two modes chosen by looking names up (xonsh, like rill2 - after `ls = 44` and
`l = 2`, `ls -l` gives 42); commands quoted inside a language (Hush's `{ }` blocks, zx's
`` $`...` `` templates). Lessons drawn: decide a line's kind by its syntax, never by what names
exist; never split or glob a value; spread lists into arguments on purpose; quote text in code;
the same characters should mean the same thing everywhere; one character should start every
substitution; errors should come from the text, not from the machine it runs on. An earlier
round of other models' reviews advised keeping Rill's `$` rule, keeping commands and function
calls apart, and better diagnostics.

### The proposal under consideration - A: one sigil, syntax decides

- **R1.** A variable is always written `$name`: read, assigned, a parameter, a loop variable
  (`$total = 0`, `$total += $n`, `def area($w, $h)`, `for $f in ...`). A bare word is never a
  variable; `total = 0` is an error that says `$total = 0`.
- **R2.** A statement's first token alone decides what it is; nothing is looked up. A keyword
  starts its statement; `$name` starts code (an assignment or an expression); `name(` with no
  space is a call; a number, a quote, `[`, `(` or `not` starts an expression; any other word
  starts a command - a program, a def or a builtin. `command $EDITOR $f` runs a program named by
  a value. A missing program is an error when its line runs, as in a shell.
- **R3.** A command's words are text. In a word, `$name` and `$name[key]` give one value as one
  argument, never split or globbed; `${name}` where letters follow; `$(...)`; `@name`,
  `@name(...)` and `@(...)` spread a list, one argument per element. A `.` after a name is text
  (`$f.bak`); globs come from the word's own characters (`$dir/*.log`), never from a value. A
  list or record given as `$x` to a program is an error that says `@x` or `$(json($x))`; given to
  a def or builtin, it passes whole.
- **R4.** `$(...)` is the one way in, for commands and expressions both, R2 deciding what is
  inside: `$(date)` is a command's output; `$($n + 1)` and `$(len($l))` are values; the shell's
  `$(( ))` falls out of it. `@(...)` gives a list (a command's lines, or an expression's list);
  `?(...)` gives whether a command succeeded.
- **R5.** In code, text is quoted. The bare words allowed in code: keywords, a call's name before
  `(`, and keys in `{key: v}` and `$m[key]`. Any other bare word is an error asking for `$dir` or
  `"dir"`.
- **R6.** A string substitutes exactly what a command word does - `$name`, `$name[key]`,
  `${name}`, `$(...)` - and nothing else: `{` and `}` are characters. `'...'` substitutes nothing.
- **R7.** Data nests: `[1, "a", [2, 3]]`, `{name: "ada", tags: ["x"]}`; one indexing everywhere,
  `$cfg[servers][0][host]`, in code, in a word and in a string. JSON in and out: `from_json(...)`,
  `json(...)`.
- **R8.** `if` and `while` take a command (its exit status) or an expression (its truth), as R2
  decides; `?(...)` mixes the two.
- **R9.** Iteration takes words, as a command's arguments do: `for $f in $dir/*.log`,
  `for $s in @stats`, `for $i in @range(10)`; comprehensions the same. `for $x in $list` is an
  error that says `@list`.

One task in rill2 today (it runs), and in A (not built yet):

    # rill2 today
    cfg = {logdir: "/var/log/app", limit: 2}
    stats = []
    for f in glob(cfg["logdir"] + "/*.log") {
        n = int($(wc -l < $f))
        errs = int($(grep -c ERROR $f))
        stats += [{file: f, lines: n, errors: errs}]
    }
    for s in sort_by(stats, "lines") {
        file = s["file"]
        lines = s["lines"]
        print("{file}: {lines} lines")
    }
    big = [s["file"] for s in stats if s["lines"] > cfg["limit"]]
    if len(big) > 0 {
        tar czf old.tgz @big
    }

    # A
    $cfg = {logdir: "/var/log/app", limit: 2}
    $stats = []
    for $f in $cfg[logdir]/*.log {
        $n = int($(wc -l < $f))
        $errs = int($(grep -c ERROR $f))
        $stats += [{file: $f, lines: $n, errors: $errs}]
    }
    for $s in @sort_by($stats, "lines") {
        print "$s[file]: $s[lines] lines"
    }
    $big = [$s[file] for $s in @stats if $s[lines] > $cfg[limit]]
    if len($big) > 0 {
        tar czf old.tgz @big
    }

**The alternatives.** A′: as A, but bound bare as the shell and Rill do (`total = 0`,
`for f in`, `def area(w, h)`), read with `$`. B: YSH's two modes - bare names in code, `$x` in
commands, the boundary fixed by syntax (`var`/`setvar`, `if (...)`, `$[expr]`). C: rill2 as it is.

### Constraints

- One compiler, hand-written in Forth, recursive descent; it reads the whole script before it runs.
- Small: the language's part is about 21 KB, and every kilobyte is noticed.
- Errors before running wherever the text allows; never a silent wrong result.
- The same syntax at the interactive prompt as in scripts; interactive use matters as much.
- A POSIX shell on the same VM stays. This language need not be POSIX-compatible, but shell
  habits - `ls -l $dir`, `cmd > file`, `a | b`, `$(cmd)` - should keep working.

## Your task: a grammar for A, and where it is ambiguous

Write a grammar (EBNF or PEG) for A's statements, command words, expressions and strings as
R1-R9 describe them - what a hand-written recursive-descent compiler needs. It may read
characters directly or tokenize first; say which you assume. Then:

1. List every decision that needs more than one token (or character) of lookahead, or depends
   on whitespace (`name(` against `name (`, `$x[0]` against `$x [0]`, `a -b` against `a - b`),
   with the lookahead each needs.
2. List every ambiguity - input the grammar can read two ways - with the input, both readings,
   and which one R1-R9 pick, or that they do not decide.
3. Parse these, as a tree or in brackets: `$x = $(ls -l | wc -l)`,
   `print "$s[file]: $($n + 1)"`, `if $n > 3 and ?(test -f $f) {`, `for $f in $dir/*.log {`,
   `tar czf a.tgz @files`, `echo $f.bak ${base}s`, `$m[a][0] += 1`,
   `[$x * 2 for $x in @l if $x > 1]`, `LANG=C sort file`, `command $EDITOR $f`,
   `if $c { tar czf a.tgz @big }` (does `}` end the command?), `echo {a,b} '{}' "{}"`.
4. Say which rules, if any, cannot be decided from the text alone.

## How to answer

At most about 900 words of prose; code, grammar and tables do not count, but keep them to what
the answer needs. Do not restate the question. Give each claim with how to check it - a script
and the result to expect, or a link. List references with links at the end. Write "unsure"
where you are unsure: here a confident wrong answer costs more than a gap.
