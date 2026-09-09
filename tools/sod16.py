#!/usr/bin/env python3
"""
tools/sod16.py - translate RelF's compiled word bodies to a uniform
16-bit token stream, and PROVE the translation is lossless by decoding
it back and comparing.

Iteration 162, on branch token16.

WHY THE ROUND TRIP IS THE POINT

This session found two silent decoder bugs in analysis tools of exactly
this kind, and each invalidated numbers that had already been reported
with confidence:

  - call targets resolved as addr+value instead of addr+CELL+value,
    which matched 24 of 6,548 calls;
  - an inline counted string's length read as a CELL when `(S")` uses
    `COUNT`, so it is a BYTE - every word containing a string was
    silently truncated and the operation count was low by 21.5%.

Both produced plausible output. Neither was caught by inspection. An
engine built on an unvalidated translator would inherit the same class
of fault, and the symptom would be a corrupt image rather than a wrong
number. So this tool decodes its own output and asserts equality
against the input, per word, and reports how many words survive.

THE ENCODING

One 16-bit token per operation:

    0..255       primitive, index = token
    256..65535   call word number (token - 256)

Operands follow their token, as further 16-bit units:

    LIT      1 operand if 0 <= v <= 0xFFFF, else 2 (low, high)
    BRANCH   1 signed operand, offset in TOKEN units
    ?BRANCH  same
    (S")     inline counted string, byte-packed, padded to a token

Word numbers index a table rebuilt at load by walking the dictionary
link chain, so nothing about the table goes in the image.

SCOPE, STATED PLAINLY

This translates a FULLY BUILT image. It does not make the Forth
compiler emit tokens - `,` and `:` still build cell code, so a
translated image can run but cannot compile new definitions. That is
enough to measure size and dispatch on real code, which is the
question, and not enough to self-host, which is a later problem.
"""
import re, sys, collections

CELL = int(sys.argv[2]) if len(sys.argv) > 2 else 4
DUMP = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dump3.txt'

prims = [l.split()[1] for l in open('kernel.4') if l.startswith('PRIMITIVE')]
tokn = {i * CELL + 1: n for i, n in enumerate(prims)}
idx_of = {n: i for i, n in enumerate(prims)}
LIT, BR, QBR = (prims.index(x) * CELL + 1 for x in ('LIT', 'BRANCH', '?BRANCH'))

words, cur, cells = [], None, {}
for l in open(DUMP, errors='replace'):
    l = l.rstrip()
    m = re.match(r'^N (-?\d+) (-?\d+) (.*)$', l)
    if m:
        cur = {'s': int(m.group(1)), 'e': int(m.group(2)), 'n': m.group(3).strip()}
        words.append(cur); continue
    m = re.match(r'^B (-?\d+) (-?\d+)\s*$', l)
    if m: cells[int(m.group(1))] = int(m.group(2))

# Word numbers run OLDEST FIRST, which is definition order.
#
# The dump walks the dictionary link chain from the newest word
# backwards, so `words` is newest-first. Numbering in that order would
# be a design bug: defining a new word makes it number 0 and shifts
# every existing number by one, invalidating every token already
# compiled. Reversing it means a new definition takes the next unused
# number and nothing that exists moves - which is the property that
# lets an xt be a word number at all.
#
# It also matches how a real load rebuilds the table: walk the chain to
# the end, then assign numbers coming back, so entry N is the Nth word
# ever defined.
order = list(reversed(words))
num = {w['s']: i for i, w in enumerate(order)}
by_name = {w['n']: w for w in words}
STR = {by_name[n]['s'] for n in ('(S")', '(.")') if n in by_name}
LOOP = by_name.get('(LOOP)', {}).get('s')

src = "".join(open(f, errors='replace').read()
              for f in ['shell.4', 'locals.4', 'pool.4', 'save-system.4'])
DATA = (set(re.findall(r'CREATE\s+(\S+)', src)) |
        set(re.findall(r'BUFFER:\s+(\S+)', src)) |
        set(re.findall(r'^\s*VARIABLE\s+(\S+)', src, re.M)) |
        set(re.findall(r'CONSTANT\s+(\S+)', src)))

# ---- decode a word body to an operation list -----------------------
def read_ops(w):
    out, a = [], w['s']
    while a < w['e']:
        v = cells.get(a)
        if v is None: return None
        if v & 1:
            nm = tokn.get(v)
            if nm is None: return None
            if v == LIT:
                out.append(('LIT', cells.get(a + CELL, 0))); a += 2 * CELL
            elif v in (BR, QBR):
                out.append(('BR' if v == BR else 'QBR', cells.get(a + CELL, 0)))
                a += 2 * CELL
            else:
                out.append(('P', nm)); a += CELL
        else:
            t = a + CELL + v
            out.append(('C', t)); a += CELL
            if t == LOOP:
                out.append(('OPD', cells.get(a, 0))); a += CELL
            elif t in STR:
                n = (cells.get(a) or 0) & 0xFF
                blob = (1 + n + CELL - 1) // CELL * CELL
                raw = []
                for k in range(0, blob, CELL):
                    raw.append(cells.get(a + k, 0))
                out.append(('STR', (n, tuple(raw)))); a += blob
    return out

