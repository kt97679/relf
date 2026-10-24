# RILL-LEDGER.md - Rill's features, each one weighed

Rill is designed in SHELL-LANGUAGE.md (Parts 2-4). This ledger is where
it is tried against real scripts before any of it is built, and where
every feature beyond that design has to earn its place.

## The rules (the user's, Iterations 725-726)

1. **Both a shell and a scripting language**, designed together: good at
   the prompt and in a 2,000-line program, so that a script that grows
   never has to be rewritten in Python. Settled at 726.
2. **Expressive, not cryptic.** A reader who knows neither sh nor Rill
   should be able to guess what a line does.
3. **Never longer than the original.** Measured by
   `tools/rill-measure.py`: code lines and characters, comments, blank
   lines, indentation, the `#!` line and a Python module's docstring not
   counted.
4. **What a real script needs is added; everything is tracked and
   audited** (revised at 732 - the user: a feature set cut until the tool
   is unusable helps nobody). A feature enters when a rewrite of a real
   script needs it - the alternatives (an external program, a Forth word
   exposed as a function, doing without) clearly worse. A function before
   syntax. Every feature is in the register, examples/rill/FEATURES.tsv,
   with its status (spec, adopted, open, rejected), the iteration it
   entered and a pattern that finds its uses; `tools/rill-audit.py`
   counts them across every rewrite and flags an adopted feature nothing
   uses any more and an open or rejected one something uses all the
   same, and measures every rewrite in examples/rill/MANIFEST.tsv against
   its original. It runs at the end of every Rill iteration, and its
   flags go into the log.

## Decisions

These override SHELL-LANGUAGE.md where the two differ.

**727 - one rule for names, everywhere.** `$name` reads a variable - in
a command, in an expression, in a string. A bare word is text - in a
command, in an expression, in a list. `name(...)` calls a function. A
name is written bare only where it is being bound: left of `=`, after
`for`, as a `def` parameter, as the target of `x[k] =`. In strings,
`"$name"` reads a variable and `"{expr}"` any expression. `@name`
spreads a list's items into arguments or a list; the list itself, as a
value, is `$name` (`len($files)`, where the design's examples wrote
`len(@files)`). Variable names are letters, digits and `_` - the dash
stays in the names of functions and commands - so `"$tag-p$p"` reads
`$tag`, then `-p`, then `$p`.

The user's vote, for consistency, over 726's leaning - `$` in commands
and bare names in expressions, which gave one token two meanings by
context: `echo hello` printed text where `x = hello` would have read a
variable. With one rule, `x = hello` is text there too, as in sh. The
design's grammar already said so (`term = var`); its examples, which
wrote `{name}`, did not. Measured on the rewrites, the rule costs almost
nothing: make-bundle 749 -> 745 characters (`"$dir/..."` is shorter than
`"{dir}/..."`), native-ab-layouts 2,489 -> 2,505, the one-liners 442 ->
444 - none longer than its original. It is also the rule of the
scripting languages that grew out of shells: Perl, PHP and PowerShell.

**732 - the needed features adopted, and an audit to watch them.** The
user's rule: if a feature is needed, add it; monitor, track and audit.
Adopted, each from the rewrites' evidence in the tables below: `$(...)`
in strings, the `all>` port, `par for`, quoted keys in record literals,
indexing and index assignment, map keys of any scalar, `k in x` and
`a not in b`, `x += n` and `x -= n`, comprehensions with a filter,
`for i, x in list`, `break` and `continue`, `{expr}` as a command's
argument, `cd DIR { }`, `fail`, `arg(n)`, `$args`, `$script`, `env()`,
`number()`, `code(run)`, `range(a, b)`, the text, file, list and path
functions, adjacent items joining. Rejected: conditions without
parentheses - they cannot stand with `{expr}` arguments, and they are
brevity, not need. Open, and used, so flagged until decided: fractional
numbers (native-ab's geometric mean; relf's Forth has no floating point,
so this is engine work) and regular expressions (one use; a matcher in
Forth, or grep and sed). The register is examples/rill/FEATURES.tsv; the
tables below keep the evidence each decision rests on.

With them, dead-words.py is 3,502 characters against Python's 3,299:
+6.2 %, from +7.5 %. The audit keeps it on its LONGER line until
something shortens it or the rule is restated.

