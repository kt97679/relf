# TOKEN-THREADING.md — the proposed change, in detail

> **Historical.** Proposed at Iteration 139, superseded by CV8 at 189,
> and the encoding it argued against was retired at 218. Its density
> analysis is still the best in the repository; its plan is not the
> plan. See `CV8.md`.

Proposed in Iteration 139, measured in 140, prototyped in 141, written
out here in 142 because it is by a wide margin the largest change ever
proposed for this project and the cost is in places nobody has looked
yet. **This is a design under consideration, not a plan of record.**
Read `VM-RESEARCH.md` and `PROGRESS.md`'s Iterations 139-141 first.

## 1. The change in one paragraph

Today a compiled word is an array of host cells: a primitive is a cell
holding `index * CELL + 1`, and a call is a cell holding a **relative
byte offset** to the callee. The offset *is* the instruction — no table,
no lookup, `ip += t`. Under token threading, compiled code becomes a
**byte stream**, and a call becomes a small **index into a table of word
addresses**. Everything else follows from that one substitution.

## 2. Why an index rather than an offset

This is the whole point, and it is worth being precise about.

An offset must be able to reach any word from any other, so it needs
roughly the address range of the image: it cannot be narrower than a
few bytes without a relaxation pass, and in practice it occupies a
whole cell. An index only has to distinguish **817 words** (measured on
the current image), which needs ten bits.

`GOALS.md`'s phase 5 rejected byte-granular encoding because `CALL`
would need a marker byte and realignment on top of its offset. That
objection is entirely correct **about an offset** and does not apply to
an index. The rejection was sound and its premise has changed.

Calls are **6,576 cells, 34% of the compiled code**. On x86-64 that is
eight bytes to name one of 817 things.

## 3. What the compiled form looks like

The first ten operations of `VALID-NAME?`, taken from the real image by
`tools/proto-gen.py`:

| source | cells (x86-64) | bytes |
|---|---|---|
| `DUP` | 8 | `0a` |
| `0=` | 8 | `80 00` |
| `?BRANCH` | 16 | `73 04 00` |
| `2DROP` | 8 | `80 01` |
| `LIT 0` | 16 | `30` |
| `EXIT` | 8 | `0b` |
| `OVER` | 8 | `0e` |
| `C@` | 8 | `08` |
| `DUP` | 8 | `0a` |
| `LIT 48` | 16 | `60` |

Whole word and closure: **936 bytes against 154**.

## 4. The encoding

256 byte values, allocated by measured frequency. The census: 15,420
operations, 1,119 distinct symbols, 817 distinct call targets, and the
**128 most frequent symbols cover 77.2%** of all operations.

    0x00-0x3F   64   primitive, index = byte
    0x40-0x5F   32   call to one of the 32 hottest words, index = byte-0x40
    0x60-0x6F   16   push a small literal, value = byte-0x60
    0x70-0x7B   12   reserved for superinstructions
    0x7C             inline counted string follows (count byte, then bytes)
    0x7D             LIT32: a 4-byte signed literal follows
    0x7E             BRANCH: a 2-byte signed offset follows
    0x7F             ?BRANCH: a 2-byte signed offset follows
    0x80-0x83    4   extended call: index = ((byte-0x80)<<8) | next byte
                     -> 1,024 words, against 817 today
    0x84             extended primitive: index = next byte -> 256 more,
                     which is where superinstructions beyond the 12
                     hot slots would live
    0x85-0xFF        free, and deliberately so

Two observations about this table.

**The one-byte tier mixes categories on purpose.** A hot call and a
primitive both cost one byte. That is Latendresse's and Hoyt's central
idea: assign short codes by *frequency*, not by kind. The measured
77.2% assumed exactly this freedom; a fixed partition by category would
do worse, and by how much is not yet measured.

