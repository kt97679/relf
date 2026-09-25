# SHELL-LANGUAGE.md — a shell language of our own

GOALS.md "What comes next", item 4: a shell language designed from its
own principles - convenient and expressive, but more testable, simpler
to implement and better formalized than the POSIX one this project has
spent five hundred iterations implementing. Part 1 measures where that
language's cost lives, so the design can refuse the right things; Part 2
is the design.

## Part 1 — where the POSIX language's cost lives (Iteration 502)

`tools/feature-cost.py` assigns each of the 821 colon definitions in
`shell.4`, `tree.4` and `edit.4` to a feature by its name - the
per-feature prefixes FORTH-STYLE.md 5 asks for make that possible - and
counts two things per feature: **code**, lines that are neither comment
nor blank; and **trouble**, how many of the 445 iteration titles in
PROGRESS.md name the feature, a proxy for how hard it was to get right
rather than merely to have. The rules are written out in the tool, to be
read and argued with; 2.8% of the code, 91 small helpers, is claimed by
none of them.

| feature | lines | % | trouble | per 100 lines |
|---|---|---|---|---|
| lexer and parser | 1,045 | 12.6 | 21 | 2.0 |
| execution and control flow | 927 | 11.1 | 61 | 6.6 |
| the expander, in general | 778 | 9.4 | 48 | 6.2 |
| line editor, history, completion (not POSIX) | 495 | 6.0 | 17 | 3.4 |
| arithmetic | 467 | 5.6 | 5 | 1.1 |
| pathname expansion and patterns | 380 | 4.6 | 13 | 3.4 |
| variables and the environment | 379 | 4.6 | 22 | 5.8 |
| job control | 328 | 3.9 | 9 | 2.7 |
| quoting, `$'...'`, word encoding | 284 | 3.4 | 25 | 8.8 |
| parameter expansion | 250 | 3.0 | 12 | 4.8 |
| traps and signals | 240 | 2.9 | 9 | 3.8 |
| read | 210 | 2.5 | 5 | 2.4 |
| redirections | 207 | 2.5 | 20 | 9.7 |
| ulimit, umask, kill, times | 200 | 2.4 | 3 | 1.5 |
| prompt escapes (not POSIX) | 196 | 2.4 | 5 | 2.6 |
| echo, printf, backslash escapes | 183 | 2.2 | 3 | 1.6 |
| field splitting (IFS) | 180 | 2.2 | 17 | 9.4 |
| cd and pwd | 170 | 2.0 | 3 | 1.8 |
| aliases | 168 | 2.0 | 10 | 6.0 |
| test and `[` | 156 | 1.9 | 10 | 6.4 |
| here-documents | 137 | 1.6 | 5 | 3.6 |
| command substitution | 134 | 1.6 | 11 | 8.2 |
| options and tracing (`set`) | 130 | 1.6 | 10 | 7.7 |
| getopts | 114 | 1.4 | 2 | 1.8 |
| functions | 87 | 1.0 | 10 | 11.5 |

The rest - plumbing, startup, `forth`, the unclaimed - is under 6%.

### What the numbers say

**No feature can be dropped to halve the source.** The largest single
one is the parser, at 12.6%. Dropping every extra POSIX does not ask for
(the line editor, prompt escapes, `forth`: 8.7%) and every builtin that
could as well be a program of its own (`test`, `echo`, `printf`,
`getopts`, `ulimit` and its kin: another 7.9%) comes to about 17%.

**The cost is the language model, and the trouble is concentrated
there.** The features that needed a fix every ten or so lines are
quoting (8.8 per 100), field splitting (9.4), redirections (9.7),
command substitution (8.2), `set`'s options (7.7) and functions (11.5);
the builtins needed one every fifty or more - arithmetic, the largest
builtin, 1.1 per 100. Trouble lives where features *meet*: one word
passes through tilde, parameter, command and arithmetic expansion, then
field splitting, pathname expansion and quote removal, and every stage
has rules that depend on what the stages before it did - whether text
came from a quote, from an expansion, from an assignment, from a
redirection target. The expander carries flags for exactly those
contexts (`XE-NOSPLIT?`, `WORD-IS-ASSIGN?`, `REDIR-TARGET-WORD?`,
`TOK-WAS-QUOTED?`), and a good part of the log is the story of those
flags leaking into each other: Iteration 471's three fuzzer bugs were
all of that one kind.

