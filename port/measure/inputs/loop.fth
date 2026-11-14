\ A deliberately narrow benchmark: nested counted loops doing stack
\ arithmetic and nothing else. No dictionary work, no parsing, no I/O
\ inside the timed part. Written in the intersection of what SOD32 and
\ kernel.4 both provide, so the SOURCE is identical for every engine.
\
\ This is here to separate two questions that the corpus benchmark runs
\ together: how fast the VM dispatches, and how fast the rest of the
\ Forth system is. The corpus answers the second; this answers the first.

: INNER ( n --- n2 )
\ Stack-neutral per iteration, on purpose: an earlier version grew the
\ stack by one cell per pass and died of stack overflow 7 ms in, which
\ every engine reported as a fast run.
  1000 0 DO
    DUP I + XOR
  LOOP ;

: BENCH ( --- )
  1
  400 0 DO INNER LOOP
  DROP ;

: BX 40 0 DO BENCH LOOP ; BX
S" BENCH-DONE" TYPE CR
BYE

BYE
