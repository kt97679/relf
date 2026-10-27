# A scripting vocabulary on Forth - the language grown from the implementation (Iteration 829)

The user's idea, asked after Q40: Rill was syntax first and a compiler after; relf's Forth is an
implementation already - the engine, the kernel, and Rill's runtime words for texts, lists,
records, regular expressions and commands. Grow the language up from it instead: words, a few of
them parsing words, until a script reads as a script - the translation layer minimal, or none.

## The evidence

The pilots (756-760, docs/PILOT-NATIVE-BY-SOURCE.md) wrote three tools in Python, Rill and Forth -
the Forth on relf's kernel and Rill's runtime words, exactly this base. Against Python, by the
pilots' count: Rill 11 % shorter, Forth 87 % longer. Defects from first run to match: Rill 13
(its youth), Forth 4 (names). Of the three Forth versions' code (comments aside, some 18,400
characters): variables - `VARIABLE x`, `x @`, `x !` - 15.5 %; stack words 7.6 %; what a vocabulary
absorbs - `S" .." R-TEXT`, boxing and unboxing, list loops and list building - about 10 %; and
library the Forth wrote itself, number formatting and a sort.

The sketch, examples/forth-script/: vocab.4, some 17 words in 761 characters - `t" .."` a text,
`texts[ .. ]texts` a list's texts in turn, `list[ .. ]list` with `#,` and `i,`, `$@`, short names
for the runtime's words, VALUE and TO. In it, native-by-source.fth's first section - the dump read
into a record - is parse-dump.4: **396 characters of code, where the pilot's Forth has 685 and
Rill 371**, and it prints what parse-dump.rill prints (tests/rill/run checks it). Writing it, one
stack slip - a DROP too many, reported as "recursion too deep for the stacks", far from its cause;
fixing the pilots (below), another - ROT reaching three deep for a fourth, error -9.

## What a vocabulary does, and what it does not

It does what is library or pattern: values boxed and unboxed behind typed words, literals, loops
over lists, building lists and records, formatting, sorting. A section made of those comes within
a tenth of Rill, as the sketch's did. It does not do the stack and the variables - a quarter of
the pilots' Forth - nor expressions: Rill's `$acc[cls][$k] + $v[cls][$k]` is a stack dance in
Forth. Locals (`{: a b :}`) and Factor's dataflow combinators narrow that; only a parser - infix,
`$x[i]`, `{expr}` in strings - closes it, and that parser is most of the compiler's 34 KB of
grammar. And the errors: Rill says the line and what is wrong before anything runs; Forth says
"Undefined word", or a stack fault far from where the stack went wrong.

Without the compiler the image is about 40 KB with the runtime alone, 52 KB with the editor; a
script runs as fast as Rill's compiled code or faster - the pilots' hand-written Forth ran 1.4
times as fast as Rill on their data scripts.

## The view

For scripts written by people who read Forth - the project's own tools - a scripting vocabulary
is a real option: small, fast, nothing to translate, the sketch's section within 7 % of Rill. For
the general shell and script language A35 asks for, Rill's syntax earns its compiler: the stack is
the price a vocabulary cannot take away. The cheap way to know more is the pilots' protocol - one
whole pilot written in the vocabulary, the vocabulary grown as it asks, characters and defects and
time measured against the three. QUESTIONS.md Q41.

## Found on the way

