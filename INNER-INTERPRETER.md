# The inner interpreter: a design brief

> **Answered in `CV8.md` (Iteration 189).** Short version: the 1.25x
> was mostly VM registers living in statics (~20%) and executed NOOP
> padding (17% of dispatches), not the dependent load; a byte stream
> whose calls are 2-byte compressed pointers (`base + v << S`) is
> 0.43x/0.64x the size and ~1.6x the speed of today's build. The brief
> below is left as written.

Written at Iteration 188, on branch `token16`, to open a design
discussion rather than to record a decision. Everything here is
measured unless it says otherwise, and it says where each number came
from so it can be re-run or disbelieved.

Read `GOALS.md` first for what the project is for, and `SOD16.md` for
the token-encoding work this brief comes out of. This file does not
repeat them; it collects the parts that constrain the inner
interpreter, and adds what was learned by building one and measuring
it.

---

## 1. What "the inner interpreter" means here

`relf.c`'s `NEXT`, and nothing else:

```c
#define NEXT() do { \
        t = CELL(ip); ip += CELL_BYTES; \
        if (t & 1) goto *dispatch[(t - 1) >> CELL_SHIFT]; \
        RPUSH(ip); ip += t; \
        goto next; \
    } while (0)
```

One cell per operation. **Odd** is a primitive: the value is the
primitive's index times the cell width, plus one, so the shift recovers
the index. **Even** is a call: the value is a byte offset from the cell
after it to the target's body. The offset is relative, which is what
makes an image relocatable.

A word body is a sequence of these, ending in `EXIT`. There is no
separate code field. `ip` is a raw host address.

That is the whole design. Everything below is about what could replace
it and what any replacement has to survive.

---

## 2. The constraints that kill designs

These are not preferences. Each one has already invalidated at least
one plausible idea.

### 2.1 A cell must be as wide as a host pointer

`CELL(reg)` is `*(UNS64*)(reg)` — it dereferences the value as a real
pointer. This is deliberate and load-bearing: it is what lets the image
be relocated to wherever `mmap` puts it. It means any encoding that
wants a narrower cell has to answer what happens to every stored
address, and the answer cannot be "truncate".

### 2.2 Seven words read inline operands *in Forth*

`kernel.4` line 252 states it: `(LOOP)` and `(+LOOP)` are followed by
an inline loop address, `(?DO)` and `(LEAVE)` by an inline leave
address. `(S")`, `(.")` and `(ABORT")` are followed by an inline
counted string. `(POSTPONE)` is an eighth — its own comment says "has
inline argument".

All of them reach the operand with `R>` and read it with cell-width
arithmetic: `DUP @ +`, `CELL+`, `COUNT ... ALIGNED`. **They are Forth
source, not engine C.** Any change to how code is represented has to
either keep their arithmetic valid or change them.

The rule that made SOD16 work was: *only the opcode stream changes;
inline operands and strings keep cell granularity and cell alignment.*
That cost padding and bought a kernel that needed no edits at all.

### 2.3 An xt is an address, not an index

```forth
: EXECUTE ( xt --- )  >R ;
```

`EXECUTE` is pure Forth and is not a primitive. It makes the xt the
return address and lets `EXIT` jump to it. `COLD` agrees:
`BOOT @ ?DUP IF START @ + EXECUTE THEN`.

So an xt must be something `ip` can be set to. A design where "an xt is
a word number" contradicts this, and that contradiction stood
unexamined in `SOD16.md` for about twenty iterations, costing at least
two wrong turns. A *call token* may be an index; an *xt* may not.

### 2.4 Nothing may store an absolute address

`SS-SCRUB` exists because a saved image is reloaded at a different
base. `cross.4`'s link fields are relative "so it survives relocation".
Every offset in the image is relative to something.

Worth knowing: `(?DO)` and `(LEAVE)` *do* compile an absolute address —
`RESOLVE-LEAVE` stores a bare `HERE`. It is latent, not live, because
both words have zero call sites in the current image. Anything that
adds a `?DO` or a `LEAVE` to `shell.4` breaks saved images before it
reaches any of this.

### 2.5 Both cell widths, always

