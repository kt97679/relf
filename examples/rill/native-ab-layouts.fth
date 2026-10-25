\ examples/rill/native-ab-layouts.fth - tools/native-ab-layouts.py in Forth (Iteration 761)
\
\ The third pilot's Forth version, written after its Rill version
\ (docs/PILOT-NATIVE-BY-SOURCE.md). relf's Forth and Rill's runtime words:
\ commands through its pipeline words (PL-BEGIN, PL-STAGE, PL-END), texts,
\ lists, records, regular expressions, log and exp. Loaded with INCLUDED in
\ Rill's image, BASE-REV ROUNDS PADS as its arguments, as the original's.

VARIABLE ROOT  VARIABLE BASE-REV  VARIABLE ROUNDS  VARIABLE PADS  VARIABLE WL  VARIABLE SCALE
VARIABLE OUTD  VARIABLE MARK  VARIABLE WT  VARIABLE B  VARIABLE N  VARIABLE RATIO  VARIABLE NWL

: T ( c-addr u --- t )   R-TEXT ;
: T+ ( t1 t2 --- t )   2 R-CONCAT ;
: ITEM ( l i --- t )   R-AT R-ANY>TEXT ;
: RUN? ( t1 .. tn n --- status )   >R 0 PL-BEGIN R> -1 PL-STAGE PL-END ;     \ a command; its status
: RUN ( t1 .. tn n --- )   RUN? R-CHECK ;                                   \ ... failure stops the script
: CAPTURE ( t1 .. tn n --- t )   >R -1 PL-BEGIN R> -1 PL-STAGE PL-END R-CHECK ;   \ what it printed
: DIE ( t --- )   R-FAIL ;                                                    \ sys.exit(message)
: ARG-OR ( n c-addr u --- t )   R-TEXT SWAP R-ARG SWAP R-DEFAULT ;

\ the kernel with p bytes of target space before its runtime, built in tree
: KCUT ( --- status )   \ the original's KCUT: each step only if the last went well
  S" python3" T S" tools/gen-native-os.py" T S" native-os.4" T 3 RUN? ?DUP IF EXIT THEN
  0 PL-BEGIN S" native-kcut9.4" T W/O 1 R-RD-FILE
  S" sed" T S" /^\\ PART 10: TOP LEVEL/,$d" T S" forth/kernel.4" T 3 -1 PL-STAGE PL-END ?DUP IF EXIT THEN
  0 PL-BEGIN S" native-kcut9.4" T A/O 1 R-RD-FILE  S" echo" T S" END-CROSS" T 2 -1 PL-STAGE PL-END ?DUP IF EXIT THEN
  0 PL-BEGIN S" native-kcut10.4" T W/O 1 R-RD-FILE  S" echo" T S" CROSS-COMPILE" T 2 -1 PL-STAGE PL-END DROP
  0 PL-BEGIN S" native-kcut10.4" T A/O 1 R-RD-FILE
  S" sed" T S" -n" T S" /^\\ PART 10: TOP LEVEL/,$p" T S" forth/kernel.4" T 4 -1 PL-STAGE PL-END ?DUP IF EXIT THEN
  S" rm" T S" -f" T S" native-kernel" T 3 RUN? ?DUP IF EXIT THEN
  0 PL-BEGIN S" native-kernel-padded.4" T R/O 0 R-RD-FILE  S" native-kernel.log" T W/O 1 R-RD-FILE  1 2 R-RD-DUP
  S" ./relf64" T S" forth/kernel64.img" T 2 -1 PL-STAGE PL-END ;
VARIABLE KT  VARIABLE KP
: KERNEL ( tree p --- )
  KP ! KT !
  KT @ S" /forth/native-kernel.4" T T+ R-READ
  DUP MARK @ R-CONTAINS 0= IF DROP S" native-ab-layouts: " T KT @ T+ S" : native-kernel.4 has no runtime line to pad before" T T+ DIE THEN
  MARK @  KP @ R-NUM S"  DP-T +!   \ layout pad (688)" T T+ 10 1 R-BYTES T+ MARK @ T+  R-REPLACE
  KT @ S" /native-kernel-padded.4" T T+ SWAP R-WRITE
  R-CWD-PUSH KT @ R-CD
  KCUT DROP  S" test" T S" -x" T S" native-kernel" T 3 RUN?
  S" rm" T S" -f" T S" native-kernel-padded.4" T 3 RUN
  R-CWD-POP
  IF S" native-ab-layouts: " T KT @ T+ S" : kernel pad " T T+ KP @ R-NUM T+ S"  not built" T T+ DIE THEN ;

