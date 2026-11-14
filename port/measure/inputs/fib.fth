\ fib.fth - naive recursive Fibonacci. The point is CALLS.
\
\ Every other workload here is dominated by the kernel's own words:
\ parsing, dictionary search, compiling. This one is almost nothing but
\ call, return and a little arithmetic, which matters because the call
\ is the ONE operation every encoding in this repository encodes
\ differently - a relative offset cell, a word number through a table,
\ a scaled offset computed from a base, two bytes with the top bit set.
\
\ It is also the benchmark the ladder's design decisions should show up
\ in most directly, and the one readers expect to see.
\
\ N is 30 rather than the traditional 34: about 40 ms on a fast x86 and
\ a few seconds on an ARMv7 board, which is enough to measure and short
\ enough to repeat.

: FIB ( n1 --- n2 )
  DUP 2 < IF
    DROP 1
  ELSE
    DUP
    -1 + RECURSE
    SWAP -2 + RECURSE
    +
  THEN ;

: BENCH ( --- )
  30 FIB DROP ;

: BX 4 0 DO BENCH LOOP ; BX
S" BENCH-DONE" TYPE CR
BYE

BYE