**The parser is big but was not where the trouble was** - 2.0 per 100
lines. Its difficulty is the language's: here-documents that begin on
one line and whose bodies come after it, aliases that rewrite the input
as it is read, line continuations inside every construct, reserved
words that are reserved only in some positions, `$(...)` whose end can
only be found by parsing what is inside. The lexer and parser are large
because the grammar is context-dependent at the level of characters.

So the design input is: **a language in which text is never re-read.**
Every one of the troublesome stages exists because POSIX sh turns
values back into text and parses that text again - splitting it,
globbing it, removing quotes from it. Part 2 starts there.

## Part 2 — Rill (Iteration 503)

A design, not an implementation: what it is, how it reads, what it
removes, and what is still open. Where an idea echoes an existing shell
it says so; nothing here has yet been checked for novelty against the
literature (`prompts/02-escape-recall.md` comes before any such claim
goes into the article).

### The five decisions

1. **Text is never re-read.** A value is a value. `$x` is always one
   argument, whatever it contains; nothing splits it, globs it or
   removes quotes from it. Splitting is a function you call, globbing
   happens only to patterns written in the source. This one rule deletes
   field splitting, quote removal, the second pass of pathname expansion
   and every context flag the expander carries.
2. **A command is a value until it is used.** `make -j4` written as a
   statement runs; the same words in parentheses are a *run*, a value
   that can be piped, captured, timed, retried, run in the background -
   or handed to a test that never runs it. Pipelines, command
   substitution, background jobs and process substitution become four
   uses of one thing instead of four mechanisms.
3. **The world is an interface.** Everything a script does outside
   itself - start a program, open a file, read the clock, list a
   directory - goes through a small, named set of operations. The
   interpreter is given a world. The real world runs programs; a
   recording world prints what would happen (`--plan`); a scripted world
   answers from a test's fixtures. Scripts become testable without a
   container, and a dry run is not a feature anyone had to write.
4. **Failure is a value, and it stops things.** A statement that fails
   ends its block - `set -e`, but everywhere, with no exceptions buried
   in the standard for `&&` lists and negation. Guarding a failure is
   explicit: `try`, `??`, or a condition.
5. **The grammar is context-free at the level of tokens.** Words are
   separated by blanks; a fixed set of characters are operators
   everywhere outside a string; there are two string forms. No aliases
   rewriting input as it is read, no here-document bodies arriving
   after their line, no words that are reserved only in some positions.

### How it reads

```rill
# a command is a line of words, as always
ls -la /tmp
git log --oneline | head -5

# variables: one value each; lists spread only with @
name = world
echo "hello {name}"            # "..." interpolates {expressions}; '...' is raw
files = *.c                    # a pattern in the SOURCE: a list of paths
cc @files -o app               # the list becomes arguments - explicitly
echo "{len(@files)} C files"   # len() is a function; # only begins a comment

# (...) is a run - a command not yet run; $(...) is its output
today = $(date +%F)            # text, trailing newline removed
commits = lines($(git log --oneline))   # splitting is a call
for c in @commits { echo $c }

# ports instead of descriptor numbers: in, out, err, and any you name
make > build.log  err> errors.log
make  err>out | less           # err joined to out, then piped
diff (sort a.txt) (sort b.txt) # a run as an argument: a path to its output

# failure stops the block; guarding is explicit
try { make } else { echo "build failed: {status.code}" }
rm stale.lock ?? true          # ?? - if the left fails, run the right
if (test -f config) { load config }

# structured concurrency instead of & and wait
par {
    make -C lib
    make -C app
}                              # waits for both; one failing cancels the other

# text blocks instead of here-documents: the body is what is indented
mail -s report ops <- text
    Build {today} finished.
    {len(@files)} files compiled.
echo done                      # the block ended with its indentation

# functions: named parameters; output and return value are different things
def greet who { echo "hi {who}" }
def c-count dir -> number { return len(glob("{dir}/*.c")) }

# records, for tools that speak structure
host = {name: "db1", port: 5432}
ssh -p $host.port $host.name
```

