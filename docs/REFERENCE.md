# The command model - a reference for writing scripts

The language `bin/cm` runs: a shell whose commands pass values - texts, numbers, lists, maps, blocks -
as well as bytes. This page is the language as it stands; docs/COMMAND-MODEL.md is how it came to be.
Every example here is in `tests/cm/scripts/reference.cm`, which the suite runs, and prints what is shown.

    bin/cm script.cm [args...]      run a script; $args holds the arguments
    bin/cm                          the prompt: a line at a time, variables and defs kept
    #!/usr/bin/env cm               a script that starts so runs as itself

## Words

A script is commands, one a line or separated by `;`. A command is words separated by blanks, and a
word's first character says what it is - as Forth reads its input:

| first character | the word is | it ends at |
|---|---|---|
| `'` | a text, exactly as written | the next `'` |
| `"` | a text with `$` values in it, and `\n` `\t` `\"` `\\` | the next `"` |
| `$` | a value: `$x`, `$l[0]`, `$m[k][j]`; `$(cmd)` a capture; `$(( ))` arithmetic | the name and its `[...]`, or the `)` |
| `@` | a spread: `@l`, `@(cmd)` - several words | likewise |
| `[` | a list `[a b c]`, or a map `[k: v  j: w]`, `[:]` empty | the matching `]` |
| `{` | a block `{ cmds }`, `{|a b| cmds }` | the matching `}` |
| `#` | a comment | the line's end |
| anything else | plain text - a number if it reads as a whole one, `true` and `false` booleans; with `*` or `?` it globs | a blank, `;`, or a closer |

A word ends where its form does: nothing may be glued after a quote, a `]`, a `}` or a `$value`, and
plain text holds no `$` and no quote. Texts and values are joined inside double quotes, where `${name}`
marks where a name ends:

    var k 3
    echo "name: $name, first: $l[0], sum: $(( $l[0] + $l[1] )), line ${k}d" 'no $subst here'
    # name: grace, first: 3, sum: 4, line 3d no $subst here

Operators are words of their own, with blanks round them: `|` `&&` `||` `&` `>` `>>` `<` `2>` `2>>`
`&>` `2>&1` `>&2`. Glued to a word, as sh writes `2>/dev/null` or `a|b`, they are an error when the
script is read. A substituted value is never split into words and never globbed.

## Values

    echo $(kind hello) $(kind 42) $(kind 1.5) $(kind true) $(kind [a]) $(kind [k: v]) $(kind { })
    # text number text bool list map block

Numbers are whole, 64-bit. Lists and maps are held by reference: two variables can hold one list.
`$l[-1]` is a list's last item. `echo`, a value nobody takes, and a value inside `"..."` or given to `join` all
use one printed form - a list as `[a b]`, a map as `[k: v]`, a block as `<block>`.

## Variables

    var name ada                    # a new variable, in this scope
    var l [3 1 2]
    var m [name: ada  born: 1815]
    set name grace                  # one that exists
    set m[born] 1906                # an element; set m[k][j] too
    append l 4 5                    # items onto a list
    echo $name $l $l[0] $l[-1] $m[born] $(count $l) $(count $m) $(count $name)
    # grace [3 1 2 4 5] 3 5 1906 5 2 5

Scope is lexical. A def sees its parameters, its own variables, and the script's variables declared
before it. A loop's variable is a new one each time round, so a block made in a loop keeps that time's
value. `$env[HOME]` reads the environment and `set env[NAME] value` sets it for programs run after;
`$args` is the script's arguments, a list; `$status` the last command's status. Reading a variable
that does not exist is an error.

## Arithmetic and comparison

`$(( ))` is the one place with infix operators: `+ - * / %`, `== != < <= > >=`, `&& || !`, and
parentheses. It takes numbers, `$values`, and texts that read as whole numbers; `==` and `!=` compare
texts too. A comparison gives a boolean.

    echo $(( 7 / 2 )) $(( -7 % 2 )) $(( 2 * (3 + 4) )) $(( 3 > 2 )) $(( "abc" == "abc" && !(1 > 2) ))
    # 3 1 14 true true

## Control

`if`, `while`, `for` and `def` are commands that take blocks. A condition is a command: its status
says - or a value: a boolean, as `$(( ))` gives, or a block, run, its status saying.

    for i @(range 4) { if $(( $i == 1 )) { continue } elif $(( $i == 3 )) { break } else { echo i $i } }
    # i 0
    # i 2
    var n 0
    while $(( $n < 3 )) { set n $(( $n + 1 )) }

`else` and `elif` go on the line of the `}` before them. `&&`, `||` and `!` join commands by their
status, as in sh.

## Functions

    def greet {|who| echo hello $who }
    def sq {|x| put $(( $x * $x )) }
    def pair { put a b }
    greet world                         # hello world
    echo $(sq 7) [@(pair)] $(count [@(pair)])
    # 49 [a b] 2