Every commit builds and passes at 4-byte and 8-byte cells. A design
that is only worked out for 64-bit is not worked out. `tests/verify` is
the whole check and it must say VERIFIED.

---

## 3. What was built, and what it measured

A complete 16-bit token encoding (`SOD16.md`), translated from the cell
image, booting and running the shell at both cell widths.

**Encoding.** One 16-bit token per operation. `< 256` is a primitive
index; `>= 256` is word number minus 256, resolved through a word table
built at load time by walking the link chain. Inline operands and
strings stay cell-granular.

**Correctness.** 556 word bodies round-trip exactly, 0 differ, at both
widths. Eleven relocation categories, all resolving with none
unresolved. `tests/diff` 20/20 at both widths. `tests/shell` passes
except `run-forth`, which needs runtime compilation — the one thing not
built.

### 3.1 Size — SOD16 wins clearly

Stripped engine plus image, the way `tests/sizes` counts:

| | engine | image | total | |
|---|---|---|---|---|
| x86-64 cell | 22,744 | 206,416 | 229,160 | |
| x86-64 token | 22,744 | 83,496 | **106,240** | 0.464x |
| `dash` | 129,784 | — | 129,784 | |
| i386 cell | 17,808 | 109,876 | 127,684 | |
| i386 token | 17,808 | 70,456 | **88,264** | 0.691x |

The two engines strip to *identical* sizes. At 106,240 the token build
is smaller than `dash`, which inverts the headline in `GOALS.md`'s size
table.

Bodies alone go to 0.28x. Headers, names and data bodies do not shrink
at all and are 35,688 bytes of the x86-64 image — which is why the
whole-image figure is the one to quote.

### 3.2 Speed — SOD16 loses, inherently

`tests/bench`, token image against `./relf kernel-shell.img`, word sets
matched:

| workload | token | cell | |
|---|---|---|---|
| loop | 1099.1 ms | 880.4 ms | **1.25x slower** |
| spawn | 157.1 ms | 143.3 ms | 1.10x slower |
| start | 342.3 ms | 275.1 ms | 1.24x slower |

Absolute times drift several percent between runs. **Quote the ratio.**

### 3.3 Why — one dependent load

`tools/thread-chase.S` writes both call mechanisms by hand and
`tools/thread-chase.c` drives them over the same pseudo-random slot
sequence, so cache behaviour is matched and only the mechanism differs:

| slots | asm ratio | C ratio |
|---|---|---|
| 1,082 (this image's word count) | 1.65 | 1.68 |
| 4,096 | 1.73 | 1.69 |
| 65,535 | 1.86 | 1.89 |

**Hand-written assembly gives the same ratio as C.** The cost is the
mechanism, not codegen:

```
cell     ip = ip + CELL_BYTES + *(long *)ip     load, then ALU
token    ip = wordtab[*(short *)ip]             load, then a
                                                DEPENDENT load
```

1.91 ns against 3.15 ns per step — roughly 5 cycles against 10, one L1
latency against two serialised. **Threaded code is latency-bound on
this chain: nothing can start until the next `ip` is known.** That
sentence is the single most useful thing in this brief.

The call path alone is ~1.7x while the whole engine is 1.25x. The
difference is the primitives, where SOD16 is no worse. So 1.25x is a
blend and moves with the call density of the code being run.

### 3.4 The word table is not free

`SOD16.md` called it "OUTSIDE the image", which is true of the image's
size and says nothing about the cache. It is 8 bytes per word of hot,
randomly-accessed memory, touched on **every call**. At 1,082 words it
is 8.7 KB and cheap; at 65,535 words it is 511 KB and the ratio
worsens to 1.86. It scales with the dictionary.

---

## 4. The design space

Listed to be argued with. Only the first two have been measured.

**A. Cell threading (today).** One host-pointer-wide cell per
operation, relative call offsets. Fastest measured. Largest. The
offset is already in a register when it is needed, which is the whole
of its advantage.

**B. SOD16, 16-bit tokens with a word table.** 0.46x size, 1.25x
slower. Measured end to end and it boots.

**C. Hybrid near/far calls.** A token carries a relative offset when
the target is close and indexes the table only when it is not. Cuts
the dependent load on the common case. Costs the single-compare decode
that won the original comparison, and needs a rule for what "close"
means that a translator can apply and a loader can trust. **Not
measured.** This is the obvious response to §3.3 and nobody has tried
it.

**D. Wider tokens — 24 or 32 bit.** A 32-bit token could hold a
relative offset directly, no table at all, on both cell widths. Size
would land between A and B. Is the size/speed point better than B? A
translator already exists that could answer this cheaply.

**E. Subroutine threading / JIT / AOT.** `GOALS.md` phase 4 and goal 2.
Native calls instead of an interpreter loop. Out of scope for a
brainstorm about `NEXT`, but it is where the project is going, and a
representation that makes it harder is a bad choice.

**F. Leave it alone.** `GOALS.md` ranks minimalism above performance and
names size as a goal. 57% smaller for 25% slower on a shell — where
`spawn`, the most realistic workload, is only 10% slower because
fork/exec dominates — may simply be the right trade. The strongest
argument for SOD16 was never speed; it was that `sod16.c` is `relf.c`
with eight executable lines changed.

---

## 5. The open questions

1. Is the dependent load avoidable at all while keeping a token
   narrower than a pointer? C is the only idea on the table.
2. Should the decision be made on `loop` or on `spawn`? They disagree
   by more than a factor of two on how bad SOD16 is.
3. Does the choice of representation constrain phase 3 (a Forth-hosted
   compiler emitting tokens) or phase 4 (JIT/AOT)? Phase 3 is unbuilt,
   so changing the representation is cheap *now* and expensive later.
4. Is there a representation that is smaller than A and has no
   dependent load? D is the candidate and it has never been costed.
5. `GOALS.md`'s encoding comparison chose SOD16 partly on a decode
   microbenchmark that measured the part SOD16 makes cheaper and
   omitted the part it makes dearer. **What else in that table is
   measuring the wrong thing?**

---

## 6. How to argue about this

The method that worked, stated because it kept catching things:

- **Check against the source, not against these notes.** `SOD16.md` was
  confidently wrong about branch offsets, about xts, and about the word
  table being free. Each error cost iterations. `grep` beats recall.
- **A measurement that agrees with itself proves nothing.** A round
  trip only tests a transformation the two directions disagree about.
  Sabotage the transformation on purpose and confirm the harness
  notices.
- **A count is not evidence that anything was written.** One fix
  reported "926 resolved" and changed no bytes. Check the artifact.
- **Run the control first.** A probe that fails on `relf` too says
  nothing about anything.
- **Distrust a number that improves too much.** A rule that truncated
  106 word bodies and dropped 49 KB of code was caught by a size ratio
  that got better than it should have, with every test still green.
- **Quote ratios, not absolutes**, for anything timed here.

---

## 7. Where the code is

| | |
|---|---|
| `relf.c` | the cell engine; `NEXT` at line ~342 |
| `sod16.c` | the token engine; `relf.c` plus eight executable lines |
| `tools/sod16.py` | translator and round-trip proof |
| `tools/layout.py` | whole-image layout, relocation, `--emit-image` |
| `tools/thread-chase.S` `.c` | the two call mechanisms by hand, and the driver |
| `tools/dict-dump-addr.4` | the dump everything above reads |
| `tests/bench` | takes `THIS_SH`; always adds `./relf kernel-shell.img` |

To reproduce the token build:

```sh
printf 'S" pool.4" INCLUDED\nS" locals.4" INCLUDED\nS" save-system.4" INCLUDED\nS" shell.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n' \
  | ./relf kernel.img | tr -d '\r' > /tmp/d64.txt
python3 tools/layout.py /tmp/d64.txt 8 --emit-image /tmp/s.s16
cc -O2 -o /tmp/sod16 sod16.c
/tmp/sod16 /tmp/s.s16 -c 'echo it works'
```

`tr -d '\r'` on every dump, always. Nothing after `END-CROSS`
cross-compiles. `LINE-MAX` eats long one-liner probes and looks like an
engine bug. `."` prints nothing at this kernel's interpreter — it is
compile-only. A `DO`/`+LOOP` typed at the interpreter runs once and
stops.
