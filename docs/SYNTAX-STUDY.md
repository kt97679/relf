# Shell and language in one: a syntax study (842)

## The question

The shell is already a fair scripting language: functions, global and local variables, arrays, maps.
What it lacks is nesting - an array or a map cannot hold another, so real data goes through JSON and
jq. And in a shell `ls $dir` is natural, while a language like Python or Ruby writes a variable
bare; mixing `var` and `$var` in one language looks inconsistent, confuses, and invites mistakes.
Asked: look at other languages, shells above all, and see what makes one language that is a shell
and a real language - consistent, convenient, expressive, not confusing.

## The collision

In a shell a bare word is **text**: `ls -l /tmp` is three texts. In Python or Ruby a bare word is a
**name**: `print(total)`. A language that is both must decide, for every word it reads, which it is.
Every shell-and-language joins this in one of four ways, and each way has been built and lived with.

## Four answers

**1. One sigil, everywhere** - fish, Elvish, PowerShell, Nushell (and Tcl, Perl, PHP). A variable
is read as `$x` wherever it is read, in arithmetic too: Nushell's `let val = 42` then `$val += 27`;
PowerShell's `$a + 2`; Elvish's `var foo = bar` then `echo $foo`. A bare word is text where it is an
argument and a command where it comes first. fish, Elvish and Nushell never split a value into
words; in fish every variable is a list and each element is its own argument, so `rm $files` is
safe with spaces in the names, and a glob never comes out of a variable's value. The costs: `$` in
arithmetic, and some keep arithmetic out of the language altogether (Elvish's `+ 1 2`, fish's
`math $i + 1`). Nushell's own book advises quoting strings in real programs rather than relying on
bare words, and in 0.97 a bare word after `=` changed from a text to a command - bare words as
text are the part these shells keep revising.

**2. Two modes, chosen by syntax** - YSH (Oils), and PowerShell's parsing. YSH's command mode is
the shell; its expression mode is Python-like and appears only in fixed places: after `=` in
`var`/`setvar`, inside `if (...)`, `while (...)`, `for x in (...)`, after `=` and `call`. Crossings
are explicit: `$[expr]` puts an expression in a word, `@x` and `@[expr]` splice lists, `$(cmd)` and
`@(cmd)` bring a command into an expression; `{}` is a block in a command and a dict in an
expression. YSH's own summary shows the price: `echo $filename.py` and `var x = filename ++ '.py'`
name one variable two ways - each tied to a visible place, never guessed. PowerShell has an
expression mode and an argument mode, chosen by a statement's first token, with `$` in both; its
known trap is the same characters meaning two things - `$a+2` alone is 6, `Write-Output $a+2`
passes the text "4+2". It splices with `@args` and runs an expression inside arguments with `(...)`.

**3. Two modes, chosen by looking names up** - xonsh, and rill2. xonsh reads a line as Python if
its leftmost name is a Python variable, as a command otherwise; its tutorial shows the trap: after
`ls = 44` and `l = 2`, typing `ls -l` prints 42. Its strings follow the mode too: `"my home is
$HOME"` expands on a command line and not in Python. `$[...]` and `![...]` force a command when the
guess is wrong.

**4. Commands quoted inside a language** - Hush, zx. Hush is Lua-like; commands live only in
blocks, `{ cmd $var; ... }`, and `${ cmd }` captures. zx is JavaScript; a command is a template,
`` $`mkdir ${name}` ``, and whatever goes through `${...}` is escaped and quoted - an array becomes
one argument per element. Clean everywhere but at a prompt, where every command needs its wrapper.

## What they teach

| | Lesson | Where seen |
|---|---|---|
| L1 | Decide what a line is by its syntax, never by what names exist | xonsh's `ls -l` giving 42; rill2, below |
| L2 | A value is never split into words or globbed | fish, Elvish, Nushell, YSH, zx |
| L3 | Spread a list into arguments on purpose | YSH `@x`, PowerShell `@args`; fish and zx spread every list, safe only with flat lists |
| L4 | In code, text is quoted | Nushell's own advice and its 0.97 change |
| L5 | The same characters mean the same thing everywhere | PowerShell's `$a+2`; xonsh's `$HOME` in strings |
| L6 | One character starts every substitution | sh: `$x`, `${x}`, `$(cmd)`, `$((n+1))` - all `$`; Python needed an `f` prefix before `{}` interpolated |
| L7 | Errors come from the text, not from the machine it runs on | rill2's PATH check, below |

## Rill and rill2 against them, measured

Probes run on both (842):

