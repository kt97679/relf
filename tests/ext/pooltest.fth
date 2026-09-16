\ tests/ext/pooltest.fth - pool.4's growing buffers (Iteration 249).
\
\ BUF-ENSURE must keep a buffer's contents, zero what it adds, leave
\ the OLD block readable until BUF-FREE-RETIRED (code holds addresses
\ into these buffers), do nothing when the buffer is already big
\ enough, and grow by at least doubling.
\
\ Needs tester.fr and extend.4 loaded first, in that order.

DECIMAL
S" pool.4" INCLUDED

100 BUFFER: GT-BUF
VARIABLE GT-OLD
: GT-SIZE ( --- u )  BUFFER-SIZE GT-BUF ;
: GT-GROW ( u --- )  ENSURE-BUFFER GT-BUF ;
: GT-FILL ( --- )    GT-BUF 100 65 FILL  GT-BUF 99 + 66 SWAP C! ;

{ GT-SIZE -> 100 }
{ GT-FILL GT-BUF GT-OLD ! -> }
{ 50 GT-GROW GT-SIZE -> 100 }
{ GT-BUF GT-OLD @ = -> TRUE }
{ 100 GT-GROW GT-SIZE -> 100 }

\ Growing: at least twice the size, rounded to a cell.
{ 101 GT-GROW GT-SIZE 200 < -> FALSE }
{ GT-BUF GT-OLD @ = -> FALSE }
\ The contents came along, and the new part is zero.
{ GT-BUF C@ GT-BUF 98 + C@ GT-BUF 99 + C@ -> 65 65 66 }
{ GT-BUF 100 + C@ GT-BUF GT-SIZE + 1- C@ -> 0 0 }
\ The old block is still readable.
{ GT-OLD @ C@ GT-OLD @ 99 + C@ -> 65 66 }
\ A request larger than double is met exactly, rounded to a cell.
{ 5000 GT-GROW GT-SIZE 5000 < -> FALSE }
{ GT-SIZE 5000 1 CELLS + < -> TRUE }
{ GT-BUF 99 + C@ -> 66 }
\ Two blocks were retired, and freeing them empties the list.
{ BUF-RETIRED @ 0= -> FALSE }
{ BUF-FREE-RETIRED BUF-RETIRED @ -> 0 }
{ GT-BUF 99 + C@ -> 66 }
