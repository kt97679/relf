\ tests/ext/filetest2.fth - more of the official File-Access tests.
\
\ From github.com/gerryjackson/forth2012-test-suite, src/filetest.fth
\ (public domain, Gerry Jackson, with contributions from Helmut Eller
\ as marked), T{ / }T rewritten to { / }. filetest.fth stops at the
\ first section needing /STRING; these are four of the sections after
\ it, added in Iteration 245 when READ-FILE, READ-LINE, WRITE-FILE and
\ WRITE-LINE moved from the engine into Forth and DELETE-FILE turned
\ out to segfault on success - a word no test called.
\
\ Sections: R/O FILE-POSITION READ-LINE (including Eller's short and
\ exact-length buffers, which exercise READ-LINE giving back what it
\ read past the newline); R/W WRITE-FILE REPOSITION-FILE READ-FILE
\ FILE-POSITION; BIN READ-FILE FILE-SIZE; DELETE-FILE.
\ Left out: S" in interpretation mode (needs upstream's $" helper) and
\ RESIZE-FILE (not implemented). One line changed: FLUSH-FILE, which
\ this system does not have, is dropped from a WRITE-FILE test - there
\ is no buffer to flush.
\
\ Self-contained: it recreates fatest1.txt the way filetest.fth leaves
\ it, and deletes both files it uses at the end.
\
\ Needs tester.fr and extend.4 loaded first, in that order.

DECIMAL

\ Test scaffolding from upstream's utilities, not system words.
: S= ( c-addr1 u1 c-addr2 u2 --- f )  COMPARE 0= ;
: /STRING ( c-addr u n --- c-addr' u' )  ROT OVER + ROT ROT - ;

: FN1 S" fatest1.txt" ;
VARIABLE FID1
: LINE1 S" Line 1" ;
{ FN1 W/O CREATE-FILE SWAP FID1 ! -> 0 }
{ LINE1 FID1 @ WRITE-LINE -> 0 }
{ FID1 @ CLOSE-FILE -> 0 }

\ ------------------------------------------------------------------------------
TESTING R/O FILE-POSITION (simple)  READ-LINE 

200 CONSTANT BSIZE
CREATE BUF BSIZE ALLOT
VARIABLE #CHARS

