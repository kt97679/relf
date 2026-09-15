\ tests/coreext.fth - the ANS CORE EXT words added to extend.4.
\
\ Every word extend.4 adds has a case here. The rule comes from
\ Iteration 220, which retired 0> and U> from kernel.4: they were
\ unused AND untested, so nothing would have noticed if they were
\ wrong. Adding thirty words without tests would have recreated that
\ problem at ten times the size.
\
\ Run by tools/lab/forth-tests.sh and by tests/run_tests.sh, on an
\ image that has extend.4 loaded.

\ SELF-CONTAINED, deliberately: it does NOT use tester.fr's T{ }T.
\ extend.4 ends by building a ROOT wordlist and resetting the search
\ order, so anything loaded before it - including tester.fr's harness -
\ stops being findable. Rather than order the loads around that, this
\ file carries nine lines of checker and depends on nothing but the
\ kernel.
\
\ Run as:  S" extend.4" INCLUDED  S" tests/ext/coreext.fth" INCLUDED
\
\ It lives in tests/ext/ rather than tests/ because tests/*.fth is
\ globbed into the ANS CORE suite, which runs on a PLAIN kernel with no
\ extend.4 - so every word tested here would be undefined there. The
\ suite went from 1998 ok-markers to zero the first time this file was
\ in the glob.

VARIABLE #FAIL
VARIABLE #RUN

: EXPECT= ( got want --- )
  1 #RUN +!
  OVER OVER = IF 2DROP EXIT THEN
  1 #FAIL +!
  CR ." FAIL: got " SWAP . ." want " . ;

: REPORT ( --- )
  CR #RUN @ . ." CORE EXT assertions, " #FAIL @ . ." failed"
  #FAIL @ IF ." - FAILING" ELSE ." - ok" THEN CR ;

\ ---- stack and comparison -------------------------------------------
1 2 NIP                     2 EXPECT=
1 2 TUCK DROP               1 EXPECT=
1 2 TUCK NIP NIP            2 EXPECT=
0 0<>                       0 EXPECT=
5 0<>                      -1 EXPECT=
-5 0<>                     -1 EXPECT=
1 0>                       -1 EXPECT=
0 0>                        0 EXPECT=
-1 0>                       0 EXPECT=
3 2 U>                     -1 EXPECT=
2 3 U>                      0 EXPECT=
2 2 U>                      0 EXPECT=

\ WITHIN is lo <= x < hi, half-open at the top.
5 1 10 WITHIN              -1 EXPECT=
1 1 10 WITHIN              -1 EXPECT=
10 1 10 WITHIN              0 EXPECT=
0 1 10 WITHIN               0 EXPECT=

\ ---- constants ------------------------------------------------------
TRUE                       -1 EXPECT=
FALSE                       0 EXPECT=

\ ---- ERASE ----------------------------------------------------------
VARIABLE EBUF 8 CHARS ALLOT
EBUF 8 65 FILL  EBUF C@    65 EXPECT=
EBUF 8 ERASE    EBUF C@     0 EXPECT=
EBUF 7 CHARS + C@           0 EXPECT=

\ ---- AGAIN ----------------------------------------------------------
: AG1 ( --- n )  0 BEGIN 1+ DUP 4 > IF EXIT THEN AGAIN ;
AG1                         5 EXPECT=

\ ---- CASE OF ENDOF ENDCASE ------------------------------------------
\ ENDCASE DISCARDS THE SELECTOR, so the default arm runs with it still
\ on the stack and has to arrange for ENDCASE's DROP to take the
\ selector rather than the answer - hence the SWAP. A matched arm does
\ not need it: OF has already dropped the selector, and ENDOF jumps
\ past ENDCASE's DROP. Getting this backwards is what the first
\ version of these tests did, and the implementation was right.
: CS1 ( n --- n )  CASE 1 OF 11 ENDOF 2 OF 22 ENDOF 99 SWAP ENDCASE ;
1 CS1                      11 EXPECT=
2 CS1                      22 EXPECT=
7 CS1                      99 EXPECT=

\ The default arm can use the selector, which is the point of it being
\ left there.
: CS2 ( n --- n )  CASE 1 OF 0 ENDOF DUP 1+ SWAP ENDCASE ;
5 CS2                       6 EXPECT=
1 CS2                       0 EXPECT=

\ ---- [COMPILE] ------------------------------------------------------
: BC1 ( --- n ) [COMPILE] TRUE ;
BC1                        -1 EXPECT=

\ ---- ENVIRONMENT? ---------------------------------------------------
\ Unrecognised queries return false, which is all this answers.
S" WORDLISTS" ENVIRONMENT?      0 EXPECT=
S" /COUNTED-STRING" ENVIRONMENT? 0 EXPECT=

REPORT
