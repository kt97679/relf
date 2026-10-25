# Rill's memory - the collector (Iteration 776)

Rill keeps every text, item, list and record in an arena: 128 MB of address
space, used from its start up, touched only as used. Until 776 nothing in it
was ever given back - a long loop that made short-lived values filled it and
stopped with "rill: the arena is full". Now a collector copies out what the
script can still reach and frees the rest.

## How

- Safe points. Before each statement of the script's top level - in loops at
  the top level too, not inside a def or on EXIT - no value is held anywhere
  but in variables. There the compilers put R-GC?, which collects once the
  arena has grown past R-GC-AT. (Gene gc, on.)
- Roots. The compilers register every variable of the script that can hold a
  text, a list, a record or an item, with its kind (R-ROOT), and the source
  of every top-level for loop. Kinds are sound since 765: one per variable.
- The copy. From each root, by kind: a text is copied; an item is copied, and
  what it holds; a list's header is copied, its items array cut to its count,
  each item copied; a record's keys, values and hash table (indices, no
  pointers) are copied. A bitmap marks what has moved, its new place written
  into its old first cell, so what is shared stays shared. The new arena is
  fresh; the old one is freed back to the system.
- Next time. R-GC-AT is set to twice what was live, at least 16 MB more.
- Outside the arena, for good: literal texts made once (gene littext, now on;
  R-FIX) and the regex cache's patterns.

## Measured

| | peak memory, collector off | on |
|---|---:|---:|
| tests/rill/memory.rill (2,000,000 short-lived texts and lists) | 129 MB, then "the arena is full" | 17 MB, done |
| dead-words | 13 MB | 13 MB |
| native-by-source | 15 MB | 15 MB |

The pilots never reach the first collection; the safe points cost them 1.2 %
and 0.6 % more dispatches. Literal texts made once save 5 %, and keep those
texts from filling the arena at all.

## Tested

RILL_GC_STRESS=1 collects at the first safe point and then after every 64 KB:
every test and all three pilots (and dead-words' --delete) give the same
output under it as without. Two slips on the way, both found that way: a
variable R-BASE hidden by the runtime's own base() word, defined later in the
same file - rill-forth-lint now reports a name the runtime defines twice -
and a >R inside a DO loop, under which I read the wrong index.

## What it does not do

- Inside a def no collection runs: a def that loops making values grows the
  arena until it returns.
- The arena is 128 MB of address space; a script that keeps more than that
  live still stops, with the message.

## Leaks outside the arena, and the check (Iteration 778)

tools/rill-memcheck.py runs each runtime feature in a top-level loop at N
and 10 N rounds, under RILL_GC_STRESS so the arena stays small - growth is
then memory kept for good. It found one: a regex pattern made at run time,
past the 32 the cache holds, compiled into a 24 KB program never freed - 22
KB a round. Now a program the cache cannot keep frees the one before it like
it (RX-LOOSE), and every program is cut to its own size before its jumps
become addresses (its start filter's address in a header slot before it).
The check runs in tests/rill/run (24 passed); against iteration 777's image
it fails on that feature, as it should.
