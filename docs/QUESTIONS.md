# QUESTIONS.md — what is waiting on the user

Kept at the user's request (Iteration 514): every question raised with
the user is written here, with where it came from, the options and a
recommendation, so none lives only in a chat reply. **Nothing is
deleted.** An answered question moves to "Answered", with the answer
and where the decision was recorded; an open one stays open for as long
as it takes, and the work that depends on it says so and waits.

When a reply to the user asks something, the question goes here in the
same iteration.

## What blocks what - in the order the work needs them

1. *(Q2, Q3 and Q4, which blocked the assembly engine's Milestone 1,
   were answered at 516.)*
2. *(Q5 and Q6, before its Milestone 4, were answered at 523.)*
3. **Rill's features that wait on these** (Rill itself exists since 736;
   809 corrected this line): Q36 answered (A36) and built - JSON at 811,
   jobs at 813 - Q10 and Q11 with it; **Q7** (text blocks), **Q8** (the
   prompt's questions, the name).
4. **Blocking nothing**: Q1 (the space options), Q9 (divergences kept
   on purpose), Q12 (binary plugins), Q13 (the assembly engine: size or
   speed). *(Q14 was answered at 523.)*
5. *(Q15, before the self-hosted assembler, was answered at 528.)*
6. *(Q16, the speed gap, was answered at 535: accepted. Q18, local time,
   at 544: UTC everywhere.)*
8. *(Q19, the memory region, was answered at 545: 4 MB.)*
9. *(Q20, self-hosting's last step, was answered at 549: done.)*
7. *(Q17, self-hosting's four choices, was answered at 536.)*
10. *(Q33, the native back end's decisions, was answered at 609: beside
   CV8, x86-64 only, size weighed against speed, the targets, one shell
   source for both. N1 may begin.)*

## Open

**Q39. Rill's image: which of the size options? (826)** The image is 91,526
bytes, 70 % of relfsh's; docs/RILL-SIZE.md has where it goes (the compiler 43 %,
the runtime 22 %, the editor and its tables 13 %, the shared base 16 %) and six
options with their bytes. *Recommendation*: (1) two images now - 12.3 KB off
the script image, nothing slower or lost; (4) the dead words with it; (3) and
(2) as measured follow-ups; (5) only if size comes to matter more than a
change to the kernel every image shares. *Blocks*: nothing.

**Q40. Rill: the compiler - rewritten, replaced, or moved out? (826)** Asked
whether Rill could be done as BASIC is in Forth. docs/RILL-SIZE.md, "Alternatives
to the compiler", measures it: (1) a compiler in Forth's own manner, keywords as
words and code compiled directly, would save some 6-9 KB and compile faster, as a
rewrite of compile.4 that leaves the oracle nothing to compare; (2) an
interpreter would be no smaller and several times slower; (3) scripts compiled
once and cached, run in an image of the runtime alone, would run in about 40 KB
- 44 % of today's - with the compiler and editor kept for the prompt; (4) Q39's
options. 828, asked for bytecode directly (docs/RILL-SIZE.md, "Bytecode directly"):
a 177-line script starts in about half the time (15 ms of its 28 are EVALUATE),
the image saves only some 3-6 KB, the text's five out-of-order places need
restructuring, and the oracle becomes outputs only - the kernel has no
decompiler. *Recommendation*: (3) if a script's running size is what matters, with
Q39's (1) for the prompt's image; bytecode directly if start-up time is the goal,
staged behind a gene with an output-comparing oracle built first; not (2).
*Blocks*: nothing.

**Q41. A scripting vocabulary on Forth: how far? (829)** The user's idea -
grow the language up from the Forth implementation, words instead of a
compiler. docs/FORTH-SCRIPTING.md: a sketch (examples/forth-script/) brings a
pilot section from 685 characters of Forth to 396 - Rill's is 371 - with no
compiler; the stack and variables (a quarter of the pilots' Forth) and
expressions stay, and errors come late and far from their cause. Three
questions: (1) who writes these scripts - people who read Forth, or the
general shell and script users A35 names? (2) beside Rill, or in its place?
(3) a vocabulary only, or a little syntax too (locals, an infix word)?
*Recommendation*: beside Rill, for the project's own tools; first one whole
pilot in the vocabulary, measured by the pilots' protocol. *Blocks*: nothing.

**Q42. The minimal parser: Rill's next form? (830)** The user wants a
general-purpose scripting language and shell in regular notation (`a = b + c`)
with a small translation layer. The prototype, examples/forth-script/mini.4
(docs/FORTH-SCRIPTING.md, "The minimal parser"), does it in 12.7 KB where
Rill's compiler is 39: the image without its editor 52.8 KB against 79.2, with
values checked when used - and fib(25) in 78 ms against Rill's 10 and Python's
25. Questions: (1) make this Rill's design - the compiler replaced by the
minimal parser, the scripts and tests moved to bare names (`a = b + c`;
`$name` only in a command line)? (2) speed - answered by measuring at 831,
asked whether it can be as fast as Rill: numbers tagged (2n+1) and counted
`for i in range(n)` took fib(25) from 78 ms to 25 and a 300,000-add loop from
66 to 19 (Rill 7 and 10, Python 18 and 31); Rill's speed is its purestack and
rangeloop genes, which the parser can carry over - the first next. (3) of
Rill's other features, which to carry over first? *Recommendation*: (1) yes,
step by step - the minimal parser grown feature by feature until Rill's tests
and scripts run in it, then the compiler removed; (2) defs of numbers on the
stack next; (3) pipelines, `$(...)` and `{expr}` in strings, records, break
and continue. *Blocks*: nothing.

**Q43. The prototype's syntax, and the shell: what next? (832)**
docs/FORTH-SCRIPTING.md, "The syntax, how friendly": eight things tried, one
mended (else on its own line ran both branches); seven improvements priced at
some 2.3 KB of parser and nothing at run time. The shell: pipes,
redirections, quotes, $( ) and & cost 1,960 bytes of parser; each command
costs what Rill's does, twice dash's, the runtime execing through env. And a
Rill bug: a def's parameter is the global of its name, so a def called
meanwhile reads the parameter - garbage where the kinds differ. Questions:
(1) the seven improvements, all? (2) commands through env: search PATH in the
runtime instead? *Recommendation*: fix Rill's scope first (a def's names its
own, both compilers, the oracle with them); (2) yes, it halves every
command's cost; (1) all, in the order listed. *Blocks*: nothing.

**Q44. Rill 2: what next? (834)** The prototype is Rill 2 now (docs/RILL2.md):
the issues of 832 mended, its tour checked, an image of 61,155 bytes against
Rill's 91,795 - its own part 20.8 KB against Rill's compiler and editor's 51.4.
Questions: (1) Rill 2 the language from here - Rill's compiler, its 61 oracle
programs and its examples carried over or retired? (2) its prompt: relfsh's
editor, as Rill's, 12.3 KB? (3) defs of numbers on the stack (fib 18 ms to
Rill's 8)? (4) Rill's scope bug (832): mend it in Rill, or let Rill 2 take
its place? *Recommendation*: (1) yes - the examples carried over one by one,
the length rule kept; (2) next; (3) after; (4) only if Rill stays.
*Blocks*: nothing.

**A45. Rill 2: smaller first (835 -> 836).** The user: "proceed" - the
recommendation's first: the characters' widths at 3 bytes a bound (836),
the wide table's 8-byte cells too, one halving search for both tables
(CP-RANGE?, CP-IN? and CP-ZW? gone): 1,321 bytes off shell.4's section -
relfsh's images 130,348 to 129,028 and 121,408 to 120,596, Rill's 91,795 to
90,475, Rill 2's 71,458 to 70,130. Every code point's width the same before
and after (all 1,114,112: 7,393 none, 923,734 one, 182,985 two, one hash);
the tables checked ascending. Stack mode and TAB stay open in Q45.

**Q45. Rill 2: smaller and faster - which next? (835)** (1) Stack mode for
defs of numbers (docs/RILL2.md, "Stack mode"): fib 18 ms to about Rill's 8, some
1-1.5 KB. (2) The characters' widths at 3 bytes a bound, not 4: 0.9 KB off both
Rill 2's image and relfsh's (shell.4's section is theirs, and the editor's);
checked by every code point's width before and after. (3) TAB completion at
Rill 2's prompt: back in, 3.3 KB, or a smaller one of its own. *Recommendation*:
(2) first, cheap and exact; (1) when speed asks; (3) left out. *Blocks*: nothing.
*Since*: (2) done at 836 (A45); (1) at 837, the user's second "proceed" - fib(25)
18 ms to 11, Rill's 9 (docs/RILL2.md, "Stack mode"), and found on the way: numbers
past 62 bits wrapped silently since 831, mended. (3) open.

**Q46. One syntax for shell and language - which? (842)** The user: mixing
`var` and `$var` is inconsistent and confusing; how do other shells join a shell
and a real language? docs/SYNTAX-STUDY.md: four ways others take (one sigil
everywhere; two modes by syntax; two modes by name lookup; commands quoted in a
language), seven lessons, Rill and rill2 probed against them. (A) One sigil,
syntax decides: every variable `$name`, bound or read; a statement's first token
says command or code; `$(...)` for commands and expressions both, `@` spreads,
`?(...)` for success; text quoted in code; `{}` no longer interpolates. (A') The
same, binding bare as the shell and Rill do (`total = 0`, read `$total`). (B)
YSH's two modes: bare names in code, `$` in commands, the boundary in the syntax.
(C) rill2 as it is. *Recommendation*: (A) - one rule for a variable, nothing
guessed; in rill2, whose runtime stays; two or three turns, size about even.
*Blocks*: the syntax work, till chosen. Out with other models since 845:
four prompts in docs/asks/ (a review, users, a grammar, prior art). The review
back (846): five models, three for A; ten holes held, filled as A.1
(docs/asks/ask-rill-syntax-answers-845.md). The users round (847): no mistake
left that runs wrongly under A once five more are refused - A.2. The grammar round
(848): one parser shape agreed; six gaps measured and filled - A.3. At the owner's
asking for minimalism (849): A.4, the minimal cut - eleven rules in place of twenty-two;
*recommended* now, over A.3. And (850) option C, the command model -
docs/COMMAND-MODEL.md, a draft: a function is a command, arguments and streams carry
values; a base for further development, not yet weighed against A.4.

**A44. Rill 2: what next (834 -> 835).** The user: "let's not retire rill
yet"; "add prompt with line editing and history, see if it can be refactored
and optimized for smaller code size" - done at 835: rill2/prompt.4, 920 bytes,
no session table (a rill2 input is a script of its own; its names are the
dictionary's); relfsh's editor without its TAB completion, cut out by the
build, and a shim of 239 bytes for Rill's 526 - the editor 8.6 KB against
Rill's 12.3; "what exactly is stack mode" - docs/RILL2.md, "Stack mode", Q45;
"let's put rill fixes on the backburner" - GOALS.md 15 says so. And asked: no
list functions but append? - pop, insert, extend, index, values, `in`, lists
joined by + (835); delete from a list or a record - pop; lists and records
hold lists and records - yes, as deep as wanted.

**Q1. The space audit: which, if any? (509)**
`tools/image-budget.py` found: headers are 21.6% of the 64-bit shell
image and 23.1% of the 32-bit; full cells holding offsets or sizes come
to about 2 KB, at 64-bit only; every DOVAR word carries three unused
bytes, about 2 KB. Options:
(a) an image that keeps names only for a documented extension API -
about a sixth smaller at both widths, and `forth` sees only that API;
(b) 4-byte fields for the offset cells - ~2 KB, 64-bit only;
(c) DOVAR without the three bytes - ~2 KB, against the one rule for a
parameter field that four past defects came from (FORTH-STYLE.md 12);
(d) none.
*Recommendation*: (a) if size matters to you - it is the only lever
at both widths; I would leave (b) and (c). *Blocks*: nothing.

**Q8. Rill's other open questions (503).** Records at the prompt
(JSON on a marked port?); a softer failure rule at the prompt than in
scripts; the kernel in Forth. And the name - SHELL-LANGUAGE.md, "Why
Rill", says why; it is easy to change. *At 822*: the kernel in Forth is
how Rill was built (it compiles to Forth in the image, 736 on); JSON is
read where the script says, from-json (A36); the prompt's points are
Q38's. Left here: the name.

**Q12. Forth plugins in image form? (516)** The user's thought: load
compiled extensions, not source. What it takes: a plugin compiled
against one shell image calls that image's words by their offsets, so
loading it means relocating its own calls by where it lands, resolving
its calls into the host by name (`FIND`), and linking its headers into
the host's 32 hashed threads - a small linker, perhaps 150 lines of
Forth; variable slots and branches are relative already and move
untouched. What it buys, measured: loading from source costs about
0.4 ms per KB, so for extensions of a few KB nothing; it matters for
extensions of tens of KB, for distributing one without its source, and
as a first step towards GOALS.md item 6, where Forth writes machine
code into images. *Recommendation*: design recorded, build when an
extension is big enough to need it. CV8.md 13.

**Q13. The assembly engine: the last kilobytes, or speed? (520)**
You asked for the smallest binary with no external dependencies. The
free part is done: a hand-written ELF header and one segment, as in
itsy-linux, took the engine from 27,936 bytes to 11,053 with nothing
running differently. Two levers remain, and both cost speed - measured
on a 100-million-iteration loop, best of five (C engine: 306 ms):

| build | bytes | time |
|---|---|---|
| as now: `NEXT` copied into every handler, 8-byte table entries | 11,053 | 331 ms |
| 4-byte table entries (`mov ecx, [t]; jmp rcx`) | 9,229 | 438 ms (+32%) |
| one shared `NEXT` (`jmp next`) | 10,069 | 652 ms (+90%) |
| both | 8,029 | - |

A shared `NEXT` is one indirect jump for every handler, which the
branch predictor cannot tell apart - itsy's choice, and right for 1.8
KB, but it halves the speed here. The numbers will shift as the
engine grows (54 escaped primitives are still stubs, and their names
go when they are written). *Recommendation*: keep speed as the
default; a `make relfasm64-small` with both levers, if a size-critical
build is ever wanted, is a two-line switch.

**Q9. Divergences kept on purpose - revisit any? (GOALS.md)**
Recorded as deliberate, listed so they are not forgotten:
`return` outside a function inside a loop reports and carries on, as
bash does, where dash leaves the script (426); `a=b exec 1>&1` exports
`a`, as bash does (424); the expansion order for special builtins,
functions and external commands is bash's (484); `echo` processes no
escapes, as bash's does. *Recommendation*: keep them all.


## Answered

**Q7. Rill's text blocks: indentation, or a delimiter? (503, 514; answered A7)**
You asked for pros and cons, especially with several levels of
indentation: SHELL-LANGUAGE.md, "Text blocks", sets out four designs
with a nested example of each.
*Recommendation*: the closing delimiter whose indentation is the
margin (design C there). *At 822*: a string already spans lines, but
its source indentation is its text - a usage message written inside a
def prints its later lines indented; C would end that in the tokenizer,
one rule in each compiler.

**Q37. Rill: speed - a phase 4, or not now? (822; answered A37)** Where it stands,
measured at 822 (best of five or three, this one-CPU machine): startup
with the script compiled about 1-2 ms (dash 1, Python 12); a million
additions 27 ms (Python 96, dash about 1,600); dead-words over the
shell's eight source files, lists, records and texts, 136 ms (Python
58); compiling the 176-line pack-results 21 ms, paid on every run.
Phase 4's list (RILL-ROADMAP.md), untouched since 775: typed lists (no
box an item), regular expressions compiled to Forth, temporaries
released (the arena frees nothing between collections), Rill on the
native kernel (waiting on GOALS.md 12). *Options*: (1) not now - Rill is
at sh's speed or better everywhere and at Python's on numbers; (2) one
measured round - profile dead-words (tools/rill-profile.py) and fix
its top costs, each a dispatch count before and after, as 768 and 775
did; (3) a phase - typed lists, compiled patterns. *Recommendation*: (2)
when a script is slow in practice; (3) weighed as A33 weighed code size
against speed (+50 % code for +5 % not worth it): minimal first.
*Blocks*: nothing.

**Q38. Rill: a prompt of its own? (822; Q8's prompt points; answered A38)** Rill runs
scripts (`rill script`, `rill -c 'code'`); typing commands is relfsh's,
the POSIX shell. A Rill prompt was 503's picture - `ls -la` typed works,
`&` at the prompt, a softer failure rule there than in scripts. What it
takes: the compiler works on whole programs (two passes; a variable's
kind joined over the whole script), so a line at a time - each line's
variables kept for the next - is a real change to both compilers; then
line editing (relfsh's editor), and job control if `&` comes back.
*Options*: (1) none - Rill for scripts, relfsh for typing; (2) a plain
read-eval loop - a statement at a time, variables kept, an error said
and the loop going on; (3) Rill as the interactive shell. *Recommendation*:
(1), minimal and simple (A35): one language for each job. *Blocks*:
Q8's prompt points.

**Q11. Rill: the default lifetime of a job (515; answered by A36: stopped when the script ends, 813).**
`par` covers fork-join work; a server started for a test run, a
coprocess, and a daemon need jobs as values (`spawn`, `kill`, `wait`,
ports to talk through). What happens to a job its script never waited
for: it runs on, orphaned (as in sh); it is stopped when the script
ends; or it is stopped when the block that started it ends.
*Recommendation*: stopped when the script ends, by default - no orphan
is an accident; `with` binds a job to a block; `detach` lets one
outlive the script; at the interactive prompt, jobs live as long as the
shell, as in sh.

**Q10. Rill: how structured values cross a process boundary (515, 516; answered by A36: from-json and json, explicit, 811).**
*Refined at 516, from the user's proposal*: JSON in the environment,
recognised - but by the script's use, not the value's content: every
value arrives as text; a list or record exports as JSON automatically;
a structural operation on text (`$CFG.host`, iterating, spreading)
decodes it there, an error if it is not JSON; scalars are never
converted, so `VERSION=1.0` stays `1.0`. SHELL-LANGUAGE.md Part 4 shows
why detection by content misfires (the "Norway problem").
*Recommendation now*: that. The earlier options follow.
The environment is `NAME=VALUE` strings for every program, most not
Rill. Options, argued in SHELL-LANGUAGE.md Part 4: (1) only text is
exported, and a structure crosses by explicit encoding
(`export CFG = json($cfg)`, `from-json($CFG)` on the other side);
(2) automatic, with a marker variable recording each export's kind -
seamless, but stale when anything in between changes the value, and
it re-reads text unasked; (3) lists tied to a separator, as zsh's
`PATH`. For Rill-to-Rill calls, a value port (descriptor 3, JSON) that
carries a script's `return` value back to its caller.
*Recommendation*: (1), JSON as the standard codec, plus value ports
for Rill-to-Rill calls; never functions in the environment (bash's
exported functions were Shellshock).

**Q36. Rill, general and minimal: the balance (810; answered A36)**
The user, A35: a general shell and script language, minimal and simple -
"let's see if we can find reasonable balance". Proposed, as a filter and
what it lets in:
(1) *The filter.* The language does what commands cannot: hold values
(lists, records), decide and repeat, name and reuse (def), and turn text
into values and back. Commands do the rest, one way each (799). A feature
joins when a real script needs it - this repository's or a general one -
and no existing way does it (732); each is measured (the image's bytes,
both compilers, the reference) and kept in FEATURES.tsv; the rewrites
together stay shorter (A35).
(2) *In: JSON.* The bridge from tools' structured output to Rill's values,
which no command can give a script: `from-json(t)` reads, `json(x)`
writes - Q10's option (1), explicit, not the automatic export of 516
(by the script's use, a value crosses only where the script says). A
writer is mostly R-SHOW with every key quoted; a reader is a recursive
descent in the runtime; one library name each in both compilers; tested
against Python's json module. Estimated, not measured: 2-3 KB of the
image. Two details: JSON's `null` (Rill has none) reads as an empty text -
one rule, false as the shell's unset is, and `json()` never writes null;
a number reads as decimal() reads it - an integer a number, a fraction or
an exponent a decimal of six places, past the range the overflow error.
(3) *In, after JSON: jobs, minimal.* `spawn((cmd args))` starts one and
returns it, `wait($job)` gives its status, `kill` stays the command; a
job not waited for is stopped when the script ends (Q11's recommendation:
no orphan by accident). A script that starts a server, tests it and stops
it cannot be written with commands alone - `sh -c` gives no handle.
(4) *Out - one way exists:* try (?? , a condition, on EXIT); default
arguments (pass them; at() for $args); options() (a loop with case);
`x = if ...` (an if); `{k: v for ...}` (a loop); `x[a:b]` (slice());
`def f() -> k = expr` (return); `m[k] ?= v` (if not in); load (a script
is one file).
(5) *Later, on evidence:* text blocks (Q7) - strings span lines already;
the indentation question waits for a script that needs it.
(6) *Kept as decided:* texts as bytes; no collection inside a function.
Found while weighing (2): `decimal("1e3")` gives 1.0 - it stops at the e
and drops the rest, silently; decimal() truncates past six places. The
reader and decimal() get one rule, (2)'s.
*Recommendation*: confirm (1)-(6); then JSON, then jobs. *Blocks*: both.

**Q35. Rill after 805-808: the length rule, and who Rill is for (809; answered A35)**
GOALS.md 15's open items, assessed at 809 (the reply had the detail):
(a) *The length rule.* 726: a rewrite is never longer than its original.
By tools/rill-audit.py's own count, at 798 three rewrites were longer
(run-utf8 +26.9%, dead-words +9.0%, native-by-source +5.0%) and the eight
together 8.4% shorter; now six are (make-bundle +0.8%, intrfuzz-stress
+3.8%, pack-results +4.0% tipped over by the one-way review) and the eight
2.8% shorter. The review cost 1,374 characters across them (+6.1%);
native-by-source most (+17 points: upper() gone, its names gathered and
upper-cased by one tr rather than a process a word). Options: (1) 726 per
script - conveniences come back, against 799; (2) the eight judged
together - shorter in total, as now; (3) per script within a tolerance
(say 5%), each excess named with its reason.
*Recommendation*: (2), with (3)'s record for any script past 5% (run-utf8
is a shell test harness - the shell's own ground).
(b) *Who Rill is for.* For this repository's tools, none of the remaining
gaps is needed: the eight rewrites use no JSON, run things side by side
once (sh -c with & and wait), recover from failure with ?? (8 uses),
code() (3) and (test ...) (5), and take defaults only for script
arguments (at($args, i, d), 7); their Python originals used try once and
one default argument. For scripts in general, JSON matters most (Q10: a
reader and a writer in the runtime, one library name each in the
compilers), then jobs (Q11); try and default arguments would be second
ways (?? and conditions; at()) and stay out.
*Recommendation*: decide (b). Meanwhile, needing no decision: a Rill
fuzzer - mutated tests and rewrites, reporting engine crashes, hangs and
the two compilers disagreeing; 805-808 found two crashes, three refusals
and several silent wrong results, every one by accident. Texts as bytes
and no collection inside a function were decided already (RILL-REFERENCE.md
"on purpose"; 791-792, the user's choice) and stay unless a script hits them.
*Blocks*: the length rule's verdicts (a); which gaps get built (b).

**Q34. Rill: which conveniences go, of those one line of other features
replaces? (799; written here at 805; answered A34)** The duplication review's third
section, left to you at 799 and recorded until 805 only as a line in
GOALS.md. 799-802 removed the second ways and what commands do well. These
are not second ways - each is the one way for its operation - but one line
of other features could stand in. Uses are in the eight rewrites
(examples/rill, tools/rill-audit.py's sources), counted at 805:

| feature | uses | one line instead | what that costs |
|---|---|---|---|
| `keys($r)` | 1 | `[$k for k, v in $r]` | nothing - as `values` went at 799 |
| `starts($t, $p)` | 7 | `slice($t, 0, len($p)) == $p` | longer; a regex `^...` needs its text escaped |
| `ends($t, $s)` | 3 | a `slice` from `len($t) - len($s)` | longer, and easy to get wrong by one |
| `trim($t)` | 3 | `sub($t, '^[ \t\n]+\|[ \t\n]+$', '')` | a regex for a common need |
| `default($t, $o)` | 8 | an `if` on its own lines | two lines a use, in pack-results five times |
| `sum($l)` | 1 | a loop: three lines | longer |
| `for i, x in $l` | 19 | `for i in range(len($l))` and `x = $l[$i]` | a line and an index read a loop |
| comprehensions | 8 (+ filters) | a loop and `push` | three lines for one |

Six rewrites are already longer than the scripts they replace (799-802,
GOALS.md 15), against the 726 rule "never longer"; every removal above
except `keys` lengthens them further.
*Recommendation*: remove `keys` (the comprehension is its one way, as for
`values`); keep the rest - each is the only way to its operation in Rill,
and what replaces it is longer or easier to get wrong. *Blocks*: nothing;
the rewrites' lengths wait on it.

**Q33. A native-code back end: the decisions before N1 (608; answered A33)**
The user, after the ForthHub announcement: a Forth that compiles into
machine code close to gcc's for dash - small words inlined, bigger ones
native functions; "most likely different from CV8". The design is
docs/NATIVE.md; OPTIMIZATIONS.md S7 points to it. To decide:
(a) *Beside CV8 or instead of it?* Beside: CV8 and the C engine stay,
as A13 keeps them, for every machine; the native back end compiles the
same Forth for x86-64. Instead: one engine fewer, and every non-x86-64
machine lost.
(b) *x86-64 only?* An ARM back end needs an ARMv7 assembler in Forth
first; decide after N3.
(c) *Size*: the code may grow from 75 KB toward 150 KB (5-byte calls,
inlined code); headers and data unchanged. Accept, inlining only tiny
words?
(d) *What counts as success*: as exit targets, Forth benchmarks within 3
times of C (now 16-17) at N2, and scripts within 5 times of dash (now
29-42) at N3 - measured and recorded either way.
(e) *The shell's source*: on master it stays the same for both back
ends, and what in it depends on CV8 - `!XT` offsets, for one - goes
behind a word each back end defines. Small changes to shell.4 for that.
*Recommendation*: (a) beside; (b) x86-64 only, ARM decided after N3;
(c) accept; (d) these targets; (e) yes. All on master; article-2026 is
not touched.

**A1. The five questions of Iteration 499** - answered at 500 and
recorded in GOALS.md "What comes next": measure the two-bit call tag
(done, 501); design a shell language from its own principles (Rill,
503); no two-pass compiler, audit the full cells instead (509);
an assembly engine; examples of `forth` with sockets (505).

**A2. The assembly engine's architecture (513 -> 514).** x86-64 now;
the 32-bit engine is revisited when the 64-bit one is complete.
ASM-ENGINE.md.

**A3. The environment in the assembly engine (513 -> 514).** Keep the
C engine's behaviour, for consistency between engines: the engine keeps
the environment, as libc does, and `EXECVE` passes it. No shell change.
ASM-ENGINE.md.

**A4. The bare engines (507).** Kept, beside the single-file shells:
they run the kernels, which bootstrap everything. And everything is
named by cell width - `relf64`/`relf32`, `kernel64`/`kernel32`,
`relfsh64`/`relfsh32`.

**A5. `prompts/` and the article (497).** The prompt library is kept
whole - you extend it across projects - and the article about the
Forth shell is written when the project is complete.

**A6. The two-bit call tag (Q2; 501 -> 516).** Not now: the format
stays, and switching later is not a big deal, in the user's words.

**A7. One source for the opcode numbering (Q3; CV8.md 13 -> 516).**
Yes, as the assembly engine's Milestone 1's first step. **Done at
518**: `opcodes.tab`; the engine's tables generated, the Forth checked.

**A8. `LSAVE`/`LRESTORE` as real primitives (Q4; CV8.md 13 -> 516).**
Yes. Looked at closely it is less small than first said: the Forth
versions report overflow with `ABORT"`, a catchable error, and an engine
that owns the save stack must still raise exactly that. So: the engine
owns the stack, and the five cells at image offset 8 become one - a
word the engine calls to report the error in Forth. **Done at 517**,
with the image format's version raised to 6.

**A9. `~user` without libc (Q5; 513 -> 523).** Agreed: the assembly
engine reads `/etc/passwd`, and only that - no NSS, which a libc-free
engine cannot have.

**A10. The time zone without libc (Q6; 513 -> 523).** Agreed:
`LOCAL-TIME` gives UTC first; reading `TZ` and `/etc/localtime` is its
own later step.

**A11. The assembly engine's memory, W^X (Q14; 521 -> 523).** Asked back:
"keep engine code in the code segment and the Forth image in the data
segment?" - yes, exactly: the file part (headers, machine code, tables,
messages) read-execute, never written; the zero-filled tail (the
engine's variables and the machine's 16 MB, where the Forth image
lives) read-write, never executed. The Forth image is data to the CPU:
the engine interprets it and never jumps into it. Done at 523, for 56
bytes. A later self-hosted assembler (GOALS.md item 6) would want an
executable region for the code it generates - a mapping of its own,
made when it exists.

**A12. Fewer dispatches (Q15; 527 -> 528).** Agreed: the small runtime
words as opcodes first, one at a time, each measured with a paired
benchmark; then `tools/superinst.py` again, and the pairs that still pay
fused. **With the user's correction**: track not only the frequently
executed opcodes and pairs but also the RARELY executed ones, which
could move out of the one-byte primitives - into the escape band, or
into Forth - so the slots go where the dispatches are. The one-byte
space is finite: 32 free slots.

**A13. The speed gap (Q16; 534 -> 535): accepted.** "I really want relf
and forth shell to be as simple as possible, so let's stop optimizations
- we already used all the low-hanging fruit, and further changes would
hurt minimalism and simplicity." Scripts run ~30x slower than dash and
start fastest; that stands. No more opcodes or fusions for speed. Next:
self-hosting - relf compiling its own engine (SELF-HOSTING.md, Q17).

**A14. Self-hosting's four choices (Q17; 535 -> 536).** (a) Yes: the
x86-64 assembly engine, byte-identical to the GNU `as` build, then
rebuilding itself; `cv8.c` stays the portable engine. (b) Yes: a
Forth-syntax assembler, the engine translated once, relfasm64.S retired
when they agree. (c) Yes: the four unused folded returns and the nine
superinstructions removed, the runtime words kept - **done at 536**.
(d) JIT/AOT: revisited once relf self-hosts its engine. And, in the
user's words: "simplicity and minimalism should outweigh minor
performance improvements" - agreed; the one nuance kept is that a change
making things both simpler and faster (the runtime words) is worth
keeping.

**A15. The opcode set: 64, the call encoding as it is (537 -> 538).**
Asked whether simplification would bring the one-byte opcodes to 64 or
fewer, where the two-bit tag of Q2/A6 becomes possible: not by itself -
98 after 536 - but by choice: drop the folded returns and move the
coldest primitives to the escape band. The user: "use the smaller opcode
set, but don't implement the 1 GB call range yet". So: no folded return
anywhere (538), the coldest primitives escaped until 64 remain (539),
and today's calls - two bytes to 16 KB, three to 4 MB - unchanged. The
opcodes keep their numbers where they are; packing them into 0x00-0x3F
is the tag's prerequisite, done if the tag ever is.

**A16. UTC everywhere (Q18; 543 -> 544).** The user: /etc/localtime is
not on every platform, so a shell that reads it behaves differently from
machine to machine. The shell keeps its time in UTC wherever it runs:
the C engine's LOCAL-TIME uses gmtime_r, as the assembly engine's always
did, and the prompt's `\d` and `\A` are UTC. `make verify` sets
TZ=UTC-9, so no test can pass only because the machine's zone is UTC.
(Written up at 586: the entry was missing though the README cites it,
and the articles' "thirty-two decisions" counted it - the eighth review.)

**A17. The memory region: 4 MB, the call reach (Q19; 544 -> 545).** The
16 MB region cost no RAM, but a call reaches 4 MB and CALL, did not
check, and ALLOT ran into the stacks. **Done at 545**: 4 MB in both
engines, so every byte of the dictionary can be called; a new escaped
primitive DICT-LIMIT - the data stack's floor, the same in both engines
(base + 4 MB - 64 KB - 256 KB) - and on it the standard UNUSED; ALLOT
refuses to pass it and HEADER refuses a new definition within 4 KB of it
("dictionary full"), the margin covering the unchecked , and C, of a
definition. 3.6 MB of dictionary; the shell uses ~130 KB of it. The
user's intent, checked (FINDINGS.md 8): the shell's data is already in
the allocator's heap, outside the dictionary.

**A18. relfsh's memory: minimize it, after self-hosting (546).** The
user: "ideally I would like to minimize relfsh RAM usage as well, please
capture that and let's revisit after asm self hosting will be done."
Captured in GOALS.md ("After self-hosting: to revisit"), with where it
stands and the candidates, OPTIMIZATIONS.md M1-M3.

**A19. M5: relfasm64.4 the engine's one source (Q20; 548 -> 549).** The
user agreed to all three: (a) the translator carried the comments over,
as `\` comments, before the switch; (b) the build bootstraps from the C
engine - gcc builds relf64, relf64 assembles relfasm64 - no committed
binary; (c) gen-opcodes.sh writes the tables as a Forth include
(relfasm-ops.4, relfasm-consts.4). **Done at 549**: relfasm64.S retired;
`make relfasm64` is relf's; identical to the last GNU as build.


**A20. Names stay in the image (Q1; 509 -> 552).** The user: keep the
names, so that the shell's Forth builtin has every word. Headers stay
~21% of the image; OPTIMIZATIONS.md Z1 declined.

**A21. Data and code stay interleaved (552).** The user: do not separate
them. Mapping the image therefore gains nothing (FINDINGS.md 8b);
OPTIMIZATIONS.md M2 declined for good.

**A22. Polish before the announcement (552).** Agreed: compile-only
words refuse to run outside a definition, `.(`, README refreshed, `make
clean` complete; and a directory structure separating the engines, the
Forth system and the shell; and new kinds of tests (TESTING-IDEAS.md).

**A23. No more standard words (553).** The user: the Forth 2012 words
relf lacks (TESTING-IDEAS.md 12) are not added - whoever needs them can
define them with the `forth` builtin. Two things that answer does not
cover, raised and accepted as they are: number syntax (`$FF #12 %101
'c'`, double literals `12.`) is the text interpreter's, not a word, so
a user cannot add it without a hook into number conversion; and the
standard suite cannot be a regression test beyond CORE, since it stops
at the first word missing. CORE stays the conformance claim, and the
announcement says exactly that.

**A24. A Forth error fails its command only (554).** The user: `forth`
with an error sets $? non-zero and the next command runs, like any
builtin - consistent with POSIX, where only special builtins may end a
shell. Done for every builtin: RUN-A-BUILTIN runs each under CATCH;
CATCH and THROW moved into the kernel so its errors reach them; error
messages go to standard error. Status 1. Since 582 an unbalanced
stack too: RUN-CAUGHT puts it back and fails the command (the Habr
review; the user: fix it rather than state it).

**A25. ASCII art rather than images in the articles (554).** The user:
no images an article does not need; ASCII art often does better, and
some punishment for it is acceptable. Agreed: ForthHub is read in email
digests, where text survives; the Habr complaint was an article that
promised graphics. Kept to 60-64 columns for readers on phones.

**Q20. Refuse >R R> R@ outside a definition? (554, open)** Forth 2012
leaves their interpretation undefined, and in relf interpreting them
crashes - the interpreter's own return address is what they reach; my
own tests did it twice in 554. IF and its kind refuse now (552: ?COMP),
but >R R> R@ are primitives, not colon words, so a check inside them
would cost every use. The cheap way: a compile-only bit in the header,
which the text interpreter checks before it executes a word - gforth
warns this way. Options: (a) refuse them so; (b) leave it, as most
Forths do. Recommended: (a) - one flag bit and one test in INTERPRET,
and a crash becomes a message.

**Q21. A zero divisor kills the shell (555, open).** tools/twin-fuzz.py's
probes: `7 0 /` and `5 0 0 UM/MOD` end the process with SIGFPE on both
engines, and inside the shell `forth '1 0 /'; echo after` never echoes
- the shell is gone. A24 says a Forth error fails its command only, but
this one is the CPU's trap, which no CATCH sees; so is a bad address
(`0 @`). Forth 2012 has codes for them: -10 division by zero, -9
invalid memory address. Options: (a) each engine's signal handler turns
SIGFPE (and SIGSEGV off the stack guards) into a THROW with that code,
which the builtin's CATCH then handles like any other error - both
engines change, the C one and relfasm64.4; (b) the division words test
their divisor and THROW -10 - cheaper to write, a compare in every
division, and it covers division only; (c) leave it. Recommended: (a),
for it covers every trap and costs nothing until one happens.

**A26. Traps become THROWs (Q21; 556).** The user: yes, option (a).
Each engine turns SIGFPE, and a SIGSEGV off the stack guards, into -10
or -9 at the word the kernel registered (TRAP-XT!, from TRAP-ENTRY in
COLD): forth/safety.4's TRAPPED prints the message and THROWs to the
innermost CATCH; with none, exit 70, as before but with a message.
Since 586 the stack guards too (the eighth review): a runaway recursion
or push loop ended the shell - 70 on cv8.c, and relfasm64 had no guard
pages at all, so its data stack ran into the dictionary. Both engines
now protect the two pages and THROW -3 at the data stack's, -5 at the
return stack's. That page also stops a data stack underflow past its
top, but only once the executor's cells are gone: at forth's prompt a
second push then overwrote them, and 19 DROPs still ended the shell (the
ninth review). Since 589 S0 is the command's own stack while it runs,
so INTERPRET's ?STACK stops the first cell too many - "Stack error",
status 1 - and the guard is left for a single word that underflows.

**A27. Compile-only words by a list, not a header bit (Q20; 556).** The
user asked whether a header bit meant shorter names: it would - the
count byte's low five bits are the length (31, the longest name in the
shell) and its top three are taken, so a fourth flag halves the limit
to 15. So a list of execution tokens - no names stored, one node per
word, in the dictionary, extended at run time by COMPILE-ONLY (the last
definition) and COMPILE-ONLY-XT; checked by INTERPRET only when
interpreting. forth/safety.4 marks >R R> R@ I EXIT. And names over 31
characters are refused now: they were stored mod 32.

**A28. PATH unset: dash's default (561).** The user: with PATH absent,
use dash's default, /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:
/sbin:/bin. Done as dash does it: set at startup when the environment
has none, not exported; an `unset PATH` later leaves it unset. Doing it
found that the command search read the environment only - so an
unexported PATH, and `command -p`, found nothing - fixed. Open, not
covered by A28: PATH set to the empty string - dash searches the current
directory there, relf nothing (POSIX: implementation-defined).

**A29. An empty PATH searches nothing (562).** The user: keep relf's
behaviour - the current directory in PATH is dangerous. dash searches it
for an empty PATH (implementation-defined in POSIX) and for an empty
entry in one - `/bin:`, `:/bin`, `/a::/b` - which POSIX specifies as a
legacy feature for the current directory. relf searches it for neither,
only for an explicit `.`: a deliberate difference from POSIX for empty
entries, read as covered by the user's reason (DASH.md).

**Q30. Word keys in the line editor? (567; answered A30)** tools/editor-vs-bash.py
found relf's editor without readline's C-w (kill the word behind), M-b
and M-f (a word back and forward), M-d and M-BS (kill a word ahead,
behind), C-t (transpose) and C-y (yank what a kill took). Options: (a)
add them - C-w above all, which an emacs-mode user types without
thinking; (b) some; (c) none, the editor kept minimal. Recommended: (a)
C-w, M-b, M-f, M-d, M-BS and C-y with a one-entry kill buffer that C-k,
C-u and C-w fill - a few dozen lines of edit.4, each key testable
against bash with the tool as it is; C-t is rarely missed.

**A30. The word keys (568).** The user: as recommended - C-w, M-b,
M-f, M-d, M-Backspace, and C-y with a kill buffer that C-k, C-u, C-w,
M-d and M-Backspace fill; not C-t. One entry, but kills in a row join
into it, as readline's do - C-w C-w C-y puts both words back.

## Your notes, captured (514)

- **The input line limit, 80 to 256 columns** - done at 514.
- **SHELL-LANGUAGE.md**: a formal specification, POSIX constructs
  translated into Rill, why "Rill", what each language can do that the
  other cannot, and text-block indentation argued pro and con - Part 3,
  written at 514; Q7 and Q8 wait for you.
- **The assembly engine**: x86-64 first, 32-bit later; the environment
  as the C engine has it - A2 and A3.

## Your notes, captured (516)

- **JSON in environment variables, detected** - Q10, refined: detection
  by the script's use rather than the value's content.
- **"Can't change the libc contract; data comes back only through
  stdout, stderr and the exit code"** - right, with two refinements
  (the arguments, and every inherited descriptor):
  SHELL-LANGUAGE.md Part 4, "What a process can exchange".
- **Forth plugins in image form** - Q12, with what it would take.

**A31. Ctrl-C at an interactive shell (Iteration 571).** The user: proceed
with the bugs the last reviews found, Ctrl-C first - `while :; do :; done`
could not be stopped; the signal was consumed between commands and
nothing more. ^C now stops the command line: a pending flag,
INTERRUPT-PENDING?, which every list and loop checks through STOP? and
LOOP-AFTER-BODY - the way break and return already unwind, so
redirections are undone on the way out, not jumped over - and which the
prompt clears, making $? 130, as dash and bash. It is raised where the
shell takes SIGINT itself (CHECK-TRAPS; WAIT-SIGNAL-CASE, for `wait`) and
where a foreground child dies of it (FOREGROUND-CHILD, REPORT-SIGNAL-DEATH,
JOB-WAIT-FG) - only with no user trap on INT (INT-STOPS?): with one, the
trap runs and the line goes on, as in both references. A subshell puts
INT, QUIT and TERM back to their default, and raises again a ^C taken
before that reset, as dash's handler does in a child. Forth run by the
forth builtin: SIGNAL-ACTION's new action 4 sends SIGINT down the traps'
route (A26) - the VM restarts in TRAPPED with -28, Forth 2012's user
interrupt, thrown to DO-FORTH's own CATCH - except inside the allocator
(cv8.c: a flag around calloc, free and realloc; relfasm64: the range from
alloc_block to L_allocate), where only the flag is raised. Ordinary
execution pays nothing: no check on any branch.

**A32. PWD at startup follows XCU 2.5.3 (Iteration 573).** A review found
PWD left empty under `env -i`, so `cd -` failed after the first cd. Now
the environment's PWD is kept when it is absolute, has no . or ..
component, and names the current directory (the same device and inode:
FILE-MODE's follow? 1 and 2, new in both engines); otherwise the shell
sets, and exports, what pwd -P prints. dash and bash keep a PWD with a .
or .. component that names the directory; POSIX says to replace it - the
standard's text was taken, the user continuing on that recommendation.
Recorded in DASH.md.

**A33. A native-code back end (Q33; 608 -> 609).** The user, point by
point: (a) beside CV8 - "cv8 stays as is. We may improve it but we are
definitely not replacing it." (b) x86-64 only: "this is experiment". (c)
Performance is the primary goal; the code may grow, but every growth is
watched, weighed against the speed it buys, and discussed - "+50% in
code size and +5% performance probably not worth it." (d) The exit
targets stand: Forth benchmarks within 3 times of C at N2, scripts within
5 times of dash at N3. (e) Both back ends run the same shell sources and
all the tests. Recorded in docs/NATIVE.md; N1 may begin.

**A34. Rill: the conveniences one line replaces (Q34; 805 -> 807).** The
user, to the reply that recommended removing `keys` and keeping the rest:
"please proceed with open action items as you suggested" - read as taking
the recommendation, which the reply had named as the user's decision.
Done at 807: `keys()` removed ("keys() is not defined", as `values` at
799; its count is `len($r)`, its list `[$k for k, v in $r]`), its four
uses rewritten; starts, ends, trim, default, sum, `for i, x` and
comprehensions kept. Reversible: the user can still choose otherwise.

**A35. Rill: the length rule, and who Rill is for (Q35; 809 -> 810).** The
user: "length rule: do as you suggested" - done at 810: tools/rill-audit.py
judges the rewrites together (not longer in lines or characters), and one
rewrite more than 5 % longer names its reason in MANIFEST.tsv (run-utf8,
dead-words and native-by-source do). "who rill is for: I want rill to be
general shell/script language. But I also want it to be minimal and
simple. Let's see if we can find reasonable balance" - the balance
proposed as Q36.

**A36. Rill, general and minimal: the balance (Q36; 810 -> 811).** The
user: "I confirm q36" - (1)-(6) as proposed. JSON built at 811 (from-json,
json; decimal() on the same number reader, which fixed decimal("1e3") and
its kin); jobs, minimal, are next.

**A7, A37, A38. Rill: text blocks, speed, a prompt (Q7, Q37, Q38; 822 -> 823).**
The user: "1. I agree with option C" - text blocks with the closing
delimiter's indentation as the margin, built at 823. "2. I agree with `do
nothing` for now" - no speed work until a script is slow in practice.
"3. I want to see if rill can be used as interactive shell so please
implement interactive prompt with line editing and history. I wonder if we
can reuse what was done for relfsh." - the work after 823, relfsh's line
editor the first thing to try. And: "don't forget to add regression tests
each time bug is discovered".

