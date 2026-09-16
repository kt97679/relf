\ tests/coreplus-loop.fth - the DO ... +LOOP sections of the
\ Forth-2012 test suite's coreplustest.fth.
\
\ From github.com/gerryjackson/forth2012-test-suite, src/coreplustest.fth
\ (public domain, Gerry Jackson, with contributions from Reinhold Straub
\ and Andrew Haley as marked below), with T{ / }T rewritten to this
\ project's { / } - the same adaptation tester.fr already carries.
\
\ Only the four +LOOP sections are here. They were kept out of the tree
\ until (+LOOP)'s crossing test was fixed in Iteration 243: seven of
\ these cases failed, all stepping by a 256th of the cell range. The
\ rest of coreplustest.fth needs words this kernel does not have
\ without extend.4 (NIP, TUCK, :NONAME) and number prefixes (# $ %).
\
\ Needs tester.fr loaded first.

DECIMAL

TESTING DO +LOOP with run-time increment, negative increment, infinite loop
\ Contributed by Reinhold Straub

VARIABLE ITERATIONS
VARIABLE INCREMENT
: GD7 ( LIMIT START INCREMENT -- )
   INCREMENT !
   0 ITERATIONS !
   DO
      1 ITERATIONS +!
      I
      ITERATIONS @  6 = IF LEAVE THEN
      INCREMENT @
   +LOOP ITERATIONS @
;

{  4  4 -1 GD7 -> 4 1 }
{  1  4 -1 GD7 -> 4 3 2 1 4 }
{  4  1 -1 GD7 -> 1 0 -1 -2 -3 -4 6 }
{  4  1  0 GD7 -> 1 1 1 1 1 1 6 }
{  0  0  0 GD7 -> 0 0 0 0 0 0 6 }
{  1  4  0 GD7 -> 4 4 4 4 4 4 6 }
{  1  4  1 GD7 -> 4 5 6 7 8 9 6 }
{  4  1  1 GD7 -> 1 2 3 3 }
{  4  4  1 GD7 -> 4 5 6 7 8 9 6 }
{  2 -1 -1 GD7 -> -1 -2 -3 -4 -5 -6 6 }
{ -1  2 -1 GD7 -> 2 1 0 -1 4 }
{  2 -1  0 GD7 -> -1 -1 -1 -1 -1 -1 6 }
{ -1  2  0 GD7 -> 2 2 2 2 2 2 6 }
{ -1  2  1 GD7 -> 2 3 4 5 6 7 6 }
{  2 -1  1 GD7 -> -1 0 1 3 }
{ -20 30 -10 GD7 -> 30 20 10 0 -10 -20 6 }
{ -20 31 -10 GD7 -> 31 21 11 1 -9 -19 6 }
{ -20 29 -10 GD7 -> 29 19 9 -1 -11 5 }

\ ------------------------------------------------------------------------------
TESTING DO +LOOP with large and small increments

\ Contributed by Andrew Haley

MAX-UINT 8 RSHIFT 1+ CONSTANT USTEP
USTEP NEGATE CONSTANT -USTEP
MAX-INT 7 RSHIFT 1+ CONSTANT STEP
STEP NEGATE CONSTANT -STEP

VARIABLE BUMP

{ : GD8 BUMP ! DO 1+ BUMP @ +LOOP ; -> }

{ 0 MAX-UINT 0 USTEP GD8 -> 256 }
{ 0 0 MAX-UINT -USTEP GD8 -> 256 }

{ 0 MAX-INT MIN-INT STEP GD8 -> 256 }
{ 0 MIN-INT MAX-INT -STEP GD8 -> 256 }

\ Two's complement arithmetic, wraps around modulo wordsize
\ Only tested if the Forth system does wrap around, use of conditional
\ compilation deliberately avoided

MAX-INT 1+ MIN-INT = CONSTANT +WRAP?
MIN-INT 1- MAX-INT = CONSTANT -WRAP?
MAX-UINT 1+ 0=       CONSTANT +UWRAP?
0 1- MAX-UINT =      CONSTANT -UWRAP?

: GD9  ( n limit start step f result -- )
   >R IF GD8 ELSE 2DROP 2DROP R@ THEN -> R> }
;

{ 0 0 0  USTEP +UWRAP? 256 GD9
{ 0 0 0 -USTEP -UWRAP?   1 GD9
{ 0 MIN-INT MAX-INT  STEP +WRAP? 1 GD9
{ 0 MAX-INT MIN-INT -STEP -WRAP? 1 GD9

\ ------------------------------------------------------------------------------
TESTING DO +LOOP with maximum and minimum increments

: (-MI) MAX-INT DUP NEGATE + 0= IF MAX-INT NEGATE ELSE -32767 THEN ;
(-MI) CONSTANT -MAX-INT

{ 0 1 0 MAX-INT GD8  -> 1 }
{ 0 -MAX-INT NEGATE -MAX-INT OVER GD8  -> 2 }

{ 0 MAX-INT  0 MAX-INT GD8  -> 1 }
{ 0 MAX-INT  1 MAX-INT GD8  -> 1 }
{ 0 MAX-INT -1 MAX-INT GD8  -> 2 }
{ 0 MAX-INT DUP 1- MAX-INT GD8  -> 1 }

{ 0 MIN-INT 1+   0 MIN-INT GD8  -> 1 }
{ 0 MIN-INT 1+  -1 MIN-INT GD8  -> 1 }
{ 0 MIN-INT 1+   1 MIN-INT GD8  -> 2 }
{ 0 MIN-INT 1+ DUP MIN-INT GD8  -> 1 }

\ ------------------------------------------------------------------------------
\ TESTING +LOOP setting I to an arbitrary value

\ The specification for +LOOP permits the loop index I to be set to any value
\ including a value outside the range given to the corresponding  DO.

\ SET-I is a helper to set I in a DO ... +LOOP to a given value
\ n2 is the value of I in a DO ... +LOOP
\ n3 is a test value
\ If n2=n3 then return n1-n2 else return 1
: SET-I  ( n1 n2 n3 -- n1-n2 | 1 ) 
   OVER = IF - ELSE 2DROP 1 THEN
;

: -SET-I ( n1 n2 n3 -- n1-n2 | -1 )
   SET-I DUP 1 = IF NEGATE THEN
;

: PL1 20 1 DO I 18 I 3 SET-I +LOOP ;
{ PL1 -> 1 2 3 18 19 }
: PL2 20 1 DO I 20 I 2 SET-I +LOOP ;
{ PL2 -> 1 2 }
: PL3 20 5 DO I 19 I 2 SET-I DUP 1 = IF DROP 0 I 6 SET-I THEN +LOOP ;
{ PL3 -> 5 6 0 1 2 19 }
: PL4 20 1 DO I MAX-INT I 4 SET-I +LOOP ;
{ PL4 -> 1 2 3 4 }
: PL5 -20 -1 DO I -19 I -3 -SET-I +LOOP ;
{ PL5 -> -1 -2 -3 -19 -20 }
: PL6 -20 -1 DO I -21 I -4 -SET-I +LOOP ;
{ PL6 -> -1 -2 -3 -4 }
: PL7 -20 -1 DO I MIN-INT I -5 -SET-I +LOOP ;
{ PL7 -> -1 -2 -3 -4 -5 }
: PL8 -20 -5 DO I -20 I -2 -SET-I DUP -1 = IF DROP 0 I -6 -SET-I THEN +LOOP ;
{ PL8 -> -5 -6 0 -1 -2 -20 }