Two of the pilots' Forth versions had not loaded since 799, which took R-UPPER, R-LOG and R-EXP
from the runtime, and nothing ran them: native-by-source.fth has its own UPPER now, and
native-ab-layouts.fth takes its geometric mean from awk, as its Rill version has since 799 (GM:
1.144714 for 1.5, 0.5, 2.0, as Python's). tests/rill/run loads each examples/rill/*.fth now, its
closing MAIN left out, and fails on a word undefined.

## The minimal parser (830)

The user, after Q41: a general-purpose scripting language and shell; regular notation, `a = b + c`;
perhaps a small translation layer with a minimal parser that hides the stack. examples/forth-script/
mini.4 is that layer as a prototype: 197 lines of Forth over Rill's runtime words. Values carry their
kinds and are checked when used, as Python's are - so there is no kind inference, no second pass, no
per-function knowledge: a library function is a word L.name, called by name. A statement is compiled
to Forth and run, then the next is read, as a shell does. It has expressions with precedence (`or`,
`and`, `not`, comparisons, `+ -`, `* / %`, unary minus, `x[i]`, calls, lists, strings with escapes);
assignment, `if`/`elif`/`else`, `while`, `for x in`, `def` with `return` (recursion through RECURSE,
parameters and what a def sets shadowed); and command lines - a line that is no assignment, call or
known name runs as a command, `$name` its variables, its status in `status`. demo.mini runs in it, as
tests/rill/run checks, and the same under RILL_GC_STRESS=1:

    a = b + c * 4                      def fib(n) {
    print(greeting + ", world")            if n < 2 { return n }
    for i in range(5) {                    return fib(n - 1) + fib(n - 2)
        append(squares, i * i)         }
    }                                  echo hello from $name

| | image (no editor) | fib(25) |
|---|---:|---:|
| Rill: its compiler | 79.2 KB | 10 ms |
| the runtime and mini.4 | 52.8 KB | 78 ms |
| the runtime alone | 40.1 KB | |
| Python | | 25 ms |

The parser is 12.7 KB, a third of the compiler's 39. The price is speed where numbers are many: every
number is a box on the heap, made and dropped, so fib runs eight times Rill's time and three times
Python's. Tagged small numbers - a number told by its low bit, never boxed - would win most of that
back: a change to the runtime, not to the parser. Not in the prototype, each a matter of the parser's
growing, the runtime having them already: decimals, records, pipelines and redirections, `$(...)`,
`{expr}` in strings, text blocks, comprehensions, break and continue, line numbers in errors at run
time (compile errors have them). Writing it, three stack slips of the author's own, found by running:
the case for a parser that keeps them from a script's writer. QUESTIONS.md Q42.

## Bytecode, and speed (831)

Asked: can the minimal parser make bytecode itself, and be as fast as Rill? Bytecode directly is
possible, and simpler here than in Rill's compiler - mini's Forth comes in order - but it changes how
fast a script starts, not how fast it runs: EVALUATE makes the same CV8 code a direct compiler would.
Running speed is a matter of values. Measured, best of five:

| | fib(25) | 300,000 additions in a loop |
|---|---:|---:|
| mini, 830: numbers boxed | 78 ms | 66 ms |
| mini, 831: numbers tagged, `for i in range(n)` counted | 25 ms | 19 ms |
| Rill | 7 ms | 10 ms |
| Rill without its purestack gene | 43 ms | |
| Python | 18 ms | 31 ms |

A number is 2n+1 now - its low bit tells it, as in Lisp's and OCaml's runtimes - and two such add in
an instruction or two, with nothing made; a number goes into a list, or to the runtime's words, boxed.
true and false are two boxes made once. `for i in range(n)` is a counted loop, no list made - Rill's
rangeloop gene. The collector leaves an odd value alone (G-BOX: boxes are aligned, never odd). It all
cost the parser 328 bytes: the runtime and mini.4, 53,119.

What the table shows of Rill: its speed is a few targeted choices, not its typing in general - without
purestack, which runs a def of numbers on the stack, its fib takes 43 ms, the parameter an item and
every result boxed. So mini can be as fast as Rill where it ports those choices: tagged numbers and
counted loops done; a def of numbers on the stack next (Rill's purestack, some 1.4 KB of its compiler);
the loop's last factor of two is a safe point at every statement and a tag looked at on every add.

## The syntax, how friendly; the shell, what it costs (832)

Asked: how friendly is the prototype's syntax, should it be better and at what cost; and what do
pipes, redirections and processes add? Each suspicion was run, not argued:

| tried | what happened |
|---|---|
| `def f(x)` calls `g()`, which reads a global x | g sees f's x - scope dynamic, where Python's is lexical |
| `ls = 1`, then `ls -l /tmp` | `ls - l`: "l is not defined" - a variable hides a command |
| `prnt "hi"` (a typo) | run as a command: env's "No such file or directory" |
| `else` on the line after `}` | both branches ran, `else` run as a command - fixed (below) |
| `x = (1 +` newline `2)` | an error: a line may not go on inside brackets |
| `a * b`, b a text | "a number was wanted" - no line, no operator |
| an error on line 3 | lines 1 and 2 had run - a statement runs as soon as it is read |
| `"n is {n}"` | printed as it is: no interpolation |

The `else` one ran the wrong code without a word, so it is mended now: else and elif may follow
their block on the lines after it, a stray one is an error (layout.mini, run by tests/rill/run).
The rest, and what each would cost the parser - all decided when a script is compiled, none slower
when it runs (all-but-free: Rill's R-MARK table gives lines to errors at run time for nothing):

1. a script read whole before it runs, the prompt still a line at a time - some 0.1 KB;
2. lines that go on inside ( [ - 0.1 KB;
3. a def's names its own (lexical scope) - 0.1 KB, and no slower;
4. commands told plainly: a first word that names nothing is checked against PATH when compiled, so
   a typo is an error, not a command; `!ls` when a variable hides one - 0.2 KB;
5. `{expr}` in strings - 0.4 KB;
6. errors with their line and their operator at run time - 0.1 KB;
7. break and continue, `+=`, records, slices, decimals, print of several - some 1.2 KB.

Some 2.3 KB in all: the image without the editor about 57 KB, against Rill's 79.

The shell, measured. Pipes, redirections (`> >> < 2>`), quotes, `$( )` and `&` are in mini.4 now
(demo.mini): 1,960 bytes of parser - Rill's compiler gives its command syntax 1,980 - and nothing new
in the runtime, which has had pipelines, redirections, jobs and signals all along. Running them:

| | 300 runs of true | 100 three-stage pipelines |
|---|---:|---:|
| mini | 477 ms | 546 ms |
| Rill | 456 ms | 514 ms |
| dash | 201 ms | 224 ms |
| Python, subprocess | 268 ms | |

mini and Rill are one runtime, and the same. dash is twice as fast because the runtime runs every
command as `/usr/bin/env cmd args` - a second exec, for env to search PATH: in dash, 300 runs
through env take 434 ms, 194 directly. Searching PATH in the runtime, one exec (execvp's way):
some 20 lines of rill/rt.4, and every command and pipeline twice as fast, for Rill and mini alike.

Found on the way, in Rill: the scope test run in Rill prints `@C`. A def's parameter is the
variable of the global with its name - shadowed for the call, as mini's - so a def reading that
global during the call reads the parameter; and where their kinds differ, one is read as the other:
garbage. The next fix - QUESTIONS.md Q43, GOALS.md 15.
