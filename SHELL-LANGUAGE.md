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
echo "{#files} C files"        # #list is its length

# capture is parentheses; splitting is a call
today = (date +%F)             # text, trailing newline removed
commits = lines (git log --oneline)
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
    {#files} files compiled.
echo done                      # the block ended with its indentation

# functions: named parameters; output and return value are different things
def greet who { echo "hi {who}" }
def c-count dir -> number { return #(glob "{dir}/*.c") }

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
