#!/usr/bin/env python3
"""
tools/tokenize-image.py - translate RelF's compiled word bodies into a
uniform 16-bit token stream, and report what it costs.

Iteration 160. This is a PROTOTYPE MEASUREMENT, not a working engine.
It answers "what would the image weigh" on real compiled code rather
than on a synthetic stream, which is what every previous number in this
line of work was based on.

THE ENCODING

Every operation is one 16-bit token:

    0..255      primitive or inline form (the engine's own opcodes)
    256..65535  word number: call the (v-256)th entry of the
                dictionary, in link-chain order

Operands follow their token as further 16-bit units:

    LIT16  value fits 16 bits unsigned   -> 1 token operand
    LIT32  otherwise                     -> 2 token operands
    BRANCH / ?BRANCH                     -> 1 token, signed offset in
                                            token units

No tag bits, no varint, no packing, no branch on token width. Decode is
one aligned 16-bit load, one compare against 256, one branch.

THE TABLE IS NOT IN THE IMAGE

Word numbers index a table that is rebuilt at startup by walking the
dictionary link chain, so it is derived data: never saved, nothing for
SS-SCRUB to clean, holds absolute addresses (so dispatch is one load
with no base add), and grown by realloc outside mem[] so it never
collides with HERE. That is why this script reports the token stream
size WITHOUT a table - the table costs image bytes nowhere.

WHAT IS NOT MODELLED

Headers are left exactly as they are - 16,576 bytes of the image that
this scheme does not touch. Data words (VARIABLE, BUFFER:, CREATE) keep
their bodies verbatim; only code bodies are translated.

Branch offsets are re-expressed in token units, which changes their
magnitude; this checks they still fit 16 bits signed rather than
assuming it.
"""
import re, sys, collections

DUMP = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dump3.txt'
CELL = int(sys.argv[2]) if len(sys.argv) > 2 else 4

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

# Word numbers in link-chain order, which is the order the dump walks
# and the order a startup rebuild would reproduce.
num = {w['s']: i for i, w in enumerate(words)}
by_name = {w['n']: w for w in words}
STR = {by_name[n]['s'] for n in ('(S")', '(.")') if n in by_name}
LOOP = by_name.get('(LOOP)', {}).get('s')

src = "".join(open(f, errors='replace').read()
              for f in ['shell.4', 'locals.4', 'pool.4', 'save-system.4'])
data = (set(re.findall(r'CREATE\s+(\S+)', src)) |
        set(re.findall(r'BUFFER:\s+(\S+)', src)) |
        set(re.findall(r'^\s*VARIABLE\s+(\S+)', src, re.M)) |
        set(re.findall(r'CONSTANT\s+(\S+)', src)))

stat = collections.Counter()
tot_cell = tot_tok = 0
undecoded = 0
big_branch = 0
maxword = 0

for w in words:
    span = w['e'] - w['s']
    if w['n'] in data:
        tot_cell += span; tot_tok += span     # data bodies unchanged
        stat['data words'] += 1
        continue
    a = w['s']; out = 0; ok = True
    while a < w['e']:
        v = cells.get(a)
        if v is None: break
        if v & 1:
            nm = tok.get(v)
            if nm is None: ok = False; break
            if v == LIT:
                val = cells.get(a + CELL, 0)
                out += 2 if 0 <= val <= 0xFFFF else 3
                stat['LIT16' if 0 <= val <= 0xFFFF else 'LIT32'] += 1
                a += 2 * CELL; continue
            if v in (BR, QBR):
                off = cells.get(a + CELL, 0)
                # offset is in bytes of cell code; in token units it is
                # roughly halved on i386, quartered on x86-64 - but the
                # stream also shrinks, so re-derive conservatively
                if abs(off // CELL) > 32767: big_branch += 1
                out += 2; stat['branch'] += 1
                a += 2 * CELL; continue
            out += 1; stat['primitive'] += 1
            a += CELL
        else:
            t = a + CELL + v
            out += 1; stat['call'] += 1
            if t not in num: stat['call to unknown'] += 1
            else: maxword = max(maxword, num[t])
            a += CELL
            if t == LOOP: out += 1; a += CELL
            elif t in STR:
                n = (cells.get(a) or 0) & 0xFF     # COUNT: length is a BYTE
                blob = (1 + n + CELL - 1) // CELL * CELL
                out += (blob + 1) // 2        # inline bytes, packed
                a += blob
    if not ok:
        undecoded += 1
        tot_cell += span; tot_tok += span
        continue
    tot_cell += span
    tot_tok += out * 2
    stat['code words'] += 1

print("dump %s, cell width %d" % (DUMP, CELL))
print("words %d   code %d   data %d   undecoded %d"
      % (len(words), stat['code words'], stat['data words'], undecoded))
print("highest word number used by a call: %d  (16-bit field holds %d)"
      % (maxword, 65535 - 256))
print("branch offsets needing more than 16 signed bits: %d" % big_branch)
print()
print("operation census: " + "  ".join("%s %d" % (k, v) for k, v in stat.most_common()
                                       if k not in ('code words', 'data words')))
print()
print("word bodies:  cell form %7d B   token form %7d B   %.2fx"
      % (tot_cell, tot_tok, tot_tok / tot_cell))
