# Syntax as genes: shells and languages split into features (864)

**The question (the owner, after 863):** take the syntax of other shells and languages, split it into
features, and use the features for genetic programming - to find the syntax and design that give the
smallest binary and the best performance.

**The short answer.** The split works: 33 systems, 23 independent choices ("axes"), 95 ways of making
them, 26 rules for which ways cannot go together - `docs/syntax-features.tsv`, checked by
`tools/syntax-space.py`, which every system in it passes. A search over it is possible in this
repository, with a strong, cheap gate (below), but only after each feature's alternatives are written
as modules of one front end - today 44 of the 95 exist in no front end here, and one front end has two
values of only one axis. What a search can measure is bytes, program length, known hazards and
compile time; **run speed it cannot move**, since every syntax in the space compiles to the same Forth;
and what decides a syntax - whether people read and write it correctly - no search here can measure.
So: a search can draw the owner a front of trade-offs; it cannot choose for him.

## What was surveyed

POSIX sh, bash, ksh and zsh; fish; rc (Plan 9) and es; execline; Elvish; Nushell; PowerShell; YSH
(Oils); xonsh; Hush; zx; murex; Ion (Redox); cosh, a concatenative shell; Tcl; Lua; Python; Forth,
Joy and Factor; scsh, Rash and Closh (Lisp shells); Perl; and this repository's Rill, rill2 and the
command model (C.2). docs/SYNTAX-STUDY.md (842-849) has the first eight in detail; this adds the
rest, and splits all of them along the same axes.

What the newly read ones bring to the table:

- **rc** - every variable a list of strings, never re-split when expanded; `^` concatenates, and
  distributes over lists (`$src^.c`); `` `{cmd} `` captures; `>[2]` and `|[2]` redirect by number;
  its users asked for the caret to be inserted automatically where words abut (Duff, "Rc - The
  Plan 9 Shell").
- **es** - rc's syntax over new semantics: lexical scope, first-class functions, exceptions; a
  lambda is `@ params { cmds }`, and `fn name args { }` is only an assignment of one to `fn-name`;
  program fragments in braces are values, closing over the lexical variables; the primitives behind
  the syntax (pipes, path search) can be replaced like any function (Haahr and Rakitzis, USENIX
  Winter 1993).
- **execline** - no interpreter stays in memory: `execlineb` turns the script into one argv and
  execs it, and control flow is done by programs that act and then exec the rest of the argv
  ("Bernstein chaining"); its grammar is a few lines (skarnet.org, "The execline language design
  and grammar").
- **murex** - pipes stay bytes but carry the name of their format (JSON, YAML, CSV ...), so
  existing tools keep working; `$x = v`, `[a, b, c]` (murex's documentation and README).
- **Ion** - the sigil says the kind: `$x` a text, `@x` an array; `$(cmd)` captures text and
  `@(cmd)` an array; `let` binds, with optional types; Ion names parse and execution efficiency
  among the three tests a feature must pass (the Ion manual and README).
- **cosh** - a shell in postfix: quotations in `[ ]`, functions as `: name ... ,,`, external
  commands set apart by a leading space - the shape of this repository's own substrate, used as a
  shell (github.com/tomhrr/cosh).

## Prior art for the method

- **Grammatical evolution** (O'Neill and Ryan, IEEE TEC 2001) evolves *programs* under a fixed
  grammar - integer genomes mapped through the grammar's rules; attribute-grammar variants add
  semantics. It searches inside one language, not across languages.
- **Language product lines** (Kühn, Cazzola and others; Neverlang; AiDE 2): a language decomposed
  into features - constructs or concepts - with a feature model saying which subsets are valid
  languages; JavaScript has been decomposed so. Their empirical study of 26 such lines found that a
  poor decomposition leaves the features tangled with each other, which shrinks the space of valid
  variants (Cazzola and Favalli, Empirical Software Engineering 27, 2022). This is the closest prior
  art to what the owner asks: the features here are axes of such a model.
- **Searching feature models** (Sayyad, Menzies, Ammar, ICSE 2013, and after): configuring product
  lines by multi-objective evolutionary search. With many objectives, NSGA-II and SPEA2 did much worse
  than IBEA; valid products were hard to find at all, and constraint-respecting operators and seeding
  were needed. The feature table's rules are such constraints (3.57% of uniform samples satisfy them,
  below).
- **One abstract syntax, many concrete ones.** Model-driven language work keeps the abstract syntax
  fixed and varies the concrete one; GrammarOptimizer (Zhang and others, 2024) does it by a catalogue
  of configurable rules - keywords, braces, layout - applied to a generated grammar. The design below
  is the same idea, with this repository's node tree as the abstract syntax.
- **What people make of a syntax.** Stefik and Siebert (ACM TOCE 13(4), 2013) measured novices'
  accuracy across languages, with Randomo - keywords drawn at random - as a placebo: Perl and Java
  were not significantly more accurate than it, while Quorum, Python and Ruby were; their Token
  Accuracy Maps find which tokens people get wrong. Such evidence is costly and thin: a review found
  156 publications comparing language design decisions at all (University of Washington,
  "Programming Languages and Learning", citing Kaijanaho's meta-analysis).
- **This repository's own searches**: GOALS.md item 10 (700-701: one knob at a time; a search over
  many could not tell its candidates apart at a 2.3% noise floor) and docs/RILL-SEARCH.md (748-767:
  seven genes, 360 designs enumerated in five minutes, most choices found right, several genes later
  taken out). The lessons stand: a gene is a choice already written two ways; enumerate before
  evolving; count dispatches, not time.

## The axes (prompts/02)

The recall first - what came to mind before enumerating:

| candidate I was about to propose | a named system? | where |
|---|---|---|
| genes for `$` sigils, keywords and blocks | yes | the shells above |
| NSGA-II over them | yes | forth-vm-evolution's lab |
| grammatical evolution | yes | O'Neill and Ryan |

All three recalled, so the space was then enumerated by axis, not by system: for each place a
parser or runtime must decide something, every way any surveyed system decides it, plus the ways
none does.

**The groups.** L - lexical: renames, no meaning (comments, keyword spellings, line continuation).
S - structural: the parser's shape (variables, binding, blocks, control, lists, maps, captures,
interpolation, expressions, parameters, spread, the first word). V - values: the runtime's model
too (splitting, kinds of values, what pipes carry, returns, errors, scope, code as a value).
F - where the front end lives. The full table, with who uses each value and which front end here
has it, is `docs/syntax-features.tsv`.

| axis | values in the table | of which here (relfsh, rill2, cm) | missing, and why |
|---|---:|---:|---|
| L1 comments | 3 | 1 | `//`, `;` - Lisp's: no shell uses them |
| L2 defining word | 6 | 3 | `sub` (Perl), `func` (YSH has it beside `proc`): spellings only |
| L3 continuation | 3 | 2 | |
| S1 variable read | 5 | 3 | Perl's `$ @ %` beside sigil-by-kind: one value |
| S2 binding | 7 | 3 | `:=` (Go): an infix spelling of keyword-eq |
| S3 block delimiters | 5 | 2 | `do`/`end` (Ruby, Lua's loops): a spelling of end |
| S4 control | 3 | 3 | |
| S5 list literal | 4 | 3 | |
| S6 map literal | 5 | 3 | |
| S7 capture | 4 | 3 | process substitution `<{cmd}` (rc, bash): a redirection, not a value |
| S8 interpolation | 4 | 2 | |
| S9 expressions | 6 | 3 | |
| S10 parameters | 5 | 3 | |
| S11 spread | 4 | 3 | |
| S12 first word | 5 | 3 | |
| V1 splitting | 2 | 2 | zsh's options: per variable, a mix of the two |
| V2 values | 3 | 3 | |
| V3 pipes | 4 | 3 | streaming function stages: a design gene (step 4, 860-862), not syntax |
| V4 returns | 4 | 3 | |
| V5 errors | 4 | 3 | |
| V6 scope | 2 | 2 | |
| V7 code as a value | 4 | 2 | |
| F1 front end | 3 | 1 | |

Left out of the table, and why: brace expansion, here-documents, job control, history and
completion - present or absent, never a choice among forms, and decided by what the product offers;
regular expressions and the line editor - libraries, not syntax.

**Deliberate strangers** - values chosen because nobody, or almost nobody, uses them:

- **F1 = ahead or overlay: no front end in the image at all.** execline's launcher parses once and
  leaves; Rill began so, its compiler a Python program outside the image. Measured here, the front
  end is 12,691 of the command model's 66,845 bytes - 19% that a script compiled ahead, or a prompt
  that loads the parser only to compile, would not carry. Out of practice because a shell is used at
  a prompt, and a prompt needs the parser; an overlay answers that. Kept: the largest single size
  gene in the table, and it is not syntax.
- **S1 = stack, S9 = postfix (Forth, cosh, Joy).** The parser is the Forth interpreter that is
  already in the image: the front end's bytes go to nearly nothing. Out of practice for shell users'
  reading habits, not for any technical reason. Kept: it is the size floor every other genome is
  measured against, and the reason size alone cannot be the fitness.
- **S8 = none-concatenate (rc's `^`, es, Elvish).** No interpolation inside strings at all: words
  side by side join. rc's users wanted carets inserted for them - a usability cost, measured by its
  own users. Kept: it removes the quoted-text parser (360 bytes here).
- **S4 = functions-on-fragments (es, execline).** Control constructs are replaceable functions or
  programs given code; the parser knows no `if`. Out of practice: es's own releases stopped in 1997, a fork goes on.
  Kept: the smallest parser that still reads as a shell.
- **S1 = sigil-by-kind (Ion, Perl).** The sigil tells the kind, so `@x` spreads without a rule of
  its own. Perl's reputation, not a measured defect, keeps it out of new designs. Kept.

## Measured

`tools/syntax-space.py` (200,000 samples, seed 864):

- the table: 23 axes, 95 values, 26 rules; the 33 systems named in it each fit the rules - the check
  the rules must pass, since a real system that breaks a rule proves the rule wrong. Shown to fail:
  a planted rule that braces exclude closures was broken by C.2, Elvish, Nushell and es, and a rule
  naming a value the table lacks was reported.
- the space: 50,164,531,200,000 genomes; 928,972,800,000 without the lexical group, whose values
  interact with nothing and are chosen apart. Exhaustive enumeration is out; so is time per
  candidate of more than milliseconds, for a search of any useful depth.
- a uniform sample: 7,149 of 200,000 break no rule - 3.57%; the rest break 1 to 11. A search must
  repair or reject 96 of every 100 children, as the product-line work found.
- what is built: relfsh has 22 values on 22 axes, rill2 20 on 20, cm 24 on 23 - each front end is
  one point of the space; only cm has two values on one axis (S7: `$( )` and `@( )`, which coexist).
  44 of the 95 values exist in no front end here.

What a gene can move in size, from `cm/cmc.4` measured word by word (12,691 bytes in all): the
arithmetic of `(( ))` 1,256; pipelines, programs and redirections 1,579; variables and `$` 940;
`if`, `for`, `while` and `break` 893; `var` and `set` 714; defs 694; lists and maps 452; blocks 393;
quoted texts 360; captures and spread 348; and the parts every syntax needs - reading characters and
words 1,300, the tree, strings and memory about 1,500, command dispatch and the script 2,308. A
structural gene moves a few hundred bytes to about 1.5 KB; the whole syntax-dependent part is under
13 KB of a 67 KB image; F1 moves all of it.

## How a search would work here

1. **One abstract syntax.** cm/cmc.4's tree (863) - the nodes every concrete syntax is parsed into.
   The test scripts are kept in it once, not once per syntax.
2. **A genome is one value per axis**, read from `docs/syntax-features.tsv`; the rules prune it,
   children repaired toward a valid genome rather than discarded (the product-line lesson).
3. **Each value is a module of one front end**, between `\ [gene NAME]` and `\ [/gene]` as
   rill/genes.tsv's genes already are (751) - so a genome's image holds only its own modules' bytes,
   and the measurement is honest. Beside each module, a renderer (Python) that prints the tree in
   that syntax.
4. **The gate: the same Forth.** Each script, rendered in the genome's syntax and compiled by the
   genome's front end, must make the Forth cmc.py makes of it, token for token - `tools/cm-diff.py`
   (863) is that check today. Then the scripts run, as tests/rill/run runs them. A planted wrong
   module must die.
5. **The objectives** - all deterministic, so no noise floor: the image's bytes; the scripts' length
   in the genome's syntax, in tokens (terseness - and a proxy only); a hazard count, each value
   carrying the documented mistakes it invites (word splitting - ShellCheck's SC2086; a loop variable
   shared by closures - Go before 1.22; a bare word read as a command - xonsh's `ls -l`, SYNTAX-STUDY
   L1); and compile time in dispatches. Run time is not an objective: the gate makes it the same.
6. **The search.** IBEA rather than NSGA-II for four or more objectives (Sayyad and others);
   exhaustive over any subspace small enough; held-out scripts - the six tasks of 851, the repo's
   own shell scripts rewritten - never selected on (prompts/26).
7. **What it hands the owner:** a front - for each size, the shortest and least hazardous syntaxes
   that reach it - and the owner reads the candidates. Readability is not in the fitness; a placebo
   (Randomo's idea: random spellings for the lexical genes) belongs in any trial with readers.

## Premortem (prompts/24)

Suppose it was built and failed. Most likely, in order:

1. **The modules did not compose.** Braces for blocks and for maps, `( )` for captures and for
   grouping, `[` for lists and for `test` - features meet in the characters they use, and a
   decomposition that hides it tangles them (Cazzola and Favalli). Sign: rules multiply faster than
   values. Guard: a value is a module only if its parser fragment is entered from one character.
2. **The front preferred the cryptic.** Size and token count both reward postfix and no syntax; the
   front's small end is Forth. Not a failure of the search - the information that readability is
   not in it. Guard: say so with the front; never report one winner.
3. **The cost was in the modules, not the search.** 44 values to write, each a parser fragment, a
   renderer and its tests, in Forth and Python, before the first useful run. Guard: start with the
   axes that cost least to modularize, and stop if the first measured genes move under a few hundred
   bytes.
4. **The corpus decided.** Six scripts selected on would fit their own constructs. Guard: held-out
   tasks, and a token count per construct, not per script.
5. **A switchable front end measured differently from a fixed one.** Guard: genes as source filters
   (step 3), so a genome's image is the fixed front end it describes.

## What is fixed

The runtime (Rill's rt.4 and cm's), so the V group's values that need another runtime - objects in
pipes, typed bytes, exceptions - are rows in the table and not buildable genes; the Forth engine and
kernel; compiling to Forth (no interpreter genes); the test scripts' meaning. Varying the runtime
would make run speed an objective again, and multiply the cost of a value by the runtime's.

## A first experiment, if the owner wants one

Four axes whose second value is a module of a few hundred bytes in cm/cmc.4, each with a renderer:
S8 (interpolation, or none), S9 (`(( ))`, or a `math` command), S2 (`var x v`, or `var x = v`), S7
(`$( )`, or `( )`). 16 genomes, enumerated, gated by cm-diff on the six scripts and checked on held-out
ones; measured in bytes, tokens and hazards. And, apart from syntax, F1: the image with and without
its front end resident, with a prompt that loads it. The question it answers first is the one this
document cannot: whether syntax genes move the bytes enough to be worth a search at all.

## Sources

Duff, "Rc - The Plan 9 Shell" (plan9.io/sys/doc/rc.html); Haahr and Rakitzis, "Es: A shell with
higher-order functions", USENIX Winter 1993; skarnet.org, "The execline language design and
grammar"; murex (github.com/lmorg/murex); the Ion manual (doc.redox-os.org/ion-manual); cosh
(github.com/tomhrr/cosh); O'Neill and Ryan, "Grammatical Evolution", IEEE TEC 5(4), 2001; Cazzola and
Favalli, "Towards a recipe for language decomposition", Empirical Software Engineering 27:82, 2022;
Kühn, Cazzola and Olivares, "Choosy and Picky: Configuration of Language Product Lines", SPLC 2015;
Sayyad, Menzies and Ammar, "On the Value of User Preferences in Search-Based Software Engineering",
ICSE 2013; Zhang and others, "Supporting Meta-model-based Language Evolution and Rapid Prototyping
with Automated Grammar Optimization", arXiv 2401.17351; Stefik and Siebert, "An Empirical
Investigation into Programming Language Syntax", ACM TOCE 13(4), 2013; University of Washington,
"Programming Languages and Learning"; and for fish, Elvish, Nushell, PowerShell, YSH, xonsh, Hush
and zx, docs/SYNTAX-STUDY.md's sources.
