# rill3 - a reference for writing scripts

rill3 is the working name (918) of the language the repository calls the command model; its runner is
still `bin/cm` and its scripts `.cm`.

The language `bin/cm` runs: a shell whose commands pass values - texts, numbers, lists, maps, blocks -
as well as bytes. This page is the language as it stands; docs/COMMAND-MODEL.md is how it came to be.
Every example here is in `tests/cm/scripts/reference.cm`, which the suite runs, and prints what is shown.
At the prompt TAB completes builtins, functions, programs and file names, `$names`, and after a value its
operations - `$l co` TAB, `$l count` - those of the kind the variable holds.

    bin/cm script.cm [args...]      run a script; $args holds the arguments
    bin/cm                          the prompt: a line at a time, variables and functions kept
    #!/usr/bin/env cm               a script that starts so runs as itself, bin/ on PATH

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
4. A command's first word says what runs: a builtin, a function, a value, or else the program of that
   name. A block runs, a boolean is a status; a list, a map or a text does the operation the next word
   names - the value is the command, the operation its subcommand: `$l count`, `$m has k`, `$l set 0 x`.
   A word with a `/` in it is a program's path, never a builtin's or a function's name; a text holding a
   `/` is one too, when the next word names none of a text's operations: `var cmd /bin/date; $cmd`.
5. Values are texts, whole 64-bit numbers, booleans, lists, maps and blocks; a value is one word,
   never split or globbed - `@` spreads a list into words.
6. `$(cmd)` is the text cmd printed, `@(cmd)` its values one by one, `$(( ))` arithmetic and
   comparison.
7. `var` makes a variable in its block, `set` gives one another value; a block sees the variables
   around it, and keeps them - one made in a loop, or by a function that has returned. A list or a map
   changes by its operations - `set`, `append`, `del` - in place: every variable holding it sees it.
8. Every command has a status; `if`, `while`, `&&`, `||` and `!` test it. In a script, a command that
   fails and is not tested ends it, with its status.
9. `|` carries bytes between programs and values between functions; `>` `>>` `<` `2>` `&>` `2>&1`
   redirect as sh's, and `<< END` makes the lines after its line, up to `END`, the command's stdin.
10. The rest are builtins (the table below), the shell's own verbs: control (`if` `for` `while`
   `each` `case` `return` `break` `continue`), values (`put` `range` `glob` `kind` ...), programs
   (`run`), the script (`source` `trap` `exit` `forth`). What is about a value is its operation
   instead - `count` `has` `slice` `split` `set` `append` `del` ...: `$l count`, not `count $l`; what is
   the shell's - a program run, a directory changed, a loop - is a builtin: `run $EDITOR f`, `cd dir`.

## Words

A script is commands, one a line or separated by `;`. A command is words separated by blanks, and a
word's first character says what it is - as Forth reads its input:

| first character | the word is | it ends at |
|---|---|---|
| `'` | a text, exactly as written | the next `'` |
| `"` | a text with `$` values in it, and the escapes `\n` `\t` `\r` `\\` `\"` `\$` `\@` `\[` - any other `\` an error | the next `"` |
| `$` | a value: `$x`, `$l[0]`, `$m[k][j]`; `$(cmd)` a capture; `$(( ))` arithmetic | the name and its `[...]`, or the `)` |
| `@` | a spread: `@l`, `@(cmd)`, `@[a b c]` - several words; inside `"..."` an error (`\@` the character) | likewise |
| `[` | a list `[a b c]`, or a map `[k: v  j: w]`, `["a b": v]`, `[:]` empty | the matching `]` |
| `{` | a block `{ cmds }`, `{|a b| cmds }` | the matching `}` |
| `#` | a comment | the line's end |
| anything else | plain text - a number if written as a whole one is (`42`, `-7`; `01` and `-0` stay texts), `true` and `false` booleans; with `*` or `?` it globs: the paths it matches, sorted, a word each, none an error; a `[`, `]` or `#` inside it is itself | a blank, `;`, or a closer |

A word ends where its form does: nothing may be glued after a quote, a `]`, a `}` or a `$value` but
index keys (below) and, in a map, a quoted key's `:`, and
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
`$l[-1]` is a list's last item, `$t[-1]` a text's last character; past either end an index is an error,
where a slice stops at the ends. An index may follow any value written in one word - a list or map, a
text, a capture - as it follows a variable; `@(cmd)[k]` is the k-th of cmd's values, spread if a list:

    echo [a b c][-1] [k: v  j: w][j] $(printf hello)[0] @('a,b,c' split ,)[2]