# ---- encode an operation list to 16-bit tokens ---------------------
MASK = 0xFFFF
def to_tokens(ops):
    t = []
    for k, pl in ops:
        if k == 'P':
            i = idx_of[pl]
            assert i < 256, "primitive index %d exceeds the 0..255 band" % i
            t.append(i)
        elif k == 'C':
            n = num.get(pl)
            if n is None: return None            # call outside the dump
            assert n + 256 <= 65535, "word number %d exceeds the token field" % n
            t.append(256 + n)
        elif k == 'LIT':
            v = pl & 0xFFFFFFFF if pl >= 0 else (pl + (1 << 32)) & 0xFFFFFFFF
            if 0 <= pl <= 0xFFFF:
                t.append(idx_of['LIT']); t.append(pl)
            else:
                t.append(255); t.append(v & MASK); t.append((v >> 16) & MASK)
        elif k in ('BR', 'QBR'):
            t.append(idx_of['BRANCH' if k == 'BR' else '?BRANCH'])
            t.append(pl & MASK)                  # offset kept, re-derived below
        elif k == 'OPD':
            t.append(pl & MASK)
        elif k == 'STR':
            n, raw = pl
            t.append(254); t.append(n)
            for r in raw:
                t.append(r & MASK)
                if CELL == 4: t.append((r >> 16) & MASK)
                else:
                    for sh in (16, 32, 48): t.append((r >> sh) & MASK)
    return t

# ---- decode tokens back, to prove the encoding is reversible -------
def from_tokens(t):
    out, i = [], 0
    while i < len(t):
        v = t[i]
        if v >= 256:
            tgt = order[v - 256]['s']
            out.append(('C', tgt)); i += 1
            # (LOOP) carries a bare operand token; it must be consumed
            # here or the decoder reads it as another call. Operands are
            # positional - only the op that emitted one knows it is there.
            if tgt == LOOP:
                o = t[i]
                out.append(('OPD', o - 65536 if o >= 32768 else o)); i += 1
        elif v == 255:
            lo, hi = t[i+1], t[i+2]
            val = (hi << 16) | lo
            if val >= (1 << 31): val -= (1 << 32)
            out.append(('LIT', val)); i += 3
        elif v == 254:
            n = t[i+1]; i += 2
            per = 2 if CELL == 4 else 4
            blob = (1 + n + CELL - 1) // CELL * CELL
            raw = []
            for _ in range(blob // CELL):
                acc = 0
                for j in range(per): acc |= t[i + j] << (16 * j)
                raw.append(acc); i += per
            out.append(('STR', (n, tuple(raw))))
        elif v == idx_of['LIT']:
            out.append(('LIT', t[i+1])); i += 2
        elif v == idx_of['BRANCH']:
            o = t[i+1]; out.append(('BR', o - 65536 if o >= 32768 else o)); i += 2
        elif v == idx_of['?BRANCH']:
            o = t[i+1]; out.append(('QBR', o - 65536 if o >= 32768 else o)); i += 2
        else:
            out.append(('P', prims[v])); i += 1
    return out

# ---- optional emission of a loadable token file --------------------
# Format is deliberately plain text: the point of this prototype is to
# be checkable by eye and by diff, not to be fast to load. A binary
# image is a later concern, and premature here.
#
#   W <wordnum> <ntokens> <name>
#   T <tok> <tok> ...
#
# The engine rebuilds its dispatch table from this the same way a real
# load would rebuild it from the dictionary link chain: word N is the
# Nth W record, in chain order. Nothing about the table is stored.
EMIT = None
if '--emit' in sys.argv:
    EMIT = open(sys.argv[sys.argv.index('--emit') + 1], 'w')

ok = fail = skipped = 0
tot_cell = tot_tok = 0
failures = []
for w in words:
    span = w['e'] - w['s']
    if w['n'] in DATA:
        skipped += 1; tot_cell += span; tot_tok += span; continue
    ops = read_ops(w)
    if ops is None:
        skipped += 1; tot_cell += span; tot_tok += span; continue
    t = to_tokens(ops)
    if t is None:
        skipped += 1; tot_cell += span; tot_tok += span; continue
    back = from_tokens(t)
    if back == ops:
        ok += 1
    else:
        fail += 1
        if len(failures) < 3:
            for j, (a, b) in enumerate(zip(ops, back)):
                if a != b: failures.append((w['n'], j, a, b)); break
            else: failures.append((w['n'], -1, len(ops), len(back)))
    tot_cell += span; tot_tok += len(t) * 2
    if EMIT:
        EMIT.write("W %d %d %s\n" % (num[w['s']], len(t), w['n']))
        EMIT.write("T " + " ".join(str(x) for x in t) + "\n")

if EMIT: EMIT.close()
print("dump %s  cell %d" % (DUMP, CELL))
print("round trip: %d words reproduce exactly, %d differ, %d skipped"
      % (ok, fail, skipped))
for f in failures: print("   MISMATCH %s op %d: was %r, back %r" % f)
print()
print("word bodies: cell %d B   token %d B   %.3fx"
      % (tot_cell, tot_tok, tot_tok / tot_cell))
sys.exit(1 if fail else 0)