**731 - relfsh is not to break.** The user's rule. A Rill iteration
changes only Rill's files (rill/, examples/rill/, tests/rill/, its
tools) and the docs; `tools/rill-guard.sh` fails if anything else
changed since the last commit that changed relfsh, and verify must pass
with every row of tests/BASELINE unmoved - relfsh's image sums among
them. At 731, in a workspace rebuilt from the bundle: VERIFIED.

**729 - one language: Rill supersedes Fern.** The user's decision:
Rill is both relf's shell language and its scripting language; Fern,
designed in forth-vm-evolution for the scripting half, is obsolete and
not to be built. Rill takes Fern's compiler and runtime - compiled as
parsed into Forth words, kinds fixed at compile time, integer `+`, an
arena per script, no fractions, CATCH and THROW, a `--list` of the
generated Forth - and keeps its own syntax where the two differed
(blocks in `{ }`, `$name`, `return` with output apart, `"$name"` and
`"{expr}"`). How it compiles: SHELL-LANGUAGE.md Part 5.

**730 - its own image.** Rill is not loaded into the shell's image: it
is built as its own, from the kernel, the Forth libraries the shell's
image also loads, and Rill's sources - so relfsh stays untouched and
the two compare directly, image to image, on one kernel. Rill has its
own small executor on the kernel's process words; whether the shell's
job control and editor become a library both share is decided when Rill
reaches the prompt. SHELL-LANGUAGE.md Part 5.

## From forth-vm-evolution: Fern and the c4 family (728)

Two notes the user pointed to (results/drafts/fern-design-457.md and
c4-family-459.md in kt97679/forth-vm-evolution). Fern is a design for
the same thing Rill's scripting half is: a small Ruby- or Python-like
language compiled into Forth words, close to hand-written Forth in cost
- and it names RelF's shell as a place it could serve.

**What Rill takes from Fern - its compiler and runtime, not its syntax:**
- **Compiled as it is parsed**: a tokenizer and a recursive-descent
  parser emitting with COMPILE, and LITERAL as they read, as Forth
  compiles itself - no syntax tree, no interpreter loop; every function
  a Forth word, every Forth word callable. Fern's expected cost: within
  0-20 % of hand-written Forth, a call about two dispatches.
- **Kinds chosen at compile time**: Fern leaves out run-time type tags -
  a tag check on every `+` would be the largest cost - and has the
  compiler pick an operation from what it knows, or the program name
  it. For Rill's kinds: known statically wherever they can be (literals,
  `$(...)` is text, a `def`'s `-> kind`), a check only where they cannot.
- **Memory: an arena per script, freed at its end** - Fern's choice,
  "right for shell-style scripts". The simplest memory model, as the
  ledger asks; per command at the prompt. A collector waits for an
  example that needs one.
- **No fractional numbers**: the Forth is integer-only (relf's kernel
  too). Supports the leaning against them.
- **Errors through CATCH and THROW**, as Rill's failure model already
  maps.
- **A listing of the generated Forth** beside each source line, after
  c4's `-s`: the overhead in plain sight - for Rill, from the start.
- **Expressions by precedence climbing** (c4's `expr`): one function.
- Locals: Fern plans frames on the return stack; relf has shallow-bound
  locals already (shadow.4, engine opcodes since 517 - CV8.md 6.3, the
  largest single speed-up CV8 has), one dispatch an access. Rill uses
  those.

**Where Fern and Rill differ - one language would have to choose:**
blocks (`def ... end`, Fern's, for an easy Forth parse; `{ }`, Rill's);
variables (bare, Fern's; `$name`, Rill's 727 rule, which a shell needs);
a function's value (its last expression, Fern's; `return`, with output
apart, Rill's - a shell function prints); interpolation (`#{...}` and
`{...}`/`$name`). Decided at 729: one language, Rill's syntax, Fern's
compiler.

## Conversions

`python3 tools/rill-audit.py` prints the current figures; the table is
as of the iteration that last changed it.

