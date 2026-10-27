# Rill 2 - a scripting language and shell in regular notation (Iteration 834; 835 its prompt and lists' functions)

`bin/rill2 script.r2 [args...]` (a script starting `#!/usr/bin/env rill2` runs as itself); `bin/rill2`
alone, the prompt.
tests/rill2/tour.r2 uses every part of the language below, and tests/rill/run checks its output,
the error scripts in tests/rill2/errors and the rest. It grew from the minimal parser prototyped at
830-833 (docs/FORTH-SCRIPTING.md): one file, rill2/rill2.4, 403 lines of Forth over Rill's runtime.

## Values

Whole numbers; decimals (`2.5`); texts - `"..."` with `\n \t \" \\ \{` and `{expr}` inside, `'...'`
as written; lists `[a, b]`; records `{name: "ada", "born": 1815}`, a key a name or a string; `true`,
`false`, `none`. none, 0, false, "", [] and {} are false. A list or a record holds any value - other
lists and records too, as deep as wanted: `grid[1][0] = 5`, `rec["c"]["e"] = [1, {f: 2}]`. A list prints as Rill prints one: its items
joined by blanks, a list inside it in brackets.

## Expressions

From the loosest: `or`, `and`, `not`, comparisons (`== != < <= > >=`, `in`, `not in`), `+ -`, `* / %`, unary `-`,
then `x[i]`, `x[a:b]` and calls `f(a, b)`. `+` adds numbers, or joins two texts or two lists into a new
one; `x in c` is a list's item, a record's key or a text's part; `/` of two whole
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

`print(a, b, ...)`, `str int decimal len range`; lists: `append(l, x)`, `insert(l, i, x)`, `extend(l, m)`,
`pop(l)` (the last), `pop(l, i)`, `index(l, x)` (-1 if not there); records: `keys values has`, `pop(r, key)` -
taking an item or a field out is pop, which gives it back; `read write lines words split join
trim starts ends contains`, `match sub` (regular expressions), `sort json from_json env args exit wait`.

## Errors

A script is read whole before any of it runs, so a mistake anywhere in it stops it with nothing run:
`rill2: line 3: prnt is not a variable, a def or a command`. An error while running says its line,
inside a def too: `rill: index 2 past a list of 1 (line 3)` - the runtime's words, Rill's.

## The prompt (835)

`bin/rill2` with no script: each input - more lines while a bracket or a string is open, or a line
ends in an operator - is read and run as a script of its own; its variables and defs are the
dictionary's, so they outlive it with no table kept. At a terminal relfsh's line editor reads it: the
arrows and control keys, the session's history and ^R - not TAB completion, which rill2's image leaves
out (3.3 KB of the editor's 7.7; tools/build-rill2-image.sh cuts its section out of shell/edit.4, as
it cuts the characters' widths out of shell.4). An error is said and the prompt comes back; ^C drops a
line being typed and ends what runs; exit() or ^D ends the prompt. At the prompt `else` goes on the
`}` line: a block closed is an input whole. tests/rill2/prompt and tests/rill2/prompt-probe.py.

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
| Rill 2 (836) | 70,130 | 29,776: rill2.4 21.6 KB, its prompt 0.9, editor 7.3 | 18 ms | 12 ms | 233 ms |
| Rill (836) | 90,475 | 50,121: compiler 39.1 KB, editor 11.0 | 8 ms | 10 ms | 229 ms |
| Python | | | 18 ms | 29 ms | 254 ms |
| dash | | | | | 198 ms |

Both images share 40,354 bytes: the kernel, the Forth libraries, the runtime and the regex engine;
the editor's character widths (2.8 KB since 836: 3 bytes a bound, not 4, one search for both
tables) both have too. Rill 2's image is 22 % smaller, prompt and all;
its language less than half Rill's compiler. Rill runs fib faster by its purestack gene (below); the
rest is level, and commands cost what the process costs.

## Stack mode - what Rill's purestack gene does

A def whose parameters are used only as numbers - in arithmetic, comparisons, and calls to itself -
can keep them on Forth's data stack: no variable, nothing saved and restored around each call, no
kinds looked at. For the same `fib`, Rill makes, with it and without, and Rill 2 makes:

    : R:fib  DUP 2 < IF EXIT THEN  DUP 1- RECURSE  OVER 2 R-MINUS RECURSE  R-ADD NIP EXIT ;
    : R:fib  SHADOW{ R.n | }  R.n @ 2 R-CMP-AN < IF R.n @ R-ANY>NUM EXIT THEN
             R.n @ 1 1 R-ARITH-AN RECURSE  R.n @ 2 1 R-ARITH-AN RECURSE R-ADD EXIT ;
    : F.fib  SHADOW{ L1.n | }  L1.n @ 5 D< D-TRUE? IF L1.n @ EXIT THEN
             L1.n @ 3 D- RECURSE  L1.n @ 5 D- RECURSE D+ EXIT 0 ;

8 ms, 43 ms and 18 ms for fib(25). Rill knows `n` is a number from its kinds. Rill 2 would have to
see it in the def - only numbers, its own calls and literals - and check the arguments once on entry,
falling back to the def as it is when one is not a whole number: a second way of making a def's code,
some 1-1.5 KB. QUESTIONS.md Q45.

## Not yet

A list spread into a command's words (Rill's `@list`); setenv; on EXIT; comprehensions; text blocks;
TAB completion at the prompt; defs of numbers on the stack. QUESTIONS.md Q45.
