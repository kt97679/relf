\ tests/kernel-words.fth - kernel words no test reached (Iteration 958):
\ tools/coverage.py found NAME>STRING, SEARCH-WORDLIST and CMOVE> never run,
\ words the forth builtin offers (A20). Run after tester.fr, on the bare
\ kernel, at both cell widths and on both engines, as every tests/*.fth.

CR TESTING NAME>STRING

\ A name comes back as it was written, from each form it is laid in
\ (CV8.md, packed names, 949): characters of one nibble (E - R T A S L O I
\ N D C P M F), of an escape and a nibble (U H B G X K W V ? Y > ( # ) +),
\ raw bytes (Z ! and any byte above 127), an odd count of nibbles and an
\ even one, the longest name, 31 characters, and a lower-case name, which
\ does not pack shorter and is laid as written.
: NAME-IS ( xt c-addr u --- f )   ROT >NAME NAME>STRING COMPARE 0= ;
: SET ;   : SETS ;   : HUB ;   : Z! ;   : <Q> ;   : naïve ;   : lower-case ;
: ABCDEFGHIJKLMNOPQRSTUVWXYZ01234 ;
{ ' DUP S" DUP" NAME-IS -> -1 }
{ ' SET S" SET" NAME-IS -> -1 }
{ ' SETS S" SETS" NAME-IS -> -1 }
{ ' HUB S" HUB" NAME-IS -> -1 }
{ ' Z! S" Z!" NAME-IS -> -1 }
{ ' <Q> S" <Q>" NAME-IS -> -1 }
{ ' naïve S" naïve" NAME-IS -> -1 }
{ ' lower-case S" lower-case" NAME-IS -> -1 }
{ ' ABCDEFGHIJKLMNOPQRSTUVWXYZ01234 S" ABCDEFGHIJKLMNOPQRSTUVWXYZ01234" NAME-IS -> -1 }
{ ' SET S" SETS" NAME-IS -> 0 }

CR TESTING SEARCH-WORDLIST

{ S" DUP" FORTH-WORDLIST SEARCH-WORDLIST SWAP ' DUP = -> -1 -1 }
{ S" IF" FORTH-WORDLIST SEARCH-WORDLIST SWAP DROP -> 1 }
{ S" NO-SUCH-WORD-958" FORTH-WORDLIST SEARCH-WORDLIST -> 0 }

CR TESTING CMOVE>

\ It copies from the top down, so a move up over itself keeps its bytes;
\ CMOVE, from the bottom up, repeats the first ones.
CREATE CMB 8 ALLOT
: CMB! ( --- )   S" ABCDEFGH" CMB SWAP CMOVE ;
{ CMB! CMB CMB 2 + 4 CMOVE> CMB 8 S" ABABCDGH" COMPARE -> 0 }
{ CMB! CMB CMB 2 + 4 CMOVE  CMB 8 S" ABABABGH" COMPARE -> 0 }
{ CMB! CMB 3 + CMB 1 + 0 CMOVE> CMB 8 S" ABCDEFGH" COMPARE -> 0 }
{ CMB! CMB 4 + CMB 4 CMOVE> CMB 8 S" EFGHEFGH" COMPARE -> 0 }

CR TESTING KERNEL WORDS COMPLETE
