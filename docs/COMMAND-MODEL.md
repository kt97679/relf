# The command model (850; the language since 867)

**Status: the language (867).** Drafted at 850 as Q46's option C, a base for further development; at
867, the owner having handed the choice over, chosen over A.4 by the owner's criteria - the smallest
binary and image, good speed, short scripts, a consistent and friendly syntax, and exactly one way to
do each thing - for the reasons in "One way" below. The rules here are the language's; where a rule
below says more than one way, "One way" says which is left.

## The idea

A shell command has one interface: arguments, standard input, the environment and signals in;
standard output, standard error and an exit status out. A typical scripting language has no such
shape, which is why joining the two kept producing special rules (docs/SYNTAX-STUDY.md, A to A.4).
The owner's observation turns it around: the shell is already close to a high-level scripting
language, and the gap is data - no nested structures, and no way to pass a list or a map to a
function or a command. So instead of fitting commands into a language, fit the language into the
command model:

- **A function is a command.** Everything callable - a function, a builtin, a program - takes
  arguments, reads an input, writes an output and an error output, and ends with a status.
- **Arguments and streams carry values**, not only bytes: text, numbers, lists, maps, nested
  freely, and blocks of code. A program sees text: a list given to it is spread into words, or
  written as JSON; a program's output read by the language is lines of text.
- **A function returns by writing values to its output**, and a capture collects them. This is
  Elvish's model: its commands have no return values, they write to a structured output, and each
  of its pipes has a byte part and a value part. The status stays a status - success or failure,
  for `if`, `while`, `&&` and `||`.
- **Every line parses the same way: as words.** Only the first word is looked up - a function, a
  builtin, then a program - and only to choose what runs. A lookup that changes how a line is read
  was the trap measured in rill2 (a variable named `ls` broke `ls -l`); a lookup that only chooses
  what runs is the shell's own (functions before PATH), and harmless.

This is Forth's outer interpreter turned prefix. Forth passes text to a word through parsing words
- `."`, `S"`, `:` read what follows them, and gforth's `sh` hands the rest of the line to the
system shell (measured: `sh echo hello from the rest of the line | tr a-z A-Z` printed it in
capitals). An unknown word read as a command is an implicit `sh`; consulting the dictionary for a
line's first word only keeps the parse uniform. And it is Tcl's model: a script is commands, a
command is words, `if` and `while` are commands; its whole syntax is twelve rules.

## Draft rules

1. A script is commands, separated by newlines or `;`. A command is words separated by blanks. The
   first word names what runs - a function, a builtin, or a program, looked up when it runs; the
   rest are its arguments.
2. A bare word is text. `$name` is a variable's value; `$name[key]` an element of it, any depth;
   (867: no `${name}` - `$name` the one way); `@name` and `@name[key]` spread a list into several arguments. `$(cmd)` is
   exactly one value - a function's single value, or a program's text with its trailing newlines
   dropped; `@(cmd)` is several - a function's values, a program's lines. A capture takes value
   output only: a function's `echo` text is never captured, it goes on to the byte output (852).
3. A substitution's result is a value and is never read again: never split, never globbed. Globs
   come from a word's own characters.
4. `'...'` is text; `"..."` substitutes as rule 2 does, `$` only.
5. `[ ... ]` is a list whose elements are words, `[a b $x]`; `[key: value ...]` a map, `[:]` an empty one (853). Nesting is free.
6. `{ ... }` is a block - code handed to a command, which runs it: `if`, `while`, `for`, `each`
   and `def` are commands that take blocks. `{|a b| ... }` names a block's arguments.
7. `$(( ... ))` is arithmetic and comparison, infix - the one place with an expression grammar,
   bash's own form (in an ordinary word `*` globs and `>` redirects); its value is a value like any
   other, `if $(( $n > 2 ))` too (867: a bare `(( ))` is an error - one way).