`echo`, a value nobody takes, and a value inside `"..."` or joined by `join` all
use one printed form - a list as `[a b]`, a map as `[k: v]`, a block as `<block>` - and a list's or a
map's reads back: pasted into a script, it is an equal value. Inside a list or a map a text is written
as a script would write it - plain when that reads back as the text, quoted when it is empty, `true` or
`false`, ends in `:`, begins with `#` or `@`, is `\`, or holds a blank, a control character or one of
``" ' ` [ ] { } ( ) $ ; | & < > * ?`` - `[a "b c" "" "true" "x:"]`; in the quotes `\"`, `\\`, `\$`,
`\@` before `(`, and `\n` `\t` `\r` - where `echo` of the text itself prints it as it is. A text
that reads as a number is written as one, and reads back as the number, `==` to it; a block does not
read back.

A map's key in `[k: v]` is a word with `:` right after it - plain, `[1: a  a-b: c]`, or quoted,
`["a b": 1  'c d': 2  "$k": 3]`, a `"..."` key with its `$`s as anywhere; `$m set $k v` puts one in
too. A printed map writes its keys so - quoted as a text is, but for `true`, `false` and a `:` at the
end, which a key keeps plain: `["a b": 1  x:: 2]`. Keys are texts - `$m[1]` reads the key `1` -
kept in the order they came; two maps are `==` when they hold the same keys with equal values.

## Variables

    var name ada                    # a new variable, in this scope
    var l [3 1 2]
    var m [name: ada  born: 1815]
    set name grace                  # one that exists
    $m set born 1906                # an element, its value's operation: $m[k] set j too
    $l append 4 5                   # items onto a list
    echo $name $l $l[0] $l[-1] $m[born] $($l count) $($m count) $($name count)
    # grace [3 1 2 4 5] 3 5 1906 5 2 5

`set` gives a variable another value; an element changes by its value's operation - `$m set k v`,
`$l append x`, `$l del 0` - in place (976: `set m[k] v`, `append l x` and `del l[0]` had been builtins).
A list or a map is one value however many variables hold it: after `var b $a`, `$b set 0 9` changes
what `$a` reads too, and a function given a list changes its caller's; `set b [7 8]` gives `b` another
list and leaves `a` its own. `[@l]` is a new list of the same items, `$m merge [:]` a new map.