{ FN1 R/O OPEN-FILE SWAP FID1 ! -> 0 }
{ FID1 @ FILE-POSITION -> 0 0 0 }
{ BUF 100 FID1 @ READ-LINE ROT DUP #CHARS ! -> TRUE 0 LINE1 SWAP DROP }
{ BUF #CHARS @ LINE1 S= -> TRUE }
{ FID1 @ CLOSE-FILE -> 0 }

\ Additional test contributed by Helmut Eller
\ Test with buffer shorter than the line including zero length buffer.
{ FN1 R/O OPEN-FILE SWAP FID1 ! -> 0 }
{ FID1 @ FILE-POSITION -> 0 0 0 }
{ BUF 0 FID1 @ READ-LINE ROT DUP #CHARS ! -> TRUE 0 0 }
{ BUF 3 FID1 @ READ-LINE ROT DUP #CHARS ! -> TRUE 0 3 }
{ BUF #CHARS @ LINE1 DROP 3 S= -> TRUE }
{ BUF 100 FID1 @ READ-LINE ROT DUP #CHARS ! -> TRUE 0 LINE1 NIP 3 - }
{ BUF #CHARS @ LINE1 3 /STRING S= -> TRUE }
{ FID1 @ CLOSE-FILE -> 0 }

\ Additional test contributed by Helmut Eller
\ Test with buffer exactly as long as the line.
{ FN1 R/O OPEN-FILE SWAP FID1 ! -> 0 }
{ FID1 @ FILE-POSITION -> 0 0 0 }
{ BUF LINE1 NIP FID1 @ READ-LINE ROT DUP #CHARS ! -> TRUE 0 LINE1 NIP }
{ BUF #CHARS @ LINE1 S= -> TRUE }
{ FID1 @ CLOSE-FILE -> 0 }

\ ------------------------------------------------------------------------------
TESTING R/W WRITE-FILE REPOSITION-FILE READ-FILE FILE-POSITION S"

: LINE2 S" Line 2 blah blah blah" ;
: RL1  BUF 100 FID1 @ READ-LINE  ;
CREATE FP 0 , 0 ,    \ Don't use 2VARIABLE
: DEQ  ( d -- f )  ROT = >R = R> AND  ;  \ Same as D= in Double Number word set

{ FN1 R/W OPEN-FILE SWAP FID1 ! -> 0 }
{ FID1 @ FILE-SIZE DROP FID1 @ REPOSITION-FILE -> 0 }
{ FID1 @ FILE-SIZE -> FID1 @ FILE-POSITION }
{ LINE2 FID1 @ WRITE-FILE -> 0 }
{ 10 0 FID1 @ REPOSITION-FILE -> 0 }
{ FID1 @ FILE-POSITION -> 10 0 0 }
{ 0 0 FID1 @ REPOSITION-FILE -> 0 }
{ RL1 -> LINE1 SWAP DROP TRUE 0 }
{ RL1 ROT DUP #CHARS ! -> TRUE 0 LINE2 SWAP DROP }
{ BUF #CHARS @ LINE2 S= -> TRUE }
{ RL1 -> 0 FALSE 0 }
{ FID1 @ FILE-POSITION ROT ROT FP 2! -> 0 }
{ FP 2@ FID1 @ FILE-SIZE DROP DEQ -> TRUE }
{ S" " FID1 @ WRITE-LINE -> 0 }
{ S" " FID1 @ WRITE-LINE -> 0 }
{ FP 2@ FID1 @ REPOSITION-FILE -> 0 }
{ RL1 -> 0 TRUE 0 }
{ RL1 -> 0 TRUE 0 }
{ RL1 -> 0 FALSE 0 }
{ FID1 @ CLOSE-FILE -> 0 }

\ ------------------------------------------------------------------------------
TESTING BIN READ-FILE FILE-SIZE

: CBUF BUF BSIZE 0 FILL ;
: FN2 S" FATEST2.TXT" ;
VARIABLE FID2
: SETPAD PAD 50 0 DO I OVER C! CHAR+ LOOP DROP ;

SETPAD   \ If anything else is defined setpad must be called again
         \ as pad may move

{ FN2 R/W BIN CREATE-FILE SWAP FID2 ! -> 0 }
{ PAD 50 FID2 @ WRITE-FILE -> 0 }   \ FLUSH-FILE dropped, see above
{ FID2 @ FILE-SIZE -> 50 0 0 }
{ 0 0 FID2 @ REPOSITION-FILE -> 0 }
{ CBUF BUF 29 FID2 @ READ-FILE -> 29 0 }
{ PAD 29 BUF 29 S= -> TRUE }
{ PAD 30 BUF 30 S= -> FALSE }
{ CBUF BUF 29 FID2 @ READ-FILE -> 21 0 }
{ PAD 29 + 21 BUF 21 S= -> TRUE }
{ FID2 @ FILE-SIZE DROP FID2 @ FILE-POSITION DROP DEQ -> TRUE }
{ BUF 10 FID2 @ READ-FILE -> 0 0 }
{ FID2 @ CLOSE-FILE -> 0 }

\ ------------------------------------------------------------------------------
TESTING DELETE-FILE

{ FN2 DELETE-FILE -> 0 }
{ FN2 R/W BIN OPEN-FILE SWAP DROP 0= -> FALSE }
{ FN2 DELETE-FILE 0= -> FALSE }

\ ------------------------------------------------------------------------------
\ Not upstream: CRLF lines. A CR before the newline is part of the line
\ terminator; a CR at the end of a FULL buffer is not known to be, and
\ is kept (Iteration 249).
CREATE CRLF-TXT 97 C, 98 C, 13 C, 10 C, 99 C, 10 C,
{ FN1 W/O CREATE-FILE SWAP FID1 ! -> 0 }
{ CRLF-TXT 6 FID1 @ WRITE-FILE -> 0 }
{ FID1 @ CLOSE-FILE -> 0 }
{ FN1 R/O OPEN-FILE SWAP FID1 ! -> 0 }
{ BUF 100 FID1 @ READ-LINE -> 2 TRUE 0 }
{ BUF 100 FID1 @ READ-LINE -> 1 TRUE 0 }
{ FID1 @ CLOSE-FILE -> 0 }
{ FN1 R/O OPEN-FILE SWAP FID1 ! -> 0 }
{ BUF 3 FID1 @ READ-LINE -> 3 TRUE 0 }
{ BUF 2 + C@ -> 13 }
{ BUF 3 FID1 @ READ-LINE -> 0 TRUE 0 }
{ FID1 @ CLOSE-FILE -> 0 }

\ ------------------------------------------------------------------------------
\ Not upstream: leave nothing behind in the repository.
{ FN1 DELETE-FILE -> 0 }

CR