\ a shell per pad, each with the kernel padded alike: [name path] pairs
: EXISTS? ( t --- f )   R-T@ R/O OPEN-FILE IF DROP 0 ELSE CLOSE-FILE DROP -1 THEN ;
VARIABLE ST  VARIABLE STAG  VARIABLE SMADE
: SHELLS ( tree tag --- l )
  STAG ! ST !  R-NEW-LIST SMADE !
  PADS @ R-LEN 0 ?DO
    ST @ PADS @ I ITEM R-NUMBER KERNEL
    OUTD @ S" /" T T+ STAG @ T+ S" -p" T T+ PADS @ I ITEM T+
    R-CWD-PUSH ST @ R-CD
    S" NATIVE_LAYOUT_PAD=" T PADS @ I ITEM T+  S" sh" T  ROOT @ S" /tools/build-native-shell.sh" T T+  3 PICK  4 RUN?
    R-CWD-POP
    OVER EXISTS? 0= OR IF DROP S" native-ab-layouts: " T STAG @ T+ S"  pad " T T+ PADS @ I ITEM T+ S"  not built" T T+ DIE THEN
    R-NEW-LIST  STAG @ S" -p" T T+ PADS @ I ITEM T+ K-TEXT R-BOX OVER R-PUSH  SWAP K-TEXT R-BOX OVER R-PUSH
    K-LIST R-BOX SMADE @ R-PUSH
  LOOP SMADE @ ;

\ the base in a scratch worktree, then the checkout; the original's finally after
: BUILD-BOTH ( --- )
  R-CWD-PUSH WT @ R-CD  S" make" T S" -s" T S" native-kernel" T 3 RUN?  R-CWD-POP
  IF S" native-ab-layouts: " T BASE-REV @ T+ S" : no native kernel" T T+ DIE THEN
  WT @ S" base" T SHELLS B !  ROOT @ S" now" T SHELLS N ! ;
: CLEANUP ( --- )   \ the checkout's own kernel back, unpadded; the worktree gone
  ROOT @ R-CD
  S" rm" T S" -f" T S" native-kernel" T 3 RUN? 0= IF S" make" T S" -s" T S" native-kernel" T 3 RUN? DROP THEN
  S" git" T S" worktree" T S" remove" T S" --force" T WT @ 5 RUN? DROP  S" git" T S" worktree" T S" prune" T 3 RUN? DROP ;

\ the bench, and what it says of each configuration
: CONFIGS ( --- l )   R-NEW-LIST DUP B @ R-EXTEND DUP N @ R-EXTEND ;
: CONFIG? ( t --- f )
  CONFIGS DUP R-LEN 0 ?DO DUP I R-AT R-UNBOX DROP 0 ITEM 2 PICK R-T= IF 2DROP -1 UNLOOP EXIT THEN LOOP 2DROP 0 ;
: WRITE-CFG ( --- )   \ name|/tmp|path {w}, a line each
  R-NEW-LIST  CONFIGS DUP R-LEN 0 ?DO
    DUP I R-AT R-UNBOX DROP  DUP 0 ITEM S" |/tmp|" T T+ SWAP 1 ITEM T+ S"  {w}" T T+ 10 1 R-BYTES T+
    K-TEXT R-BOX 2 PICK R-PUSH
  LOOP DROP  OUTD @ S" /cfg" T T+ SWAP S" " T R-JOIN R-WRITE ;
: BENCH ( --- t )   \ its output, whatever its status - as the original
  S" SCALE=" T SCALE @ T+  S" WL=" T WL @ T+  S" python3" T S" tools/bench-vm.py" T  ROUNDS @  OUTD @ S" /cfg" T T+
  >R >R >R >R >R >R  -1 PL-BEGIN  R> R> R> R> R> R>  6 -1 PL-STAGE PL-END DROP ;