What is gone: `IFS`, `set -e` and its exceptions, `$@` versus `$*`,
quoting to *prevent* splitting, `eval` to re-read text, `&` and `$!` in
scripts, `2>&1` numerals, `<<EOF` bodies, aliases (functions do what
they did), backquotes, `$((...))` (numbers are values:
`n = $n + 1`), `[ ]` as a program for conditions.

What stays: typing `ls -la` works; `|`, `>`, `<`, `>>` mean what they
always meant; `&` still backgrounds a job at the prompt, where job
control is for people.

### The core, formally

The surface syntax is sugar over a kernel of twelve forms, and the
kernel is what has a semantics:

```
e ::= t                      text literal
    | [e ...]                list
    | x                      variable
    | glob p                 pattern from the source -> list of paths
    | run c [e ...] P        a run: command c, arguments, port wiring P
    | force e                run it; its value is a status
    | capture e              run it; its value is its out, as text
    | let x = e in e         binding
    | seq e e                if the first fails, stop
    | try e e                if the first fails, the second
    | par [e ...]            fork all, join all, first failure cancels
    | lam (x ...) e / e(e...) functions
```

Evaluation is a relation `W, E ⊢ e ⇓ v, W'` - an environment `E`, a
world `W` before and after. The world is a value with seven operations:
`spawn(program, argv, ports) -> handle`, `wait(handle) -> status`,
`open(path, mode) -> port`, `read(port)`, `write(port, bytes)`,
`glob(pattern) -> list`, `clock()`. That is the whole of the outside.
Everything a POSIX shell spends its expander on - which characters of a
word came from where - does not exist to be specified, because values
are never text-with-history.

### Testable, because of the world

```rill
# test/deploy.test.rill
world = scripted {
    rsync -a build/ $any:host:/srv -> ok
    ssh $any systemctl restart app  -> fail 3
}
result = with $world { deploy prod }
expect $result.status == fail
expect $world.calls[0].argv == [rsync -a build/ web1:/srv]
```

A script's effects are data before they are actions, so a test can say
exactly which programs would run, with which arguments, and what
happens when one of them fails - without a container and without
writing a mock of every program. `rill --plan deploy.rill` is the same
mechanism with a world that records and does not act.

### What it would cost to build here

From Part 1's table, the machinery Rill does not need: field splitting
(180 lines), most of quoting and word encoding (284), aliases (168),
here-documents as a separate mechanism (137), parameter-expansion
operators as syntax (250 - they become functions: `trim-prefix`,
`default`), command substitution's text path (134), arithmetic's
separate language (467 - numbers are values, and the evaluator's
parser folds into the expression grammar), and most of the expander's
context flags (a large part of 778). The lexer, context-free with two
string forms and an indentation rule for text blocks, is a fraction of
1,045 lines. Execution (927), job control, traps, redirections and
the line editor are reused as they are.

A guess, to be measured by building it: **about half the source for the
same practical power** - which is the halving Part 1 found no feature
list could give, obtained by a different model rather than fewer
features. POSIX sh is not abandoned: `#!/bin/sh` scripts keep running
on the shell that exists, and both languages share the engine, the
executor and the job table.

### Open questions

- **Blocks by indentation** make text blocks context-free but give
  whitespace meaning, which sh never did. The alternative is a
  delimiter that must be alone on a line and is found by the lexer, not
  after the line; indentation is the braver choice.
- **Records at the prompt**: worth it only if tools emit them; Rill
  could read JSON on a port marked for it and leave the rest as text.
- **Interactive brevity**: `?? true` and `try` must not make one-liners
  longer than sh's. The prompt may deserve a softer failure rule than
  scripts.
