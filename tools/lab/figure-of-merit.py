#!/usr/bin/env python3
"""figure-of-merit.py - compare every inner-interpreter design on one
axis: speed, size and complexity combined.

    Q = (1/time) / (size^a * complexity^b)      normalised to design A

All three inputs are ratios against design A (today's `token16` engine),
so Q is dimensionless and Q(A) = 1. Bigger is better.

  time        median of the four script workloads, paired CPU time
              (tools/lab/bench-vm.py). `start` is reported but excluded:
              it is dominated by compiling shell.4 from source, not by
              the VM.
  size        stripped engine + image, the way tests/sizes counts.
  complexity  a rubric, below. This is the one input that is a
              judgement, not a measurement, so `--sens` shows how the
              ranking moves as its weight changes.

The exponents a and b say how much a doubling of size or complexity
must buy in speed to be worth it. a = b = 1 means "2x the size must
buy 2x the speed". GOALS.md ranks size above speed, so a = 1 is a
defensible default; b = 0.5 treats complexity as real but secondary.

COMPLEXITY RUBRIC (points; each is a thing that can be got wrong, and
that a reader of the system must hold in their head)

  engine .text over baseline, per 1 KB            1.0 each
  new invariant the COMPILER must maintain        2.0 each
  new invariant the LOADER/image format carries   1.0 each
  new coupling between the engine and Forth code  3.0 each
  a hard ceiling that needs future work           2.0 each

Engine-only changes (TOS, shared call path) cost .text and nothing
else: they cannot produce a wrong image, only a slow or buggy engine,
which the test suite catches.
"""
import sys, json

A = 'A cell (token16)'
# ---- measured inputs -------------------------------------------------
# time: median over loop/fn/str/arith, ratio to A (tools/lab/bench-vm.py,
#       4 rounds, x86-64; see PROGRESS.md Iteration 192)
# size: stripped engine + image, bytes
D = [
    # name                        time64  size64   time32  size32
    # O and S are NOT whole-system measurements - see the notes below.
    ('O relf 2016 (original)',     None,  None,    2.21,  30300),
    ('S SOD32 (modelled)',         1.15,  208584,  1.67,  117396),
    ('A cell (token16)',           1.000, 229160,  1.000, 127684),
    ('B cell + reg locals',        0.791, 229160,  0.795, 127684),
    ('C SOD16 table',              0.778, 106776,  0.800, 88672),
    ('D CPT16',                    0.750, 106776,  0.793, 88672),
    ('E CPT16 + prims + fold',     0.631, 110232,  0.652, 87904),
    ('F CV8',                      0.653,  99488,  0.590, 81224),
    ('G CV8 + TOS',                0.568,  99488,  0.571, 77196),
    ('H CV8 + specialisations',    0.197,  97080,  0.194, 74792),
]

# ---- complexity rubric, scored ---------------------------------------
# (text_kb_over_A, compiler_invariants, format_invariants,
#  engine<->forth couplings, ceilings)
C = {
 # the 2016 original: same cell threading, but a switch dispatch, no
 # bounds checks, no 64-bit support, no image header/magic
 'O relf 2016 (original)':  (0.0, 0, 0, 0, 0),
 # packed 5-bit fields: pack/unpack in the engine, a field counter, the
 # compiler must pack and must not split a pack across a call/branch,
 # 32 opcodes only (escape needed for the rest), 32-bit only
 'S SOD32 (modelled)':      (0.5, 3, 2, 0, 2),
 'A cell (token16)':        (0.0, 0, 0, 0, 0),
 # pure C refactor: same image, same format, nothing new to get wrong
 'B cell + reg locals':     (0.0, 0, 0, 0, 0),
 # tokens; word table (load-time chain walk + DOES> side table +
 # xt<->word-number map = 3 format invariants); LIT32 split; operand
 # cell-alignment; ceiling: 65280 words
 'C SOD16 table':           (1.0, 2, 3, 0, 1),
 # tokens, calls are scaled offsets: no table, but call targets must be
 # aligned; LIT32 split; ceiling: 15-bit reach
 'D CPT16':                 (0.9, 2, 1, 0, 1),
 # + DOVAR/DODOES primitives (data-body layout) and folded prim;EXIT
 # (compiler must not fold when a branch targets the EXIT)
 'E CPT16 + prims + fold':  (2.2, 4, 2, 0, 1),
 # + variable-length bytes: LIT8/16/32 choice, unaligned operands,
 # byte branch offsets, opcode-vs-call byte test
 'F CV8':                   (3.1, 6, 3, 0, 1),
 # TOS is engine-only: every primitive must spill/fill, caught by tests
 'G CV8 + TOS':             (4.2, 6, 3, 0, 1),
 # + 28 specialised opcodes; locals opcodes reach into locals.4's data
 # structures (2 couplings: save-stack layout, fallback entry points);
 # exact-body matching for the tiny words; opcode space nearly full
 'H CV8 + specialisations': (6.0, 9, 4, 2, 2),
}
W = (1.0, 2.0, 1.0, 3.0, 2.0)

def cplx(n):
    return 1.0 + sum(w * x for w, x in zip(W, C[n]))

def table(bits, a, b):
    # rows with a missing measurement are skipped for that width
    base = [r for r in D if r[0] == A][0]
    base_s = base[2] if bits == 64 else base[4]
    base_c = cplx(A)
    rows = []
    for name, t64, s64, t32, s32 in D:
        t = t64 if bits == 64 else t32
        s = s64 if bits == 64 else s32
        if t is None or s is None: continue
        speed = 1.0 / t
        sr = s / base_s
        cr = cplx(name) / base_c
        rows.append((name, speed, sr, cr, speed / (sr ** a * cr ** b)))
    return rows

def show(bits, a, b):
    print("\n=== %d-bit   Q = speed / (size^%.2g * complexity^%.2g),  A = 1.00"
          % (bits, a, b))
    print("%-26s %6s %7s %7s %8s" % ("design", "speed", "size", "cplx", "Q"))
    for n, sp, sr, cr, q in sorted(table(bits, a, b), key=lambda r: -r[4]):
        print("%-26s %6.2fx %6.2fx %6.2fx %7.2f" % (n, sp, sr, cr, q))

show(64, 1.0, 0.5)
show(32, 1.0, 0.5)

print("\n=== sensitivity: winner (and Q of H) as the weights change, 64-bit")
print("%-28s %-26s" % ("weights", "best design"))
for a, b, lbl in [(0, 0, "speed only"),
                  (1, 0, "size matters, complexity free"),
                  (0, 1, "complexity matters, size free"),
                  (1, 0.5, "default"),
                  (1, 1, "size and complexity full weight"),
                  (2, 1, "size double-weighted"),
                  (0.5, 2, "complexity double-weighted")]:
    r = sorted(table(64, a, b), key=lambda x: -x[4])
    print("%-28s %-26s (H=%.2f, top=%.2f)" % (lbl, r[0][0], 
          [x[4] for x in r if x[0].startswith('H')][0], r[0][4]))
