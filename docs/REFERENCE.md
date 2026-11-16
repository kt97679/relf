# rill3 - a reference for writing scripts

rill3 is the working name (918) of the language the repository calls the command model; its runner is
still `bin/cm` and its scripts `.cm`.

The language `bin/cm` runs: a shell whose commands pass values - texts, numbers, lists, maps, blocks -
as well as bytes. This page is the language as it stands; docs/COMMAND-MODEL.md is how it came to be.
Every example here is in `tests/cm/scripts/reference.cm`, which the suite runs, and prints what is shown.
At the prompt TAB completes builtins, defs, programs and file names.

    bin/cm script.cm [args...]      run a script; $args holds the arguments
    bin/cm                          the prompt: a line at a time, variables and defs kept
    #!/usr/bin/env cm               a script that starts so runs as itself

## rill3 in ten rules

The whole language, each feature below under one of these (925); a new feature fits one, or argues for
an eleventh.

1. A script is commands, one a line or separated by `;`; a command is words separated by blanks. A
   line goes on after `|`, `&&`, `||`, inside brackets, before `else` or `elif`, and after a lone `\`.
2. A word's first character says what it is: `'` a text as written, `"` a text with `$` values, `$` a
   value, `@` a spread, `[` a list or map, `{` a block, `#` a comment; anything else plain text - a
   number if written as one, `true` and `false`, a glob with `*` or `?`.
3. A word ends where its form does; only index keys may follow a value. Operators - `|` `&&` `||` `&`
   and the redirections - are words of their own.
4. A command's first word says what runs: a builtin, a function, a value (a block runs, a boolean is a
   status, a text names a program), or else the program of that name.
5. Values are texts, whole 64-bit numbers, booleans, lists, maps and blocks; a value is one word,
   never split or globbed - `@` spreads a list into words.
6. `$(cmd)` is the text cmd printed, `@(cmd)` its values one by one, `$(( ))` arithmetic and
   comparison.
7. `var` makes a variable in its block, `set` changes one, `del` takes from one; a block sees
   the variables made before them, and keep them.
8. Every command has a status; `if`, `while`, `&&`, `||` and `!` test it. In a script, a command that
   fails and is not tested ends it, with its status.
9. `|` carries bytes between programs and values between functions; `>` `>>` `<` `2>` `&>` `2>&1`
   redirect as sh's, and `<< END` makes the lines after its line, up to `END`, the command's stdin.
10. The rest are builtins (the table below): control (`if` `for` `while` `case` `return`
   `break` `continue`), values (`put` `count` `split` `slice` ...), the script (`source` `trap`
   `exit` `forth`).

## Words

A script is commands, one a line or separated by `;`. A command is words separated by blanks, and a
word's first character says what it is - as Forth reads its input:

| first character | the word is | it ends at |
|---|---|---|
| `'` | a text, exactly as written | the next `'` |
| `"` | a text with `$` values in it, and `\n` `\t` `\"` `\\` | the next `"` |
| `$` | a value: `$x`, `$l[0]`, `$m[k][j]`; `$(cmd)` a capture; `$(( ))` arithmetic | the name and its `[...]`, or the `)` |
| `@` | a spread: `@l`, `@(cmd)`, `@[a b c]` - several words; inside `"..."` an error (`\@` the character) | likewise |
| `[` | a list `[a b c]`, or a map `[k: v  j: w]`, `[:]` empty | the matching `]` |
| `{` | a block `{ cmds }`, `{|a b| cmds }` | the matching `}` |
| `#` | a comment | the line's end |
| anything else | plain text - a number if written as a whole one is (`42`, `-7`; `01` and `-0` stay texts), `true` and `false` booleans; with `*` or `?` it globs | a blank, `;`, or a closer |

A word ends where its form does: nothing may be glued after a quote, a `]`, a `}` or a `$value` but
index keys (below), and
plain text holds no `$` and no quote. Texts and values are joined inside double quotes, where `${name}`
marks where a name ends:

    var k 3
    echo "name: $name, first: $l[0], sum: $(( $l[0] + $l[1] )), line ${k}d" 'no $subst here'
    # name: grace, first: 3, sum: 4, line 3d no $subst here

