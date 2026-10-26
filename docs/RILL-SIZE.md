# Where Rill's image goes - the audit, and what would keep it small (Iteration 826)

At the user's asking, when kernel64-rill.img (91,526 bytes) had grown to 70 % of relfsh's
kernel64-shell.img (130,348). Measured by tools/rill-size.py, which builds the image a file at a
time and walks its dictionary; run it again whenever the image grows.

| layer | bytes | share | words | headers | bodies |
|---|---:|---:|---:|---:|---:|
| kernel64.img and the shared Forth (extend, safety, pool, shadow, save-system) | 14,839 | 16 % | 458 | 4,102 | 10,441 |
| genes | 193 | 0 % | 15 | 159 | 34 |
| rt.4, the runtime | 20,538 | 22 % | 418 | 3,965 | 16,573 |
| regex.4 | 4,560 | 5 % | 95 | 931 | 3,629 |
| the characters' widths (shell.4's tables) | 4,109 | 4 % | 12 | 121 | 3,988 |
| edit-shim.4 and edit.4, the prompt's editor | 8,187 | 9 % | 165 | 2,060 | 6,127 |
| **compile.4, the image's compiler** | **39,044** | **43 %** | 466 | 4,440 | 34,604 |

Headers - a word's link, count byte and name - are 15.8 KB of the image (17 %): what EVALUATE needs
of the runtime's words, since the compiler writes Forth as text, and what nothing needs of the
compiler's and the editor's own once the image is built. The compiler holds 882 string literals,
7,152 bytes of text: Forth it writes (`S" R-NEW-LIST" OUT+`), tokens it compares (`S" (" CUR-IS?`, 23
times), and 116 error messages, 3,852 bytes. Repeated literals cost about 2.8 KB. The largest words:
ZERO-WIDTH (2,595, a table), LIBRARY (2,361), BINOP (1,623), WIDE-CHARS (1,049, a table), DEF-STMT,
FOR-STMT. The genes cost 6.6 KB together, purestack 1,368 and infer 1,128 the most; the search that
chose them (RILL-SEARCH.md) weighed speed, generated Forth and source - never the image's bytes. Five
runtime words nothing uses: LM-K, R-EXEC, RC-D, RC-HI, RC-LO.

## What would keep it small (QUESTIONS.md Q39)

1. **Two images**: scripts without the editor, the prompt with it - the script image 91.5 KB to
   about 79.2 KB, nothing slower or lost; `rill` with no script at a terminal loads the second.
2. **The genes scored again with the image's bytes in the score** (tools/rill-search.py): up to
   6.6 KB at stake; the search's own numbers show most genes buying 3 % or less - perhaps 1-3 KB.
3. **The compiler's repeated literals as words** - a token compared (`(`, `)`, `{`, `}`), the prefix
   `rillc: line ` (15 times): perhaps 1-1.5 KB of the 2.8 KB; the oracle checks it.
4. **The five dead words**: some 0.2 KB.
5. **No names for words nothing looks up** - the compiler's 466, the editor's 165, the runtime's own
   helpers: up to 7-8 KB, but it needs a kernel feature (a definition without a header, or an image
   stripped and relinked), and the kernel is every image's.
6. Not recommended: shorter error messages (3.9 KB - their clarity is the point); an image without
   its compiler (43 %) - the prompt and `rill script.rill` need it.

## Alternatives to the compiler (QUESTIONS.md Q40)

Asked at 826: BASIC has been written in Forth - can Rill do the same? Forth BASICs come in two
kinds. An interpreter keeps the program as tokens and runs them through a dispatcher each time. A
compiler in Forth's own manner makes each keyword a Forth word that, when met, reads what follows
and compiles code at once - `COMPILE,` and `LITERAL` - so there is no text written and read back,
and the dictionary does the dispatch. This kernel's interpreter has no hook for a word it does not
know (`WORD FIND ... NUMBER? 0= ABORT" Undefined word"`), so Rill would run its own read loop and use
the dictionary for its keywords and library names.

compile.4 by part: the tokens 2.9 KB; the output text and tables 1.0 KB; expressions 16.3 KB;
statements, defs and the program 17.8 KB; the prompt 1.0 KB. Inside them, the Forth written or
compared is about 4.9 KB and the messages 3.7 KB. What Rill's grammar asks for - precedence,
strings with {expr} and $(...), lists and records, comprehensions, commands and their ports,
defs with kinds, text blocks - is the 34 KB of parts 3 and 4, however it is written; a BASIC is
small because BASIC is.

1. **Compiling in Forth's manner** - keywords as words, code compiled directly, nothing EVALUATEd:
   the output machinery (1 KB), most of the Forth text (some 3.5 KB of the 4.9), part of the
   tokenizer, and the runtime's names (most of its 4 KB of headers, since generated code would no
   longer look them up) - some 6-9 KB, and compiling faster. A rewrite of compile.4; and the oracle,
   rillc.py's Forth against the image's word for word, has nothing to compare - its 61 programs'
   evidence would rest on their outputs.
2. **An interpreter** in place of the compiler, as relfsh's tree.4 is: no smaller - the parser
   stays, an evaluator replaces the code selection - and several times slower in a loop, where Rill
   now outruns Python.
3. **The compiler out of the image a script runs in**: `rill --forth` already writes a script's
   Forth, and the image runs a .4 itself - so a script compiled once (kept by its text's hash and the
   image's) runs in an image of the runtime alone: about 40 KB, 44 % of today's, the editor and the
   compiler kept for the prompt and for a first run. To settle: where the cache lives, and that
   `$script` names the script, not its compiled copy.
4. **Smaller as it is**: Q39's options.

### Bytecode directly, without the Forth between (828)

Asked next. Possible: the compiler would lay down CV8 code itself - `COMPILE,` for a call,
`LITERAL` for a number, branches resolved as IF and THEN resolve them - in place of the text it
writes now for EVALUATE to read again. Measured on pack-results.rill (177 lines): compiled to
text in 13.1 ms; the text (28,460 bytes) EVALUATEd in another 15 ms. A large script would start
in about half the time, and each compile would not need its 2.25 MB of text buffers.

The image would save less than it seems: the Forth text is some 3.5 KB of the compiler, but code
made directly still names every runtime word it calls - an execution token kept for each, where
the text kept its name - and the runtime's 4 KB of headers could go only if nothing read
generated Forth any more (`rill --forth`, a cached compile, the prompt's R-MAIN). Some 3-6 KB in
all. The work is in five places where the text is made out of order, which code laid down in
order cannot do as it is: a def's locals header, written after its body; a stage's redirections,
before its words; literal texts and VARIABLEs, at the program's top; loop bodies hoisted into
words of their own; defs put off to the second pass. And the oracle - rillc.py's Forth against the
image's, word for word, 61 programs - has no Forth on the image's side to compare: the kernel has
no decompiler. It would compare outputs instead, as the fuzzer could.

Found on the way: the prompt kept every line's text buffers and token tables, and a string's own
tables in any compile - some 5.5 MB of address space a line (21 MB resident at 400 lines). Made
once and reused now, and a string's freed: flat, 2 MB, at 1,600 lines (tests/rill/prompt/
many-lines.in, in 400 MB). And an error code not Rill's own is said at the prompt as R-BOOT says it.
