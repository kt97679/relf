# rill3 to bytecode directly (923, the owner's decision; done 926)

## Today

cm/cmc.4 reads a script into a tree, and writes Forth source text from it - each definition `: name
... ;`, the script's commands last in CM.MAIN - which the Forth text interpreter then EVALUATEs into
the engine's bytecode. The front end composes the text out of order with `++`, `SEQ+` and `TOP$`;
bodies of loops, blocks and defs become words of their own (B1.1, L2.2, W3.5 - FRESH names), written
before the word that calls them (DEF-WORD, OUT+).

Measured (923) on a 2,001-line script of 400 defs: reading and writing the text ~110 ms, the whole run
~250 ms - EVALUATE is more than half of start-up - and the text is 213,961 bytes, ~107 a line. In the
image: 12.9 KB of quoted text across the sources (messages, and the Forth the front end writes), and
some 20 KB of word headers (1,084 names), kept because the text names the runtime's words, so the
text interpreter must find them. Q40 (828) weighed the same for Rill: half the start-up time, 3-6 KB
of image, five out-of-order places to restructure.

## The engine's bytecode

forth/kernel.4: COMPILE, lays a primitive as its opcode (one byte, or ESC and a selector), inlines a
small straight word, a constant as its literal, a `@ ;` DOES> word as VAR@, and anything else as a call
- two bytes if its offset from the image base fits 14 bits, else three. LITERAL lays a literal; IF,
ELSE, THEN, BEGIN, WHILE, REPEAT, DO, LOOP mark and resolve branches. So the front end can make the
same bytecode the text makes by calling these words itself - no text, and no name looked up.

## The plan

Stage 1 - the generator calls the compiler, in two passes. A first pass over the tree makes the inner
words - each loop's body, each block, each def - depth first, with :NONAME, keeping their xts in the
tree's nodes; the second makes each word's own code with COMPILE, and LITERAL and the control words,
executed as the text interpreter would have executed them. The five kinds of out-of-order places - a
condition before its body (if, while, case), the arms of case, keys after a value, a capture's body
before the capture, a loop's body before its loop - each read its parts from the tree, which is
already whole, rather than from strings made earlier. Defs stay found at compile time (DEF-FIND); a
call is the def's xt, recursion the xt :NONAME gives at its start.

Not done - the owner's word (924): the image keeps its names. `forth words values...` (924) runs Forth
in rill3's image, by name, so the names are part of the language now.

Stage 2 - what the text needed and nothing else does: FRESH names, `#$` numbers as text, OUT+ and
its buffer growing per sourced file (CM-COMPILE's retry, 890), CM-SHOW (a disassembler or a node dump
instead, for debugging).

Checks throughout: tests/cm/run on both engines and under GC stress - the oracle is outputs, as Q40
said (no decompiler); a script's start-up time and the image's size measured at each stage; calls.cm
and loop.cm against the text compiler's, which must not slow - the bytecode is the same.

## Done (926)

Not in two passes over the tree, as Stage 1 planned: the front end's out-of-order joining of strings
stays, and only what it joins changed - tokens, not text. cm/ir.4: a token is a word already found (its
offset from START, three bytes, as CALL, keeps one), a number, a text, a made word's call or xt by its
number, or a made word's start and end. T" ..." makes a fragment's tokens when cm/cmc.4 is loaded, so
the runtime's words are found then, once; INSTALL lays the tokens down - COMPILE, and LIT, inside a made
word, EXECUTE outside one, the control words run - as the text interpreter would have, with no text read
and nothing looked up. A made word is numbered per compile, its xt HERE when it begins; it ends with
EXIT, and STATE 0 - not `;`, whose REVEAL read LAST, stale in a reloaded image until a word is named. A
def is a record, [xt][frame][mask], that DEF-SET fills and each call reads - so a def made again at the
prompt is the one called, as its DEFER was; the record, not the body's xt, rides the return stack while
its arguments are bound, or R-WHERE took the xt for a return into the def's lines. Gone with the text: the
made words' names, DNAME, the 256-thread word list (909), the DEFER and two VARIABLEs a def had. CM-SHOW
prints the tokens as the Forth they stand for - for one script the same, line for line, as the text was.

Measured against 925's image: a 2,001-line script starts in 145-197 ms against 285-358; 4,000 defs load
in 266-288 ms against 1,106-1,177; calls.cm and loop.cm the same - the bytecode is. The image 83,312
bytes against 83,512, with the installer and the reader of tokens in it.
