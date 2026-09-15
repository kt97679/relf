#!/usr/bin/env python3
"""size-estimate.py DUMP CELL - whole-image size under alternative code
unit widths, reusing the layout pass's classification. Code bodies are
re-sized per scheme; headers, names, data bodies and tails are shared.

  u16    the 16-bit CPT16 stream actually emitted (the reference)
  u32    32-bit units: every token 4 bytes, operands 4 bytes
  v8     variable: primitive 1 byte, call 2, LIT8 2 / LIT16 3 / LIT32 5,
         branch 3, (LOOP)/xt operands padded to CELL with 1-byte NOOPs
"""
import sys, subprocess, collections
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], '--cpt', '1', '--dataprims', '--fold']
src = open(__file__.replace('size-estimate.py', 'layout.py')).read()
src = src[:src.index('# ---- report')]
G2 = {'__name__': 'lay', '__file__': __file__.replace('size-estimate.py', 'layout.py')}
exec(compile(src, 'lay', 'exec'), G2)
order, kind, info, CELL = G2['order'], G2['kind'], G2['info'], G2['CELL']
align_up, tail_bytes, stub_ops = G2['align_up'], G2['tail_bytes'], G2['stub_ops']

def body(ops, scheme):
    t = 0
    for j, (k, pl) in enumerate(ops):
        if k == 'ALN': t = align_up(t, 2 if scheme != 'v8' else 1); continue
        nxt = ops[j + 1][0] if j + 1 < len(ops) else None
        if scheme == 'u32':
            if k == 'C' and nxt in ('OPD', 'XT'): t = align_up(t + 4, CELL) - 4
            t += {'P': 4, 'PX': 4, 'C': 4, 'LIT': 8, 'LITX': 8, 'LITOFF': 8,
                  'BR': 8, 'QBR': 8}.get(k, 0)
            if k in ('OPD', 'XT'): t += CELL
            if k == 'STR': t = align_up(t + len(pl), CELL)
        elif scheme == 'v8':
            if k == 'C' and nxt in ('OPD', 'XT'): t = align_up(t + 2, CELL) - 2
            if k in ('P', 'PX'): t += 1
            elif k == 'C': t += 2
            elif k in ('LIT', 'LITX'):
                t += 2 if 0 <= pl < 256 else 3 if -32768 <= pl < 65536 else 5
            elif k == 'LITOFF': t += 5
            elif k in ('BR', 'QBR'): t += 3
            elif k in ('OPD', 'XT'): t += CELL
            elif k == 'STR': t = align_up(t + len(pl), CELL)
    return t

tot = collections.Counter()
for w in order:
    b = G2['new_body_bytes'](w)
    hdr = CELL + align_up(len(w['n']) + 1, CELL)
    for sc in ('u16', 'u32', 'v8'):
        if kind[w['s']] == 'code' and sc != 'u16':
            nb = align_up(body(info[w['s']], sc), CELL) + tail_bytes(w)
        else:
            nb = b
        tot[sc] += hdr + nb
    tot['code-u16'] += b if kind[w['s']] == 'code' else 0
    if kind[w['s']] == 'code':
        tot['code-u32'] += align_up(body(info[w['s']], 'u32'), CELL) + tail_bytes(w)
        tot['code-v8'] += align_up(body(info[w['s']], 'v8'), CELL) + tail_bytes(w)
print("cell %d" % CELL, {k: v + G2['PROLOGUE'] if not k.startswith('code') else v
                         for k, v in sorted(tot.items())})
