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
