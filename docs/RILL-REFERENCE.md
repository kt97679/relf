# Rill reference

Rill is the scripting language of this repository: Python's expressions and
values, the shell's commands and pipelines, compiled to Forth and run by the
CV8 engine. This document says what Rill is as of Iteration 824; the design
notes are in docs/SHELL-LANGUAGE.md, the history in docs/RILL-ROADMAP.md.

## Running a script

    bin/rill script.rill arg1 arg2 ...
    bin/rill -c 'echo {6 * 7}'          a line or two
    bin/rill --forth script.rill        the Forth it compiles to

Put `bin/` on PATH, or link `bin/rill` into a directory that is (the link is
followed back to this checkout); then a script can start
`#!/usr/bin/env rill`, be made executable, and run as a command - a file
whose first line starts `#!` is Rill whatever its name. The launcher
rebuilds the image when it is missing or older than Rill's sources, and
takes RILL_HOME, RILL_ENGINE and RILL_IMAGE to look elsewhere. Underneath
it is

    ./relf64 kernel64-rill.img script.rill arg1 arg2 ...

The image (built by `sh tools/build-rill-image.sh`) holds the runtime and a
compiler written in Forth. The script is compiled whole, then run.
tools/rillc.py is the same compiler written in Python; the two produce the
same Forth (tests/rill/oracle checks it), and `python3 tools/rillc.py
script.rill` prints that Forth.

## The prompt

`rill` with no script reads Rill a line at a time (824): each line is
compiled and run, and its variables and defs are there for the next - a
variable at the prompt is an item, so a line may bind it to any kind; a
def defined again is the new one from then on (code already compiled
keeps calling the old). A line with a bracket, a string or a text block
left open goes on to the next (`...> `); an error is said and the prompt
comes back; a failed command ends its line only; `exit` or the end of
the input ends the prompt, with that status. With a terminal it prompts
`rill> `; without one, lines are read as they come - `rill < session`.

## Lines, words, comments

A statement ends at a newline or `;`. Inside `[ ]` a newline does not end
anything, so a list can be written over several lines. `#` starts a comment
to the end of the line. Blocks are `{ ... }`.

## Values

| kind | what | written |
|---|---|---|
| number | a 64-bit integer | `42`, `-7` |
| decimal | fixed point, six places | `0.25`, `3.14159` |
| bool | true or false | `true`, `false` |
| text | bytes, UTF-8 as written | `"..."`, `'...'`, a bare word |
| list | items in order | `[1, 2, 3]` |
| record | named fields, in the order set | `{name: "x", n: 3}` |
| item | any of these, its kind known when the script runs | a list's or a record's element, a parameter |

Truth: `false`, `0`, an empty text, list or record are false; all else is
true.

As text (echo, `"$x"`, `join`): a list is its items with a blank between;
a list or a record inside another, and any record, as Rill writes them -
`[1, 2]`, `{a: 1, name: "x"}`, texts in them quoted.

## Texts

- `"..."`: `\n`, `\t`, `\r`, `\uXXXX` (UTF-8), and a backslash before a mark
  (`\"`, `\\`, `\{`, `\$`) is the mark; any other letter after a backslash is an
  error. `$name` puts a
  variable in; `{expression}` puts an expression in; `$(command)` puts a
  command's output in. Inside `{...}` and `$(...)` a `"..."` is a string of its
  own: `"{join($l, ", ")}"`. A `{` always starts an expression: a literal
  brace is `\{`, or goes in single quotes.
- After `$name` in a string comes text, as the shell reads it: `"$name.log"`
  is the name and then `.log`. A field goes in braces, `"{$r[name]}"`; `"$r.f"`
  with a record `r` is an error that says so.
- `'...'`: raw - nothing escaped, nothing put in. Regular expressions are
  usually written so.
- A text block (823) is a `"..."` over lines whose indentation is the
  code's: `"""` ends its line; the lines after it, up to one holding only
  `"""`, are the text, with that closing `"""`'s indentation taken off
  each - a line may go deeper, none less. Escapes, `$name`, `{expr}` and
  `$(...)` as in `"..."`; no newline after the last line.

      def usage(name) {
          echo """
              usage: $name [-v] FILE
                -v    say more
              """
      }
