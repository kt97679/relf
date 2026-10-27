# Rill 2 - a scripting language and shell in regular notation (Iteration 834; 835 its prompt and lists' functions; 837 stack mode)

`bin/rill2 script.r2 [args...]` (a script starting `#!/usr/bin/env rill2` runs as itself); `bin/rill2`
alone, the prompt.
tests/rill2/tour.r2 uses every part of the language below, and tests/rill/run checks its output,
the error scripts in tests/rill2/errors and the rest. It grew from the minimal parser prototyped at
830-833 (docs/FORTH-SCRIPTING.md): one file, rill2/rill2.4, 403 lines of Forth over Rill's runtime.

## Values

Whole numbers - 64 bits, past which an error says so (837); decimals (`2.5`); texts - `"..."` with `\n \t \" \\ \{` and `{expr}` inside, `'...'`
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
| Rill 2 (837) | 71,770 | 31,416: rill2.4 23.2 KB, its prompt 0.9, editor 7.3 | 11 ms | 17 ms | 233 ms |
| Rill (836) | 90,475 | 50,121: compiler 39.1 KB, editor 11.0 | 9 ms | 12 ms | 229 ms |
| Python | | | 18 ms | 29 ms | 254 ms |
| dash | | | | | 198 ms |

Both images share 40,354 bytes: the kernel, the Forth libraries, the runtime and the regex engine;
the editor's character widths (2.8 KB since 836: 3 bytes a bound, not 4, one search for both
tables) both have too. Rill 2's image is 22 % smaller, prompt and all;
its language less than half Rill's compiler. fib runs on the stack in both (below); a loop of adds
costs Rill 2 its numbers' checks - tagged, and looked at for overflow - and commands cost what the
process costs.

## Stack mode (837)

A def whose parameters are whole numbers it only does arithmetic on, compares, and passes to itself
or to another such def - `if`, `elif`, `else` and `return` its only statements, a truth used only to
decide an `if`, and its last statement a `return` with a value - is made twice: `FS.name` keeps the
numbers raw on Forth's data stack, where Rill's purestack gene keeps them - no variable, nothing saved
around a call, no kinds looked at - and `G.name` is the def as any other's. `F.name` looks at its
arguments once: whole numbers go to `FS.name`, anything else - `fib(2.5)` - to `G.name`, so nothing a
script sees changes. The arithmetic is Rill's checked words, and a result past 62 bits comes back
boxed. For fib:

    : FS.fib  DUP 2 < IF EXIT THEN  DUP 1 R-MINUS RECURSE  OVER 2 R-MINUS RECURSE  R-ADD NIP EXIT ;
    : F.fib   DUP 1 AND IF 2/ FS.fib N>ITEM ELSE G.fib THEN ;

Rill's purestack makes `: R:fib DUP 2 < IF EXIT THEN DUP 1- RECURSE OVER 2 R-MINUS RECURSE R-ADD NIP
EXIT ;`. fib(25): 11 ms, Rill's 9; without stack mode 30. `RILL2_STACK=0` turns it off, and
tests/rill/run runs every tests/rill2/*.r2 both ways against one expected output. Some 1.2 KB.

Numbers past 62 bits (837): the tagged arithmetic of 831 wrapped silently - 2^62-1 + 1 was -2^62.
Adds and subtracts now look at the overflow, a multiply takes the fast way only under 2^30, a
comparison no longer subtracts; a number past 62 bits is boxed, past 64 an error with its line
(tests/rill2/numbers.r2, errors/overflow.r2).

## Rill and Rill 2 side by side (838)

The same program in each - tests/rill2/compare/side.rill and side.r2, 541 and 542 bytes - prints
the same lines, and tests/rill/run checks it. Where they differ:

| | Rill | Rill 2 |
|---|---|---|
| a variable read | `$x`; a bare word is a text (`files = [a.txt, b.txt]`) | `x`; texts quoted |
| into a string | `"$name {$x * 2}"` | `"{name} {x * 2}"` |
| a condition | `if ($x > 1) { }`, `else if` | `if x > 1 { }`, `elif` |
| adding to | `x = $x + 1` (one way) | `x += 1`, `-= *= /= %=` |
| a def | `def f(a) -> number { }` - its kind said | `def f(a) { }` |
| kinds | inferred when compiled; a mismatch found before it runs | looked at when used |
| a failed command | stops the script, unless `?? statement`, `(cmd)` or `code((cmd))` | sets `status`; the script goes on |
| ports | `out> err> all> out>> err>> err>out out>err <` | `> >> 2> <` |
| a job | `j = spawn((cmd))`, `wait($j)` | `cmd &`, `wait(job)` |
| echo | Rill's own, no process | /bin/echo; `print()` its own |
| a list into words | `@list`, `@args` | - |
| scope | a def's parameter shadows the global of its name for the call (the bug of 832) | lexical |
| a def | above its first call | anywhere: called before it is defined too |
| the prompt | the editor with TAB completion | the editor, no TAB |

Only Rill: comprehensions `[$x * 2 for x in $l if $x > 1]`; text blocks `"""`; `case` with the
shell's patterns; `on EXIT`; `cd dir { }`; `for i, x in` and `for k, v in`; `range(a, b, step)`;
`setenv`, `glob`, `code`, `default`, `at`, `find`, `sum`, `max`, `min`, `abs`, `replace`, `all`,
`slice`, `sort-by`, `number`; a function as a pipeline's stage; `$script`; two compilers whose Forth
the oracle compares, and a fuzzer. Only Rill 2: `+=` and the rest; `print` of several; `insert`,
`extend`, `values`, `has`, `index` (Rill's `find`), `str`, `int`; slices as `x[a:b]`; lists joined
by `+`; `!cmd`; a typo a command caught on PATH before it runs; defs called before they are defined.
Both: numbers checked at 64 bits, decimals, Python's division (`-7 / 2` is -4), texts, lists,
records, `in`, regular expressions, JSON, `$(...)`, pipes, `cd`, the prompt with its editor and
history, the same runtime and collector.

## Not yet

A list spread into a command's words (Rill's `@list`); setenv; on EXIT; comprehensions; text blocks;
TAB completion at the prompt. QUESTIONS.md Q45.
