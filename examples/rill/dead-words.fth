\ examples/rill/dead-words.fth - tools/dead-words.py in Forth (Iteration 757)
\
\ The second pilot (docs/PILOT-NATIVE-BY-SOURCE.md), written before its Rill
\ version this time. relf's Forth and Rill's runtime words, loaded with
\ INCLUDED in Rill's image; the files, and --delete or --why WORD, as arguments:
\     printf 'S" examples/rill/dead-words.fth" INCLUDED\n' > /tmp/d.4
\     ./relf64 kernel64-rill.img /tmp/d.4 shell/shell.4 shell/edit.4 shell/tree.4

VARIABLE DELETE?  VARIABLE WHY  VARIABLE FILES  VARIABLE LINES     \ LINES: a record, file -> its lines
VARIABLE N-NAME  VARIABLE N-FILE  VARIABLE N-A  VARIABLE N-B  VARIABLE N-REFS   \ the nodes, a list each
VARIABLE NAMES-NOW  VARIABLE ROOTS  VARIABLE ISL  VARIABLE LAST-IS  VARIABLE REACH  VARIABLE PARENT

: ITEM ( l i --- t )   R-AT R-ANY>TEXT ;
: NUM ( l i --- n )   R-AT R-ANY>NUM ;
: T, ( t l --- )   SWAP K-TEXT R-BOX SWAP R-PUSH ;
: N, ( n l --- )   SWAP K-NUM R-BOX SWAP R-PUSH ;
: ITEMS ( l --- addr n )   DUP R-ITEMS SWAP R-LEN ;    \ the box array and its length
: T= ( t c-addr u --- f )   R-TEXT R-T= ;

\ a file's lines as Python's split('\n') has them: a last empty one kept
: SPLIT-NL ( t --- l )
  R-NEW-LIST >R  R-T@
  BEGIN  2DUP 10 SCAN  2SWAP DROP 2 PICK OVER - R-TEXT R@ T,  DUP WHILE 1 /STRING  REPEAT  2DROP R> ;

\ a line's words, comments and string literals out - the string's own word kept
: QWORD? ( c-addr u --- f )   \ S" ." ABORT" C" - a word whose string ends at a quote
  DUP 0= IF 2DROP 0 EXIT THEN  2DUP + 1- C@ 34 <> IF 2DROP 0 EXIT THEN  1-
  2DUP S" S" COMPARE 0= >R 2DUP S" ." COMPARE 0= >R 2DUP S" ABORT" COMPARE 0= >R S" C" COMPARE 0= R> OR R> OR R> OR ;