- **The kernel in Forth**: each kernel form maps onto a few Forth words,
  and the world's seven operations onto engine primitives - which makes
  `forth` the natural place to extend Rill, and the assembly engine of
  item 5 its eventual floor.

## Part 3 — Rill, specified (Iteration 514)

Asked for at 514: a formal specification, POSIX constructs translated,
why the name, what each language can do that the other cannot, and
the text-block question argued rather than asserted.

### Why "Rill"

A rill is a very small stream. The picture at the language's centre is
data flowing - a command is a value until it is used, and then a
stream - and a shell's work is mostly plumbing streams together. The
name is also four letters, like `bash` and `dash`, pleasant to type
as a command, and not, as far as I know, the name of a well-known
language - unchecked; `prompts/02` comes first if it ever matters. It
is a working name, and costs nothing to change today.

### What writing the grammar changed

Writing it down found two places where Part 2 depended on context -
the very thing the language exists to avoid - and Part 2 is corrected:

1. **`#` meant two things**: a comment, and a length operator
   (`{#files}`). Now `#` only begins a comment, where a word could
   begin; length is the function `len(...)`.
2. **`( )` meant two things**: in `x = (date)` the output, in
   `if (test -f x)` the status - decided by where it stood. Now `(...)`
   is always a *run*, a command not yet run, and `$(...)` is always its
   output. A condition runs a run and asks its status; that is the one
   conversion, and the grammar's position says where it happens.

### Lexical structure

```
blank    = " " | TAB ;                newline = LF ;
comment  = "#" { any but LF } ;       only where a word could begin
name     = letter { letter | digit | "_" | "-" } ;
word     = wchar { wchar } ;          wchar: anything but blank, LF,
                                      and  | & ; ( ) { } [ ] " ' $ @ < > =
var      = "$" name { "." name } ;    one value, never split or globbed
spread   = "@" name ;                 a list, its items as arguments
string   = '"' { char | "\" esc | "{" expr "}" } '"' ;   interpolates
raw      = "'" { any but "'" } "'" ;                     verbatim
pattern  = a word holding * ? or [ : globbed once, to a list of paths
ops      = | |& & ; ( ) $( { } [ ] = == != < <= > >= + - * / % ?? -> <-
           and redirections  > >> <  and  NAME> NAME>> NAME>NAME
keywords = if else for in while def return try par on and or not
```

The lexer has two states besides the ordinary one - inside a string
(where `{ }` nests an expression) and inside a text block - and nothing
else changes how a character is read. **Keywords are always reserved**,
wherever they stand: `if` is never a command name (quote it, `'if'`, to
run a program so called). There are no aliases.

### Syntax

```
program     = { statement terminator } ;
terminator  = LF | ";" ;
statement   = assignment | definition | control | background | pipeline ;
assignment  = name "=" expr ;
definition  = "def" name { name } [ "->" kind ] block ;
control     = "if" cond block [ "else" ( block | control ) ]
            | "for" name "in" expr block
            | "while" cond block
            | "try" block [ "else" block ]
            | "par" block
            | "on" name block                       (a signal, or EXIT)
            | "return" [ expr ] ;
background  = pipeline "&" ;
cond        = run | expr ;
block       = "{" program "}" ;
pipeline    = command { ( "|" | "|&" ) command } [ "??" pipeline ] ;
command     = item { item } ;
item        = word | var | spread | string | raw | pattern
            | run | output | list | redirect ;
run         = "(" pipeline ")" ;
output      = "$(" pipeline ")" ;
redirect    = [ name ] ( ">" | ">>" | "<" ) target
            | name ">" name                         (a port joined to another)
            | "<-" textblock ;
target      = word | var | string | raw | run | output ;
expr        = unary { binop unary } ;
unary       = [ "not" | "-" ] term ;
term        = number | var | spread | string | raw | pattern | run | output
            | list | record | call | "(" expr ")" ;
call        = name "(" [ expr { "," expr } ] ")" ;
list        = "[" { term } "]" ;
record      = "{" [ name ":" term { "," name ":" term } ] "}" ;
binop       = "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | "<=" | ">"
            | ">=" | "and" | "or" ;
```