- A bare word that is not a variable is its own text: `case.sh`, `--check`.
  A bare word naming a variable is an error: write `$x`, or `"x"` for the text.

## Variables

    x = 1
    x = $x + 2                      one way: there is no +=
    total = $total - $cost

A variable has one kind over its scope, inferred from everything assigned
to it (a first compiler pass): a number and a decimal join to a decimal, any
other two kinds to an item.

A read that may find a variable not yet set is checked when it runs: `rill:
$x is not set (line N)`. A name never set anywhere is a compile error.

A function reads the script's variables when it runs, set above it or below
it, as a Python function reads its module's globals. Assigning inside a
function makes a local of that name, as in Python without `global`; a
function can change what a script's list or record holds (`seen[$k] = true`)
when that variable is set above the function.

## Expressions

Precedence, lowest first: `or`; `and`; `in`, `not in`, `==`, `!=`, `<`,
`<=`, `>`, `>=`; `+`, `-`; `*`, `/`, `%`. Unary `-` and `not`. `and` and `or`
stop early, as Python's.

- Arithmetic: number with number is a number - `/` is integer division and
  `%` the remainder, as the shell's `$((...))`; a decimal on either side
  makes a decimal. An item meets a number or an item at run time: a decimal
  in either, decimal arithmetic; the result is an item.
- Overflow is an error, not a wrapped number: past 64 bits, or a decimal past
  9223372036854.775807 - `rill: a number too big ... (line N)`; so is a
  division by zero. A literal too big is a compile error. One exception:
  `+ 1` and `- 1` are not checked (counting cannot get there).
