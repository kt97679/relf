\ The sieve of Eratosthenes, as the BYTE benchmarks of 1981 ran it: 8190
\ flags, the primes counted, the whole repeated. The HELD-OUT workload
\ since Iteration 41, when loop joined the selection: what evolution does
\ not see, to show whether what it selects for carries over. Memory - C@
\ C! FILL - and a BEGIN ... WHILE ... REPEAT inner loop, which none of the
\ selected workloads leans on. Written in CORE words only, as the others.
\ 1899 primes; the count is printed, so a design that gets it wrong shows.

8190 CONSTANT SIZE
CREATE FLAGS SIZE ALLOT

: PRIMES ( --- n )
  FLAGS SIZE 1 FILL
  0 SIZE 0 DO
    FLAGS I + C@ IF
      I DUP + 3 +  DUP I +
      BEGIN DUP SIZE < WHILE  0 OVER FLAGS + C!  OVER +  REPEAT
      2DROP 1+
    THEN
  LOOP ;

: BENCH ( --- )  0  15 0 DO DROP PRIMES LOOP  . CR ;

: BX 25 0 DO BENCH LOOP ; BX
S" BENCH-DONE" TYPE CR

BYE
