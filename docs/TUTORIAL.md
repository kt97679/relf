# rill3 in an hour - a tutorial

rill3 is a shell and a scripting language in one: it runs programs and pipes them as sh does, and
it has values - numbers, lists, maps, functions - so a script needs no Python to hold its data. This
tutorial walks through it in order; docs/REFERENCE.md is the whole of it. Every example here is run by
the test suite (tests/cm/scripts/tutorial.cm), so what it shows is what rill3 does.

Run a script with `bin/cm script.cm`, or start the prompt with `bin/cm` alone.

## 1. Commands and words

A line is a command: words separated by blanks. The first word says what runs - a builtin, a function
of yours, a value, or a program.

    echo hello world
    ls /tmp > /dev/null

A word's first character says what it is: `'...'` a text exactly as written, `"..."` a text with
`$values` in it, `$` a value, `[` a list or a map, `{` a block, a digit a number.

    echo 'single: $x stays' "double: $(( 2 + 3 ))"
    # single: $x stays double: 5

## 2. Variables and values

`var` makes a variable, `set` changes it. A value is never split or globbed: one value, one word.

    var name 'Ada Lovelace'
    var langs [forth rill3]
    var born [year: 1815  city: London]
    set langs[1] sh
    echo "$name knows $langs, born in $born[city]"
    # Ada Lovelace knows [forth sh], born in London

Numbers are whole; arithmetic and comparison live in `$(( ))`.

    var n 7
    echo $(( $n * 6 )) $(( $n > 5 ))
    # 42 true

## 3. Lists and maps

    var l [3 1 2]
    append l 5
    echo $($l count) $l[0] $l[-1] [@($l slice 1 3)]
    # 4 3 5 [1 2]
    var m [a: 1]
    set m[b] 2
    for k @($m keys) { echo $k is $m[$k] }

A list, a map or a text is a command, its operations its subcommands - as `git commit` is git's: `$l
count`, `$l slice 1 3`, `$m keys`, `$t split ,`, `$t upper`; `$m has a` and `$t match '*.txt'` give a
status, for `if`.

`@` spreads a list into words: `@l` is its items, one word each.

## 4. Control

    for x @[1 2 3] { if $(( $x == 2 )) { continue }; echo x $x }
    var i 0
    while $(( $i < 2 )) { set i $(( $i + 1 )) }
    case report.md { *.txt *.md { echo a text file } * { echo something else } }

A condition is a command; its status decides. `&&`, `||` and `!` join commands by status, as sh's do.

    if grep -q root /etc/passwd { echo there is a root }
    false || echo the first failed

## 5. Functions

A function is a block written to a variable, called by the variable's name. `put` gives values back;
`echo` gives text.

    var greet {|who| echo hello $who }
    greet world
    var sq {|x| put $(( $x * $x )) }
    echo $(sq 9)
    # 81

A function is a value: `$sq` is the block itself, to pass on. Blocks keep the variables they see.

    var twice {|f x| put @($f @($f $x)) }
    echo @(twice $sq 3)
    # 81
    var counter {|| var c 0; put { set c $(( $c + 1 )); put $c } }
    var next @(counter)
    echo $($next) $($next)
    # 1 2

## 6. Programs, pipes and captures

Programs and functions mix in one pipeline: between programs flow bytes, between functions values.

    var evens { each {|x| if $(( $x % 2 == 0 )) { put $x } } }
    printf '1\n2\n3\n4\n' | evens | sort -r
    # 4
    # 2

`$(cmd)` is the text a command printed; `@(cmd)` its values, one by one. A program whose name a value
holds runs with `run`: `run $EDITOR notes.txt`.

    var today $(date +%Y)
    var lines [@(printf 'a\nb\n')]
    echo $($lines count) lines
    # 2 lines

## 7. When things fail

A command that fails stops the script, with its status - unless its status is tested: by `if`,
`while`, `&&`, `||` or `!`. `cmd || true` lets one fail.

    var hits $(grep -c nothing-here /etc/passwd || true)
    echo $hits hits

`trap` runs a block however the script ends - to clean up.

    trap { echo cleaned up } EXIT

## 8. Libraries, and Forth

`source` reads another script once; a name with no `/` is found next to the script or on
`$env[RILL3_PATH]` - rill3's own library, in rill3, is there through `bin/cm`.

`forth` runs Forth in rill3's own image: values go onto its stack, what it leaves comes back.

    echo @(forth '*' 6 7)
    # 42

## Where next

docs/REFERENCE.md has every word, its ten rules first; lib/json.cm and lib/args.cm are rill3 written
in rill3; tests/cm/scripts/ws-*.cm are whole scripts, each a small program to read.