| original | code lines | chars | Rill lines | chars | |
|---|---:|---:|---:|---:|---|
| tools/make-bundle.sh | 24 | 773 | 17 | 745 | shorter |
| tools/native-ab-layouts.py | 87 | 3,863 | 65 | 2,501 | shorter |
| 12 prompt one-liners | - | 476 | - | 444 | none longer |
| tools/intrfuzz-stress.sh | 38 | 1,199 | 32 | 1,118 | shorter |
| tests/shell/run-utf8 | 20 | 774 | 16 | 661 | shorter |
| tools/dead-words.py | 148 | 3,299 | 112 | 3,502 | **longer, by 6.2 %** (7.5 % before 732) |

The rewrites are in examples/rill/. What they show:

- **Glue that sh already does well gains little in length** -
  make-bundle is 3 % shorter in characters, the sed that pulls the
  iteration number out of the subject and the messages being the same
  words. What it gains is in kind: no quoting anywhere, failure stops
  without `set -e`, `on EXIT` for the trap, the refs a list rather than a
  string to be split.
- **Python's orchestration shrinks most** - a quarter of the lines, a
  third of the characters: commands run as written instead of strings
  handed to `subprocess.run(..., shell=True)`, interpolation instead of
  `%` formatting, failure that stops instead of a return code checked
  after each call, `cd DIR { }` instead of `cwd=`.
- **Python's density has to be matched, not just its reach**: four list
  comprehensions and its indexing are why the Rill version is shorter
  and not longer. Written as loops, it would still be shorter than the
  Python, by less.
- **The one-liners hold only with three small additions** - `stem()`,
  the `all>` port and adjacency - without which three of the twelve
  would be longer than sh's.

### dead-words.py: the first rewrite that is longer (731)

dead-words is Python's home ground: no commands at all, a tokenizer, a
graph of definitions, sets and maps, a breadth-first search, a file
rewritten. Rill takes a quarter fewer lines and 248 more characters. Where
they come from, counted:

| source | characters |
|---|---:|
| `$` on 225 reads of a variable (727's rule) | +225 |
| parentheses around 29 `if` and `while` conditions | +58 |
| 23 lines that only close a block (`}`), where Python dedents | +23 |
| `x = $x + 1`, 7 times, where Python writes `x += 1` | +28 |
| `not ($a in $b)`, 7 times, where Python writes `a not in b` | +28 |

So the one rule for names is what costs most, as expected where nearly
every word is a variable: about one character in fifteen. What could pay
it back, each a candidate below: `x += 1` (-28), `a not in b` (-28),
conditions without parentheses (-58, but in conflict with `{expr}` as a
command's argument: in `if test -f $x {`, is `{` the block?), slicing
`$t[2:]` (-12), `break` and `continue` (a flag and a level of nesting
less). All of them together leave it about 2-3 % longer. The user's two
rules meet here: consistency, and never longer than the original - for
a program that is all variables, they cannot both hold without some of
these, and maybe not with all of them.

The shell scripts are not affected: intrfuzz-stress and run-utf8 came
out shorter under the same rule, and make-bundle shorter than before it.

## Features the rewrites used

**From the design (SHELL-LANGUAGE.md):** commands as lines of words; `$`
for one value, `@` to spread a list; `"...{expr}..."` and raw `'...'`;
patterns in the source as lists; `$(...)` and runs `(...)`; named ports
(`err> /dev/null`, `out>err`); `??`; `if`, `for`, `def`, `return`, `on
EXIT`; lists `[...]` and records `{k: v}`; `load`; `default()`.

**Candidates these rewrites introduced** - each proposed, none adopted
yet; the uses are the evidence so far:

| candidate | used by | instead of | without it | leaning |
|---|---|---|---|---|
| `fail "message"` | make-bundle 2, native-ab 3 | `echo ... >&2; exit 1` | `echo "..." out>err; exit 1`, 16 characters more each | yes: a builtin |
| `arg(n)` | make-bundle 1, native-ab 3 | `${1:-.}`, `sys.argv[1] if ...` | an `args` list and indexing | open: `arg(n)` or `args[n]` |
| `env(name)` | native-ab 2 | `os.environ.get` | - (the environment must be reachable) | yes: a function |
| ~~bare names in expressions~~ | every rewrite | - | - | **no** - decided at 727: `$name` everywhere (Decisions, above) |
| `cd DIR { block }` | native-ab 3 | `cwd=`, `(cd x; cmd)` | a run cannot hold a list of statements | yes |
| `read`, `write`, `contains`, `replace`, `split`, `words`, `lines`, `first`, `len` | native-ab | Python's str and file methods | `cat`, `grep -F`, `sed` with every special character escaped | yes, as the small library |
| `all(text, regex)` | native-ab 1 | `re.findall` | `awk` (cryptic), or `words()` and a loop (+3 lines) | open: dead-words.py decides |
| fractional numbers, `log`, `exp`, `min`, `max` | native-ab (a geometric mean) | Python floats | an `awk` program for the statistics | open: one use so far |
| `x[i]`, `x[k] = v`, `k in x` | native-ab 6 | Python indexing | `at()`, `put()`, `has()` functions, longer | yes: postfix in expressions |
| `[expr for x in list]` | native-ab 4 | Python's comprehension | a loop, two lines more each | open: syntax, but one rule and familiar |
| `for i, x in list` | native-ab 1 | `enumerate` | a counter, two lines more | no, until more uses |
| `{expr}` as a command's argument | native-ab 5 (printf) | `"{expr}"` | two quotes more each | open: unambiguous after a command word |
| `stem(path)` (and `ext`, `dir`, `base`) | one-liner | `${f%.jpg}`, `basename`, `dirname` | `trim-suffix(f, ".jpg")` - longer than sh | yes: the path functions |
| the `all>` port: out and err together | one-liner | `>/dev/null 2>&1` | `> /dev/null err>out`, longer than sh | yes: a port name, no syntax |
| adjacent items join: `backup-$(date +%F).tgz` | one-liner | sh's word joining | `"backup-{$(date +%F)}.tgz"`, longer | yes: as sh; the design does not say |
| `;` as "and then" | one-liner | `&&` | - | none needed: failure stops |
| `par for x in list { }` - iterations at once, waits for all | intrfuzz 1 | `( ... ) &`, `pids`, `wait $pids` | a list of runs started and waited, longer | yes: one keyword before `for` |
| `range(a, b)`, both ends included | intrfuzz 3, dead-words 1 | `while [ $r -le ... ]` counters | a counter and `while`, three lines more | yes: a function |
| `$(...)` in strings, as sh | intrfuzz 3 | `"...$(cmd)..."` | `"...{$(cmd)}..."`, two more each | yes: the `$` rule reads an output too |
| `$script`, the script's own path | run-utf8 2 | `$(dirname "$0")` | - | yes |
| `abs(path)`, `dir(path)` | run-utf8 3 | `cd ... && pwd`, `dirname` | joins `stem()`'s path functions | yes |
| `code(run)`: a run's exit status, failure not stopping | run-utf8 1 | `cmd; echo $?` | `try` and a variable, longer | open |
| `$args`, the arguments as a list | dead-words 4 | `sys.argv` | `arg(n)` alone cannot loop | yes - and `arg(n)` perhaps only sugar for it |
| `push`, `extend`, `shift`, `slice` (lists in place) | dead-words 14 | `append`, `+=`, `pop(0)`, `t[2:]` | `[@l x]`, which copies | yes as functions; slicing syntax open |
| `starts`, `ends`, `trim`, `join`, `sort`, `values` | dead-words 10 | str methods, `sorted`, `.values()` | - | yes, to the small library |
| map keys of any scalar, quoted keys in literals | dead-words 4 | Python dicts | `"{$n}"` keys - clumsy | yes |
| a filter in a comprehension, `[x for x in l if c]` | dead-words 3 | Python's | a loop | with the comprehension |
| `x += 1` | dead-words 7, intrfuzz 3 | `x += 1` | `x = $x + 1`, four more each | open - weighs against 727's cost |
| `a not in b` | dead-words 7 | `not in` | `not ($a in $b)`, four more | open |
| conditions without parentheses | everywhere | Python's `if x:` | two more each | open - conflicts with `{expr}` arguments |
| `break`, `continue` | dead-words 3, intrfuzz 1 (avoided) | Python's, sh's | a flag, or `else` and a level deeper | open |

## Next conversions

tools/gen-opcodes.sh (text to code), tools/pack-results.sh (a 244-line
program), tools/size-research/native-by-source.py (records as maps), and
a small JSON API client - each measured, each adding to the table
above or to a candidate's evidence.