- Comparison: numbers and decimals by value (`1 == 1.0`); texts by their
  bytes (Python's order for UTF-8); lists and records by what they hold, as
  Python's `==`; two items by their kinds when the script runs. A text and a
  number cannot be put in order: an error.
- `x in list`, `k in record` (a field's name), `part in text`; `not in`.
- `+` adds numbers only. Texts join in a string, `"$name.log"`, `"{$a}{$b}"`;
  lists in a list, `[@a, @b]`.
- `$l[i]`: an item of a list, `i` from 0, negative from the end; `$r[k]`: a
  record's field (`k` a bare word, a string, or `$name` for a field named by a
  variable); chains `$m[1][0]`, `$r[a][b]`. One way: there is no `$r.k`.
- `[1, 2, 3]`: each item an expression, a comma between them and none after
  the last - `[$x - 1, $x * 2]`; a sign glued to a number is part of it,
  `[1, -2]`; an operator meant as text is quoted, `['-', u8]`. `[@xs, more]`
  spreads a list in (or an item holding one). A record is the same with
  fields, `{a: 1, 'b c': 2}`. Items may go on several lines, the comma at the
  end of each.
- `-x` keeps the kind: a number's, a decimal's, an item's.
- Comprehensions: `[expr for x in list if cond]`, `[expr for i, x in list]`,
  `[expr for k, v in record]`; the `if` takes truth as an `if` does. Their
  variables are their own, as Python 3's: a script variable of the same name
  is neither read nor changed, and after the `]` the name is the script's
  again (`$x` there is an error if nothing else sets it).
- `name(args)` calls a function or the library.
- `(command args)` in a condition is true when the command succeeds;
  `(true)` and `(false)` alone are the values, not the programs. `(name)`
  alone, where name is a variable, is an error - `($name)` is its truth,
  `(env name)` runs a program of that name.

## Statements

    if (cond) { ... } else if (cond) { ... } else { ... }
    while (cond) { ... }
    for x in $list { ... }          for i, x in $list { ... }
    for k in $record { ... }        for k, v in $record { ... }
    for i in range(10) { ... }      range(b), range(a, b), range(a, b, step) - up to b, not with it
    break    continue
    x = v    x[i] = v    a[i][j] = v   x = $x + 1 changes a number: no +=
    case $subject { pat1 pat2 { ... } * { ... } }
    def name(p1, p2) -> kind { ...; return expr }
    on EXIT { ... }
    cd dir    cd dir { ... }        the second goes back after the block
    echo words and "strings"        no options: printf '%s' ... prints without a newline
    echo words out>err              to the error port, without a process
    echo @list | cmd                piped, redirected or captured: the same echo, in a child
    exit    exit n                  a message and a stop: echo "message" out>err; exit 1

- `case`: the first arm with a pattern that matches runs. Patterns are the
  shell's: `*`, `?`, `[...]` (`!` or `^` to negate, ranges), `\` before a
  character; a quoted pattern is the text itself; `$x` as a pattern is one.
- `def`: written as it is called, `def name(a, b)` (no parameters: `def
  name()`); parameters are items; `-> kind` (number, decimal, text, bool, list,
  record) when it returns a value: then every `return` has one. A def without
  `-> kind` returns nothing - `return` alone leaves it, from anywhere in it.
  `return` outside a def is an error: `exit` ends a script. A function is
  defined before its use - in the file, above its first call. It calls itself
  freely; two calling each other cannot be written. Called one way only:
  `name(args)`.
- `on EXIT`: runs however the script ends - its last line, `exit`, a
  failed command, a run-time error, or INT or TERM (see Signals).

## Commands

A statement that starts with a word that is not a keyword, a variable or a
function runs a program, found on PATH:

    git status --short
    make all relfsh-native
    printf '%s\n' "$name" @rest

- Arguments: bare words, strings, `$x`, `@list` (each item an argument,
  of a list or an item holding one; `@args` the script's own).
- A redirection names its port: `out> f`, `out>> f` (appending), `err> f`,
  `err>> f`, `all> f` (both); `err>out` joins errors to output, `out>err`
  output to errors; `< f` is the input. A plain `>` is an error. Pipelines: `a | b | c`; a function can be a stage (no arguments).
- A command that fails stops the script with its status - unless it is a
  condition `(cmd)`, its status is taken with `code((cmd))`, or it is followed
  by `?? statement`, which runs when it fails (`rm stale.lock ?? true`).
- A pipeline fails when any stage fails: its status is the rightmost stage
  that failed (bash's pipefail). A stage stopped because its reader stopped
  (SIGPIPE, as in `yes | head -1`) is not a failure. Where a stage may say
  "nothing" - `grep` finding nothing is 1 - write `?? true`.
- `$(cmd)`: its output as a text, its last newline off; a failing one stops
  the script, unless `$(a ?? b)`: `a`'s output, or - `a` failing - `b`'s
  after it, as the shell's `$(a || b)`.
- `setenv(name, value)`: `env(name)` and every command run after it see it.

## Library

| function | what |
|---|---|
| `len(x)` | items of a list, fields of a record, bytes of a text (a record's fields: `[$k for k, v in $r]`, its values `[$v for k, v in $r]`) |
| `words(t)`, `lines(t)` | a text split at whitespace, at line ends |
| `split(t, sep)` | pieces between seps, empty ones kept (Python's) |
| `join(list, sep)` | the items as texts, sep between |
| `range(...)` | as Python's: 1 to 3 arguments, up to the end, not with it |
| `number(t)`, `decimal(t)` | a text read whole as a number or a decimal, or an error; `number` reads `0x` hex too, `decimal` an exponent (`1e3`); past six places a decimal is truncated (a value as a text: `"$x"`) |
| `from-json(t)` | a JSON text as a value: an object a record, an array a list, a string a text, true and false bools, `null` an empty text; a number as `decimal()` reads it - an integer a number, a fraction or an exponent a decimal |
| `json(x)` | a value as JSON, compact (`{"a":[1,2.5]}`); pretty-printing is a command's (`jq .`) |
| `push(l, x)` | append an item (a list's items: `l = [@l, @more]`) |
| `pop(x, key)` | a list's item (negative from the end) or a record's field, taken out and returned: `pop($l, -1)` the last, `pop($l, 0)` the first |
| `find(x, part)` | where a part first stands in a text (bytes), or an item's index in a list; -1 when not there |
| `sort(l)` | a sorted copy, Python's order, stable; records have none - sort-by |
| `sort-by(rows, field)`, `sort-by(rows, field, desc)` | a list of records by a field, stable |
| `slice(x, a, b)` | part of a list, a text, a record |
| `at(x, key, default)` | a record's field or a list's item (negative from the end), else the default |
| `sum(l)`, `max(l)`, `min(l)` | as Python's: a sum with a decimal among the items is a decimal; max and min give the item itself (of two values: `max([$a, $b])`) |
| `abs(x)` | a number's or decimal's absolute value |
| `starts(t, p)`, `ends(t, s)` | tests on texts (a part anywhere: `part in t`) |
| `replace(t, old, new)`, `trim(t)` | texts changed |
| `match(t, re)` | `[whole, group 1, ...]` of the first match anywhere, or `[]` (re.search) |
| `all(t, re)` | every match: group 1, or the whole (re.findall) |
| `sub(t, re, repl)` | every match replaced; `\1`..`\9` the groups, `\\` a backslash (as sed's) |
| `read(path)`, `write(path, t)` | a file whole |
| `glob(pattern)` | matching paths sorted, `[]` for none - wildcards in the last part |
| `env(name)` | the environment (the script's arguments: `$args`, from `$args[0]`; its path: `$script`) |
| `default(t, other)` | `t`, or `other` when `t` is empty |
| `code((cmd))` | a command's status, a number |
| `spawn((cmd))` | a pipeline started and not waited for - a job: its last stage's pid, a number; its stdin `/dev/null` unless redirected. A job not waited for gets TERM when the script ends; `kill $job` is the command |
| `wait(job)` | waits for a job's stages: its status, as the pipeline's would be (an unknown job, or one waited for, an error) |

Standard commands do the rest, one way each: `printf` formats, `date +%s`
is the clock, `tr a-z A-Z` changes case, `basename`, `dirname` and
`realpath` take paths apart, `awk` has logarithms and the like, and
`xargs -P` (or `sh -c '... & ... wait'`) runs commands side by side. A
command started inside a loop of thousands costs a process each round: do
the whole text at once (`lines($(tr a-z A-Z < file))`), or keep it in Rill
(`sub($p, '^.*/', '')` for a basename).

## Errors and statuses

- A compile error stops before anything runs: `rillc: line N : message`,
  status 2.
- A run-time error names the line of the statement running, innermost
  first: `rill: index 5 past a list of 3 (line 4)`, status 2. An error in the
  engine itself (a crash) gives only its number.
- A command that fails: its status. `exit n`: n.

## Signals

A script with an `on EXIT` block, or one that spawns jobs, catches INT and
TERM: the block runs, the jobs get TERM, and the script exits 128 + the
signal (130, 143), as the shell's trap would - at once while it waits for a
job, at the next statement of the top level otherwise. A script with
neither is stopped at once by them, as any program.

## Memory

Values live in an arena of 128 MB, collected (by copying what is live) at
the safe points between the script's top-level statements - every round of
a top-level loop is one. Inside a function nothing is collected: a function
that loops long making garbage can fill the arena - `rill: out of memory -
... not inside a function (line N)`. Keep such a loop at the top level and
call the function from it.

## Differences from Python, on purpose

- `/` of two whole numbers is integer division, as the shell's.
- Texts are bytes: compared, sliced and counted as bytes.
- Decimals are fixed point with six places, exact in decimal.
- JSON's `null` reads as an empty text (Rill has no None); `json()` never writes it.
- A number variable read before it is set is an error, through a sentinel:
  a script whose number really is -9223372036854775808 would be told it is
  not set.
- Functions are defined before their use and called one way, `name(args)`;
  there is no `global`, no `try` (a condition with `and` says it), no `load`
  or `import` (a script is one file, read whole).
- Globbing is a function, `glob()`, never implicit.

## The compilers' genes

Choices the compilers can make one way or the other - shorter forms, the
collector, line marks, kind inference - are genes, listed with their
defaults in rill/genes.tsv, read by both compilers; RILL_GENES overrides
them for a build (`RILL_GENES=rxcache=0 sh tools/build-rill-image.sh`).

## Tests

`sh tests/rill/run`: every tests/rill/*.rill against its expected output
(most produced by the same program in Python or sh), the error programs in
tests/rill/errors, the signal checks, the memory check
(tools/rill-memcheck.py), and the three rewrites at work (gen-opcodes,
run-utf8) against the scripts they rewrite. `sh tests/rill/oracle`: both
compilers' Forth, word for word. `python3 tools/rill-regex-diff.py N`: the
regular expressions against Python's.