Operators are words of their own, with blanks round them: `|` `&&` `||` `&` `>` `>>` `<` `<<` `2>`
`2>>` `&>` `2>&1` `>&2`. Glued to a word, as sh writes `2>/dev/null` or `a|b`, they are an error when the
script is read. A substituted value is never split into words and never globbed.

A newline ends a command, except after `|`, `&&` or `||`, before `else` or `elif`, inside brackets, and
after a `\` that is a word of its own at a line's end:

    printf '%s\n' a \
        b

## Values

    echo $(kind hello) $(kind 42) $(kind 1.5) $(kind true) $(kind [a]) $(kind [k: v]) $(kind { })
    # text number text bool list map block

Numbers are whole, 64-bit - -9223372036854775808 to 9223372036854775807, past which arithmetic is an
error; wherever one is wanted - `$(( ))`, an index, `range`, `slice`, `exit` - a
text that reads as one does, as `$(f)` gives a function's number back. Lists and maps are held by reference: two variables can hold one list.
`$l[-1]` is a list's last item. An index may follow any value written in one word - a list or map, a
text, a capture - as it follows a variable; `@(cmd)[k]` is the k-th of cmd's values, spread if a list:

    echo [a b c][-1] [k: v  j: w][j] $(printf hello)[0] @(split 'a,b,c' ,)[2]

`echo`, a value nobody takes, and a value inside `"..."` or given to `join` all
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

Scope is lexical. A function - a block - sees its parameters, its own variables, the variables around
it, and the script's top-level variables wherever they are declared: those are known from the script's
start, though one read before its `var` has run is not yet set. A loop's variable is a new one each time round, so a block made in a loop keeps that time's
value. `$env[HOME]` reads the environment, `set env[NAME] value` sets it for programs run after, and
`del env[NAME]` takes it away;
`$args` is the script's arguments, a list; `$status` the last command's status; `$job` the last job `&`
started, for `wait $job` (sh's `$!`). Reading a variable
that does not exist is an error.

## Arithmetic and comparison

`$(( ))` is the one place with infix operators: `+ - * / %`, `== != < <= > >=`, `&& || !`, and
parentheses. It takes numbers, `$values`, and texts that read as whole numbers; `==` and `!=` compare
texts too, and lists item by item - a map or a block equals only itself. A comparison gives a boolean.

    echo $(( 7 / 2 )) $(( -7 % 2 )) $(( 2 * (3 + 4) )) $(( 3 > 2 )) $(( "abc" == "abc" && !(1 > 2) ))
    # 3 1 14 true true

## Control

`if`, `while` and `for` are commands that take blocks. A condition is a command: its status
says - or a value: a boolean, as `$(( ))` gives, or a block, run, its status saying.

    for i @(range 4) { if $(( $i == 1 )) { continue } elif $(( $i == 3 )) { break } else { echo i $i } }
    # i 0
    # i 2
    var n 0
    while $(( $n < 3 )) { set n $(( $n + 1 )) }

`else` and `elif` follow the `}` before them, on its line or starting the next - a newline ends a
command, but not before them, as a line ending in `|`, `&&` or `||` goes on - and see the
condition's status in `$status`. A condition that tests `$status` replaces it, as in sh: keep it first,
`var s $status`, to use it in the branch.
`&&`, `||` and `!` join commands by their status, as in sh - in a condition too: `if a && ! b { }`.

`case` tests a value's text against patterns - `*`, `?`, `[...]`, as `match` does - an arm a line, or
several on one; the first arm one of whose patterns matches runs; none, status 0. A plain word is the
pattern as written, not globbed; a quoted one is a pattern too, as `match`'s - a `*` itself is `[*]`:

    case report.md { *.txt *.md { echo text } * { echo other } }
    case '*' { '[*]' { echo a star } * { echo other } }

## Functions

A function is a block written to a variable, and called by the variable's name; `$name` is the block
itself, a value to pass on. Only a variable a block was written to is called so - `var date $(date)`
leaves the `date` program alone. A name may hold a `-` between letters: `run-task`.

    var greet {|who| echo hello $who }
    var sq {|x| put $(( $x * $x )) }
    var pair { put a b }
    greet world                         # hello world
    echo $(sq 7) [@(pair)] $(count [@(pair)])
    # 49 [a b] 2

A function is a command: its arguments are its words, given in the number its parameters name.
`echo` writes bytes; `put` writes values, one by one. `return n` ends the function with status n,
from inside its `if` and loop bodies; inside a block called as a function - a callback - it ends that
block. `break` and `continue` end or skip a loop's turn.

    var find {|x| for v @l { if $(( $v == $x )) { return 0 } }; return 1 }
    if find 4 { echo 4 is in l }
    find 9 || echo 9 is not

A block alone as a command, or alone between `&&` and `||`, is a group, as sh's `{ ...; }`: its commands
run in place, and `return`, `break` and `continue` in it are the function's and the loop's (960).

    var need {|f| test -f $f || { echo no $f; return 1 }; echo have $f }
    need /no/such || echo need: $status

A value can stand first in a command: a block runs, its parameters the words after; a boolean gives its
status; a text names a program to run, as `$EDITOR file` does: `var ed vi; $ed notes.txt`.

    var twice {|f x| $f $($f $x) }
    echo $($twice { |v| put $(( $v * 2 )) } 5)          # 20
    var counter {|start| var c $start; put [inc: { set c $(( $c + 1 )); put $c }] }
    var ctr @(counter 10)

## Output, and taking it

- `$(cmd)` is **text**: everything the commands print - a program's bytes, `echo`'s, and values nobody
  takes, in their printed form - one text, its trailing newlines dropped. As sh's.
- `@(cmd)` is **values**: a function's, one by one, or a program's lines - spread where they stand -
  when cmd is a pipeline ending in a program, or its last pipeline after `&&` or `||` is:
  `[@(cd $dir && ls)]`. `[@(cmd)]` makes them a list.
- `var x @(f)` and `set x @(f)` take the one value; none or several is an error.
- `var` and `set` give the status of the last capture in their value, as sh's `x=$(cmd)`; 0 with none.

        var both [@(pair)]                  # [a b]
        var one @(sq 3)                     # the number 9
        echo $(range 3) @(range 3)          # "0\n1\n2" as one word, then 0 1 2
        var out $(grep x /no/such 2>&1) || echo var status $status   # var status 2

A function whose number of results varies is taken with `[@(f)]` - always a list - or `for x @(f)`.
A number taken with `$(f)` is printed and read back as text; in a hot loop, `var x @(f)` keeps it a
number and is about three times faster.

## Pipes, programs and redirections

A word that names no builtin and no function runs a program, found on PATH. Between functions a pipe carries
values, and function stages stream; from a program to a function, lines; from a function to a program,
its values' printed forms, a line each.

    printf 'one\ntwo\n' | each {|line| echo got $line }      # got one, got two
    pair | tr a-z A-Z                                         # A, B
    grep x /no/such 2> /dev/null || echo status $status           # status 2
    echo saved > /tmp/cm-ref.txt; echo more >> /tmp/cm-ref.txt; cat < /tmp/cm-ref.txt
    greet file > /tmp/cm-ref.txt                              # functions and builtins redirect too,
                                                              # alone or as a pipeline's stage
    sleep 0 &
    wait                                                      # every job started with &

A here-document, `cmd << END`, is the lines after the one holding it, up to a line that is `END`
alone - cmd's stdin, as `< file` would be. `$` values in them as in `"..."`; `\$` and `\\` are the
characters, and `"`, `@` and every other `\` as written. `<< 'END'` takes them all as written. `END`
may be indented: that much is taken off each line, so a here-document can sit in a block:

    var greet-all {
        cat << END
            hello $name, $(count $l) numbers
              last $l[-1]
            END
    }
    greet-all                                                 # hello grace, 5 numbers / "  last 5"
    tr a-z A-Z << 'END' | cat                                 # AS $WRITTEN
    as $written
    END

