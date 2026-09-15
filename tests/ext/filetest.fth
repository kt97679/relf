\ tests/ext/filetest.fth - the official File-Access tests, as far as
\ this system's words reach.
\
\ From github.com/Forth-Standard/forth-standard-test-suite, src/
\ filetest.fth, T{ / }T rewritten to { / }, truncated at the first
\ section needing a word this system lacks (/STRING, from the STRING
\ word set).
\
\ These tests found two real defects the day they were adopted:
\ FILE-POSITION and FILE-SIZE returned a single cell where ANS
\ specifies a DOUBLE, and REPOSITION-FILE took one; and READ-LINE with
\ a zero-length buffer reported end-of-file when ANS says a request
\ for no characters cannot have reached it. Nothing in Forth called
\ any of the three, which is why the stack effects had been wrong
\ since they were written.
\
\ Needs tester.fr and extend.4 loaded first, in that order.

\ To test the ANS File Access word set and extension words

\ This program was written by Gerry Jackson in 2006, with contributions from
\ others where indicated, and is in the public domain - it can be distributed
\ and/or modified in any way but please retain this notice.

\ This program is distributed in the hope that it will be useful,
\ but WITHOUT ANY WARRANTY; without even the implied warranty of
\ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

\ The tests are not claimed to be comprehensive or correct 

\ ------------------------------------------------------------------------------
\ The tests are based on John Hayes test program for the core word set
\ and requires those files to have been loaded

\ Words tested in this file are:
\     ( BIN CLOSE-FILE CREATE-FILE DELETE-FILE FILE-POSITION FILE-SIZE
\     OPEN-FILE R/O R/W READ-FILE READ-LINE REPOSITION-FILE RESIZE-FILE 
\     S" S\" SOURCE-ID W/O WRITE-FILE WRITE-LINE 
\     FILE-STATUS FLUSH-FILE RENAME-FILE SAVE-INPUT RESTORE-INPUT
\     REFILL

\ Words not tested:
\     INCLUDED INCLUDE-FILE (as these will likely have been
\     tested in the execution of the test files)
\ ------------------------------------------------------------------------------
\ Assumptions, dependencies and notes:
\     - tester.fr (or ttester.fs), errorreport.fth and utilities.fth have been
\       included prior to this file
\     - the Core word set is available and tested
\     - These tests create files in the current directory, if all goes
\       well these will be deleted. If something fails they may not be
\       deleted. If this is a problem ensure you set a suitable 
\       directory before running this test. There is no ANS standard
\       way of doing this. Also be aware of the file names used below
\       which are:  fatest1.txt, fatest2.txt and fatest3.txt
\ ------------------------------------------------------------------------------

TESTING File Access word set

DECIMAL

\ ------------------------------------------------------------------------------
TESTING CREATE-FILE CLOSE-FILE

: FN1 S" fatest1.txt" ;
VARIABLE FID1

{ FN1 R/W CREATE-FILE SWAP FID1 ! -> 0 }
{ FID1 @ CLOSE-FILE -> 0 }

\ ------------------------------------------------------------------------------
TESTING OPEN-FILE W/O WRITE-LINE

: LINE1 S" Line 1" ;

{ FN1 W/O OPEN-FILE SWAP FID1 ! -> 0 }
{ LINE1 FID1 @ WRITE-LINE -> 0 }
{ FID1 @ CLOSE-FILE -> 0 }

\ ------------------------------------------------------------------------------
CR