: CLOSER ( t --- c | 0 )   R-T@ 2DUP QWORD? IF 2DROP 34 EXIT THEN  S" .(" COMPARE 0= IF 41 ELSE 0 THEN ;
: ENDS-WITH? ( t c --- f )   SWAP R-T@ DUP IF + 1- C@ = ELSE 2DROP DROP 0 THEN ;
VARIABLE TK-OUT  VARIABLE TK-IN  VARIABLE TK-C
: SKIP-TO ( i --- i' )   \ past the first word from i on that ends with TK-C
  BEGIN DUP TK-IN @ R-LEN < IF TK-IN @ OVER ITEM TK-C @ ENDS-WITH? 0= ELSE 0 THEN WHILE 1+ REPEAT 1+ ;
: TOKENS ( line --- l )
  R-SPLIT-WS TK-IN !  R-NEW-LIST TK-OUT !  0
  BEGIN DUP TK-IN @ R-LEN < WHILE
    TK-IN @ OVER ITEM                                              ( i t )
    DUP S" \" T= IF 2DROP TK-OUT @ EXIT THEN
    DUP S" (" T= IF DROP 41 TK-C ! SKIP-TO ELSE
    DUP CLOSER ?DUP IF TK-C ! TK-OUT @ T, 1+ SKIP-TO ELSE TK-OUT @ T, 1+ THEN THEN
  REPEAT DROP TK-OUT @ ;

\ the nodes: a definition each, with what it refers to as the names stood then
: RESOLVE ( toks --- ids )   \ the nodes the words name now
  R-NEW-LIST SWAP DUP R-LEN 0 ?DO
    DUP I ITEM DUP NAMES-NOW @ R-HAS IF NAMES-NOW @ R-GET R-ANY>NUM 2 PICK N, ELSE DROP THEN
  LOOP DROP ;
: NEW-NODE ( name f a b body --- )
  RESOLVE K-LIST R-BOX N-REFS @ R-PUSH  N-B @ N,  N-A @ N,  N-FILE @ T,  DUP N-NAME @ T,
  N-NAME @ R-LEN 1- K-NUM R-BOX SWAP NAMES-NOW @ R-PUT ;

\ reading the files in load order
: DEFINER? ( t --- f )
  DUP S" BUFFER:" R-TEXT R-ENDS IF DROP -1 EXIT THEN  R-T@
  2DUP S" VARIABLE" COMPARE 0= >R 2DUP S" CONSTANT" COMPARE 0= >R 2DUP S" CREATE" COMPARE 0= >R
  2DUP S" DEFER" COMPARE 0= >R 2DUP S" VALUE" COMPARE 0= >R S" 2VARIABLE" COMPARE 0= R> OR R> OR R> OR R> OR R> OR ;
: ROOTS+ ( toks --- )   RESOLVE ROOTS @ SWAP R-EXTEND ;
VARIABLE L  VARIABLE F  VARIABLE TT  VARIABLE CI  VARIABLE CBODY
: SEMI? ( toks --- f )   S" ;" R-TEXT K-TEXT R-BOX SWAP R-IN ;
: COLON ( --- )   \ ': name ...' from line CI to its ';' - CI left where the original's i is
  TT @ 1 ITEM  CI @  TT @ 2 OVER R-LEN R-SLICE CBODY !
  BEGIN CBODY @ SEMI? 0= IF 1 CI +! CI @ L @ R-LEN < ELSE 0 THEN WHILE
    CBODY @ L @ CI @ ITEM TOKENS R-EXTEND
  REPEAT
  F @ SWAP CI @ CBODY @ NEW-NODE ;
: IS-LINE ( --- )   \ "' X IS Y": X reachable only through Y
  TT @ 1 ITEM NAMES-NOW @ R-HAS  TT @ 3 ITEM NAMES-NOW @ R-HAS AND IF
    R-NEW-LIST  F @ OVER T,  CI @ OVER N,
    TT @ 1 ITEM NAMES-NOW @ R-GET R-ANY>NUM OVER N,  TT @ 3 ITEM NAMES-NOW @ R-GET R-ANY>NUM OVER N,
    K-LIST R-BOX ISL @ R-PUSH
  THEN ;
: OTHER-LINE ( --- )   \ a definer and its name - or a top-level line, whose words are roots
  TT @ R-LEN 0 ?DO
    TT @ I ITEM DEFINER? I 1+ TT @ R-LEN < AND IF
      TT @ I 2 + TT @ R-LEN R-SLICE ROOTS+
      TT @ I 1+ ITEM  F @  CI @ DUP  TT @ 0 I 1+ R-SLICE  NEW-NODE
      UNLOOP EXIT
    THEN
  LOOP  TT @ ROOTS+ ;
: READ-SOURCE ( f --- )
  DUP F !  DUP R-READ SPLIT-NL DUP L !  K-LIST R-BOX SWAP LINES @ R-PUT
  0 CI !
  BEGIN CI @ L @ R-LEN < WHILE
    L @ CI @ ITEM TOKENS TT !
    TT @ R-LEN 1 > IF TT @ 0 ITEM S" :" T= ELSE 0 THEN IF COLON ELSE
    TT @ R-LEN 3 > IF TT @ 0 ITEM S" '" T= TT @ 2 ITEM S" IS" T= AND ELSE 0 THEN IF IS-LINE ELSE
    OTHER-LINE THEN THEN
    1 CI +!
  REPEAT ;

\ what the roots reach - breadth first, each node's parent kept for --why
VARIABLE TODO  VARIABLE HEAD  VARIABLE NN
: REACH? ( n --- f )   CELLS REACH @ + @ ;
: PARENT@ ( n --- p )   CELLS PARENT @ + @ ;
: WALK-GRAPH ( --- )
  N-NAME @ R-LEN NN !  NN @ 1 MAX CELLS R-ALLOT REACH !  REACH @ NN @ CELLS ERASE
  NN @ 1 MAX CELLS R-ALLOT PARENT !  NN @ 0 ?DO -2 I CELLS PARENT @ + ! LOOP
  R-NEW-LIST TODO !  ROOTS @ R-LEN 0 ?DO ROOTS @ I NUM DUP TODO @ N, -1 SWAP CELLS PARENT @ + ! LOOP
  0 HEAD !
  BEGIN HEAD @ TODO @ R-LEN < WHILE
    TODO @ HEAD @ NUM  1 HEAD +!
    DUP REACH? IF DROP ELSE
      -1 OVER CELLS REACH @ + !
      N-REFS @ OVER R-AT R-UNBOX DROP
      DUP R-LEN 0 ?DO DUP I NUM
        DUP REACH? 0= OVER PARENT@ -2 = AND IF 2 PICK OVER CELLS PARENT @ + !  TODO @ N, ELSE DROP THEN
      LOOP 2DROP
    THEN
  REPEAT ;
: IS-LAST ( --- )   \ each Y's last IS line, and Y reaching its X through it
  R-NEW-RECORD LAST-IS !
  ISL @ R-LEN 0 ?DO ISL @ I R-AT  DUP R-UNBOX DROP 3 NUM R-NUM LAST-IS @ R-PUT LOOP
  LAST-IS @ R-VALS R-LEN 0 ?DO
    LAST-IS @ R-VALS I R-AT R-UNBOX DROP  DUP 2 NUM SWAP 3 NUM  N-REFS @ SWAP R-AT R-UNBOX DROP N,
  LOOP ;

\ the report
: KEY-CMP ( a b --- n )   \ the nodes compared as Python's tuples (file, line, name)
  OVER N-FILE @ SWAP ITEM R-T@ 2 PICK N-FILE @ SWAP ITEM R-T@ COMPARE ?DUP IF NIP NIP EXIT THEN
  OVER N-A @ SWAP NUM OVER N-A @ SWAP NUM 2DUP <> IF > IF 1 ELSE -1 THEN NIP NIP EXIT THEN 2DROP
  N-NAME @ SWAP ITEM R-T@ ROT N-NAME @ SWAP ITEM R-T@ 2SWAP COMPARE ;
VARIABLE DEAD  VARIABLE DIX
: D@ ( k --- n )   CELLS DIX @ + @ ;
: D! ( n k --- )   CELLS DIX @ + ! ;
: SORT-DEAD ( --- )   \ DIX: the unreachable nodes, sorted
  0 NN @ 0 ?DO I REACH? 0= IF 1+ THEN LOOP DEAD !
  DEAD @ 1 MAX CELLS R-ALLOT DIX !  0 NN @ 0 ?DO I REACH? 0= IF I OVER D! 1+ THEN LOOP DROP
  DEAD @ 1 MAX 1 ?DO
    I D@ I  BEGIN DUP 0> IF OVER OVER 1- D@ KEY-CMP 0< ELSE 0 THEN WHILE DUP 1- D@ OVER D! 1- REPEAT  D!
  LOOP ;
: .LN ( n --- )   0 <# #S #> TYPE ;
: DEAD-IS? ( e --- f )   \ an IS line whose Y is unreachable, or not Y's last
  DUP R-UNBOX DROP 3 NUM DUP REACH? 0= IF 2DROP -1 EXIT THEN
  R-NUM LAST-IS @ R-GET <> ;
: REPORT ( --- n )   \ the dead IS lines counted
  DEAD @ 0 ?DO I D@ DUP N-FILE @ SWAP ITEM R-TYPE ." :" DUP N-A @ SWAP NUM 1+ .LN ." : " N-NAME @ SWAP ITEM R-TYPE R-NL LOOP
  0 ISL @ R-LEN 0 ?DO ISL @ I R-AT DUP DEAD-IS? IF
      R-UNBOX DROP  DUP 0 ITEM R-TYPE ." :" DUP 1 NUM 1+ .LN ." : IS line  "
      DUP 2 NUM N-NAME @ SWAP ITEM R-TYPE ."  -> " 3 NUM N-NAME @ SWAP ITEM R-TYPE R-NL  1+
    ELSE DROP THEN LOOP ;
: WHY-CHAIN ( --- )   \ --why WORD: each node of that name, back along its parents
  NN @ 0 ?DO N-NAME @ I ITEM WHY @ R-T= IF
    0 I
    BEGIN DUP 0< 0= IF DUP PARENT@ -2 <> ELSE 0 THEN 2 PICK 40 < AND WHILE
      OVER IF ."  <- " THEN
      DUP N-NAME @ SWAP ITEM R-TYPE ." @" DUP N-FILE @ SWAP ITEM R-TYPE ." :" DUP N-A @ SWAP NUM 1+ .LN
      PARENT@ SWAP 1+ SWAP
    REPEAT 2DROP
    I PARENT@ -2 = IF ."   (unreachable)" THEN R-NL
  THEN LOOP ;

\ --delete: each unreachable definition out with the comment lines just above it; the dead IS lines
VARIABLE KILLS  VARIABLE BLANK
: FILE-LINES ( f --- l )   LINES @ R-GET R-UNBOX DROP ;
: KILL-LINES ( f a b --- )   ROT KILLS @ R-GET R-ANY>NUM -ROT 1+ SWAP ?DO -1 OVER I CELLS + ! LOOP DROP ;
: WRITE-BACK ( f --- )   \ the lines not killed, a run of blank lines kept as one
  DUP KILLS @ R-GET R-ANY>NUM  OVER FILE-LINES  R-NEW-LIST  0 BLANK !
  OVER R-LEN 0 ?DO
    2 PICK I CELLS + @ 0= IF
      OVER I ITEM DUP R-TRIM @ 0= IF BLANK @ IF DROP ELSE -1 BLANK ! OVER T, THEN ELSE 0 BLANK ! OVER T, THEN
    THEN
  LOOP  NIP NIP  10 1 R-BYTES R-JOIN R-WRITE ;
: DELETE ( --- )
  R-NEW-RECORD KILLS !
  FILES @ R-LEN 0 ?DO
    FILES @ I ITEM DUP FILE-LINES R-LEN 1 MAX CELLS R-ALLOT
    DUP 2 PICK FILE-LINES R-LEN CELLS ERASE  K-NUM R-BOX SWAP KILLS @ R-PUT
  LOOP
  NN @ 0 ?DO I REACH? 0= IF
    N-FILE @ I ITEM  N-A @ I NUM
    BEGIN DUP 0> IF OVER FILE-LINES OVER 1- ITEM R-TRIM S" \" R-TEXT R-STARTS ELSE 0 THEN WHILE 1- REPEAT
    N-B @ I NUM KILL-LINES
  THEN LOOP
  ISL @ R-LEN 0 ?DO ISL @ I R-AT DUP DEAD-IS? IF R-UNBOX DROP DUP 0 ITEM SWAP 1 NUM DUP KILL-LINES ELSE DROP THEN LOOP
  FILES @ R-LEN 0 ?DO FILES @ I ITEM WRITE-BACK LOOP ;

: READ-ARGS ( --- )   \ the files; --delete; --why WORD
  R-ARGS  0 DELETE? !  0 WHY !  R-NEW-LIST FILES !
  0 BEGIN DUP 2 PICK R-LEN < WHILE
    2DUP ITEM
    DUP S" --delete" T= IF DROP -1 DELETE? ! ELSE
    DUP S" --why" T= IF DROP 1+ 2DUP ITEM WHY ! ELSE FILES @ T, THEN THEN
    1+
  REPEAT 2DROP ;
: MAIN ( --- )
  READ-ARGS  R-NEW-RECORD LINES !  R-NEW-RECORD NAMES-NOW !  R-NEW-LIST ROOTS !  R-NEW-LIST ISL !
  R-NEW-LIST N-NAME !  R-NEW-LIST N-FILE !  R-NEW-LIST N-A !  R-NEW-LIST N-B !  R-NEW-LIST N-REFS !
  FILES @ R-LEN 0 ?DO FILES @ I ITEM READ-SOURCE LOOP
  S" MAIN" R-TEXT NAMES-NOW @ R-HAS IF S" MAIN" R-TEXT NAMES-NOW @ R-GET ROOTS @ R-PUSH THEN
  IS-LAST WALK-GRAPH
  WHY @ IF WHY-CHAIN EXIT THEN
  SORT-DEAD REPORT >R
  DEAD @ R-NUM  S"  unreachable definitions, " R-TEXT  R> R-NUM  S"  dead IS lines, " R-TEXT
  0 NN @ 0 ?DO I REACH? IF 1+ THEN LOOP R-NUM  S"  reachable" R-TEXT  6 R-CONCAT R-ERR-TYPE
  DELETE? @ IF DELETE THEN ;
MAIN