A function is a command: its arguments are its words, given in the number its parameters name.
`echo` writes bytes; `put` writes values, one by one. `return n` ends the function with status n,
from inside any blocks; `break` and `continue` end or skip a loop's turn the same way.

    def find {|x| for v @l { if $(( $v == $x )) { return 0 } }; return 1 }
    if find 4 { echo 4 is in l }
    find 9 || echo 9 is not

A block is a value: called by putting it first, its parameters the words after.

    var twice {|f x| $f $($f $x) }
    echo $($twice { |v| put $(( $v * 2 )) } 5)          # 20
    def counter {|start| var c $start; put [inc: { set c $(( $c + 1 )); put $c }] }
    var ctr @(counter 10)

## Output, and taking it

- `$(cmd)` is **text**: everything the commands print - a program's bytes, `echo`'s, and values nobody
  takes, in their printed form - one text, its trailing newlines dropped. As sh's.
- `@(cmd)` is **values**: a function's, one by one, or a program's lines - spread where they stand.
  `[@(cmd)]` makes them a list.
- `var x @(f)` and `set x @(f)` take the one value; none or several is an error.
- `var` and `set` give the status of the last capture in their value, as sh's `x=$(cmd)`; 0 with none.

        var both [@(pair)]                  # [a b]
        var one @(sq 3)                     # the number 9
        echo $(range 3) @(range 3)          # "0\n1\n2" as one word, then 0 1 2
        var out $(ls /no/such 2>&1)         # $status 2

A function whose number of results varies is taken with `[@(f)]` - always a list - or `for x @(f)`.
A number taken with `$(f)` is printed and read back as text; in a hot loop, `var x @(f)` keeps it a
number and is about three times faster.

## Pipes, programs and redirections

A word that names no builtin and no def runs a program, found on PATH. Between functions a pipe carries
values, and function stages stream; from a program to a function, lines; from a function to a program,
its values' printed forms, a line each.

    printf 'one\ntwo\n' | each {|line| echo got $line }      # got one, got two
    pair | tr a-z A-Z                                         # A, B
    ls /no/such 2> /dev/null || echo status $status           # status 2
    echo saved > /tmp/cm-ref.txt; echo more >> /tmp/cm-ref.txt; cat < /tmp/cm-ref.txt
    greet file > /tmp/cm-ref.txt                              # functions and builtins redirect too
    sleep 0 &
    wait                                                      # every job started with &

A pipeline's status is its rightmost failing stage's. `&` starts a pipeline of programs without waiting;
`wait` waits for every one; at the script's end any left get TERM.

## Builtins

| builtin | does |
|---|---|
| `var name value`, `set name value`, `set name[k] value` | make a variable, change one, change an element |
| `append name values...` | add values to a list |
| `put values...` | write values |
| `echo words...` | write the words' printed forms, a blank between, a newline after |
| `if c {..} elif c {..} else {..}`, `while c {..}`, `for x values... {..}` | control |
| `def name {|params| ..}`, `return [n]`, `break`, `continue` | functions and loops |
| `count v` | a list's or map's items, a text's characters (UTF-8) |
| `range n` | 0 to n-1, put one by one |
| `split text sep`, `join sep values...` | a text's parts put; values joined into one text |
| `keys map`, `merge a b` | a map's keys put; a new map, b's entries over a's |
| `has container v` | status 0 if a map has the key, a list the value, a text the text |
| `match text pattern` | status 0 if the whole text matches a glob pattern |
| `each {|x| ..}` | the block, run with each value of the function's input |
| `kind v` | text, number, bool, list, map or block |
| `glob patterns...` | the paths each matches, sorted, put - none, none put |
| `read name` | a line of stdin into name; status 1 at the end |
| `source file` | another script read in where the line stands - at the top level, its path from this file's directory |
| `cd [dir]`, `exit [n]`, `wait` | as sh's |
| `true`, `false` | booleans: as a command, status 0 or 1 |

## Errors

An error found when the script is read stops it before anything runs, and says its line:
`cm: line 4: ...`. One found as it runs says the line of the command it was in: `cm: index 2 past a
list of 2 (line 4)`; in a sourced file, that file's name and line. Either ends the script with status 2.
Recursion is bounded by the engine's return stack: about 2,500 calls deep, 1,000 through `$( )`, 700 in a
def that uses `return` - past it, `recursion too deep for the stacks`.

## For sh users

- Values are never split or globbed: `"$x"` and `$x` are the same word. Quote to join: `"$dir/file"`.
- `${x}` only inside `"..."`; `$x` everywhere else. No `$1`: `$args[0]`.
- Operators need blanks round them: `2> /dev/null`, `a | b`.
- `[` is a list, not `test`: `test -f x`, or `$(( ))` for numbers.
- `if has $m $k`, `if match $t '*.txt'`: statuses, as `test` gives.
- `$(cmd)` is text - the same as sh's; `@(cmd)` takes a function's values.
- Not here (yet): heredocs (a quoted text may span lines), traps, `case` (`match` is its test).