It is LL(1) but for two places that need one more token: a statement
that begins `name =` is an assignment (so `=` is never a command's
argument unless quoted), and a `{` after `=` or in a term begins a
record where at a statement it begins a block. Every other decision is
made by the next token alone.

### Kinds, and the conversions between them

A value is one of: **text**, **number**, **bool**, **list**,
**record**, **run**, **status**. Nothing converts implicitly except
these, each fixed by where the value is used:

| used as | from | becomes |
|---|---|---|
| a command's argument | text, number | itself (a number as decimal text) |
| | list | an error - `@name` spreads, `$name` does not |
| | run | a path from which its output is read (`/dev/fd/N`) |
| | record, bool, status | an error |
| a condition | status | success is true |
| | run | run it; its status |
| | bool | itself; text is never "truthy" |
| `$(...)` | run | its output, as text, one trailing newline removed |
| `"{expr}"` | anything but record | its text |

### The kernel's semantics

The surface desugars into the twelve forms of Part 2. Evaluation is
`W, E ⊢ e ⇓ v, W'` - world and environment before, value and world
after. A selection of the rules, the ones where shells usually go wrong:

```
          W, E ⊢ e1 ⇓ ok, W1    W1, E ⊢ e2 ⇓ v, W2
 (seq)    ─────────────────────────────────────
          W, E ⊢ seq e1 e2 ⇓ v, W2

          W, E ⊢ e1 ⇓ fail(s), W1
 (seq-f)  ───────────────────────────────                 a failure stops
          W, E ⊢ seq e1 e2 ⇓ fail(s), W1                  the rest - always

          W, E ⊢ e1 ⇓ fail(s), W1    W1, E[status := s] ⊢ e2 ⇓ v, W2
 (try)    ───────────────────────────────────────────────
          W, E ⊢ try e1 e2 ⇓ v, W2

          W, E ⊢ c ⇓ run(p, args, ports), W1
          spawn(W1, p, args, ports) = (h, W2)    wait(W2, h) = (s, W3)
 (force)  ───────────────────────────────────────────────
          W, E ⊢ force c ⇓ s, W3

          W, E ⊢ glob p ⇓ [paths matching p in W], W      the pattern is
                                                          source text: it
                                                          is never a value
```

What these do not contain is the point: no rule looks at where a
value's characters came from. A POSIX specification of the same needs
the expansion stages, field splitting and quote removal - and each
stage's rules depend on the stage before (Part 1).

### POSIX constructs, in Rill

| POSIX sh | Rill | note |
|---|---|---|
| `x="a b"; echo "$x"` | `x = "a b"; echo $x` | `$x` is one argument: no quotes needed to keep it whole |
| `echo $x` (to split it) | `echo @words($x)` | splitting is asked for |
| `for f in *.c; do cc -c "$f"; done` | `for f in *.c { cc -c $f }` | |
| `"$@"` | `@args` | |
| `n=$((n+1))` | `n = $n + 1` | numbers are values |
| `d=$(date +%F)` | `d = $(date +%F)` | the same |
| `if [ -f "$f" ]; then ...; fi` | `if (test -f $f) { ... }` | or `if exists($f)` |
| `a && b \|\| c` | `try { a; b } else { c }` | or `a; b ?? c` - see the rule |
| `set -e` | the default | and without POSIX's exceptions |
| `cmd \|\| true` | `cmd ?? true` | a failure, explicitly accepted |
| `cmd 2>&1 \| less` | `cmd err>out \| less` | |
| `cmd >out.log 2>err.log` | `cmd > out.log err> err.log` | |
| `diff <(sort a) <(sort b)` | `diff (sort a) (sort b)` | not in POSIX at all |
| `cat <<EOF ... EOF` | `cat <- text` + a block | see "Text blocks" |
| `while read -r l; do ...; done < f` | `for l in lines($(cat f)) { ... }` | or a streaming `read` builtin |
| `case $x in a*) ...;; esac` | `if matches($x, "a*") { ... }` | a `match` statement is an open question |
| `f() { echo "$1"; }` | `def f a { echo $a }` | named parameters |
| `trap 'rm -f $t' EXIT` | `on EXIT { rm -f $t }` | |
| `cmd & pid=$!; wait $pid` | `j = (cmd) &; wait $j` | a job is a value |
| `(cd d && make)` | `in d { make }` | a builtin block; no subshell needed |
| `IFS=: read -r a b` | `[a b] = split($line, ":")` | list destructuring |
| `eval "$cmd"` | - | deliberately absent |