A pipeline's status is its rightmost failing stage's. `&` starts a pipeline of programs without waiting
and sets `$job`; `wait` waits for every one, `wait $job` for that one; at the script's end any left get TERM.

## Builtins

| builtin | does |
|---|---|
| `var name value`, `set name value`, `set name[k] value` | make a variable, change one, change an element |
| `append name values...` | add values to a list |
| `del name[k]` | take an item out of a list - by index, negative from the end - or a key out of a map, in place; `del env[NAME]` unsets |
| `put values...` | write values |
| `echo words...` | write the words' printed forms, a blank between, a newline after |
| `if c {..} elif c {..} else {..}`, `while c {..}`, `for x values... {..}` | control |
| `var name {|params| ..}`, `return [n]`, `break`, `continue` | functions and loops |
| `count v` | a list's or map's items, a text's characters (UTF-8) |
| `range n` | 0 to n-1, put one by one |
| `split text sep`, `join sep values...` | a text's parts put; values joined into one text |
| `slice v start [end]` | a list's items from start up to end, put one by one, or a text's characters as one text; negative from the end, held to the length |
| `keys map`, `merge a b` | a map's keys put; a new map, b's entries over a's |
| `has container v` | status 0 if a map has the key, a list the value, a text the text |
| `match text pattern` | status 0 if the whole text matches a glob pattern - `*`, `?` and `[...]` by character |
| `each {|x| ..}` | the block, run with each value of the function's input |
| `kind v` | text, number, bool, list, map or block |
| `upper text`, `lower text` | the text in capitals or small letters, by Unicode's simple case mapping: é to É, ж to Ж |
| `glob patterns...` | the paths each matches, sorted, put - none, none put |
| `read name` | a line of stdin into name; status 1 at the end |
| `source file` | another script read in where the line stands, once - its path from this file's directory; a name with no `/` not there, from the directories of `$env[RILL3_PATH]`; at the prompt, a later line's source reloads |
| `forth words values...` | Forth run in rill3's own image: the values onto its stack (a number a cell, a text its address and length), the words run, what they leave put as numbers |
| `source json.cm`, `source args.cm` | rill3's own library, written in rill3, in `lib/` - `bin/cm` puts it last on `$env[RILL3_PATH]`: `to-json value`, `from-json text`; `parse-args spec argv` (a map of option defaults: a boolean a flag, else a value; `--help` lists them), `usage spec` |
| `wait`, `wait $job` | wait for every job `&` started, the status the last ended with - or for that one job, its status |
| `cd [dir]`, `exit [n]` | as sh's |
| `trap { block } [EXIT INT TERM HUP]` | the block run when the script ends - at its end, by `exit`, by an error, or by a signal named, which then ends it with status 128 + the signal |
| `true`, `false` | booleans: as a command, status 0 or 1 |

