\ Adapted from forth2012-test-suite/src/core.fr (John Hayes / Applied
\ Physics Laboratory), which carries the notice:
\   (C) 1995 JOHNS HOPKINS UNIVERSITY / APPLIED PHYSICS LABORATORY
\   MAY BE DISTRIBUTED FREELY AS LONG AS THIS COPYRIGHT NOTICE REMAINS.
\ Source: https://github.com/gerryjackson/forth2012-test-suite
\
\ These are a small, hand-picked, directly-applicable subset, translated
\ from that suite's T{ -> }T syntax into RelF's own { -> } convention
\ (see tester.fr, already bundled in this repo). RelF does not implement
\ the full ANS/Forth-2012 word set, so most of the original suite does
\ not apply yet - see PROGRESS.md for the scope decision on this.

CR
TESTING ADDITIONAL CORE ARITHMETIC AND STACK CASES ( from forth2012-test-suite )

{ 0 1 + -> 1 }
{ 1 2 + -> 3 }
{ -1 1 + -> 0 }
{ -1 -1 + -> -2 }
{ 1 1 - -> 0 }
{ 0 1 - -> -1 }

{ 0 0 AND -> 0 }
{ 0 1 AND -> 0 }
{ 1 0 AND -> 0 }
{ 1 1 AND -> 1 }

{ 0 0 OR -> 0 }
{ 0 1 OR -> 1 }
{ 1 1 OR -> 1 }

{ 0 0 XOR -> 0 }
{ 0 1 XOR -> 1 }
{ 1 1 XOR -> 0 }

{ 1 DUP -> 1 1 }
{ 1 2 SWAP -> 2 1 }
{ 1 2 DROP -> 1 }
{ 1 2 OVER -> 1 2 1 }
{ 1 2 3 ROT -> 2 3 1 }

{ 0 0= -> -1 }
{ 1 0= -> 0 }
{ -1 0= -> 0 }

{ 0 1 < -> -1 }
{ 1 0 < -> 0 }
{ 1 1 < -> 0 }
{ -1 0 < -> -1 }

CR TESTING ADDITIONAL CASES COMPLETE
