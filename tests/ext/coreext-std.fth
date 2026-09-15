\ tests/ext/coreext-std.fth - the official ANS/Forth-2012 CORE EXT tests.
\
\ From github.com/Forth-Standard/forth-standard-test-suite, src/
\ coreexttest.fth, with T{ / }T rewritten to this project's { / }
\ - the same adaptation tester.fr already carries.
\
\ TEN of its twenty-eight sections are here: the ones whose words this
\ system has. The other eighteen need words it does not implement -
\ 2>R 2R@ 2R>, UNUSED, MARKER, BUFFER:, VALUE TO, :NONAME, C", .(,
\ .R U.R, PARSE, PARSE-NAME, DEFER and friends, HOLDS, S\", and
\ SAVE-INPUT/RESTORE-INPUT. Adding a word means adding its section
\ back, which is the point of keeping the split explicit rather than
\ deleting what does not run.
\
\ Needs tester.fr and extend.4 loaded first, in that order.

\ ------------------------------------------------------------------------------
\ Version 0.15 1 August 2025 Added two tests to VALUE
\         0.14 21 July 2022 Updated first line of BUFFER: test as recommended
\              in issue 32
\         0.13 28 October 2015
\              Replace <FALSE> and <TRUE> with FALSE and TRUE to avoid
\              dependence on Core tests
\              Moved SAVE-INPUT and RESTORE-INPUT tests in a file to filetest.fth
\              Use of 2VARIABLE (from optional wordset) replaced with CREATE.
\              Minor lower to upper case conversions.
\              Calls to COMPARE replaced by S= (in utilities.fth) to avoid use
\              of a word from an optional word set.
\              UNUSED tests revised as UNUSED UNUSED = may return FALSE when an
\              implementation has the data stack sharing unused dataspace.
\              Double number input dependency removed from the HOLDS tests.
\              Minor case sensitivities removed in definition names.
\         0.11 25 April 2015
\              Added tests for PARSE-NAME HOLDS BUFFER:
\              S\" tests added
\              DEFER IS ACTION-OF DEFER! DEFER@ tests added
\              Empty CASE statement test added
\              [COMPILE] tests removed because it is obsolescent in Forth 2012
\         0.10 1 August 2014
\             Added tests contributed by James Bowman for:
\                <> U> 0<> 0> NIP TUCK ROLL PICK 2>R 2R@ 2R>
\                HEX WITHIN UNUSED AGAIN MARKER
\             Added tests for:
\                .R U.R ERASE PAD REFILL SOURCE-ID 
\             Removed ABORT from NeverExecuted to enable Win32
\             to continue after failure of RESTORE-INPUT.
\             Removed max-intx which is no longer used.
\         0.7 6 June 2012 Extra CASE test added
\         0.6 1 April 2012 Tests placed in the public domain.
\             SAVE-INPUT & RESTORE-INPUT tests, position
\             of { moved so that tests work with ttester.fs
\             CONVERT test deleted - obsolete word removed from Forth 200X
\             IMMEDIATE VALUEs tested
\             RECURSE with :NONAME tested
\             PARSE and .( tested
\             Parsing behaviour of C" added
\         0.5 14 September 2011 Removed the double [ELSE] from the
\             initial SAVE-INPUT & RESTORE-INPUT test
\         0.4 30 November 2009  max-int replaced with max-intx to
\             avoid redefinition warnings.
\         0.3  6 March 2009 { and } replaced with { and }
\                           CONVERT test now independent of cell size
\         0.2  20 April 2007 ANS Forth words changed to upper case
\                            Tests qd3 to qd6 by Reinhold Straub
\         0.1  Oct 2006 First version released
\ -----------------------------------------------------------------------------
\ The tests are based on John Hayes test program for the core word set

\ Words tested in this file are:
\     .( .R 0<> 0> 2>R 2R> 2R@ :NONAME <> ?DO AGAIN C" CASE COMPILE, ENDCASE
\     ENDOF ERASE FALSE HEX MARKER NIP OF PAD PARSE PICK REFILL
\     RESTORE-INPUT ROLL SAVE-INPUT SOURCE-ID TO TRUE TUCK U.R U> UNUSED
\     VALUE WITHIN [COMPILE]

\ Words not tested or partially tested:
\     \ because it has been extensively used already and is, hence, unnecessary
\     REFILL and SOURCE-ID from the user input device which are not possible
\     when testing from a file such as this one
\     UNUSED (partially tested) as the value returned is system dependent
\     Obsolescent words #TIB CONVERT EXPECT QUERY SPAN TIB as they have been
\     removed from the Forth 2012 standard

\ Results from words that output to the user output device have to visually
\ checked for correctness. These are .R U.R .(

\ -----------------------------------------------------------------------------
\ Assumptions & dependencies:
\     - tester.fr (or ttester.fs), errorreport.fth and utilities.fth have been
\       included prior to this file
\     - the Core word set available
\ -----------------------------------------------------------------------------
TESTING TRUE FALSE

{ TRUE  -> 0 INVERT }
{ FALSE -> 0 }

\ -----------------------------------------------------------------------------
TESTING <> U>   (contributed by James Bowman)

{ 0 0 <> -> FALSE }
{ 1 1 <> -> FALSE }
{ -1 -1 <> -> FALSE }
{ 1 0 <> -> TRUE }
{ -1 0 <> -> TRUE }
{ 0 1 <> -> TRUE }
{ 0 -1 <> -> TRUE }

{ 0 1 U> -> FALSE }
{ 1 2 U> -> FALSE }
{ 0 MID-UINT U> -> FALSE }
{ 0 MAX-UINT U> -> FALSE }
{ MID-UINT MAX-UINT U> -> FALSE }
{ 0 0 U> -> FALSE }
{ 1 1 U> -> FALSE }
{ 1 0 U> -> TRUE }
{ 2 1 U> -> TRUE }
{ MID-UINT 0 U> -> TRUE }
{ MAX-UINT 0 U> -> TRUE }
{ MAX-UINT MID-UINT U> -> TRUE }

\ -----------------------------------------------------------------------------
TESTING 0<> 0>   (contributed by James Bowman)

{ 0 0<> -> FALSE }
{ 1 0<> -> TRUE }
{ 2 0<> -> TRUE }
{ -1 0<> -> TRUE }
{ MAX-UINT 0<> -> TRUE }
{ MIN-INT 0<> -> TRUE }
{ MAX-INT 0<> -> TRUE }

{ 0 0> -> FALSE }
{ -1 0> -> FALSE }
{ MIN-INT 0> -> FALSE }
{ 1 0> -> TRUE }
{ MAX-INT 0> -> TRUE }

\ -----------------------------------------------------------------------------
TESTING NIP TUCK ROLL PICK   (contributed by James Bowman)

{ 1 2 NIP -> 2 }
{ 1 2 3 NIP -> 1 3 }

{ 1 2 TUCK -> 2 1 2 }
{ 1 2 3 TUCK -> 1 3 2 3 }

{ : RO5 100 200 300 400 500 ; -> }
{ RO5 3 ROLL -> 100 300 400 500 200 }
{ RO5 2 ROLL -> RO5 ROT }
{ RO5 1 ROLL -> RO5 SWAP }
{ RO5 0 ROLL -> RO5 }

{ RO5 2 PICK -> 100 200 300 400 500 300 }
{ RO5 1 PICK -> RO5 OVER }
{ RO5 0 PICK -> RO5 DUP }

\ -----------------------------------------------------------------------------
TESTING HEX   (contributed by James Bowman)

{ BASE @ HEX BASE @ DECIMAL BASE @ - SWAP BASE ! -> 6 }

\ -----------------------------------------------------------------------------
TESTING WITHIN   (contributed by James Bowman)

{ 0 0 0 WITHIN -> FALSE }
{ 0 0 MID-UINT WITHIN -> TRUE }
{ 0 0 MID-UINT+1 WITHIN -> TRUE }
{ 0 0 MAX-UINT WITHIN -> TRUE }
{ 0 MID-UINT 0 WITHIN -> FALSE }
{ 0 MID-UINT MID-UINT WITHIN -> FALSE }
{ 0 MID-UINT MID-UINT+1 WITHIN -> FALSE }
{ 0 MID-UINT MAX-UINT WITHIN -> FALSE }
{ 0 MID-UINT+1 0 WITHIN -> FALSE }
{ 0 MID-UINT+1 MID-UINT WITHIN -> TRUE }
{ 0 MID-UINT+1 MID-UINT+1 WITHIN -> FALSE }
{ 0 MID-UINT+1 MAX-UINT WITHIN -> FALSE }
{ 0 MAX-UINT 0 WITHIN -> FALSE }
{ 0 MAX-UINT MID-UINT WITHIN -> TRUE }
{ 0 MAX-UINT MID-UINT+1 WITHIN -> TRUE }
{ 0 MAX-UINT MAX-UINT WITHIN -> FALSE }
{ MID-UINT 0 0 WITHIN -> FALSE }
{ MID-UINT 0 MID-UINT WITHIN -> FALSE }
{ MID-UINT 0 MID-UINT+1 WITHIN -> TRUE }
{ MID-UINT 0 MAX-UINT WITHIN -> TRUE }
{ MID-UINT MID-UINT 0 WITHIN -> TRUE }
{ MID-UINT MID-UINT MID-UINT WITHIN -> FALSE }
{ MID-UINT MID-UINT MID-UINT+1 WITHIN -> TRUE }
{ MID-UINT MID-UINT MAX-UINT WITHIN -> TRUE }
{ MID-UINT MID-UINT+1 0 WITHIN -> FALSE }
{ MID-UINT MID-UINT+1 MID-UINT WITHIN -> FALSE }
{ MID-UINT MID-UINT+1 MID-UINT+1 WITHIN -> FALSE }
{ MID-UINT MID-UINT+1 MAX-UINT WITHIN -> FALSE }
{ MID-UINT MAX-UINT 0 WITHIN -> FALSE }
{ MID-UINT MAX-UINT MID-UINT WITHIN -> FALSE }
{ MID-UINT MAX-UINT MID-UINT+1 WITHIN -> TRUE }
{ MID-UINT MAX-UINT MAX-UINT WITHIN -> FALSE }
{ MID-UINT+1 0 0 WITHIN -> FALSE }
{ MID-UINT+1 0 MID-UINT WITHIN -> FALSE }
{ MID-UINT+1 0 MID-UINT+1 WITHIN -> FALSE }
{ MID-UINT+1 0 MAX-UINT WITHIN -> TRUE }
{ MID-UINT+1 MID-UINT 0 WITHIN -> TRUE }
{ MID-UINT+1 MID-UINT MID-UINT WITHIN -> FALSE }
{ MID-UINT+1 MID-UINT MID-UINT+1 WITHIN -> FALSE }
{ MID-UINT+1 MID-UINT MAX-UINT WITHIN -> TRUE }
{ MID-UINT+1 MID-UINT+1 0 WITHIN -> TRUE }
{ MID-UINT+1 MID-UINT+1 MID-UINT WITHIN -> TRUE }
{ MID-UINT+1 MID-UINT+1 MID-UINT+1 WITHIN -> FALSE }
{ MID-UINT+1 MID-UINT+1 MAX-UINT WITHIN -> TRUE }
{ MID-UINT+1 MAX-UINT 0 WITHIN -> FALSE }
{ MID-UINT+1 MAX-UINT MID-UINT WITHIN -> FALSE }
{ MID-UINT+1 MAX-UINT MID-UINT+1 WITHIN -> FALSE }
{ MID-UINT+1 MAX-UINT MAX-UINT WITHIN -> FALSE }
{ MAX-UINT 0 0 WITHIN -> FALSE }
{ MAX-UINT 0 MID-UINT WITHIN -> FALSE }
{ MAX-UINT 0 MID-UINT+1 WITHIN -> FALSE }
{ MAX-UINT 0 MAX-UINT WITHIN -> FALSE }
{ MAX-UINT MID-UINT 0 WITHIN -> TRUE }
{ MAX-UINT MID-UINT MID-UINT WITHIN -> FALSE }
{ MAX-UINT MID-UINT MID-UINT+1 WITHIN -> FALSE }
{ MAX-UINT MID-UINT MAX-UINT WITHIN -> FALSE }
{ MAX-UINT MID-UINT+1 0 WITHIN -> TRUE }
{ MAX-UINT MID-UINT+1 MID-UINT WITHIN -> TRUE }
{ MAX-UINT MID-UINT+1 MID-UINT+1 WITHIN -> FALSE }
{ MAX-UINT MID-UINT+1 MAX-UINT WITHIN -> FALSE }
{ MAX-UINT MAX-UINT 0 WITHIN -> TRUE }
{ MAX-UINT MAX-UINT MID-UINT WITHIN -> TRUE }
{ MAX-UINT MAX-UINT MID-UINT+1 WITHIN -> TRUE }
{ MAX-UINT MAX-UINT MAX-UINT WITHIN -> FALSE }

{ MIN-INT MIN-INT MIN-INT WITHIN -> FALSE }
{ MIN-INT MIN-INT 0 WITHIN -> TRUE }
{ MIN-INT MIN-INT 1 WITHIN -> TRUE }
{ MIN-INT MIN-INT MAX-INT WITHIN -> TRUE }
{ MIN-INT 0 MIN-INT WITHIN -> FALSE }
{ MIN-INT 0 0 WITHIN -> FALSE }
{ MIN-INT 0 1 WITHIN -> FALSE }
{ MIN-INT 0 MAX-INT WITHIN -> FALSE }
{ MIN-INT 1 MIN-INT WITHIN -> FALSE }
{ MIN-INT 1 0 WITHIN -> TRUE }
{ MIN-INT 1 1 WITHIN -> FALSE }
{ MIN-INT 1 MAX-INT WITHIN -> FALSE }
{ MIN-INT MAX-INT MIN-INT WITHIN -> FALSE }
{ MIN-INT MAX-INT 0 WITHIN -> TRUE }
{ MIN-INT MAX-INT 1 WITHIN -> TRUE }
{ MIN-INT MAX-INT MAX-INT WITHIN -> FALSE }
{ 0 MIN-INT MIN-INT WITHIN -> FALSE }
{ 0 MIN-INT 0 WITHIN -> FALSE }
{ 0 MIN-INT 1 WITHIN -> TRUE }
{ 0 MIN-INT MAX-INT WITHIN -> TRUE }
{ 0 0 MIN-INT WITHIN -> TRUE }
{ 0 0 0 WITHIN -> FALSE }
{ 0 0 1 WITHIN -> TRUE }
{ 0 0 MAX-INT WITHIN -> TRUE }
{ 0 1 MIN-INT WITHIN -> FALSE }
{ 0 1 0 WITHIN -> FALSE }
{ 0 1 1 WITHIN -> FALSE }
{ 0 1 MAX-INT WITHIN -> FALSE }
{ 0 MAX-INT MIN-INT WITHIN -> FALSE }
{ 0 MAX-INT 0 WITHIN -> FALSE }
{ 0 MAX-INT 1 WITHIN -> TRUE }
{ 0 MAX-INT MAX-INT WITHIN -> FALSE }
{ 1 MIN-INT MIN-INT WITHIN -> FALSE }
{ 1 MIN-INT 0 WITHIN -> FALSE }
{ 1 MIN-INT 1 WITHIN -> FALSE }
{ 1 MIN-INT MAX-INT WITHIN -> TRUE }
{ 1 0 MIN-INT WITHIN -> TRUE }
{ 1 0 0 WITHIN -> FALSE }
{ 1 0 1 WITHIN -> FALSE }
{ 1 0 MAX-INT WITHIN -> TRUE }
{ 1 1 MIN-INT WITHIN -> TRUE }
{ 1 1 0 WITHIN -> TRUE }
{ 1 1 1 WITHIN -> FALSE }
{ 1 1 MAX-INT WITHIN -> TRUE }
{ 1 MAX-INT MIN-INT WITHIN -> FALSE }
{ 1 MAX-INT 0 WITHIN -> FALSE }
{ 1 MAX-INT 1 WITHIN -> FALSE }
{ 1 MAX-INT MAX-INT WITHIN -> FALSE }
{ MAX-INT MIN-INT MIN-INT WITHIN -> FALSE }
{ MAX-INT MIN-INT 0 WITHIN -> FALSE }
{ MAX-INT MIN-INT 1 WITHIN -> FALSE }
{ MAX-INT MIN-INT MAX-INT WITHIN -> FALSE }
{ MAX-INT 0 MIN-INT WITHIN -> TRUE }
{ MAX-INT 0 0 WITHIN -> FALSE }
{ MAX-INT 0 1 WITHIN -> FALSE }
{ MAX-INT 0 MAX-INT WITHIN -> FALSE }
{ MAX-INT 1 MIN-INT WITHIN -> TRUE }
{ MAX-INT 1 0 WITHIN -> TRUE }
{ MAX-INT 1 1 WITHIN -> FALSE }
{ MAX-INT 1 MAX-INT WITHIN -> FALSE }
{ MAX-INT MAX-INT MIN-INT WITHIN -> TRUE }
{ MAX-INT MAX-INT 0 WITHIN -> TRUE }
{ MAX-INT MAX-INT 1 WITHIN -> TRUE }
{ MAX-INT MAX-INT MAX-INT WITHIN -> FALSE }

\ -----------------------------------------------------------------------------
TESTING AGAIN   (contributed by James Bowman)

{ : AG0 701 BEGIN DUP 7 MOD 0= IF EXIT THEN 1+ AGAIN ; -> }
{ AG0 -> 707 }

\ -----------------------------------------------------------------------------
TESTING ?DO

: QD ?DO I LOOP ;
{ 789 789 QD -> }
{ -9876 -9876 QD -> }
{ 5 0 QD -> 0 1 2 3 4 }

: QD1 ?DO I 10 +LOOP ;
{ 50 1 QD1 -> 1 11 21 31 41 }
{ 50 0 QD1 -> 0 10 20 30 40 }

: QD2 ?DO I 3 > IF LEAVE ELSE I THEN LOOP ;
{ 5 -1 QD2 -> -1 0 1 2 3 }

: QD3 ?DO I 1 +LOOP ;
{ 4  4 QD3 -> }
{ 4  1 QD3 -> 1 2 3 }
{ 2 -1 QD3 -> -1 0 1 }

: QD4 ?DO I -1 +LOOP ;
{  4 4 QD4 -> }
{  1 4 QD4 -> 4 3 2 1 }
{ -1 2 QD4 -> 2 1 0 -1 }

: QD5 ?DO I -10 +LOOP ;
{   1 50 QD5 -> 50 40 30 20 10 }
{   0 50 QD5 -> 50 40 30 20 10 0 }
{ -25 10 QD5 -> 10 0 -10 -20 }

VARIABLE ITERS
VARIABLE INCRMNT

: QD6 ( limit start increment -- )
   INCRMNT !
   0 ITERS !
   ?DO
      1 ITERS +!
      I
      ITERS @  6 = IF LEAVE THEN
      INCRMNT @
   +LOOP ITERS @
;

{  4  4 -1 QD6 -> 0 }
{  1  4 -1 QD6 -> 4 3 2 1 4 }
{  4  1 -1 QD6 -> 1 0 -1 -2 -3 -4 6 }
{  4  1  0 QD6 -> 1 1 1 1 1 1 6 }
{  0  0  0 QD6 -> 0 }
{  1  4  0 QD6 -> 4 4 4 4 4 4 6 }
{  1  4  1 QD6 -> 4 5 6 7 8 9 6 }
{  4  1  1 QD6 -> 1 2 3 3 }
{  4  4  1 QD6 -> 0 }
{  2 -1 -1 QD6 -> -1 -2 -3 -4 -5 -6 6 }
{ -1  2 -1 QD6 -> 2 1 0 -1 4 }
{  2 -1  0 QD6 -> -1 -1 -1 -1 -1 -1 6 }
{ -1  2  0 QD6 -> 2 2 2 2 2 2 6 }
{ -1  2  1 QD6 -> 2 3 4 5 6 7 6 }
{  2 -1  1 QD6 -> -1 0 1 3 }

\ -----------------------------------------------------------------------------
TESTING CASE OF ENDOF ENDCASE

: CS1 CASE 1 OF 111 ENDOF
           2 OF 222 ENDOF
           3 OF 333 ENDOF
           >R 999 R>
      ENDCASE
;

{ 1 CS1 -> 111 }
{ 2 CS1 -> 222 }
{ 3 CS1 -> 333 }
{ 4 CS1 -> 999 }

\ Nested CASE's

: CS2 >R CASE -1 OF CASE R@ 1 OF 100 ENDOF
                            2 OF 200 ENDOF
                           >R -300 R>
                    ENDCASE
                 ENDOF
              -2 OF CASE R@ 1 OF -99  ENDOF
                            >R -199 R>
                    ENDCASE
                 ENDOF
                 >R 299 R>
         ENDCASE R> DROP
;

{ -1 1 CS2 ->  100 }
{ -1 2 CS2 ->  200 }
{ -1 3 CS2 -> -300 }
{ -2 1 CS2 -> -99  }
{ -2 2 CS2 -> -199 }
{  0 2 CS2 ->  299 }

\ Boolean short circuiting using CASE

: CS3  ( N1 -- N2 )
   CASE 1- FALSE OF 11 ENDOF
        1- FALSE OF 22 ENDOF
        1- FALSE OF 33 ENDOF
        44 SWAP
   ENDCASE
;

{ 1 CS3 -> 11 }
{ 2 CS3 -> 22 }
{ 3 CS3 -> 33 }
{ 9 CS3 -> 44 }

\ Empty CASE statements with/without default

{ : CS4 CASE ENDCASE ; 1 CS4 -> }
{ : CS5 CASE 2 SWAP ENDCASE ; 1 CS5 -> 2 }
{ : CS6 CASE 1 OF ENDOF 2 ENDCASE ; 1 CS6 -> }
{ : CS7 CASE 3 OF ENDOF 2 ENDCASE ; 1 CS7 -> 1 }

\ -----------------------------------------------------------------------------
TESTING PAD ERASE
\ Must handle different size characters i.e. 1 CHARS >= 1 

84 CONSTANT CHARS/PAD      \ Minimum size of PAD in chars
CHARS/PAD CHARS CONSTANT AUS/PAD
: CHECKPAD  ( caddr u ch -- f )  \ f = TRUE if u chars = ch
   SWAP 0
   ?DO
      OVER I CHARS + C@ OVER <>
      IF 2DROP UNLOOP FALSE EXIT THEN
   LOOP  
   2DROP TRUE
;

{ PAD DROP -> }
{ 0 INVERT PAD C! -> }
{ PAD C@ CONSTANT MAXCHAR -> }
{ PAD CHARS/PAD 2DUP MAXCHAR FILL MAXCHAR CHECKPAD -> TRUE }
{ PAD CHARS/PAD 2DUP CHARS ERASE 0 CHECKPAD -> TRUE }
{ PAD CHARS/PAD 2DUP MAXCHAR FILL PAD 0 ERASE MAXCHAR CHECKPAD -> TRUE }
{ PAD 43 CHARS + 9 CHARS ERASE -> }
{ PAD 43 MAXCHAR CHECKPAD -> TRUE }
{ PAD 43 CHARS + 9 0 CHECKPAD -> TRUE }
{ PAD 52 CHARS + CHARS/PAD 52 - MAXCHAR CHECKPAD -> TRUE }

\ Check that use of WORD and pictured numeric output do not corrupt PAD
\ Minimum size of buffers for these are 33 chars and (2*n)+2 chars respectively
\ where n is number of bits per cell

PAD CHARS/PAD ERASE
2 BASE !
MAX-UINT MAX-UINT <# #S CHAR 1 DUP HOLD HOLD #> 2DROP
DECIMAL
BL WORD 12345678123456781234567812345678 DROP
{ PAD CHARS/PAD 0 CHECKPAD -> TRUE }

\ -----------------------------------------------------------------------------
