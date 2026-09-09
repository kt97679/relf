#!/usr/bin/env python3
"""
tools/encoding-census.py - model competing VM encodings against RelF's
own compiled image, and report what each would cost.

Added in Iteration 156. Every encoding number quoted in
ENCODING-COMPARISON.md comes from this script; regenerate rather than
transcribe, because the numbers move whenever shell.4 does.

WHAT IT MEASURES

The compiled BODY of every word in the image: the operation stream, not
the headers and not the engine. Sizes are reported in cells and in
bytes at both cell widths, since the whole point of comparing these
schemes is that some scale with cell width and some do not.

It does NOT measure speed. Several of these schemes trade decode work
for density, and nothing here can see that - see the dynamic profile
section of ENCODING-COMPARISON.md, which needs an instrumented engine.

INPUT

  tools/dict-dump-addr.4 output, default /tmp/dump3.txt. See that file's
  header for how to produce it. Cell width of the DUMP is 4 (it is
  produced by relf32); that is the width the addresses and tokens are
  in, independent of which width we are costing.

HONESTY NOTES, so the numbers are read correctly

  - Modelling SOD32's encoding on RelF's program is a comparison of
    ENCODINGS, not of systems. SOD32's own kernel is a different
    program with a different opcode mix, and its published benchmarks
    (README.md) measured a different engine on 20-year-old hardware.
    What this answers is "what would SOD32's instruction format cost
    for RelF's code", which is the only question that can be asked
    fairly here.
  - The token-threaded byte stream uses assumed field widths and is
    the least grounded row. TOKEN-THREADING.md's own worked sample is
    the better datum for that scheme.
  - Macro inlining is selected per encoding by profitability, because
    inlining a 2-op word called twenty times is a size LOSS. An earlier
    version inlined every eligible word and made the image bigger.
"""
import re, sys, collections

DUMP = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dump3.txt'
CELL = 4                      # width of the dump, not of the costing

prims = [l.split()[1] for l in open('kernel.4') if l.startswith('PRIMITIVE')]
tok = {i * CELL + 1: n for i, n in enumerate(prims)}
LIT = prims.index('LIT') * CELL + 1
BR = prims.index('BRANCH') * CELL + 1
QBR = prims.index('?BRANCH') * CELL + 1

words, cur, cells = [], None, {}
for l in open(DUMP, errors='replace'):
    l = l.rstrip()
    m = re.match(r'^N (-?\d+) (-?\d+) (.*)$', l)
    if m:
        cur = {'s': int(m.group(1)), 'e': int(m.group(2)), 'n': m.group(3).strip()}
        words.append(cur); continue
    m = re.match(r'^B (-?\d+) (-?\d+)\s*$', l)
    if m: cells[int(m.group(1))] = int(m.group(2))

name_of = {w['s']: w['n'] for w in words}
by_name = {w['n']: w for w in words}
# Runtimes whose operand is NOT a token: an inline counted string, or
# (LOOP)'s offset cell. classify-code.py calls these "the fifth
# not-a-token case"; missing them corrupts every downstream count.
STR = {by_name[n]['s'] for n in ('(S")', '(.")') if n in by_name}
LOOP = by_name.get('(LOOP)', {}).get('s')

def decode(w):
    """-> [('p',name) | ('LIT',value) | ('BR',kind) | ('c',target)] or None"""
    out, a = [], w['s']
    while a < w['e']:
        v = cells.get(a)
        if v is None: break
        if v & 1:
            nm = tok.get(v)
            if nm is None: return None
            if v == LIT:
                out.append(('LIT', cells.get(a + CELL, 0))); a += 2 * CELL; continue
            if v in (BR, QBR):
                out.append(('BR', 'u' if v == BR else 'z')); a += 2 * CELL; continue
            out.append(('p', nm)); a += CELL
        else:
            t = a + CELL + v          # relative: ip is past the cell already
            out.append(('c', t)); a += CELL
            if t == LOOP: a += CELL
            elif t in STR:
                n = (cells.get(a) or 0) & 0xFF   # COUNT: length is a BYTE
                a += (1 + n + CELL - 1) // CELL * CELL
    return out

body = {}
for w in words:
    d = decode(w)
    if d is not None: body[w['s']] = d

def core(d):
    return d[:-1] if d and d[-1] == ('p', 'EXIT') else d

freq = collections.Counter(n for d in body.values() for k, n in d if k == 'p')
lits = [v for d in body.values() for k, v in d if k == 'LIT']

# ---------------------------------------------------------------
# Encoders. Each returns a cell (or byte) count for a list of streams.
# ---------------------------------------------------------------
def alpha(n, exclude=()):
    return set(x for x, _ in freq.most_common(n + len(exclude)) if x not in exclude)

def enc_current(sts, _w):
    """RelF today: one cell per op, two for LIT and branches."""
    return sum(2 if k in ('LIT', 'BR') else 1 for st in sts for k, _ in st)

