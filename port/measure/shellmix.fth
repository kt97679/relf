\ port/measure/shellmix.fth - relfsh's mix in a small standard program (relf Iteration 953, for
\ forth-vm-evolution's question at its 684: does relf lean on TO/VALUE, ['] and DOES> words?).
\
\ relfsh's sources (Makefile's SHELL_SOURCES, 46,096 tokens) have no TO, VALUE or ['], and three DOES>
\ definitions, two of them everywhere: 118 buffers made by pool.4's BUFFER: (CREATE ... DOES> @) and 58
\ hooks made by shadow.4's DEFER (CREATE 0 , DOES> DUP @ 0= IF DROP EXIT THEN @XT EXECUTE). And 634
\ VARIABLEs: in relf VAR@ and its superinstructions, VAR! and 2VAR@ are 20 % of relfsh's dispatches, the
\ deferred calls about 3 %. This program is that mix: shell variables in a hashed table, a script's words
\ expanded through a hook ($NAME looked up and replaced, every other word copied byte by byte), then
\ each line's command run through another hook - set, add (a number read and written back as text),
\ echo (a checksum of the line). Forth 2012 core words, with ?DO and <> from core-ext - not NIP, /STRING
\ or ERASE, which relf's bare kernel lacks - at either cell width; no VALUE, TO or ['] at all. The
\ names HOOK, SET-HOOK and BUFFER: are this program's own. The same line on relf64 and relf32,
\ relfasm64 and gforth 0.7.3.
\
\     gforth shellmix.fth        relf64 forth/kernel64.img < shellmix.fth
\ prints "10000 50005000 <checksum> 80000" for 10000 turns of the script's eight lines.
DECIMAL

: HOOK ( "name" --- )   \ relfsh's DEFER: a no-op until set
  CREATE 0 ,  DOES> DUP @ 0= IF DROP EXIT THEN  @ EXECUTE ;
: SET-HOOK ( xt "name" --- )   ' >BODY ! ;
: BUFFER: ( u "name" --- )   \ relfsh's BUFFER: - the body holds the buffer's address
  CREATE HERE CELL+ , ALLOT  DOES> @ ;

64 CONSTANT #BUCKETS
#BUCKETS CELLS BUFFER: BUCKETS
4096 BUFFER: HEAP     VARIABLE HEAP-USED
64 CONSTANT ENTRY                   \ [link][count, name: 16][count, value: 32]
256 BUFFER: OUT       VARIABLE OUT-LEN
VARIABLE IN-PTR       VARIABLE IN-END
VARIABLE CHECKSUM     VARIABLE LINES

: NAME-HASH ( c-addr u --- h )   5381 SWAP 0 ?DO 33 * OVER I + C@ + LOOP SWAP DROP  #BUCKETS 1- AND ;
: STR= ( c-addr1 u1 c-addr2 u2 --- f )
  ROT OVER <> IF DROP 2DROP 0 EXIT THEN
  0 ?DO OVER I + C@ OVER I + C@ <> IF 2DROP 0 UNLOOP EXIT THEN LOOP 2DROP -1 ;
: ENTRY-NAME ( e --- c-addr u )   CELL+ COUNT ;
: ENTRY-VALUE ( e --- c-addr u )   CELL+ 16 + COUNT ;
: FIND-VAR ( c-addr u --- e | 0 )
  2DUP NAME-HASH CELLS BUCKETS + @
  BEGIN DUP WHILE  >R 2DUP R@ ENTRY-NAME STR= IF 2DROP R> EXIT THEN  R> @  REPEAT
  SWAP DROP SWAP DROP ;
: NEW-VAR ( c-addr u --- e )
  HEAP HEAP-USED @ + >R  ENTRY HEAP-USED +!
  2DUP NAME-HASH CELLS BUCKETS +  DUP @ R@ !  R@ SWAP !
  15 MIN DUP R@ CELL+ C!  R@ CELL+ 1+ SWAP MOVE  0 R@ CELL+ 16 + C!  R> ;
: SET-VAR ( c-addr1 u1 c-addr2 u2 --- )   \ value, name
  2DUP FIND-VAR ?DUP IF >R 2DROP R> ELSE NEW-VAR THEN  >R
  31 MIN DUP R@ CELL+ 16 + C!  R> CELL+ 17 + SWAP MOVE ;