### What each can do that the other cannot

**POSIX sh can; Rill cannot, as designed:**
- **`eval`** - run text built at run time as code. Absent on purpose:
  it is re-reading text, the source of Part 1's trouble. A script that
  needs it can run `sh -c`.
- **Run existing scripts.** Rill is not compatible, and no script is
  translated automatically. `#!/bin/sh` scripts keep this project's
  POSIX shell.
- **Aliases**, and anything else that rewrites the input as it is read.
- **Split and glob a value implicitly** - `$x` with IFS. Asked for,
  it is one call; unasked, it never happens.
- **Keep failures going silently.** Without `set -e`, sh carries on
  after a failure; Rill stops unless told `??` or `try`. At the prompt
  that may be too strict - an open question.
- **Hold a descriptor across commands** by number (`exec 3>f`, then
  `>&3`). Ports are named per command; a long-lived one would be a
  value (`log = open("f", "w")`) - designed, not yet specified.

**Rill can; POSIX sh cannot:**
- **Values that survive any content** - spaces, newlines, globs,
  leading dashes - with no quoting discipline to get wrong.
- **Lists and records** as values; functions that **return** values,
  not only a status and output.
- **Process substitution and named ports** in the language, not as an
  extension (`<( )` is bash's, not POSIX's).
- **Structured concurrency**: `par { }` waits for all and cancels the
  rest when one fails. POSIX has `&`, `wait` and `$!`, and the
  bookkeeping is the script's.
- **Testing a script without running its programs** - a scripted world,
  and `--plan` for a dry run.
- **Failure that is total**: POSIX's `set -e` is ignored inside `&&`
  lists, `if` conditions, negations and functions called from them.
- **A formal semantics** short enough to read - and so, to test against.

### Text blocks: indentation, or a delimiter?

A here-document's body has to end somewhere, and in nested code it has
to sit somewhere. Four designs, each shown with the same text - two
lines at the margin, one indented two more - inside a `def` and a `for`:

**A. The indentation ends it** (Part 2's choice; like YAML and Python).
The margin is the first body line's indentation; the block ends at the
first line indented less.

```rill
def report {
    for f in @files {
        mail ops <- text
            Build {f} finished.
              details follow
            Done.
        echo sent
    }
}
```

*For*: no delimiter to choose or collide with; it reads like the code
around it; the lexer needs only a line's indentation. *Against*:
whitespace becomes meaning, which sh never had - **tabs against
spaces** is now a correctness question; a body whose FIRST line is
meant to be indented further than the rest cannot say so (YAML needed
an indentation indicator, `|2`, for exactly this); trailing blank
lines are ambiguous; pasting into a terminal or an editor that
re-indents changes the text; and at the prompt, typing the indentation
by hand is tedious.

**B. A delimiter line ends it** (sh's `<<EOF`, but read in order).
The body starts on the next line and ends at a line holding only the
delimiter; the lexer reads it then and there, not after the rest of
the command line as sh does.

```rill
def report {
    for f in @files {
        mail ops <- EOF
Build {f} finished.
  details follow
Done.
EOF
        echo sent
    }
}
```

*For*: familiar; any text but the delimiter line; no whitespace
meaning. *Against*: in nested code the body must start at column 0,
breaking the shape of the code - sh's `<<-` strips TABS only, which
is why it is hardly used; a delimiter can collide with the text.

**C. The closing delimiter's indentation is the margin** (Swift's
multi-line strings, Java's text blocks). The block ends at its closing
marker, and however far that marker is indented is stripped from every
line.

```rill
def report {
    for f in @files {
        mail ops <- """
            Build {f} finished.
              details follow
            Done.
            """
        echo sent
    }
}
```

*For*: indentation is the code's, the margin is **explicit**, a first
line can be indented further than the rest, and any depth of nesting
works the same way. *Against*: a closing line is required; a line
indented less than the marker is an error that has to be reported
well; `"""` inside the text needs an escape.

**D. Every line is marked** (Zig's multi-line strings). Each line of
the text starts, after any indentation, with a marker; the block is
the run of marked lines.

```rill
def report {
    for f in @files {
        mail ops <-
            | Build {f} finished.
            |   details follow
            | Done.
        echo sent
    }
}
```

*For*: the most robust - each line says what it is, so re-indenting
cannot change the text, no terminator is needed, and the lexer's rule
is one line long. *Against*: every line carries the marker, so text
pasted in or copied out needs it added or removed, which is an editor's
job; long blocks are noisier to read.

**The comparison, on what the question was about:**

| | A indent | B delimiter | C closing marker | D line marker |
|---|---|---|---|---|
| several levels of nesting | works, implicitly | breaks the code's shape | works, explicitly | works |
| first line indented further | cannot say | yes | yes | yes |
| tabs against spaces | a hazard | no matter | a hazard only in the margin | no matter |
| pasting and re-indenting | changes the text | safe | safe if the marker moves too | safe |
| terminator needed | no | yes | yes | no |
| typing at the prompt | tedious | easy | easy | tedious |
| rule for the lexer | a margin to track | a line to match | a line to match, then strip | one line |

*My recommendation, changing Part 2*: **C** - the closing marker's
indentation is the margin. It is the only design in which several
levels of indentation are both allowed and explicit, and it keeps
whitespace meaning to one place, the marker's line. D is the more
formal and the better fit for a language generated by tools; C is the
better fit for one typed by people. The decision is the user's
(QUESTIONS.md, Q7).

## Part 4 — discussions (Iteration 515)

Two questions the user raised, argued before either is decided. Both
are about the same boundary: what a Rill value becomes when it leaves
the process, and how long a process lives once Rill has started it.

### Structured values and the environment

The environment is not Rill's to redesign: it is a list of
`NAME=VALUE` byte strings, no NUL inside, handed by `execve` to
*every* program - most of which are not Rill. So whatever a list or
record becomes in the environment, a C program or a Python script sees
text. The design question is only what Rill does at the two ends.

**Three ways it could work:**

1. **Only text crosses, and conversion is explicit.** `export` accepts
   text and numbers; a list or record is an error. Structure crosses
   because the script encodes it and the other side decodes it:

   ```rill
   cfg = {host: "db1", port: 5432, tags: ["a", "b"]}
   export CFG = json($cfg)          # text, which any program can read
   ./child.rl
   ```
   ```rill
   # child.rl
   cfg = from-json($CFG)            # the child asks for the structure
   echo $cfg.host
   ```

2. **Automatic, with the type beside it.** Exporting a record writes
   its JSON and records the kind in a second variable
   (`RILL_KINDS=CFG:record`), and a Rill child rebuilds it without
   being asked. Seamless between Rill instances - but a program in
   between (`env`, `sudo`, a C wrapper) can change `CFG` and leave the
   kind behind, so the child trusts a stale marker; and a child that
   rebuilds values from strings it did not ask to parse is *re-reading
   text*, which is the first thing Rill refuses (Part 2, decision 1).

3. **Lists tied to a separator**, as zsh ties `path` to `PATH`: a list
   declared as `:`-joined crosses as `a:b:c`, and a Rill child that
   declares the same gets it back. Right for `PATH`, `MANPATH` and
   their kind; wrong for anything whose items may contain the
   separator.

**And what the environment is poor at, whichever is chosen**: size -
Linux allows 128 KB per string and a few MB in all, shared with the
arguments; privacy - any process of the same user reads
`/proc/PID/environ`, so secrets do not belong there; and lifetime - it
is copied once, at `execve`, so it cannot carry anything that changes.
Structures that are large, private or live have better channels: an
argument, a file, or a *port*.

**Between two Rill instances, the principled channel is a port.** A
run already has ports; one can be declared to carry values - JSON, a
line each - so that when a Rill script calls another, the child's
return value comes back as a value, typed on both ends because both
ends declared it:

```rill
# the caller
stats = call(./measure.rl, "src/")      # the child's `return` value
echo "{stats.files} files, {stats.lines} lines"
```
```rill
# measure.rl
def main dir -> record {
    files = glob("{dir}/**/*.c")
    return {files: len(@files), lines: len(lines($(cat @files)))}
}
```

Underneath, `call` starts the child with descriptor 3 as a value port,
and the child's `return` writes its value there as JSON. A program that
is not Rill never sees descriptor 3. This is where Part 2's open
question about records at the prompt lands too: a structured port is
also how a Rill pipeline would pass records between Rill stages.

**Recommendation**: (1) for the environment - text only, conversion
explicit, JSON as the standard codec, since jq, Python and every other
language read it - plus value ports for Rill-to-Rill calls. Never
functions or runs in the environment: bash exported functions that
way, and the parser that rebuilt them was Shellshock.

### Processes: jobs, lifetimes, and talking to them

`par` is structured concurrency: every process it starts has ended by
the time the block does. That is right for fan-out work, and wrong for
three things a shell must also do:

- start a server, use it, and stop it - a test script's daily bread;
- start something and **talk to it** while it runs - a coprocess;
- start something meant to **outlive** the script - a daemon.

So Rill needs a second construct: **a job, as a value**.

```rill
j = spawn((server --port 8080))       # a job: running now
wait-port(8080)
run-tests
kill($j)                              # TERM; wait($j) returns its status
```

A job is a handle - process group, status once finished, and its ports.
What is done with it is ordinary function calls: `kill($j)`,
`signal($j, HUP)`, `wait($j)`, `running($j)`. The statement form `cmd &`
is `spawn((cmd))` with the job kept only in the job table, so at the
prompt `jobs`, `fg` and `bg` work as in sh.

**Talking to it**: a job's ports can stay connected to the script, which
is a coprocess - bash's `coproc`, ksh's `|&`, and in POSIX sh a
hand-built pair of FIFOs:

```rill
calc = spawn((bc -l), in: pipe, out: pipe)
send($calc, "scale=4; 2/3")
x = recv-line($calc)                  # "0.6666"
close($calc.in)                       # bc sees its end of input and exits
```

**The lifetime question - what happens to a job its script has not
waited for?** Three possible defaults:

| default | a job not waited for when the script ends | the risk |
|---|---|---|
| **as in sh** | runs on, orphaned | stray servers after a failed test run; nothing tells you |
| **bound to the instance** | is sent TERM, then KILL after a grace period | a script that meant to leave a daemon must say so |
| **bound to the block** | is stopped when the block that started it ends | most surprising; the strictest |

The block-bound form is still wanted - as a construct, not a default:

```rill
with srv = spawn((server --port 8080)) {
    run-tests                         # a failure here still stops srv
}                                     # srv is stopped here, however the block ended
```

And leaving something running on purpose is one word:

```rill
d = spawn((sync-daemon))
detach($d)                            # its own session; the script forgets it
```

**Recommendation**: jobs bound to the instance by default - no orphan
is ever an accident, which answers the question as asked: a process
started by a script is stopped when the script ends - `with` for
block-bound jobs, `detach` to outlive the script. At the interactive
prompt, jobs live as long as the shell, as in sh, since there the user
is the one managing them.

**In the formal core**, this is two operations more for the world -
`signal(handle, sig)`, and ports that stay open to the evaluator - and
one rule: when a block (or the program) ends, the world receives a
TERM for each job bound to it that has not finished. Nothing about a
job is hidden state; `jobs` is a function returning a list of job
values.
