# The command model - a draft (850)

**Status: a draft.** A potential base for further development, captured at the owner's asking
after the A.4 discussion - not a decision. Its rules, names and spellings are all open. Q46 stays
open; this is its option C.

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
   `${name}` delimits; `@name` and `@name[key]` spread a list into several arguments; `$(cmd)` is a
   command's output - a function's values, or a program's text with its trailing newlines dropped;
   `@(cmd)` the same as several arguments (a program's lines).
3. A substitution's result is a value and is never read again: never split, never globbed. Globs
   come from a word's own characters.
4. `'...'` is text; `"..."` substitutes as rule 2 does, `$` only.
5. `[ ... ]` is a list whose elements are words, `[a b $x]`; `[key: value ...]` a map. Nesting is
   free.
6. `{ ... }` is a block - code handed to a command, which runs it: `if`, `while`, `for`, `each`
   and `def` are commands that take blocks. `{|a b| ... }` names a block's arguments.
7. `(( ... ))` is arithmetic and comparison, infix - the one place with an expression grammar,
   bash's own form (in an ordinary word `*` globs and `>` redirects). `$(( ... ))` gives its value.
8. Pipes, redirections, `&&`, `||` and `&` work as in the shell, for functions and programs alike.
   A pipe between functions carries values; between programs, bytes; at a boundary, lines.
9. `set name value` assigns - a bare word is text, so `set` receives the name: no special form.
   Scope is lexical. The environment is where some variables start; reading an unset variable is
   an error when it happens.
10. `def name {|a b| ... }` defines a function. `put` writes values, `echo` writes text, `return`
    ends with a status.

Ten rules and the arithmetic grammar, against A.4's eleven rules and a whole expression grammar
(operators, calls, comprehensions, records).

## A sketch - one possible spelling

    set stats []
    for f $logdir/*.log {
        set n $(wc -l < $f)
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

## Objects without object syntax

If blocks are values (W7) and maps hold anything (W5), a map of data and blocks is an object: a
prototype object, with no class syntax - as Lua and early JavaScript have it. What it would need is
a value as a command's first word, so that `$dog[bark] loud` runs the block in the map - Tcl allows
it (`$myDog bark`), Elvish too. Open.

## What it costs

- It reads as a shell, not as Python: `set x 5`, prefix commands, no infix outside `(( ))`,
  `each` and `filter` with blocks where Python has comprehensions.
- Returning by output has a known pitfall - stray output becoming part of a result (PowerShell's).
  Separate value output (`put`) from byte output (`echo`), as Elvish does.
- `[ ... ]` as a list collides with `[ -d $d ]`: the language would use `test` and `(( ))`;
  relfsh stays for POSIX scripts.
- A new front end. rill2's runtime - values, the collector, processes - stays.

## Open

The names (`def` or `fn`, `put` or `emit`, `set` or `var`); the map's spelling; whether numbers
are a kind of their own or text read as numbers; `try`; a value as a command's first word; whether
function stages stream. Next, when taken up: the six tasks of the users prompt written in this
model, the parser's size estimated, and a side-by-side with A.4.

## Sources

Elvish - "Effective Elvish", "Pipelines and IO", "Value types" (elv.sh); Tcl's Dodekalogue
(wiki.tcl-lang.org); Bash Infinity (github.com/niieani/bash-oo-framework); ksh93's TYPES and its
maintainers' commit logs (ksh93/ksh); gforth's `sh`, bash, dash and ksh93 measured here (850).
