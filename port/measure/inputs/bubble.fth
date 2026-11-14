\ bubble.fth - a bubble sort of pseudo-random cells: loops, memory, compares.
\
\ The owner's RelF benchmark (RelF/bench/bubble.4 in his collection,
\ forth.tgz), its words as they were, ELEMENTS 300 and not 6000 so a timed run
\ stays near the others (Iteration 128; Iteration 127 had the program of
\ RelF's bench/langs/bench.4). DO loops over addresses with CELL +LOOP, 2@ and
\ 2!, a compare and a swap: execution, where parse - which it replaced in the
\ selection, with ackermann.fth - is the interpreter. VERIFY-LIST aborts if
\ the list is not sorted, and BENCH prints its first and last cells, so a
\ design that sorts wrongly shows.

: MYBOUNDS  OVER + SWAP ;

1 CELLS CONSTANT CELL

VARIABLE SEED

: INITIATE-SEED  74755 SEED ! ;
: RANDOM  SEED @ 1309 * 13849 + 65535 AND DUP SEED ! ;

300 CONSTANT ELEMENTS

ALIGN CREATE LIST ELEMENTS CELLS ALLOT

: INITIATE-LIST
  LIST ELEMENTS CELLS + LIST DO RANDOM I ! CELL +LOOP
;

: VERIFY-LIST
  LIST ELEMENTS 1- CELLS MYBOUNDS DO
    I 2@ > ABORT" BUBBLE-SORT: NOT SORTED"
  CELL +LOOP
;

: BUBBLE
  1 ELEMENTS 1 DO
    LIST ELEMENTS I - CELLS MYBOUNDS DO
      I 2@ > IF I 2@ SWAP I 2! THEN
    CELL +LOOP
  LOOP
;

: BUBBLE-SORT
  INITIATE-SEED
  INITIATE-LIST
  BUBBLE
  VERIFY-LIST
;

: BENCH ( --- )  BUBBLE-SORT  LIST @ .  LIST ELEMENTS 1- CELLS + @ . CR ;

: BX 60 0 DO BENCH LOOP ; BX
S" BENCH-DONE" TYPE CR

BYE