def make_packed(slots, opcodes, litrange, litslots, hasbranch, hot=()):
    """Generic tagged-pack encoder.

    slots     opcode fields per cell
    opcodes   size of the packable alphabet
    litrange  (lo,hi) inline-literal range, or None
    litslots  fields an inline literal consumes
    hasbranch True if unconditional BRANCH gets its own tag class;
              False models SOD32, which synthesises it as push0+JUMPZ
    hot       set of call targets foldable into the tag byte's spare bits
    """
    A = alpha(opcodes, exclude=('EXIT',))
    def enc(sts, _w):
        tot = 0
        for st in sts:
            used = 0
            def flush():
                nonlocal used, tot
                if used: tot += 1
                used = 0
            for k, pl in st:
                if k == 'c':
                    if pl in hot and used: tot += 1; used = 0   # folds into this cell
                    else: flush(); tot += 1
                elif k == 'BR':
                    flush()
                    tot += 1
                    if pl == 'u' and not hasbranch: used = 1    # push0 costs a field
                elif k == 'LIT':
                    if litrange and litrange[0] <= pl <= litrange[1]:
                        if used + litslots > slots: flush()
                        used += litslots
                    else:
                        flush(); tot += 2                        # lit op + operand cell
                elif pl == 'EXIT':
                    tot += 1; used = 0                           # return flag on the pack
                else:
                    if pl in A:
                        if used + 1 > slots: flush()
                        used += 1
                    else:
                        flush(); tot += 1                        # escape
            flush()
        return tot
    return enc

def enc_token(sts, _w):
    """Byte stream. Least grounded row - see module docstring."""
    A = alpha(32, exclude=('EXIT',))
    nb = 0
    for st in sts:
        for k, pl in st:
            if k == 'c': nb += 2
            elif k == 'BR': nb += 3
            elif k == 'LIT': nb += 1 if 0 <= pl < 16 else (2 if -128 <= pl < 128 else 5)
            else: nb += 1 if pl in A else 2
    return nb

def enc_u16(sts, _w):
    """Uniform 16-bit token (Iteration 159/160). One token per
    operation: 0..255 primitive or inline form, 256..65535 a word
    number. Operands follow as tokens - LIT one or two depending on
    magnitude, branch one signed offset. No tag, no varint, no packing,
    no branch on token width. Returned in BYTES, since it does not
    scale with cell width."""
    n = 0
    for st in sts:
        for k, pl in st:
            if k == 'LIT': n += 2 if 0 <= pl <= 0xFFFF else 3
            elif k == 'BR': n += 2
            else: n += 1
    return n * 2

def expand(macros):
    out = []
    for s, d in body.items():
        if s in macros: continue
        st = []
        for k, pl in d:
            if k == 'c' and pl in macros: st.extend(core(body[pl]))
            else: st.append((k, pl))
        out.append(st)
    return out

def with_macros(enc, w):
    cand = [s for s, d in body.items() if 0 < len(core(d)) <= 8]
    base = enc(expand(set()), w)
    ms = {s for s in cand if enc(expand({s}), w) < base}
    return ms, enc(expand(ms), w)

# hot-call targets, for the byte scheme's spare tag bits
tg = collections.Counter(pl for d in body.values() for k, pl in d if k == 'c')
HOT = {t for t, _ in tg.most_common(15)}

SCHEMES = [
  ("RelF today (1 cell/op)",            enc_current,                                        'cell'),
  ("SOD32 (5-bit x6, no BRANCH tag)",   make_packed(6, 32, None, 0, False),                 'cell'),
  ("SOD32 fields + inline literals",    make_packed(6, 29, (-7, 8), 1, False),              'cell'),
  ("tagged nibble (4-bit x7)",          make_packed(7, 14, (-7, 8), 2, True),               'cell'),
  ("tagged byte (8-bit x3/x7)",         make_packed(3, 254, (-128, 127), 2, True),          'cell'),
  ("tagged byte + hot-call (15)",       make_packed(3, 254, (-128, 127), 2, True, HOT),     'cell'),
  ("uniform 16-bit token",              enc_u16,                                            'byte'),
  ("token-threaded byte stream",        enc_token,                                          'byte'),
]

print("words %d, ops %d, call sites %d, literals %d"
      % (len(body), sum(len(d) for d in body.values()), sum(tg.values()), len(lits)))
print()
print("%-34s %9s %9s %11s %11s" % ("scheme", "cells", "macros", "i386 B", "x86-64 B"))
for lbl, enc, unit in SCHEMES:
    ms, n = with_macros(enc, 4)
    if unit == 'byte':
        print("%-34s %9s %9d %11d %11d" % (lbl, "-", len(ms), n, n))
    else:
        print("%-34s %9d %9d %11d %11d" % (lbl, n, len(ms), n * 4, n * 8))
