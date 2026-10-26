\ examples/rill/native-by-source.fth - tools/size-research/native-by-source.py in Forth (Iteration 756)
\
\ The three-way pilot's Forth version (docs/PILOT-NATIVE-BY-SOURCE.md): relf's
\ Forth and Rill's runtime words - texts, lists, records, regular expressions
\ (rill/rt.4, rill/regex.4) - as the protocol allows, so the comparison weighs
\ the languages, not a library. Run in Rill's image, loaded line by line:
\     printf 'S" examples/rill/native-by-source.fth" INCLUDED\n' > /tmp/d.4
\     ./relf64 kernel64-rill.img /tmp/d.4

VARIABLE WORDS  VARIABLE ON  VARIABLE WHERE  VARIABLE BYFILE  VARIABLE BYSEC  VARIABLE TOT
VARIABLE M  VARIABLE LS  VARIABLE FILE  VARIABLE SECTION

: .R ( n width --- )   >R DUP ABS 0 <# #S ROT SIGN #> R> OVER - 0 MAX SPACES TYPE ;
: LJ ( c-addr u width --- )   OVER - 0 MAX >R TYPE R> SPACES ;
: RJ ( c-addr u width --- )   OVER - 0 MAX SPACES TYPE ;
: ITEM ( l i --- t )   R-AT R-ANY>TEXT ;
CREATE UP-BUF 256 ALLOT
: UPPER ( t --- t' )   \ a name upper case, as the original's .upper() - R-UPPER left the runtime at 799 (829)
  R-T@ 255 MIN >R  UP-BUF R@ MOVE
  R@ 0 ?DO UP-BUF I + C@ DUP [CHAR] a [CHAR] z 1+ WITHIN IF 32 - THEN UP-BUF I + C! LOOP  UP-BUF R> R-TEXT ;

\ 1. each word's bytes and instruction classes, from native-budget.py's dump
: WORD-LINE ( t --- )   \ a line of the dump into WORDS: [bytes c0 .. c5] under the word's name
  S" ^\s+(\d+)\s+(\S+)\s+(\d+) (\d+) (\d+) (\d+) (\d+) (\d+)" R-TEXT R-MATCH M !
  M @ R-LEN 0= IF EXIT THEN
  R-NEW-LIST  M @ 1 ITEM R-NUMBER K-NUM R-BOX OVER R-PUSH
  9 3 DO  M @ I ITEM R-NUMBER K-NUM R-BOX OVER R-PUSH  LOOP
  K-LIST R-BOX  M @ 2 ITEM UPPER  WORDS @ R-PUT ;
: READ-WORDS ( --- )
  R-NEW-RECORD WORDS !  0 ON !
  S" /tmp/sz/budget-all.txt" R-TEXT R-READ R-LINES
  DUP R-LEN 0 ?DO  DUP I ITEM
    DUP S" the 3000 largest words" R-TEXT R-STARTS IF DROP -1 ON ! ELSE ON @ IF WORD-LINE ELSE DROP THEN THEN
  LOOP DROP ;

\ 2. where each word is defined: its file, and the section of the file
: RULE? ( i --- f )   LS @ SWAP ITEM S" \ ====" R-TEXT R-STARTS ;
: HEADER? ( i --- f )   \ a rule here and two lines on, as the original sees a header
  DUP RULE? 0= IF DROP 0 EXIT THEN  2 + DUP LS @ R-LEN < IF RULE? ELSE DROP 0 THEN ;
: DEFINED ( code --- )   \ the names a line defines, each into WHERE with the file and the section
  S" (?:^|\s)(?::|CODE|NCODE|VARIABLE|2VARIABLE|CONSTANT|VALUE|CREATE|DEFER|BUFFER:)\s+(\S+)" R-TEXT R-ALL
  DUP R-LEN 0 ?DO
    R-NEW-LIST FILE @ K-TEXT R-BOX OVER R-PUSH SECTION @ K-TEXT R-BOX OVER R-PUSH K-LIST R-BOX
    OVER I ITEM UPPER  WHERE @ R-PUT
  LOOP DROP ;
: WALK ( file --- )   \ one source, line by line; three lines on after a header, as the original
  FILE !  S" (start)" R-TEXT SECTION !
  S" /home/claude/relf/" R-TEXT FILE @ 2 R-CONCAT R-READ R-LINES LS !
  0 BEGIN DUP LS @ R-LEN < WHILE
    DUP HEADER? IF
      DUP 1+ LS @ SWAP ITEM S" ^[\\ ]*" R-TEXT S" " R-TEXT R-SUB R-TRIM 0 60 R-TSLICE SECTION !  3 +
    ELSE
      DUP LS @ SWAP ITEM  S" \\ .*$|\\$" R-TEXT S" " R-TEXT R-SUB  S" \( [^)]*\)" R-TEXT S" " R-TEXT R-SUB
      DEFINED  1+
    THEN
  REPEAT DROP ;

\ 3. the bytes, the words and the classes by file, and by section of the shell's files
VARIABLE AV  VARIABLE AK  VARIABLE AR
: BUMP ( n entry i --- )   2DUP R-AT R-ANY>NUM >R ROT R> + K-NUM R-BOX -ROT R-SET ;   \ entry[i] += n
: ADD ( vals key rec --- )   \ the entry for key, [bytes n c0 .. c5], made if new, the word added to it
  AR ! AK ! AV !
  AK @ AR @ R-HAS 0= IF R-NEW-LIST 8 0 DO 0 K-NUM R-BOX OVER R-PUSH LOOP K-LIST R-BOX AK @ AR @ R-PUT THEN
  AK @ AR @ R-GET R-UNBOX DROP                                    ( entry )
  AV @ 0 R-AT R-ANY>NUM OVER 0 BUMP   1 OVER 1 BUMP
  6 0 DO  AV @ I 1+ R-AT R-ANY>NUM OVER I 2 + BUMP  LOOP DROP ;
: AGGREGATE ( --- )
  R-NEW-RECORD BYFILE !  R-NEW-RECORD BYSEC !
  WORDS @ R-KEYS R-LEN 0 ?DO
    WORDS @ R-KEYS I ITEM                                         ( w )
    DUP WHERE @ R-HAS IF DUP WHERE @ R-GET R-UNBOX DROP DUP 0 ITEM SWAP 1 ITEM
    ELSE S" kernel" R-TEXT S" " R-TEXT THEN                        ( w f s )
    ROT S" (RUNTIME)" R-TEXT R-T= IF 2DROP S" runtime" R-TEXT S" " R-TEXT THEN
    WORDS @ R-VALS I R-AT R-UNBOX DROP                            ( f s vals )
    DUP 3 PICK BYFILE @ ADD
    2 PICK S" shell/" R-TEXT R-STARTS IF -ROT S"  " R-TEXT SWAP 3 R-CONCAT BYSEC @ ADD ELSE DROP 2DROP THEN
  LOOP ;

\ 4. the report: largest first, ties in the order they came (Counter.most_common's)
VARIABLE SR  VARIABLE SN  VARIABLE SIX  VARIABLE E  VARIABLE PD
: S@ ( k --- i )   CELLS SIX @ + @ ;
: S! ( i k --- )   CELLS SIX @ + ! ;
: SKEY ( i --- n )   SR @ R-VALS SWAP R-AT R-UNBOX DROP 0 R-AT R-ANY>NUM ;
: SORT-DESC ( rec --- )   \ SIX: the entries' indexes by bytes, largest first, stable
  DUP SR !  R-KEYS R-LEN SN !  SN @ CELLS R-ALLOT SIX !  SN @ 0 ?DO I I S! LOOP
  SN @ 1 MAX 1 ?DO
    I S@ I  BEGIN DUP 0> IF OVER SKEY OVER 1- S@ SKEY > ELSE 0 THEN WHILE DUP 1- S@ OVER S! 1- REPEAT  S!
  LOOP ;
: E@ ( k --- n )   E @ SWAP R-AT R-ANY>NUM ;
: ROUND10 ( num den --- tenths )   \ 1000 num / den, to the nearest, half to even (%.1f's way)
  DUP PD !  >R 1000 * R> /MOD  SWAP 2* PD @  2DUP > IF 2DROP 1+ EXIT THEN  = IF DUP 1 AND + THEN ;
: PCT. ( num den width --- )   >R ROUND10 0 <# # [CHAR] . HOLD #S #> R> RJ ;
: FILE-LINE ( k --- )   \ '  %-28s %7d  %5.1f %%  %4d words   stack %4.1f %%  call %4.1f %%'
  DUP BYFILE @ R-KEYS SWAP ITEM  SWAP BYFILE @ R-VALS SWAP R-AT R-UNBOX DROP E !
  ."   " R-T@ 28 LJ SPACE  0 E@ 7 .R  2 SPACES  0 E@ TOT @ 5 PCT. ."  %  "  1 E@ 4 .R
  ."  words   stack "  3 E@ 0 E@ 1 MAX 4 PCT. ."  %  call "  2 E@ 0 E@ 1 MAX 4 PCT. ."  %" R-NL ;
: SEC-LINE ( k --- )   \ '  %7d %4d  %-14s %s': the file's name after its /, the section after the blank
  DUP BYSEC @ R-KEYS SWAP ITEM  SWAP BYSEC @ R-VALS SWAP R-AT R-UNBOX DROP E !
  ."   " 0 E@ 7 .R SPACE 1 E@ 4 .R 2 SPACES
  R-T@ 2DUP BL SCAN 2SWAP DROP 2 PICK OVER -  [CHAR] / SCAN 1 /STRING 14 LJ SPACE  1 /STRING TYPE R-NL ;
: MAIN ( --- )
  READ-WORDS  R-NEW-RECORD WHERE !
  S" forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 forth/save-system-native.4 shell/shell.4 shell/edit.4 shell/tree.4"
  R-TEXT R-SPLIT-WS  DUP R-LEN 0 ?DO DUP I ITEM WALK LOOP DROP
  AGGREGATE
  0 BYFILE @ R-VALS DUP R-LEN 0 ?DO DUP I R-AT R-UNBOX DROP 0 R-AT R-ANY>NUM ROT + SWAP LOOP DROP TOT !
  ." total code " TOT @ 0 .R ."  bytes in " WORDS @ R-KEYS R-LEN 0 .R ."  words" R-NL
  BYFILE @ SORT-DESC  SN @ 0 ?DO I S@ FILE-LINE LOOP
  R-NL ." shell sections, largest first:" R-NL
  BYSEC @ SORT-DESC  SN @ 60 MIN 0 ?DO I S@ SEC-LINE LOOP ;
MAIN
