\ tests/shadow.fth - regression tests for shadow.4 (see GOALS.md phase
\ 8 / PROGRESS.md Iteration 38). Uses tester.fr's own { -> } convention,
\ same as every other file in this directory.
\
\ Loading shadow.4 redefines ; and EXIT (deliberately - see that file's
\ header for why), so this file is deliberately the LAST thing the core
\ suite loads: everything before it has already been compiled through
\ the original definitions, which is itself part of what's being
\ checked here - the wrappers must be transparent to code that declares
\ no shadowed variables.

\ pool.4 first: since Iteration 136 shadow.4's save stack and its
\ compile-time address table are BUFFER:s rather than CREATE ... ALLOT,
\ so BUFFER: must exist before shadow.4 is compiled. Loading shadow.4
\ alone segfaults rather than reporting an undefined word - the failed
\ declaration leaves the name undefined and every later use compiles a
\ garbage reference.
S" pool.4" INCLUDED
S" shadow.4" INCLUDED

\ tester.fr leaves BASE at 16, and core-extra.fth happens not to notice
\ because every value it uses reads the same in hex as in decimal. The
\ tests below do not have that luxury (8 LT-FACT is 40320), so force
\ decimal explicitly rather than inheriting whatever the previous file
\ left behind.
DECIMAL

CR
TESTING LOCALS ( shadow.4 )

VARIABLE LT-A
VARIABLE LT-B
VARIABLE LT-S

\ --- arguments are taken left to right = deepest to top of stack ---

: LT-SUB ( x y --- x-y )  SHADOW{ LT-A LT-B }  LT-A @ LT-B @ - ;

{ 10 3 LT-SUB -> 7 }
{ 3 10 LT-SUB -> -7 }

\ --- a scratch local after | is zeroed, not taken from the stack ---

: LT-SCRATCH ( x --- x*x+1 )  SHADOW{ LT-A | LT-S }
  LT-S @ 1+ LT-S !
  LT-A @ LT-A @ * LT-S @ + ;

{ 5 LT-SCRATCH -> 26 }
{ 0 LT-SCRATCH -> 1 }

\ --- declaring no shadowed variables at all is a no-op ---

: LT-NONE ( x --- x+5 ) SHADOW{ } 5 + ;

{ 1 LT-NONE -> 6 }

\ --- the caller's value survives the call, which is the whole point ---

111 LT-A !  222 LT-B !
{ 10 3 LT-SUB -> 7 }
{ LT-A @ -> 111 }
{ LT-B @ -> 222 }

\ --- restore happens on an early EXIT too, not just at ; ---

: LT-EARLY ( x --- y )  SHADOW{ LT-A }
  LT-A @ 0 < IF 0 EXIT THEN
  LT-A @ 2 * ;

{ 7 LT-EARLY -> 14 }
{ -7 LT-EARLY -> 0 }
{ LT-A @ -> 111 }

\ --- and on an EXIT from inside a DO LOOP ---

: LT-FIND ( n --- i )  SHADOW{ LT-A }
  10 0 DO I LT-A @ = IF I UNLOOP EXIT THEN LOOP -1 ;

{ 4 LT-FIND -> 4 }
{ 99 LT-FIND -> -1 }
{ LT-A @ -> 111 }

\ --- recursion: each invocation must see only its own values ---

: LT-FACT ( n --- n! )  SHADOW{ LT-A }
  LT-A @ 1 < IF 1 EXIT THEN
  LT-A @ 1- RECURSE LT-A @ * ;

{ 5 LT-FACT -> 120 }
{ 8 LT-FACT -> 40320 }
{ LT-A @ -> 111 }

\ --- nesting: two different words using the SAME name, one calling
\ --- the other. This is the case fixed globals cannot express, and
\ --- the reason while/for/function bodies cannot nest today.

: LT-INNER ( x --- y )  SHADOW{ LT-A } LT-A @ 10 * ;
: LT-OUTER ( x --- y )  SHADOW{ LT-A } LT-A @ LT-INNER LT-A @ + ;

{ 3 LT-OUTER -> 33 }
{ LT-A @ -> 111 }

\ --- scratch shadowed variables survive recursion independently ---

: LT-SUMTO ( n --- s )  SHADOW{ LT-A | LT-S }
  LT-A @ 0 > 0= IF 0 EXIT THEN
  LT-A @ 1- RECURSE LT-S !
  LT-S @ LT-A @ + ;

{ 10 LT-SUMTO -> 55 }
{ 1 LT-SUMTO -> 1 }
{ 0 LT-SUMTO -> 0 }

\ --- every path above must leave the save stack balanced ---
\ The stack is the engine's since Iteration 517, so its depth cannot be
\ read; this was { LSAVE-SP @ -> 0 }. Instead: fill it to its limit.
\ LT-FILL saves once per level, and 4095 down to 0 is 4096 levels -
\ exactly LSAVE_MAX - so it fits only if nothing above leaked an entry;
\ one leaked save and the last level overflows, which aborts the run.

VARIABLE LT-D
: LT-FILL ( n --- )  SHADOW{ LT-D }  LT-D @ IF LT-D @ 1- RECURSE THEN ;
{ 4095 LT-FILL -> }