**Branch offsets are fixed at two bytes.** They could be one byte for
most branches, and that would save perhaps another 1,200 bytes — and it
would drag in **assembler relaxation**, iterating to a fixed point
because shortening one branch moves every later target. `GOALS.md`
refused that complexity once already and it should stay refused. The
largest branch offset measured in the image is 2,216, comfortably
inside 16 bits.

## 5. The dispatch loop

```c
#define NEXT() do { b = *ip++; goto *dispatch[b]; } while (0)

L_dup:      ds[-1] ... ;                                  NEXT();

L_hotcall:  RPUSH(ip);
            ip = codebase + wordtab[b - 0x40];            NEXT();

L_smalllit: PUSH(b - 0x60);                               NEXT();

L_qbranch:  { int16_t d = ip[0] | (ip[1] << 8);
              if (POP()) ip += 2; else ip += 2 + d; }     NEXT();

L_call2:    { unsigned w = ((b - 0x80) << 8) | *ip++;
              RPUSH(ip); ip = codebase + wordtab[w]; }    NEXT();

L_exit:     ip = (unsigned char *)RPOP();                 NEXT();
```

One byte load, one indirect branch, exactly as now. `ip` becomes an
`unsigned char *` rather than a cell pointer. The return stack holds
byte pointers.

Note what got *simpler*: today's `NEXT()` tests `t & 1` to tell a call
from a primitive. Here the table does it, and calls stop being a
special case in the loop.

## 6. The word table

`wordtab` is one entry per defined word, holding a **byte offset from
the code base**. 817 words today; at four bytes each that is **3,268
bytes**, against roughly 39,000 saved on the calls it replaces.

It is more position-independent than what it replaces, not less: an
index in the code stream names a word rather than a location, and the
table itself holds offsets rather than addresses. `save-system.4`'s job
gets easier.

## 7. What breaks, concretely

This is the part that matters, and each item below is a real line of
the current system.

**`EXECUTE` is `: EXECUTE ( xt --- ) >R ;`** — it pushes the execution
token onto the return stack and returns, so control simply continues at
the xt. That is beautiful and it works **only because an xt is a
directly executable code address**. Under token threading an xt is an
index, and `EXECUTE` must become a primitive: `ip = codebase +
wordtab[xt]`. Every user of xts follows: `'`, `[']`, `COMPILE,`,
`DEFER`/`IS` in `locals.4`, and the `forth` builtin.

**`>BODY` is `: >BODY ( xt --- a-addr ) CELL+ ;`** — the parameter field
is one cell past the code start. Under a byte code stream, code and data
are no longer the same kind of space, so this identity dissolves. See
section 8.

**`COMPILE,`** currently compiles either an inline primitive token or a
relative offset. It becomes a byte emitter that must choose a tier.

**`,` is `: , ( x --- ) HERE ! 1 CELLS ALLOT ;`** — appends a cell at
`HERE`. There is now more than one `HERE`.

**Words that read inline operands through the return stack.** `(S")`,
`(.")` and `(LOOP)` all do `R>`, read a cell at the return address, and
push a corrected return address back. `(LOOP)`'s is `R> DUP @ + >R`.
The cell they read is no longer a cell at a cell-aligned address, so
**each must be rewritten as a primitive** with encoding-aware operand
handling. Iteration 141 found this class by having to make the
prototype actually run; there may be more of them than the three known.

**`cross.4` hand-embeds dispatch token numbers** for `LIT`, `EXIT`,
`BRANCH`, `0BRANCH` and `R>`. `GOALS.md` warns that a stale one
segfaults the *next* engine at whatever primitive lands on the wrong
value. This change rewrites all of that code.

## 8. The structural consequence: code and data must separate

Today a word's body is code and data in the same cell-granular space.
`CREATE`d bodies, `VARIABLE` cells, dictionary headers and compiled
code are all `ALLOT`ed from one `HERE`.

A byte-granular code stream cannot host cell-aligned data. So the
dictionary splits:

- **Code space**, byte-granular, containing only compiled words.
  `HERE` for code, `B,` to append a byte.
- **Data space**, cell-granular, containing headers, `VARIABLE` bodies,
  `CREATE` bodies and the word table. `,`, `ALLOT`, `ALIGN` unchanged.

This is the single largest piece of work in the proposal, and it is
also independently good. Ertl's *Threaded Code Variations* notes that
separating code and data avoids the cache-consistency penalties x86
pays when instruction and data accesses share a line — a problem this
project has never looked for. It would also make `tools/dict-report.4`
trivially correct instead of having to guess which words are buffers.

**It can be done first, on its own, with cell tokens unchanged.** That
is the key to staging it.

## 9. Staging

Each stage leaves the whole suite green on both cell widths.

1. **Split code space from data space**, keeping one cell per token and
   relative-offset calls. No encoding change. Proves the split and
   pays the cache-consistency dividend on its own. This is where the
   `>BODY`, `,`, `CREATE`, `DOES>` and `save-system.4` work happens.
2. **Make calls indices**, still one cell each. Build and save the word
   table; rewrite `EXECUTE`, `'`, `COMPILE,`, `DEFER`/`IS`. Size gets
   slightly *worse* — a cell per call plus a 3KB table — and that is
   the point: it isolates the semantic change from the encoding change,
   so a regression here has one possible cause.
3. **Narrow the code stream to bytes.** The encoding of section 4.
   Rewrite `(S")`, `(.")`, `(LOOP)` and anything else that reads inline
   operands. This is where the size arrives.
4. **Assign the hot tier by measured frequency**, and put
   superinstructions in the reserved slots. `tools/classify-code.py`
   and `tools/superinstr-search.py` already produce the input.

Stage 1 is worth doing **even if stages 2-4 never happen**. Stage 2 is
not worth doing on its own. Do not start stage 3 without a decision on
section 11.

## 10. What it is worth

Measured, on the real image and the real word:

| | i386 | x86-64 |
|---|---|---|
| compiled code today | 78,024 | 156,048 |
| estimated after | ~24,000 | ~24,000 |
| whole-image ratio | 3.26x | 6.51x |
| one real word, prototyped | 3.04x | 6.08x |

Projected totals: i386 118,912 -> about 65,000; x86-64 211,768 -> about
80,000. A same-architecture `dash` is 136,936 and 129,832. **This is
the only proposal on the table that puts the x86-64 build below
`dash`**, and Iteration 138 established that x86-64 is where this
project is actually behind.

Note the second column of that table: **the byte stream is the same
size on both architectures.** The 1.85x penalty the 8-byte build pays
today is entirely an artifact of one-cell-per-token, and it disappears.

## 11. What is unresolved, and what would kill it

**Speed is not settled.** Iteration 140's synthetic benchmark said
0.98-1.03x; Iteration 141's real-word prototype said 1.14x on x86-64
and 1.28x on i386. The difference is working-set size: 140 measured
cache misses that the byte stream wins by construction, 141 measured a
936-byte word that fits L1 several times over, leaving only decode
cost. The real image's 156KB of code sits between them.

**The decisive experiment has not been run**: the same prototype scaled
to the whole `shell.4` closure, so the working set exceeds L1 the way
the real system's does. That is a bigger generator and **no new engine
work**, and it should be run before stage 3 is started.

If that experiment says 1.15x or worse, this proposal is a **size
change that costs speed**, and it should be weighed against
`GOALS.md` goal 3 the same way Iteration 137's locals change was — not
assumed to be free, which two benchmarks in a row have now wrongly
suggested.

It would also arrive on top of Iteration 137's 42%. Two changes each
costing 15-40% of loop time, landed for size, would leave this shell
meaningfully slower than the one that already loses to `dash` by 236x.
That is a real argument for reverting 137 if this lands, and for
running Stage 2 of `PARSE-EXPAND-PLAN.md` first so there is headroom to
spend.