Scope is lexical. A function - a block - sees its parameters, its own variables, the variables around
it, and the script's top-level variables wherever they are declared: those are known from the script's
start, though one read before its `var` has run is not yet set. A loop's variable is a new one each time round, so a block made in a loop keeps that time's
value. `$env` is the environment, a map: `$env[HOME]` reads a name - one not set is an error, as a
map's missing key is; `$env get EDITOR vi` gives a default - `$env has NAME`, `$env keys` and `$env count`
as any map's; `$env set NAME value` sets it for programs run after, and `$env del NAME` takes it away;
`$args` is the script's arguments, a list; `$status` the last command's status; `$job` the last job `&`
started, for `wait $job` (sh's `$!`). Reading a variable
that does not exist is an error.

## Arithmetic and comparison

`$(( ))` is the one place with infix operators: `+ - * / %`, `== != < <= > >=`, `&& || !`, and
parentheses. Its operators take numbers and texts that read as whole numbers - a boolean, a list, a map
or a block is an error; `<` and the rest put texts in order too, by their bytes; `==` and `!=` compare any
two values, lists item by item, maps entry by entry - the same keys, their values equal, in any order -
and a block equals only itself; `!`, `&&` and `||` take true or
false - a comparison's, a boolean's, a text that reads as one - as a condition does: `$(( !$n ))` is an
error, `$(( $n == 0 ))` the test. It gives a number or a boolean: one value alone in it is read as the
operators read theirs - `$(( "7" ))` is the number 7 - a boolean is itself. `-` before a value negates
it; `/` and `%` round down, as Python's - `$(( -7 / 2 ))` is -4 and `$(( -7 % 2 ))` 1, where sh's
truncate; a division by zero is an error. Inside it a text is quoted, a variable has its `$`, and a list
or a map is a variable's - `$l`, not `[a b]`.

    echo $(( 7 / 2 )) $(( -7 % 2 )) $(( 2 * (3 + 4) )) $(( 3 > 2 )) $(( "abc" == "abc" && !(1 > 2) ))
    # 3 1 14 true true

## Control

`if`, `while`, `for` and `each` are commands that take blocks. A condition is a command, its status
saying - by rule 4 a value is one too: a boolean, as `$(( ))` gives, is its status, and a block runs.

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

`case` tests a value's text against patterns - `*`, `?`, `[...]`, as a text's `match` does - an arm a line, or
several on one; the first arm one of whose patterns matches runs; none, status 0. A plain word is the
pattern as written, not globbed; a quoted one, or a `$var`'s text, is a pattern too, as `match`'s - a `*`
itself is `[*]`:

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
    echo $(sq 7) [@(pair)] $([@(pair)] count)
    # 49 [a b] 2

A function is a command: its arguments are its words, given in the number its parameters name -
another number is an error, `cm: greet wants 1, given 2`. A function may not take a builtin's name:
`var run { }` is an error, for `run` would always be the builtin. `echo` writes bytes; `put` writes
values, one by one. `return n` ends the function with status n - 0 to 255, a larger n taken modulo 256,
as `exit`'s; a bare `return`, the last command's status, as `exit` - from inside its `if` and loop bodies; inside a block called as a function - a callback - it ends that
block. `return` outside a function is an error - `exit` ends the script; so are `break` and `continue`
outside a loop. A sourced file's top level is the script's. `break` and `continue` end or skip a loop's
turn.

    var find {|x| for v @l { if $(( $v == $x )) { return 0 } }; return 1 }
    if find 4 { echo 4 is in l }
    find 9 || echo 9 is not

A block alone as a command, or alone between `&&` and `||`, is a group, as sh's `{ ...; }`: its commands
run in place, and `return`, `break` and `continue` in it are the function's and the loop's (960).

    var need {|f| test -f $f || { echo no $f; return 1 }; echo have $f }
    need /no/such || echo need: $status

A value can stand first in a command: a block runs, its parameters the words after; a boolean gives its
status, and takes no words; a list, a map or a text does the operation the next word names (below) -
with none, an error that says what it has; a number is an error, as it has none. The program a text names runs with `run`: `run $EDITOR notes.txt`, `run @cmd` - a list's
first item the program - and `run "/opt/my tools/x"`; `run` is a program's stage, in a pipeline, with
`&` and in `$( )` and `@( )` as any program is.

    var twice {|f x| $f $($f $x) }
    echo $($twice { |v| put $(( $v * 2 )) } 5)          # 20
    var counter {|start| var c $start; put [inc: { set c $(( $c + 1 )); put $c }] }
    var ctr @(counter 10)

## A value's operations

A list, a map or a text is a command whose subcommands are its operations, as a program's are: the
value first, the operation's name next, its words after - `$l count`, `$m has $k`, `$t split ,`. Each
puts what it makes, as a function does, taken with `$( )` or `@( )`; `has` and `match` give a status;
`set`, `append` and `del` change the value itself, in place, and put nothing.

| operation | list | map | text |
|---|---|---|---|
| `count` | its items | its entries | its characters (UTF-8) |
| `get key default` | | the key's value, or the default when it has none | |
| `has x` | status 0 if an item `==` x | if x is a key | if x is part of it |
| `slice start [end]` | its items from start up to end, put one by one | | its characters, one text |
| `join sep` | one text, sep between the items' printed forms | | |
| `keys`, `merge m2` | | its keys, put; a new map, m2's entries over its | |
| `split sep` | | | its parts between the seps, put |
| `upper`, `lower` | | | in capitals, in small letters - Unicode's simple case mapping: é to É, ж to Ж |
| `match pattern` | | | status 0 if all of it matches - `*`, `?`, `[...]` by character |
| `set key value` | the item at key - an index, negative from the end - is value | the key's value is value, a new key added | |
| `append values...` | the values added at its end | | |
| `del key` | the item at key taken out, those after it moved down | the key and its value taken out | |

`slice`'s start and end may be negative, from the end, and are held to the length; a start past the end
is none. `set`'s and `del`'s index must be in the list - past it, an error; `del` of a key the map has
not, an error. `$env set NAME value` and `$env del NAME` change the environment, for programs run after. `split` by an empty separator is an error, and an empty text splits into one empty part. `has`
of a text asks for a part of it, `match` for the whole - its pattern quoted, for a bare `*.txt` globs
first, as any word does: `$t match '*.txt'`. A word as the operation's name may be a value
too, `$l $op`. A kind that has not the operation is an error that names
the ones it has: `cm: a map has no split - its operations: count has keys merge get`. A number has none -
`$(( ))` does its arithmetic, and `"$n" count` counts its digits. Before 967 they were builtins -
`count $l`, `has $m k`; tools/cm-migrate-ops.py rewrites such a script, and each name as a first word
says it is an operation now: `cm: count: no such program - count is a value's operation: $v count`.
Before 976 an element changed by builtins - `set m[k] v`, `append l x`, `del m[k]`; the same tool
rewrites those (`--976` for those alone), and each says where it went: `cm: del is gone (976) - $m del key`.

    echo $($m count) $($name upper) [@($l slice 1 3)] $($l join -) @('a,b' split ,) @([b: 1  a: 2] keys)
    # 2 GRACE [1 2] 3-1-2-4-5 a b b a
    if $m has born { echo has born }
    var langs [forth rill3]; $langs set 1 sh; $langs append awk; $langs del 0; echo $langs
    # [sh awk]
    'notes.txt' match '*.txt' && echo a text file

## Output, and taking it

- `$(cmd)` is **text**: everything the commands print - a program's bytes, `echo`'s, and values nobody
  takes, in their printed form - one text, its trailing newlines dropped. As sh's.
- `@(cmd)` is **values**: a function's, one by one, or a program's lines - spread where they stand -
  when cmd is a pipeline ending in a program, or its last pipeline after `&&` or `||` is:
  `[@(cd $dir && ls)]`. `[@(cmd)]` makes them a list.
- `var` and `set` take one value, so `var x @(f)` wants f to put one; none or several is an error,
  as `var x a b` is.
- `var` and `set` give the status of the last capture in their value, as sh's `x=$(cmd)`; 0 with none.
- A capture whose command fails, its status untested, stops the script as the command would - in any
  command's words: `echo $(false)` stops; `var x $(cmd) || echo failed` tests it.

        var both [@(pair)]                  # [a b]
        var one @(sq 3)                     # the number 9
        echo $(range 3) @(range 3)          # "0\n1\n2" as one word, then 0 1 2
        var out $(grep x /no/such 2>&1) || echo var status $status   # var status 2

A function whose number of results varies is taken with `[@(f)]` - always a list - or `for x @(f)`.
A `$(f)` in `$(( ))` takes a number f puts, with nothing else made, as the number - no text printed and
read back - as fast as `@(f)`; anywhere else `$(f)` is the text it printed, and `var x @(f)` keeps a
number a number.

## Pipes, programs and redirections

A word that names no builtin and no function runs a program, found on PATH; a word with a `/` in it -
`/bin/date`, `./build.sh` - runs the program at that path, whatever a builtin or a function is named
(978). Between functions a pipe carries values; from a program to a function, lines; from a function to
a program, its values' printed forms, a line each. Programs side by side run together, as sh's; a
function's stage runs in the shell's own process, to its end, before the stage after it starts - so
`yes | f` never ends.

A text first in a command that holds a `/` runs the program at that path, as the same text written there
would, the words after it its arguments - unless the first of them names one of a text's operations, which
it does then (`$cmd count` counts): `var cmd /usr/bin/date; $cmd +%Y`; `$($cmd)` is what it prints and
`@($cmd)` its lines, as `run`'s. It is a value's command still, known only as the script runs: in a
pipeline a function's stage, run to its end before the next starts, and not one `&` starts - `run $cmd`
for those, and for a program a text names with no `/` in it, found on PATH (978).

`each name { body }` is a loop, as `for` is, over the input where it stands: a stage's values - a
function's, or a program's lines - or, with no stage's input (a function not in a pipeline, a
pipeline's first stage, the script), stdin's lines, one at a time, as they come. `break`, `continue` and
`return` in its body are as in `for`'s (977: its body had been a block called with each value, and with
no stage's input it read nothing).

    printf 'one\ntwo\n' | each line { echo got $line }      # got one, got two
    pair | tr a-z A-Z                                         # A, B
    grep x /no/such 2> /dev/null || echo status $status           # status 2
    echo saved > /tmp/cm-ref.txt; echo more >> /tmp/cm-ref.txt; cat < /tmp/cm-ref.txt
    each line { echo read $line } < /tmp/cm-ref.txt               # read saved, read more
    greet file > /tmp/cm-ref.txt                              # functions and builtins redirect too,
                                                              # alone or as a pipeline's stage
    sleep 0 &
    wait                                                      # every job started with &

A here-document, `cmd << END`, is the lines after the one holding it, up to a line that is `END`
alone - cmd's stdin, as `< file` would be. Its lines read as a `"..."` does - `$` values, `\n` a newline,
`\t` a tab, `\r` a carriage return, `\\` `\"` `\$` `\@` `\[` those characters, any other `\` an error, `@( )`
refused - but for `"`, which is itself there. `<< 'END'` takes them all as written, as `'...'` does: for a program's text in one. `END`
may be indented: that much is taken off each line, so a here-document can sit in a block:

    var greet-all {
        cat << END
            hello $name, $($l count) numbers
              last $l[-1]
            END
    }
    greet-all                                                 # hello grace, 5 numbers / "  last 5"
    tr a-z A-Z << 'END' | cat                                 # AS $WRITTEN
    as $written
    END

A pipeline's status is its rightmost failing stage's - a program's, a function's or a builtin's: `false |
cat` fails, and `f | cat || echo failed` sees f fail. `&` starts a pipeline of programs without waiting
and sets `$job`; `wait` waits for every one, `wait $job` for that one; at the script's end any left get TERM.

## Builtins

| builtin | does |
|---|---|
| `var name value`, `set name value` | make a variable, give one another value - an element changes by its value's operation, `$m set k v` |
| `put values...` | write values |
| `echo words...` | write the words' printed forms, a blank between, a newline after - no options: `printf` for those |
| `if c {..} elif c {..} else {..}`, `while c {..}`, `for x values... {..}` | control - with no block run, status 0 |
| `case value { patterns... {..} }` | the first arm with a pattern the value's text matches; none, status 0 |
| `var name {|params| ..}`, `return [n]`, `break`, `continue` | functions and loops |
| `range n` | 0 to n-1, put one by one; none when n is 0 or less |
| `each name {..}` | a loop over the input: a stage's values, or stdin's lines - `each line { .. } < file` |
| `kind v` | text, number, bool, list, map or block |
| `glob patterns...` | each pattern's paths, sorted, put, the patterns in their order - none, none put |
| `run program words...` | the program a text names, given the words: `run $EDITOR file`, `run @cmd` - a program's stage, `&` too; `$cmd words` when the text holds a `/` |
| `read name` | a line of stdin into name, as it is - its blanks kept, nothing split; status 1 at the end - `each line {..}` for every line |
| `source file` | another script read in where the line stands, once - a second source of it does nothing; its path from this file's directory; a name with no `/` not there, from the directories of `$env[RILL3_PATH]`; at the prompt, a later line's source reloads |
| `forth words values...` | Forth run in rill3's own image: the values onto its stack (a number a cell, `true` and `false` -1 and 0, a text its address and length), the words run, what they leave put as numbers |
| `source json.cm`, `source args.cm` | rill3's own library, written in rill3, in `lib/` - `bin/cm` puts it last on `$env[RILL3_PATH]`: `to-json value`, `from-json text`; `parse-args spec argv` (a map of option defaults: a boolean a flag, else a value; `--help` lists them), `usage spec` |
| `wait`, `wait $job` | wait for every job `&` started, the status the last ended with - or for that one job, its status; with none, 0 |
| `cd [dir]`, `exit [n]` | as sh's: `cd` with none to `$env[HOME]`; `exit` with none the last status, n taken modulo 256 |
| `trap { block } [EXIT INT TERM HUP]` | the block run when the script ends - at its end, by `exit`, by an error, or by a signal named, which then ends it with status 128 + the signal; `$status` in it the status the script ends with; a later trap replaces it |

## The prompt

`bin/cm` with no script is the prompt, `cm> `. A line is read - more lines while a bracket or a quote is
open, a here-document's lines are still to come, or the line ends in `|`, `&&` or `||` - and run in one
session: the variables and functions a line makes, the next sees. A value nobody takes is printed, as in
a script. An error is said and the prompt comes back - a failing command does not end it; `^C` ends what
runs; the input's end, `^D` on an empty line, ends the prompt with the last status, as `exit` does. A
`source` there reads the file again each time. At a terminal the line editor is relfsh's
(docs/INTERACTIVE.md): the arrows, `^A` `^E` `^K` `^U` `^T` edit, up and down walk the session's
history, `^R` searches it; TAB completes, as the top of this page says.

## Errors

An error found when the script is read stops it before anything runs; one found as it runs stops it
there. Both say the message, then where: `cm: index 2 past a list of 2 (line 4)` - in a sourced file,
that file's name and line. Either ends the script with status 2. A command that fails untested ends it
with that command's status, saying so: `cm: status 1 - the script stops (line 3)`. A program not found
is status 127, as sh's; a signal a trap names, 128 + the signal.
Recursion is bounded by the engine's return stack, 1 MB: about 40,000 calls deep, 15,000 through `$( )`, 5,000
to 12,000 in a function that uses `return` - past it, `recursion too deep for the stacks`. A value may nest
as deep as memory allows, though printing or comparing one nested past about 20,000 levels says the same.

## For sh users

- Values are never split or globbed: `"$x"` and `$x` are the same word. Quote to join: `"$dir/file"`.
- A command that fails stops the script, as `set -e` would - tested ones aside (`if`, `while`, `&&`, `||`,
  `!`). `cmd || true` lets one fail: `var n $(grep -c x f || true)`.
- sh's forms are errors that name this language's way, when the script is read: `x=5`; `$1`, `$?`,
  `$#`, `$@`, `$!` (`$args[0]`, `$status`, `$($args count)`, `@args`, `$job`); `for i in ...`;
  `name() { }`, `function`, `alias`; `then`/`fi`/`do`/`done`/`esac`; `export`, `local`, `unset`;
  backticks; `echo -n`; `read -r`; `<<END`, `<<-` and `<<<`. A program not found says `cm: name: no
  such program`.
- `/` and `%` round down: `$(( -7 / 2 ))` is -4, where sh's is -3.
- Redirections are `>` `>>` `<` `2>` `2>>` `&>` `2>&1` `>&2`: no `1>` (it is `>`), no `&>>` (`>> f 2>&1`).
- `${x}` only inside `"..."`; `$x` everywhere else. No `$1`: `$args[0]`.
- In `"..."`, a `\` before a character that is no escape is an error, where sh keeps the `\`: a regex
  goes in `'...'` - `grep '\d+'`, `sed 's/\./,/'` - or doubles it, `"\\d+"`.
- Operators need blanks round them: `2> /dev/null`, `a | b`; so does a line's closing `\`.
- `[` is a list, not `test`: `test -f x`, or `$(( ))` for numbers.
- `if $m has $k`, `if $t match '*.txt'`: statuses, as `test` gives.
- `$EDITOR file` is `run $EDITOR file`: a text first in a command is a value, the next word its operation - but
  a text holding a `/` runs the program at that path: `$cmd file` when `cmd` is `/usr/bin/vi`.
- `while read line; do ...; done < f` is `each line { ... } < f`; `read name` reads one line.
- `true` and `false` are booleans, not programs: first in a command, a boolean is its status.
- `$(cmd)` is text - the same as sh's; `@(cmd)` takes a function's values.
- `{ ... }` alone is a group, as sh's `{ ...; }`: `cmd || { echo failed; return 1 }` returns from the function.
  A `{...}` word is a block, not bash's braces: `echo {a,b}` is an error, and a program is not given
  one - `'{}'` for find's `-exec ... '{}' ';'`.
- `export NAME=v` is `$env set NAME v`; `unset NAME` is `$env del NAME`.
- Here-documents as sh's, `<< END` with blanks round it; an indented `END` takes its indent off each
  line, where sh's `<<-` takes tabs. Inside, the escapes are `"..."`'s: `\$5` for a dollar sign, `\n`
  a newline; awk's or a program's text goes in `<< 'END'`.
- `$env[NAME]` of a name not set is an error, not "": `$env get NAME ''`.
- `trap` takes a block, and a signal it names ends the script after it - for cleaning up, as sh's is
  mostly used.
