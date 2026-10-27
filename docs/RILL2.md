# Rill 2 - a scripting language and shell in regular notation (Iteration 834)

`bin/rill2 script.r2 [args...]` (a script starting `#!/usr/bin/env rill2` runs as itself).
tests/rill2/tour.r2 uses every part of the language below, and tests/rill/run checks its output,
the error scripts in tests/rill2/errors and the rest. It grew from the minimal parser prototyped at
830-833 (docs/FORTH-SCRIPTING.md): one file, rill2/rill2.4, 403 lines of Forth over Rill's runtime.

## Values

Whole numbers; decimals (`2.5`); texts - `"..."` with `\n \t \" \\ \{` and `{expr}` inside, `'...'`
as written; lists `[a, b]`; records `{name: "ada", "born": 1815}`, a key a name or a string; `true`,
`false`, `none`. none, 0, false, "", [] and {} are false. A list prints as Rill prints one: its items
joined by blanks, a list inside it in brackets.

## Expressions

From the loosest: `or`, `and`, `not`, comparisons (`== != < <= > >=`), `+ -`, `* / %`, unary `-`,
then `x[i]`, `x[a:b]` and calls `f(a, b)`. `+` adds numbers or joins two texts; `/` of two whole
numbers is whole; a decimal and a number make a decimal. An index counts from 0, or from the end when
negative; a slice leaves out either bound; a record's value is `r["key"]`. A line goes on inside
brackets, and after an operator.

## Statements

`x = e`; `x += e` (`-= *= /= %=`); `x[i] = e`, `x[i] += e`, `grid[1][0] = e`. `if c { } elif c { }
else { }` - else and elif on the `}` line or the lines after. `while c { }`. `for x in list { }`, a
record's keys, `range(n)`, `range(a, b)` (counted: no list made). `break`, `continue`. `def name(a, b)
{ }` with `return e` (none without). `#` to the line's end is a comment.

## Names

The script's variables are made by their first assignment; reading one before is an error. A def's
parameters and the names it sets are its own - lexical, as Python's: a def reading a name it does not
set reads the script's. A def may be called before it is defined in the script.

## Commands

A line that is no assignment, no call and no known name runs as a command: its words, `$name` a
variable's text, quotes keeping blanks in a word, `|` between stages, `> >> < 2>` and a path, `&` at
the end to the background (its job in `job`), `#` starting a word a comment. `$(command)` in an
expression is its output. `status` is the last command's status: a failed command does not stop the
script. A command's name is looked for on PATH when the script is read, so a typo is an error, not a
run; `!word ...` runs a command a variable hides. `cd dir` (and `cd` alone: HOME) is built in.

## Library

`print(a, b, ...)`, `str int decimal len range append keys has`, `read write lines words split join
trim starts ends contains`, `match sub` (regular expressions), `sort json from_json env args exit wait`.

## Errors

A script is read whole before any of it runs, so a mistake anywhere in it stops it with nothing run:
`rill2: line 3: prnt is not a variable, a def or a command`. An error while running says its line,
inside a def too: `rill: index 2 past a list of 1 (line 3)` - the runtime's words, Rill's.

## How it works

Each statement is compiled to Forth text and that to a word of its own; a def to `F.name`, and a loop's
body to a word, so that break, continue and return leave it. A first look at the script makes each
def's `FD.name` (a DEFER) for calls before its definition. Values carry their kinds: a whole number is
2n+1 - told by its low bit, never boxed - so two add in an instruction or two; everything else is one
of Rill's items. Library functions are Forth words called by name. The runtime is Rill's, unchanged
but for two things it needed: the script ending it runs (`.rill`, `.r2`) and commands found on PATH
and run directly - one exec, not /usr/bin/env's two, which halved every command's cost for Rill too.

## Size and speed, with Rill's

| | image | the language's part | fib(25) | 300,000 adds | 300 commands |
|---|---:|---:|---:|---:|---:|
| Rill 2 | 61,155 | 20,801 (rill2.4, 403 lines) | 18 ms | 12 ms | 233 ms |
| Rill | 91,795 | 51,441 (compiler 39.1 KB, 1,374 lines; editor 12.3 KB) | 8 ms | 10 ms | 229 ms |
| Python | | | 18 ms | 29 ms | 254 ms |
| dash | | | | | 198 ms |

Both images share 40,354 bytes: the kernel, the Forth libraries, the runtime and the regex engine.
Without its line editor Rill's would be about 79.5 KB - Rill 2's is a quarter smaller, its own part
less than half Rill's compiler. Rill runs fib faster by its purestack gene (a def of numbers on the
stack); the rest is level, and commands cost what the process costs.

## Not yet

The prompt (Rill's needs its line editor: 12.3 KB); a list spread into a command's words (Rill's
`@list`); setenv; on EXIT; comprehensions; text blocks; defs of numbers on the stack. QUESTIONS.md Q44.
