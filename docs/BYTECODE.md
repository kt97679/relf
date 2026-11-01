# rill3 to bytecode directly (923, the owner's decision)

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

Stage 2 - the names go. With no text interpreted, nothing of rill3's runtime is looked up by name
while a script runs; the image may drop its headers (the build's last step, kept only for words the
prompt's Forth needs - none, once the prompt goes through the same compiler). To be measured: the
image's 20 KB of headers is the size at stake.

Stage 3 - what the text needed and nothing else does: FRESH names, `#$` numbers as text, OUT+ and
its buffer growing per sourced file (CM-COMPILE's retry, 890), CM-SHOW (a disassembler or a node dump
instead, for debugging).

Checks throughout: tests/cm/run on both engines and under GC stress - the oracle is outputs, as Q40
said (no decompiler); a script's start-up time and the image's size measured at each stage; calls.cm
and loop.cm against the text compiler's, which must not slow - the bytecode is the same.
