\ port/gforth/sys.fs - the one word port/os.4 needs of a host, and CSTRLEN,
\ for gforth: C functions in port/gforth/relfsys.c, built as a shared library
\ whose path build.sh gives in RELFSYS (an environment variable at build
\ time; the image keeps it, and PORT-BOOT opens the library again).
\
\   SYSCALL ( block num --- r )   Linux system call num, its six arguments
\                                 the cells at block, r its result or
\                                 -errno; num -1, -2, -3 give argc, argv
\                                 and the initial environ.

CREATE RELFSYS-PATH 256 ALLOT
S" RELFSYS" getenv DUP 0= [IF] .( sys.fs: RELFSYS names no library) CR ABORT [THEN]
DUP RELFSYS-PATH C!  RELFSYS-PATH 1+ SWAP MOVE
VARIABLE SYS-FN   VARIABLE STRLEN-FN   VARIABLE CALLOC-FN
: RELFSYS-OPEN ( --- )
  RELFSYS-PATH COUNT open-lib ?DUP 0= IF
    ." relfsh: cannot open " RELFSYS-PATH COUNT TYPE CR 70 (bye) THEN
  DUP >R S" relf_syscall" R@ lib-sym SYS-FN !
  S" relf_calloc" R@ lib-sym CALLOC-FN !
  S" relf_strlen" R> lib-sym STRLEN-FN !
  SYS-FN @ 0= STRLEN-FN @ 0= OR CALLOC-FN @ 0= OR IF ." relfsh: " RELFSYS-PATH COUNT TYPE ." : no functions" CR 70 (bye) THEN ;
RELFSYS-OPEN

: SYSCALL ( block num --- r )
  DUP -1 = IF 2DROP argc @ EXIT THEN
  DUP -2 = IF 2DROP argv @ EXIT THEN
  SYS-FN @ call-c ;
: CSTRLEN ( c-addr --- u )  STRLEN-FN @ call-c ;
\ ALLOCATE: calloc, freed by gforth's FREE and grown by its RESIZE (free,
\ realloc - the same C heap); port/os.4 is told it zeroes (host.4)
: ALLOCATE ( u --- a-addr ior )  CALLOC-FN @ call-c DUP 0= ;
