\ ackermann.fth - Ackermann's function: deep recursion and nothing else.
\
\ The owner's RelF benchmark (RelF/bench/ackermann.4 in his collection,
\ forth.tgz) as it was - his -ack, with 1 -1 D+ for A(x-1,1) - NUM 5, not 3,
\ so a timed run stays near the others (Iteration 128; Iteration 127 had the
\ textbook definition). fib.fth recurses some 25 deep; this goes hundreds
\ deep, and its data stack with it. A(3,5) = 253, by 42,438 calls; the value
\ is printed, so a design that gets it wrong shows.

5 CONSTANT NUM

: -ack ( y x -- n )
   DUP 0= IF
     DROP 1+
   ELSE
     OVER IF
       SWAP 1- OVER RECURSE SWAP 1- RECURSE
     ELSE
       1 -1 D+ RECURSE
     THEN
   THEN ;

: BENCH ( --- )  NUM 3 -ack . CR ;

: BX 80 0 DO BENCH LOOP ; BX
S" BENCH-DONE" TYPE CR

BYE