| Probe | Rill | rill2 |
|---|---|---|
| `ls = 5` then `ls -l /tmp` (L1) | runs ls | "l is not defined" - read as `ls - l` |
| a branch never taken names `dnf`, absent here (L7) | runs | the whole script refused: "dnf is not a variable, a def or a command" |
| a string holding `{"a": 1}` (L6) | printed `JSON-ish: \` - **wrong, silently**; an error since 843 | an error: `{` interpolates in every string |
| `"x {s["lines"]} y"` (L6) | - | printed `x 3`, the rest **lost silently** - mended in 842 |
| `x = dri`, a mistyped name (L4) | the text "dri", silently | an error |
| reading a variable | `$x` in code and commands | `x` in code, `$x` in commands - the mixing asked about |

Rill decides by syntax (L1, L7) and reads every variable with `$`, but binds bare (`x = 7`), takes
bare words in code as text (L4) and interpolates `{...}` in strings (L6). rill2 reads variables bare
in code, decides a line's kind by looking its first word up among its variables and then on PATH
(L1, L7), and interpolates `{...}` in every string (L6).

## A proposal: one sigil, syntax decides

**R1. A variable is always `$name`** - read, assigned, a parameter, a loop's variable: `$total = 0`,
`$total += $n`, `def area($w, $h)`, `for $f in *.log`. A bare word is never a variable. (PowerShell,
Perl, PHP.) The Python habit `total = 0` is an error that says `$total = 0`.

**R2. A statement's first token alone says what it is**; nothing is looked up:
a keyword - its statement; `$name` - code (an assignment or an expression); `name(` with no space -
code (a call); a number, a quote, `[`, `(`, `not` - code (at the prompt its value is shown); any
other word - a command: a program, a def or a builtin (`ls -l $dir`, `./build.sh`, `greet bob`).
`command $EDITOR $f` runs a program named by a value or named like a keyword (POSIX's `command`).
A missing program is an error when its line runs, as in every shell.

**R3. A command's words are text.** In a word: `$name` and `$name[key]` - one value, one argument,
never split or globbed; `${name}` where letters follow (`${base}s`); `$(...)` (R4); `@name`,
`@name(...)`, `@(...)` - a list, one argument per element. A `.` after a name is text (`$f.bak`);
globs come from the word's own characters (`$dir/*.log`), never from a value. A list or map given
as `$x` to a program is an error that says `@x` or `$(json($x))`; to a def or builtin it passes whole.

**R4. `$(...)` is the one way in**, for commands and expressions both - R2 reads what is inside:
`$(date)` is a command's output, its last newline dropped; `$($n + 1)` and `$(len($l))` are values,
and sh's `$(( ... ))` falls out of it. `@(...)` is a list (a command's lines, or an expression's
list); `?(...)` is whether a command succeeded: `if $force or ?(test -w $f) {`.

**R5. In code, text is quoted**: `"/tmp"`, `'raw'`. Bare words in code are keywords, a call's name
before `(`, and keys: `{name: "ada"}`, `$p[name]`. Any other bare word is an error that asks
`$dir` or `"dir"`.

**R6. A string substitutes what a word does** - `$name`, `$name[key]`, `${name}`, `$(...)` - and
nothing else: `{` and `}` are characters, so JSON text needs no escapes. `'...'` substitutes
nothing; `"""..."""` blocks stay.

**R7. Data nests**: `[1, "a", [2, 3]]`, `{name: "ada", tags: ["x", "y"]}`; one indexing everywhere,
`$cfg[servers][0][host]`, in code, in a word and in a string. JSON in and out:
`$cfg = from_json($(cat config.json))`, `curl -d $(json($req)) $url` - jq's job, built in.

**R8. `if` and `while` take a command or an expression**, by R2: `if grep -q ERROR $f {`,
`if ! test -d $d {`, `if $n > 3 {`; `?(...)` mixes them.

**R9. Iteration takes words, as a command does**: `for $f in $dir/*.log`, `for $s in @stats`,
`for $i in @range(10)`, and comprehensions the same: `[$s[file] for $s in @stats if $s[lines] > 2]`.
`for $x in $list` is an error that says `@list` - one item that is a list is a mistake.

## The same task, now and proposed

Scan the logs, record each file's lines and errors, print them sorted, archive the big ones.
rill2 now (it runs; the three assignments in the second loop are there to get fields into a string):

    cfg = {logdir: "/tmp/sx/logs", limit: 2}
    stats = []
    for f in glob(cfg["logdir"] + "/*.log") {
        n = int($(wc -l < $f))
        errs = int($(grep -c ERROR $f))
        stats += [{file: f, lines: n, errors: errs}]
    }
    for s in sort_by(stats, "lines") {
        file = s["file"]
        lines = s["lines"]
        errors = s["errors"]
        print("{file}: {lines} lines, {errors} errors")
    }
    big = [s["file"] for s in stats if s["lines"] > cfg["limit"]]
    if len(big) > 0 {
        tar czf /tmp/sx/old.tgz @big
    }

Proposed:

    $cfg = {logdir: "/tmp/sx/logs", limit: 2}
    $stats = []
    for $f in $cfg[logdir]/*.log {
        $n = int($(wc -l < $f))
        $errs = int($(grep -c ERROR $f))
        $stats += [{file: $f, lines: $n, errors: $errs}]
    }
    for $s in @sort_by($stats, "lines") {
        print "$s[file]: $s[lines] lines, $s[errors] errors"
    }
    $big = [$s[file] for $s in @stats if $s[lines] > $cfg[limit]]
    if len($big) > 0 {
        tar czf /tmp/sx/old.tgz @big
    }

`$f` is `$f` on every line; the glob is a word, as in a shell; fields go straight into strings.

## Where each rule takes a trap away

| Case | sh | rill2 now | proposed |
|---|---|---|---|
| a variable named like a program | cannot clash | breaks the command | cannot clash (R1) |
| a branch naming a program absent here | runs | script refused | runs (R2) |
| JSON-like text in a string | fine | error | fine (R6) |
| a value with a space, as an argument | split, unless quoted | one argument | one argument (R3) |
| a list to a program | `"${a[@]}"` | `@big` | `@big`; `$big` an error saying so (R3) |
| `$f.bak` | `$f` and ".bak" | `$f` and ".bak" | `$f` and ".bak" (R3) |
| a mistyped variable `$dri` | empty - `rm -rf $dri/build` is `rm -rf /build` | an error | an error before running (R1) |
| `x = 5`, Python's habit | runs a command `x` | assigns | an error saying `$x = 5` (R1) |
| a bare word after `=` | - | an error | an error saying `"word"` or `$(word)` (R5) |
| a field in a string | - | quotes inside quotes (lost text till 842) | `"$s[file]"` (R6) |

## The other way, and when it would be better

YSH's two explicit modes keep expressions Python-clean - `total = a * b + c` - at the price this
study was asked about: a variable written two ways, and a dozen sigil pairs to learn (its own table
lists them). It is the better choice for a language that is mostly computation with some commands.
For one that is a shell first, with real data, one sigil is the simpler rule. A middle way is the
shell's own convention, which Rill uses: bind bare (`total = 0`, `for f in`), read with `$` - one
form for reading, but a name seen two ways, and bare words in code then need a lookup (Rill's
"a bare word naming a variable") to catch the forgotten `$`.

## A.1 - after a first review (846)

Five models reviewed A (docs/asks/); every claim was checked against the rules as sent, bash and
dash, and today's builds (`docs/asks/ask-rill-syntax-answers-845.md`). Ten holes held, and A.1
fills them: `NAME=value` before a command is its environment; a def is called only as `name(...)`,
so `$( )` keeps one form with no silent case; `$name[` in a word or string is an error offering
bash's `${name[key]}` - `$base[0].txt` means `file[0].txt` to bash; a `$` before no name is text and
`$1`-`$9` are the script's arguments; `@` spreads in code too; braces are characters, a lone `{`
ending a header's command and a lone `}` a block's; an unbound `$NAME` in capitals reads the
environment and is an error when unset; the prompt shows an expression's value; a `(` in a word is
an error with hints; `$(...)` drops every trailing newline. Rules R1-R11 in
`docs/asks/ask-rill-syntax-grammar-846.md`.

## What it would take

In rill2, whose runtime stays: the tokenizer reads `$name` in code, `@name`, `?(`; strings drop
`{...}` for `$`-substitution; R2's first-token rule replaces the variable and PATH lookup (which
goes); `$(...)` gains its expression branch; bare words in code become errors with their hints;
`for` takes words. The tests (13 scripts, errors and the Rill comparison) convert mostly by a
script. Size: about even - the lookup and `{}` go, `?()`, `@()` and word lists in `for` come.
Two or three turns. Decision: Q46.

## Sources

fish for bash users (fishshell.com); Elvish quick tour and language reference (elv.sh); PowerShell
about_Parsing (learn.microsoft.com); Nushell book - variables, strings, 0.97 release notes
(nushell.sh); YSH - A Feel for YSH Syntax, Command vs. Expression Mode (oils.pub / oilshell.org);
xonsh tutorial and FAQ (xon.sh); Hush (hush-shell.github.io, and its UFMG paper); zx (google.github.io/zx).