: OUT-C ( c --- )   OUT OUT-LEN @ + C!  OUT-LEN @ 1+ OUT-LEN ! ;
: OUT-S ( c-addr u --- )   0 ?DO DUP I + C@ OUT-C LOOP DROP ;   \ byte by byte, as relfsh copies a word
: SKIP-BL ( --- )
  BEGIN IN-PTR @ IN-END @ < WHILE IN-PTR @ C@ BL = WHILE IN-PTR @ 1+ IN-PTR ! REPEAT THEN ;
: NEXT-WORD ( --- c-addr u )   \ u 0 at the line's end
  SKIP-BL  IN-PTR @
  BEGIN IN-PTR @ IN-END @ < WHILE IN-PTR @ C@ BL <> WHILE IN-PTR @ 1+ IN-PTR ! REPEAT THEN
  IN-PTR @ OVER - ;
: FROM ( c-addr u --- )   OVER + IN-END ! IN-PTR ! ;

HOOK EXPAND-WORD ( c-addr u --- )
HOOK RUN-COMMAND ( --- )
: EXPAND-PLAIN ( c-addr u --- )   OUT-S BL OUT-C ;
: EXPAND-DOLLAR ( c-addr u --- )
  OVER C@ [CHAR] $ = IF  SWAP 1+ SWAP 1- FIND-VAR ?DUP IF ENTRY-VALUE OUT-S THEN  BL OUT-C EXIT  THEN
  EXPAND-PLAIN ;
' EXPAND-DOLLAR SET-HOOK EXPAND-WORD
: EXPAND-LINE ( c-addr u --- )
  FROM  0 OUT-LEN !
  BEGIN NEXT-WORD DUP WHILE EXPAND-WORD REPEAT 2DROP ;

: >NUM ( c-addr u --- n )   0 0 2SWAP >NUMBER 2DROP DROP ;
: NUM> ( n --- c-addr u )   0 <# #S #> ;
: CHECKSUM-OUT ( --- )
  OUT-LEN @ 0 ?DO  OUT I + C@ CHECKSUM @ 31 * + 65535 AND CHECKSUM !  LOOP ;
: RUN ( --- )
  OUT OUT-LEN @ FROM  NEXT-WORD
  2DUP S" echo" STR= IF 2DROP CHECKSUM-OUT EXIT THEN
  2DUP S" set" STR= IF 2DROP NEXT-WORD NEXT-WORD 2SWAP SET-VAR EXIT THEN
  2DUP S" add" STR= IF
    2DROP NEXT-WORD 2DUP FIND-VAR ?DUP IF ENTRY-VALUE >NUM ELSE 0 THEN
    NEXT-WORD >NUM + NUM> 2SWAP SET-VAR EXIT
  THEN 2DROP ;
' RUN SET-HOOK RUN-COMMAND

: LINE ( c-addr u --- )   EXPAND-LINE RUN-COMMAND  1 LINES +! ;
: SCRIPT ( --- )
  S" set greeting hello" LINE
  S" echo $greeting $USER from $HOME in $PWD" LINE
  S" add i 1" LINE
  S" add total $i" LINE
  S" echo $i $total $PATH $SHELL" LINE
  S" set last $i" LINE
  S" echo done $last of $n with $missing" LINE
  S" add n 0" LINE ;
: SETUP ( --- )
  BUCKETS #BUCKETS CELLS 0 FILL  0 HEAP-USED !  0 CHECKSUM !  0 LINES !
  S" /home/relf" S" HOME" SET-VAR   S" relf" S" USER" SET-VAR   S" /bin:/usr/bin" S" PATH" SET-VAR
  S" /bin/relfsh" S" SHELL" SET-VAR   S" /tmp" S" PWD" SET-VAR
  S" 0" S" i" SET-VAR   S" 0" S" total" SET-VAR   S" 10000" S" n" SET-VAR ;
: SHELLMIX ( n --- )
  SETUP  0 ?DO SCRIPT LOOP
  S" i" FIND-VAR ENTRY-VALUE TYPE SPACE  S" total" FIND-VAR ENTRY-VALUE TYPE SPACE
  CHECKSUM @ .  LINES @ . CR ;
10000 SHELLMIX
BYE