: READ-BENCH ( res --- )   \ RATIO: each configuration's ratios, decimals; the first base's ones until the bench says
  R-NEW-RECORD RATIO !
  R-NEW-LIST NWL @ 0 ?DO 1000000 K-DEC R-BOX OVER R-PUSH LOOP K-LIST R-BOX  B @ 0 R-AT R-UNBOX DROP 0 ITEM RATIO @ R-PUT
  10 1 R-BYTES R-SPLIT DUP R-LEN 0 ?DO
    DUP I ITEM DUP R-SPLIT-WS DUP R-LEN IF 0 ITEM  DUP CONFIG? IF
        SWAP S" (\d+\.\d+)\s*\[" T R-ALL DUP R-LEN NWL @ = IF
          R-NEW-LIST SWAP DUP R-LEN 0 ?DO DUP I ITEM R-TEXT>DEC K-DEC R-BOX 2 PICK R-PUSH LOOP DROP
          K-LIST R-BOX SWAP RATIO @ R-PUT
        ELSE 2DROP THEN
      ELSE 2DROP THEN
    ELSE 2DROP THEN
  LOOP DROP
  CONFIGS DUP R-LEN 0 ?DO DUP I R-AT R-UNBOX DROP 0 ITEM DUP RATIO @ R-HAS IF DROP ELSE
    S" native-ab-layouts: no result for " T SWAP T+ DIE THEN LOOP DROP ;

\ the table: per workload, each side's spread over its layouts, and the ratio of their geometric means
: LJ ( c-addr u width --- )   OVER - 0 MAX >R TYPE R> SPACES ;
: .DEC3 ( d --- )   500 + 1000 / 0 <# # # # [CHAR] . HOLD #S #> TYPE ;
VARIABLE SK  VARIABLE VMIN  VARIABLE VMAX  VARIABLE VLOG
: SIDE ( pairs --- gm )   \ VMIN and VMAX of the SK-th ratios over a side's layouts; their geometric mean
  0 VLOG !  -1 1 RSHIFT VMIN !  0 VMAX !
  DUP R-LEN 0 ?DO
    DUP I R-AT R-UNBOX DROP 0 ITEM RATIO @ R-GET R-UNBOX DROP SK @ R-AT R-ANY>DEC
    DUP VMIN @ MIN VMIN !  DUP VMAX @ MAX VMAX !  R-LOG VLOG +!
  LOOP  R-LEN VLOG @ SWAP / R-EXP ;
: REPORT ( --- )
  ." native A/B over layouts: the checkout against " BASE-REV @ R-TYPE ." , pads " PADS @ S" ," T R-JOIN R-TYPE
  ." , " ROUNDS @ R-TYPE ."  rounds (SCALE=" SCALE @ R-TYPE ." )" R-NL
  S" workload" 11 LJ SPACE S" base's layouts" 22 LJ SPACE S" checkout's layouts" 22 LJ SPACE ." checkout / base" R-NL
  WL @ R-SPLIT-WS DUP R-LEN 0 ?DO
    I SK !  DUP I ITEM R-T@ 11 LJ SPACE
    B @ SIDE  VMIN @ .DEC3 ." -" VMAX @ .DEC3 12 SPACES
    N @ SIDE  VMIN @ .DEC3 ." -" VMAX @ .DEC3 12 SPACES
    SWAP 1000000 SWAP */ .DEC3 R-NL
  LOOP DROP ;

: MAIN ( --- )
  S" git" T S" rev-parse" T S" --show-toplevel" T 3 CAPTURE ROOT !  ROOT @ R-CD
  1 S" HEAD" ARG-OR BASE-REV !  2 S" 9" ARG-OR ROUNDS !  3 S" 0,16,32,48" ARG-OR S" ," T R-SPLIT PADS !
  S" WL" T R-ENV S" loop fn str arith realistic" T R-DEFAULT WL !  WL @ R-SPLIT-WS R-LEN NWL !
  S" SCALE" T R-ENV S" 25" T R-DEFAULT SCALE !
  S" mktemp" T S" -d" T 2 CAPTURE OUTD !
  S" N>A  S" T 34 1 R-BYTES T+ S"  forth/native-rt.4" T T+ 34 1 R-BYTES T+ S"  INCLUDED  A>N" T T+ MARK !
  S" mktemp" T S" -d" T 2 CAPTURE WT !
  S" git" T S" worktree" T S" add" T S" -q" T S" --detach" T WT @ BASE-REV @ 7 RUN?
  IF S" native-ab-layouts: no worktree for " T BASE-REV @ T+ DIE THEN
  ['] BUILD-BOTH CATCH  CLEANUP  ?DUP IF THROW THEN
  WRITE-CFG  BENCH READ-BENCH  REPORT ;
MAIN