## Errors

An error found when the script is read stops it before anything runs; one found as it runs stops it
there. Both say the message, then where: `cm: index 2 past a list of 2 (line 4)` - in a sourced file,
that file's name and line. Either ends the script with status 2.
Recursion is bounded by the engine's return stack, 1 MB: about 40,000 calls deep, 17,000 through `$( )`, 5,000
to 12,000 in a function that uses `return` - past it, `recursion too deep for the stacks`. A value may nest
as deep as memory allows, though printing or comparing one nested past about 20,000 levels says the same.

## For sh users

- Values are never split or globbed: `"$x"` and `$x` are the same word. Quote to join: `"$dir/file"`.
- A command that fails stops the script, as `set -e` would - tested ones aside (`if`, `while`, `&&`, `||`,
  `!`). `cmd || true` lets one fail: `var n $(grep -c x f || true)`.
- sh's forms are errors that name this language's way, when the script is read: `x=5`, `$1`,
  `for i in ...`, `name() { }`, `then`/`fi`/`do`/`done`, `export`, `local`, `unset`, backticks. A
  program not found says `cm: name: no such program`.
- `${x}` only inside `"..."`; `$x` everywhere else. No `$1`: `$args[0]`.
- Operators need blanks round them: `2> /dev/null`, `a | b`; so does a line's closing `\`.
- `[` is a list, not `test`: `test -f x`, or `$(( ))` for numbers.
- `if has $m $k`, `if match $t '*.txt'`: statuses, as `test` gives.
- `$(cmd)` is text - the same as sh's; `@(cmd)` takes a function's values.
- `{ ... }` alone is a group, as sh's `{ ...; }`: `cmd || { echo failed; return 1 }` returns from the function.
- Here-documents as sh's, `<< END` with blanks round it; an indented `END` takes its indent off each
  line, where sh's `<<-` takes tabs. Inside, `$` is rill3's: `\$5` for a dollar sign.
- `trap` takes a block, and a signal it names ends the script after it - for cleaning up, as sh's is
  mostly used.