8. Pipes, redirections, `&&`, `||` and `&` work as in the shell, for functions and programs alike.
   A pipe between functions carries values; between programs, bytes; at a boundary, lines.
   Function stages stream - an endless generator must not hang a pipeline (852; how is the runtime
   prompt's question). A failing command, in a capture too, keeps its output and sets `status`;
   under `strict` it stops the script unless tested by `if`, `!`, `&&` or `||` (852).
9. `var name value` creates a variable in the current scope; `set name value` assigns an existing
   one, an error if there is none, and `set name[key] value` an element (853). A bare word is text, so `var` and `set` receive the name: no
   special form. Scope is lexical, and a loop's variable is a fresh one each iteration, so a block
   made in a loop keeps that iteration's value - Go's rule since 1.22 (852). The environment is
   where some variables start, and those pass on to programs; `export name` passes one the script
   made. Reading an unset variable is an error when it happens.
10. `def name {|a b| ... }` defines a function: its arguments are its words, its value input is
    read with `each` or `read`. `put` writes values, `echo` writes text. `return` ends the nearest
    `def`, from inside any blocks; `break` and `continue` the nearest loop, the same way; run from
    a block that outlived its loop or def, they are an error (852).
11. A command's first word may be a value: a block runs, the other words its arguments; a boolean
    gives its status, as in `if $verbose`; text names a command, as `$EDITOR file` does in sh;
    anything else is an error - a list among them, whose error says `test`: `[` is never the test
    command (852).
12. Values have kinds: number, text, boolean, none, list, map, block. A bare word that reads as a
    number is a number, and `true` and `false` are booleans; quoted, they are text. A program's
    output is text. `(( ))` takes numbers, and text that reads exactly as a number; anything else
    is an error (852). Lists and maps are mutable and held by reference: two variables can hold
    one map, and a change through either shows through both; `same $a $b` tells whether they do,
    `eq` compares content, blocks by identity. Each value has a printed form for `echo` and
    strings - a list or map in its literal syntax, a block as `<block>`; given to a program as one
    argument, a list, map or block is an error that says `@` or `to-json`. `to-json` writes data at
    any depth, never truncating; a block or a cycle in it is an error that says where (853).
13. `#` at a word's start begins a comment; `\` escapes in `"..."` only - in a bare word it is itself,
    as in rc, and quotes are the one way to escape (867); a line goes on
    after `|`, `&&` and `||`, and inside an open `[`, `{` or `(`. A command that takes blocks takes
    them as its last words - `if cond... {..} else {..}` - so `if ! nc -z $h $p { ... }` runs
    `! nc -z $h $p` (852).

Thirteen rules (852: the review added kinds and lines) and the arithmetic grammar, against A.4's
eleven rules and a whole expression grammar
(operators, calls, comprehensions, records).

## A sketch - one possible spelling

    var stats []
    for f $logdir/*.log {
        var n $(wc -l < $f)
        append stats [file: $f  lines: $n]
    }
    sort-by lines $stats | each {|s| echo "$s[file]: $s[lines] lines" }
    if (( $n > 2 )) { tar czf old.tgz @big }

## The shell's weak points, from OOP built on top of it

A framework that builds objects on shell syntax has to work around each weakness of the shell's
data and function model, so its workarounds list what a design must answer.

Bash Infinity, the best known, offers named parameters (instead of `$1`, `$2`), "passing arrays and
maps as parameters" - by serializing a declaration, `"$(@get someArray)"`, or by reference,
`$ref:name` - typed slots for array arguments (`[string[4]]`), try/catch and a type system. Its
`try` runs in a subshell, "therefore you cannot assign any variables inside of it", and its author
advises against basing major projects on the whole framework.

ksh93 built types into the shell: `typeset -T` defines fields and discipline functions as methods,
types compose and derive from one another. It works - ksh 93u+m 1.0.8 here, `Pt_t p; p.len`
printed 6 - and its maintainers' commit logs call the approach "incredibly buggy". Types grafted
onto a namespace of string variables stay fragile.

Measured here, in bash, dash and ksh93:

| | weak point | measured | the draft's answer |
|---|---|---|---|
| W1 | a capture forks: a function's change of state is lost | bash: `v=$(f)` - v is `out`, the variable f set is unset | a function's capture runs in the same process; only programs fork |
| W2 | a pipeline's stages fork | `echo hi \| read v`: unset in bash and dash; `hi` in ksh93, which runs the last stage in the shell | function stages run in the same process; only programs fork |
| W3 | a function returns only a status, 0-255 | `return 300` gives 44 | values go to the output; the status stays a status |
| W4 | arrays passed to a function lose their boundaries | two arrays, three words: `1`, `2 3`, `4` - Bash Infinity's typed slots exist for this | `f $a $b`: two arguments, each a list |
| W5 | no nesting | `m[k]=(1 2)`: "cannot assign list to array member" | lists and maps nest |
| W6 | dynamic scope | a callee sees its caller's `local` | lexical scope, as rill2 has |
| W7 | functions are names, not values | a callback is run by its name, `"$1" "$2"`; no closures; objects are name prefixes | blocks are values with closures |
| W8 | no exceptions; try/catch emulated in subshells | Bash Infinity's `try` cannot set a variable | status and `strict`, as rill2; an in-process `try` if wanted |
| W9 | objects are global arrays, never freed | by construction | values are collected, as in rill2 |

W1 and W2 are the ones a design slides back into most easily: running function stages in forked
VMs, suggested in the discussion before this draft, would bring both back. Function captures and
stages run in the same process - stages one after another with their values buffered (no
streaming, enough for most scripts), or as coroutines.

## Objects (851)

Worked out at the owner's asking - still a draft. Three pieces, and only the third is a rule:

- **Blocks are values that close over the variables they use** - by reference, so a block can
  change them. New in rill2: today a def is no value (`f = sq` is "sq is not defined") and defs do
  not nest ("def is only for the top level").
- **Maps hold any value**, blocks included.
- **Rule 11: a command's first word may be a value.** A block runs, with the other words as its
  arguments; text names a command, as `$EDITOR file` does in sh - and `if $verbose`, which runs
  `true` or `false`; anything else is an error.

A counter - its state a variable its blocks close over:

    def counter {|start|
        var n $start
        put [inc: { set n $(( $n + 1 )) }  get: { put $n }]
    }
    var c $(counter 5)
    $c[inc]
    $c[inc]
    echo $($c[get])                       # 7

Methods with arguments, one calling another through a captured `self`:

    def account {|owner|
        var balance 0
        var self [
            deposit: {|amount| set balance $(( $balance + $amount )) }
            twice:   {|amount| $self[deposit] $amount; $self[deposit] $amount }
            report:  { echo "$owner has $balance" }
        ]
        put $self
    }
    var a $(account ada)
    $a[twice] 50
    $a[report]                            # ada has 100

Inheritance by copying - one map merged over another:

    def animal {|name| put [name: $name  speak: { echo "$name makes a sound" }] }
    def dog {|name| put $(merge $(animal $name) [speak: { echo "$name barks" }]) }
    var d $(dog rex)
    $d[speak]                             # rex barks

No `class`, `new`, `this` or method-call syntax: methods are closures, `self` is a variable like
any other, a subclass is a merge. Merging copies; delegation - a `proto:` key consulted when a key
is missing, as Lua's metatables and JavaScript's prototypes do - is open. So is whether a method
should receive its map implicitly (Lua's `obj:m()`); here it does not, which keeps rule 11 the
only rule objects need.

852: the review's five answers agree these three pieces suffice for everyday scripts. What users
would miss first: delegation, and an implicit `self` or a method syntax; then defined identity,
equality and printing of maps and blocks. The objects prompt asks for the evidence on each.

853, after objects' prior art (docs/asks/ask-command-model-objects-answers-852.md): the inheritance
above breaks as soon as a method calls another through `self`. A block copied by `merge` still sees
the map it was made with, so an inherited `greet` calling `$self[speak]` reaches the parent's
`speak`, never the child's. Rebol and Red copy too, but rebind a copied object's functions to the
copy; a closure cannot be rebound. The draft's answer needs no rule - a constructor fills a map it
is given, so every method, inherited or not, closes over the same map:

    def animal {|self name|
        set self[speak] { echo "$name makes a sound" }
        set self[greet] { echo hello; $self[speak] }
    }
    def dog {|self name|
        animal $self $name
        set self[speak] { echo "$name barks" }
    }
    var d [:]
    dog $d rex
    $d[greet]                             # hello, then: rex barks

It rests on maps held by reference (rule 12). `merge` stays, for data: it copies the top level, and
nested values stay shared. Delegation (a `proto:` key) and an implicit receiver wait for real
scripts to ask for them - as three of the five answers, the most careful among them, advise.

## The six tasks (851)

The users prompt's six tasks, written in the draft. Not run - nothing is built.

1. Lines and errors in each `*.log` counted, kept as records, printed sorted, the big ones archived:

        var cfg [logdir: /var/log/app  limit: 2]
        var stats []
        for f $cfg[logdir]/*.log {
            var n $(wc -l < $f)
            var errs $(grep -c ERROR $f)
            append stats [file: $f  lines: $n  errors: $errs]
        }
        sort-by lines $stats | each {|s| echo "$s[file]: $s[lines] lines, $s[errors] errors" }
        var big [ @(for s @stats { if (( $s[lines] > $cfg[limit] )) { put $s[file] } }) ]
        if (( $(count $big) > 0 )) { tar czf old.tgz @big }

2. Servers from a JSON config checked with `nc -z`, the failures printed as JSON:

        var cfg $(from-json < config.json)
        var fails []
        for s @cfg[servers] {
            if ! nc -z $s[host] $s[port] { append fails $s }
        }
        to-json $fails

3. `*.jpeg` renamed to `*.jpg`, clashes numbered:

        for f *.jpeg {
            var base $(basename $f .jpeg)
            var dest $base.jpg
            var i 1
            while test -e $dest {
                set dest $base-$i.jpg
                set i $(( $i + 1 ))
            }
            mv $f $dest
        }

4. `ps` output as records, those over 100 MB, sorted:

        var procs []
        for line @(ps -eo pid,rss,comm | tail -n +2) {
            var p [ @(words $line) ]
            if (( $p[1] > 102400 )) { append procs [pid: $p[0]  rss: $p[1]  comm: $p[2]] }
        }
        sort-by rss $procs | each {|r| echo "$r[pid] $r[rss] $r[comm]" }

5. A command tried up to five times, the sleep doubling:

        var delay 1
        for i @(range 5) {
            if mycmd { break }
            sleep $delay
            set delay $(( $delay * 2 ))
        }

6. A program's arguments built from conditions:

        var args []
        if $verbose { append args -v }
        if test -n $out { append args --out $out }
        append args @inputs
        myprog @args

Tasks 3, 5 and 6 read as the shell does; 1, 2 and 4 are where values earn their place - records,
JSON, a list kept and sorted. A comprehension is a loop's outputs captured:
`[ @(for ... { put ... }) ]`.

## Gaps found writing them (851)

| | gap | where | the draft's leaning |
|---|---|---|---|
| G1 | how many values a capture gives | 1, 4 | `$( )` exactly one - a program's text is one; a function putting several is an error that says `@( )`, which gives each |
| G2 | streams or lists from library commands (`words`, `sort-by`, `range`) | 4 | streams, `[ @( ) ]` making a list - one convention for all |
| G3 | a failing program in a capture: `grep -c ERROR` prints 0 and exits 1 when nothing matches (measured), and `strict` would stop | 1 | open |
| G4 | `break` and `return` inside blocks: a `break` in an `if` block inside a `for` must leave the `for`; a `return` in an `each` block - the block's, or the def's? | 5 | `break` leaves the nearest loop, through blocks; `return` the nearest def - open |
| G5 | creating and assigning differ once blocks close over variables | objects | `var` creates, `set` assigns (an error if nothing to assign) - rule 9 amended |
| G6 | a value as the first word | 6, objects | rule 11 |
| G7 | `if ! nc ...` | 2 | `!` is a command that runs the rest and inverts its status, as `time` runs the rest - no syntax |
| G8 | text or kinds: `if $verbose` wants text naming `true`; `to-json` wants 12 told from "12" | 2, 6 | open |
| G9 | `ps` command names hold blanks, and `words` splits at every blank | 4 | the library's (a split with a count), not syntax |

852: the review decided G1, G2, G4-G7 and G9 as the draft leaned; G3 and G8 as rules 8 and 12 now
say; and it found what the gaps missed - captures taking `echo`, loop variables in blocks, an
endless generator, and the basics: comments, escapes, continued lines, `export`, `continue`
(docs/asks/ask-command-model-review-answers-851.md).

## The parser, estimated (851)

rill2's language part measured by concern - 21,294 bytes in 375 words - and what the command model
would do with each part. Estimates; nothing is built.

| part | rill2 today | the command model |
|---|---:|---|
| statements and defs | 3,208 | ~2,000 - `if`, `while`, `for`, `def` become commands that take blocks, still compiled inline; `=`, `+=` and index assignment become `var`, `set`, `append` |
| expressions | 3,115 | ~1,400 - only `(( ))`, arithmetic and comparison: no calls, literals or comprehensions |
| Forth text: buffers, words made | 2,958 | the same |
| commands: stages, ports, captures | 2,661 | the same, and functions as stages |
| library wrappers | 1,833 | the same, called as commands |
| values checked when used | 1,634 | the same |
| names, scopes, declarations | 1,469 | the same, and closures' captured variables |
| tokenizer | 967 | about the same - words, quotes, `$`, `@`, brackets |
| the prompt | 871 | the same |
| stack mode | 717 | gone - no numeric defs |
| strings | 496 | about the same - `$` only |
| static data, errors, other | 1,365 | the same |
| new: blocks as closures | - | ~1,500-2,500 |
| new: value output, value captures, function pipelines in the process | - | ~800-1,500 |
| new: lists and maps of words, rule 11 | - | ~600-1,000 |
| total | 21,294 | ~20,000-23,000 |

About even. What moves is where the complexity lives: the syntax shrinks to one statement form and
one small expression grammar, and the runtime grows by closures and value streams, which rill2 has
none of.

## Against A.4 (851)

| | A.4 (docs/SYNTAX-STUDY.md) | the command model |
|---|---|---|
| rules | 11, and an expression grammar - Python's operators, calls, comprehensions, records | 11, and `(( ))` |
| a line is | code or a command, by its first token | a command; its first word looked up only to choose what runs |
| variables | `$x = 1`; `$x` everywhere | `var x 1`, `set x 2`; `$x` to read |
| functions | `f($x)` returns a value | commands: `put` outputs values, `$( )` captures them |
| data to programs | `@x` spreads | the same |
| pipes | programs, and defs as stages | functions and programs alike, values between functions |
| objects | records of data, no methods | maps of closures: `$obj[method] args` |
| control flow | keywords | commands that take blocks |
| reads as | Python with commands | the shell with values |
| size | about rill2's, likely less | about rill2's |
| new runtime | none | closures, value streams |
| rill2's scripts | converted by a script | rewritten |
| risks | a Python-like language with a shell bolted on - the owner's own doubt | stray output in results (`put` and `echo` kept apart); blocks' `return`; what closures cost |

## The runtime plan (854)

From the runtime answers, checked (docs/asks/ask-command-model-runtime-answers-853.md), and from
relf's own source, which no answer could see:

- **Closures**: a variable a block captures lives in a box - Lua's upvalues; the rest stay where
  rill2 keeps them. A block is its code and its boxes.
- **The collector** traces - rill2's copies what its roots reach, forwarding as it goes (rt.4,
  Iteration 776) - so the object convention's cycles are reclaimed. But it runs only between
  top-level statements, its roots a table of registered variables: boxes, blocks, value queues
  and coroutine stacks must become roots it knows, and safe points must come inside loops and
  stages - an endless pipeline never reaches the top level. It moves objects, so at a safe point
  no value may sit on a Forth stack unseen. This is the plan's largest piece.
- **Function stages** are coroutines: each its own data and return stacks (the kernel has `SP@ SP!
  RP@ RP!`) and its own exception handler, values passed through bounded queues.
- **Programs in a pipeline**: only they fork; their pipes are non-blocking and served by one poll
  loop (the engine has `poll`); standard error is drained too; SIGPIPE is ignored, and EPIPE ends
  the stage that writes - `yes | head -1` quietly.
- **`break`, `continue`, `return`** carry the identity of the loop or def they leave; a stale one
  is an error. A bare code would let a block that outlived its loop, run inside another loop,
  break that one.
- **Rule 11**: a name known when compiling is called directly; a value goes through one dispatch
  on its kind - a block runs, a boolean gives its status, text names a command.

The prototype, in this order, each step with its test: blocks, boxes and the collector's new roots
and safe points (a cycle reclaimed, a counter surviving collections); value and byte output kept
apart, and captures; `break`, `continue` and `return` with identities (a stale block refused);
coroutine stages and bounded queues (an endless generator into a stage that stops early);
programs in pipelines through poll (a stream larger than a pipe, a slow consumer, a program
writing much to standard error); then dispatch and allocation measured.

## The prototype (855-)

**Step 1 (855): blocks, upvalues, and the collector's new roots** - `cm/rt-cm.4`, driven from Forth by
`tests/cm/closures.4`; no front end yet, each test word being what a compiler would make of the line
in its comment. Built on rill2's runtime:

- **Frames the collector sees.** `FRAME`/`UNFRAME` push and pop a def's slots on a stack of items,
  the frame below saved as an odd number the collector passes by; `LS@`/`LS!` read and write a slot.
  rill2 keeps a def's locals in static variables the collector never sees - why it collects only
  between top-level statements; in frames, a safe point inside a def is safe once its values are in
  slots, not on a Forth stack.
- **Upvalues** (kind 8): one cell holding an item, shared by the frame's slot and the blocks that
  captured it - `UPV-NEW`, `UPV@`, `UPV!`.
- **Blocks** (kind 7): `[xt][n][capture 0..n-1]`; `BLK-NEW` makes one, `BLK-CALL` runs one - rule 11's
  block - with its captures at hand through `E@`, the blocks running kept where the collector sees
  them.
- **The collector**: rt.4 gains two hooks, their defaults as before - `G-PTR-KIND?`, the kinds whose
  value points into the arena, and `G-MORE`, roots beyond the registered variables. `cm/rt-cm.4`
  adds blocks and upvalues to both, and the frames' slots and the running blocks as roots.

The test, the draft's own examples: two counters made by separate calls keep two `n`s (7 and 101),
with a collection inside the constructor while its frame held the half-made map; a collection inside
a running block (8); a cycle - a map, a block, an upvalue, the map - kept through two collections
and still itself; 200,000 such cycles made and dropped, the arena under 1 MB after them; the counters
still counting. rill2's image 68,912 -> 69,008 bytes for the hooks.

**Step 2 (856): value output and byte output kept apart; captures; the printed form** - `cm/out.4`,
tested by `tests/cm/output.4`:

- **Sinks.** `PUT` sends a value to the innermost capture's list, or - none open - prints it at the
  terminal; `echo`'s bytes go to the byte output and are never captured (rule 2).
- **Captures.** `CAPTURE` runs a function with a new list as its sink, under CATCH, so a failure
  inside leaves the sinks as they were; `ONE` is `$( )` - exactly one value, else an error naming
  `@( )`; the list itself is `@( )`.
- **The printed form** (rule 12): `[a "b c" [1 2]]` - a text quoted only when it would not read back
  as one word - `[name: ada  tags: [x y]]`, `[:]`, `<block>`.
- **The collector** sees the captures' lists.

The test: the printed forms above; a capture's value is the very value put; `echo` inside a capture
printed, the value 7 captured; `@( )` of three values, `$( )` of them an error; nested captures; a
collection inside a capture keeping what it caught; a failure inside one leaving no sink behind.

**Step 3 (857): `break`, `continue` and `return`, each to its own loop or def** - `cm/ctl.4`, tested
by `tests/cm/control.4`:

- **Activations.** Each run of a loop or def gets a number of its own, kept on a stack of the live
  ones; a block captures its loop's or def's number like any value. A transfer names its target: a
  block that outlived its loop finds the number gone - an error, never the break of whichever loop
  is running then.
- **`C-FOR`** runs a loop body per element, the list, the element and the loop's number in the def's
  frame - the body takes nothing from the stack, so a collection inside it finds every value in a
  slot; **`DEF-RUN`** runs a def, slot 0 its number, and puts the frame and the activations back
  whatever a throw from deep inside left. Every construct puts back what it pushed before it passes
  a throw on.

The test: break and continue through a block; return through a loop and a block; a stale `{ break }`
run inside another loop - an error, and that loop goes to its end; a block made in an outer loop,
called from the inner, breaking the outer - a labeled break by identity, no syntax for it;
recursion, each return to its own activation, a collection at every level; an error through a
block, a loop and a def, every stack as it was after.

**The front end (858): `tools/cmc.py`**, a prototype compiler - a `.cm` script in the draft's syntax to
Forth for cm's runtime, as `rillc.py` came before Rill's in-image compiler; the in-image one comes
once the syntax settles. v0: `var`, `set` (and `set name[key]`), `put`, `echo`, `append`, `if`/`elif`/
`else`, `for`, `while`, `def`, `break`, `continue`, `return`, `count`, `range`, `merge`; rule 11; texts,
numbers, booleans, `"..."` with `$` in it, `$name[key]`, `$( )`, `@( )`, `$(( ))`, `(( ))`, `@name`,
lists, maps, blocks with `|params|`. Every variable lives in an upvalue - boxed, no capture analysis
yet - so blocks capture by reference and a loop's variable is fresh each iteration; a block is a
word with a frame of its own, a def a deferred word; a safe point before each of the script's own
statements. Not yet: programs, pipes, redirections; a def seeing the script's variables.

The draft's own examples, as written, run - `tests/cm/scripts/`: the counter (`two counters: 7 101`);
the account whose methods call each other through a captured `self` (`ada has 100`); `dog` filling a
map `animal` filled, its inherited `greet` reaching the override (`hello`, `rex barks`); break,
continue and return through block values, the labeled outer break, `while`, a stale break refused;
the printed forms, captures, `echo` not captured, `@( )`, `merge`, `append` with a spread.

**Programs (859).** A command whose first word is no builtin, def or value is a program, looked up when
it runs - a missing one is status 127, not a refusal. Pipelines of programs, redirections (`>`, `>>`,
`<`, `2>`, `2>>`, `&>`, `2>&1`), `&&` and `||` as sh chains them; `$( )` of a program its text, every
trailing newline dropped, `@( )` its lines; any command's status as a condition; `$status`. A list,
map or block given to a program is an error (rule 12). Built on rt.4's pipeline runtime - the one
rill2 uses - with cm/lib.4's `PSTAGE` turning an argument list into texts. `tests/cm/scripts/programs.cm`.

**The aim, restated by the owner (861): smaller than relfsh.** Rill and rill2 are attempts at a shell
and scripting language smaller than relfsh, the POSIX shell this VM already has - not another POSIX
shell. Measured: relfsh's image 129,028 bytes; rill2's 69,008, its language part 21,294; the command
model's runtime so far (rt-cm.4 834, out.4 782, ctl.4 918, lib.4 1,544 bytes loaded) about 4 KB. With
rill2's language part replaced by that runtime and an in-image compiler for a far smaller syntax,
the command model would come to roughly 60-64 KB - half of relfsh - if nothing heavy is added.

**Step 4, decided for size (861): function stages buffered, not streamed.** Designed first as
coroutines - each stage its own stack segments, guard pages between them, a new engine primitive
(MPROTECT) in both engines and the kernels rebuilt: built and working (859-860), and set aside,
because the shared kernel and engines - relfsh's too - are no place for the command model's needs,
and a coroutine engine is the opposite of small. Instead:

- Programs next to each other are an OS pipeline, streaming among themselves, as now.
- A function stage runs to its end in the shell's process, keeping its side effects; its values go to
  the next function as a list, read with `each`.
- A function before a program writes to a temporary file - its values as lines, its `echo` text with
  them, in order - and the program reads the file: no pipe to fill, no deadlock, no poll loop.
- A program before a function is read whole, its lines the function's input.

The price: a function stage does not stream - an endless function generator in a pipeline would
hang, as the first review warned. Programs are untouched by it. Reviews asked for streaming; the
owner's aim decides against what it costs.

Built (862): `cm/pipe.4` - a function's input stack, `each`, a function stage run to a list
(`FN-LIST`), to the output it is in (`FN-RUN`), or into a temporary file for the programs after it
(`FN>FILE`: standard output pointed at the file the way rt.4's error path points it at fd 2, values
printed into it as at the terminal), each putting everything back on a failure; `cmc.py` groups
programs side by side into one OS pipeline and buffers at each function's edge. `tests/cm/scripts/
pipes.cm`: function to function to function, `echo` into a program, a function's values into `sort`,
programs into a function, function to program to function, captures of mixed pipelines, a block as a
stage keeping its side effects - no temporary file left. The runtime, all of it, 4684 bytes loaded.

**The front end in Forth (863): `cm/cmc.4`.** The number 861 left open - what an in-image front end
costs - measured. `cm/cmc.4` is `cmc.py` ported construct by construct, 206 words: a first pass parses
the script into a flat tree (nodes of three cells - a kind and two of its own - in an array, an opening
node's children up to an end node), a second makes each command's Forth from it as `cmc.py`'s `Gen`
does, looking ahead by skipping nodes where `cmc.py` looks at a whole list. The Forth is made as
strings in a heap of their own and EVALUATEd; nothing in it is kept by an absolute address, so it can
be saved in an image. `tools/cm-diff.py` compares the two front ends' Forth token by token: for every
script in `tests/cm/scripts/` it is the same. `tools/build-cm-image.sh` builds `kernel64-cm.img` -
rill2's image with its language part replaced: of `rill2/rill2.4` only its values (up to its library,
the words cm's runtime and the Forth made use), then cm's runtime and `cm/cmc.4`, a `.cm` script read,
made Forth and run: `./relf64 kernel64-cm.img script.cm`. The scripts run in it as they do through
`cmc.py`, with `RILL_GC_STRESS=1` too.

Measured as rill2's language part was - the dictionary's growth as each file loads, which gives
`rill2/rill2.4` 20,375 bytes and `rill2/prompt.4` 919, the 21,294 of 851:

| | rill2 | the command model |
|---|---:|---:|
| values (`rill2.4` up to its library) | 1,694 | 1,694, the same words |
| the rest of the language | 18,681 (`rill2.4`'s compiler and library) | 17,418: runtime 4,727, front end 12,691 |
| the prompt | 919 | none yet |
| the language, all | 21,294 | 19,112 |
| the image | 69,008 | 66,845 |

The command model's image is 2,163 bytes smaller, and has no prompt yet and no library - rill2's
library wrappers alone were 1,833 bytes in 851's measure. Like for like, about even, as 851 estimated;
not the 60-64 KB 861 projected, which assumed a front end of a few kilobytes: it is 12.7 KB. The
image is 52% of relfsh's. A port that makes `cmc.py`'s Forth word for word, not one written for size:
206 words, their names 1,137 characters; one pass instead of two, and shorter names, would cut it -
and rill2's compiler could be cut the same way. On size, Q46 is a draw.

**Syntax genes and the comparison (865).** Four of the syntax's choices made genes of `cm/cmc.4`
(`cm/genes.tsv`: `var x = v`, `(cmd)`, `"{x}"`, prefix arithmetic) and all 16 genomes built and gated -
the same Forth as cmc.py from each script rendered in each syntax: the most any moves the image is 280
bytes, and C.2's choice is the smallest on every axis. With the front end loaded beside the image
instead of in it (`CM_FRONT=overlay`) the image is 54,510 bytes, 18.7% less, each script starting 13.6 ms
later. Against Rill and Rill 2 on the same programs: 2.0 KB smaller than Rill 2, its programs longer,
a loop 1.4 times as slow and calls 4.7 times - a def returns through a capture, every variable is
boxed, a safe point comes before every statement (docs/SYNTAX-GENES.md). Found running Rill 2's
program in it: indexing a list faulted - a list keeps its items as they are, and rill2's D-AT and
D-SET unbox a list's - so `CM-AT` and `CM-SET` (cm/lib.4); and `has`, for `in`.

**Design genes (866).** Measured by dispatches, the command model's loop and call costs taken apart:
loops now test for break and continue only when their body threw (adopted), and three genes, off by
default - `put` of one value without a list, plain loops where no transfer can come, capture analysis
(a variable no block value refers to kept unboxed) - bring `loop` to 1.15 times Rill 2's dispatches
and `calls` to 3.4 times (docs/SYNTAX-GENES.md).

## One way (867)

The owner asked for exactly one way to do each thing, and handed the choice over. What was decided,
each from what was measured (docs/SYNTAX-GENES.md):

- **The language is the command model, not A.4.** On size the two are even and the command model a
  little smaller (its image 68,288 bytes against Rill 2's 69,008); it has one form of statement - words,
  the first choosing what runs - where A.4 has two, code and commands, chosen by the first token, and two
  ways to call (`f(x)` and `f x`); its scripts are longer (7-60%) and its calls slower (3.3 times Rill
  2's dispatches), which design can work on, as 866 began to.
- **The syntax genes stay at C.2's forms:** `var x v`, `$(cmd)`, `"$x"`, infix `$(( ))` - each the
  smallest, and `(cmd)` would have kept `$(cmd)` beside it in quotes, two ways.
- **The design genes are the one way the Forth is made:** `put` of one value without a list, plain
  loops where no transfer can come, capture analysis. Their alternatives are gone from cm/cmc.4.
- **Three second ways cut:** `${name}` (an error that says `$name`), a bare `(( ))` (an error that says
  `$(( ))` - not a program named `((` that quietly fails), `\` escaping in bare words (now itself, as rc
  has it; quotes escape).
- **One front end:** cm/cmc.4. tools/cmc.py, the Python prototype it was checked against word for word
  (863), is retired, with the tools of the genes' experiments; the scripts' outputs check the one left.
- **The front end stays in the image.** As an overlay (865) the image was 18.7% smaller, but the front
  end beside it is 32 KB of source against 12.7 KB compiled - more on disk in all - and every script
  started three times slower.

A call's two lists went at 868: a def called with exactly its words gets them on the stack, and `$( )`
of a function keeps its one value in the sink's own cell - `calls` 30% fewer dispatches, 2.3 times Rill
2's. The prompt came at 869 (cm/prompt.4): one session across lines, its variables boxed, an error said
and the prompt going on. With it two rules made true that the prototype had not: every command sets a
status - a builtin, an `if` taking no branch and a loop 0, `false` 1 - so `&&` and `||` see the command
before them, and a script ends with its last status; and a line goes on after `|`, `&&` and `||`.
At 870 its values became its own (cm/values.4): `+` is arithmetic only - texts join side by side - and a
text that reads as a whole number is that number in `$(( ))`, as the shell's, so `$(( $n + 1 ))` works on a
program's output. Its library, what values need and programs cannot do: `split $t sep` and `keys $m` put
each part or key, `join sep items...` one text; with `has`, `count`, `range`, `merge`, `each`. `$env[NAME]`
reads the environment, `set env[NAME] v` sets it for programs; `$args` is the script's arguments. At 871
Rill and Rill 2 were retired - one language: the image is the command model's own (66,338 bytes: Rill's
regex engine, which nothing of the command model used, left out), `bin/cm` runs it, `tests/cm/run` checks
it. Globbing came at 872, as rule 7 said and the prototype had not done: an unquoted word with `*` or `?`
among a command's words - a program's, a builtin's, a list's - is the paths it matches, sorted (a name
starting with `.` only for a pattern that does, as the shell's); none an error that names the pattern, as
zsh and fish have it - one way: quote a pattern to pass it as it is. As var's value it stays itself.
`cd` and `exit` came at 873 - a shell has to have them, and only a builtin can change the shell's own
directory: `cd dir`, `cd` alone for `$env[HOME]`, a failure said with status 1 and the script going on;
`exit n`, or `exit` with the last status, ending a script or the prompt. And the runtime made the command
model's: its genes fixed, and the 80 words of Rill's that nothing of the command model reaches taken out
- the image 62,238 bytes - with tools/cm-reach.py in the suite to keep it so.
Rule 8's `&`, never built, came at 874: a program pipeline ending in `&` runs in the background, its stdin
/dev/null; `wait` waits for every job, its status the last's; a job not waited for gets TERM when the
script ends (a function cannot go in the background - it runs in the shell: an error says so). And a
quoted text is a value in `$(( ))`, so `if $(( $answer == "yes" ))` is the one way to compare with a text.
Still to come: a smaller front end, and a call's remaining cost.

## What it costs

- It reads as a shell, not as Python: `set x 5`, prefix commands, no infix outside `(( ))`,
  `each` and `filter` with blocks where Python has comprehensions.
- Returning by output has a known pitfall - stray output becoming part of a result (PowerShell's).
  Separate value output (`put`) from byte output (`echo`), as Elvish does.
- `[ ... ]` as a list collides with `[ -d $d ]`: the language would use `test` and `(( ))`;
  relfsh stays for POSIX scripts.
- A new front end. rill2's runtime - values, the collector, processes - stays.

## Open

The names (`def` or `fn`, `put` or `emit`); the map's spelling; `try`; delegation and an implicit
receiver, if real scripts ask for them. Asked of other models, answered and checked: the review
(852), objects (853), the runtime (854) - docs/asks/. Nothing is left to ask before a prototype;
what is open now, scripts written in one will settle.

## Sources

Elvish - "Effective Elvish", "Pipelines and IO", "Value types" (elv.sh); Tcl's Dodekalogue
(wiki.tcl-lang.org); Bash Infinity (github.com/niieani/bash-oo-framework); ksh93's TYPES and its
maintainers' commit logs (ksh93/ksh); gforth's `sh`, bash, dash and ksh93 measured here (850).
