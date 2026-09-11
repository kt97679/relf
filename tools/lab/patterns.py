#!/usr/bin/env python3
"""patterns.py DUMP CELL PROF... - static and dynamic frequency of the
operation patterns that other VMs specialise.

Static = sites in the CV8 image (size). Dynamic = executions, from the
per-address histogram that vm-lab.c -DPROFILE writes as "I off count"
lines (the address of an op's first byte is counted once per dispatch).
The layout pass is re-run with the CV8 options to recover, for every op,
the byte offset it was emitted at, so the two can be joined exactly.

Must be run with the SAME layout options the profiled image was built
with, or the join is meaningless: the script asserts that every
profiled address it attributes lands on an op start.
"""
import sys, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
DUMP, CELL, PROFS = sys.argv[1], sys.argv[2], sys.argv[3:]
HOT = '+,=,!,@,LSHIFT,RSHIFT,C@,C!,AND,OR,XOR,LIT,<,U<,OVER,DROP,DUP,SWAP,ROT,>R,R>,R@,NEGATE'
S = '3' if CELL == '8' else '2'
LAY = os.path.join(HERE, '..', 'sod16-layout.py')
sys.argv = [LAY, DUMP, CELL, '--v8', '--cpt', S, '--dataprims', '--fold', '--fold-set', HOT]
src = open(LAY).read(); src = src[:src.index('# ---- report')]
G = {'__name__': 'lay', '__file__': LAY}
exec(compile(src, 'lay', 'exec'), G)
order, kind, info, new_off, layout = G['order'], G['kind'], G['info'], G['new_off'], G['layout']
starts, DOVAR, TAILS = G['starts'], G['DOVAR'], G['TAILS']
C = int(CELL)

ipc = collections.Counter()
for f in PROFS:
    for l in open(f):
        if l.startswith('I '):
            _, a, n = l.split(); ipc[int(a)] += int(n)

name = {w['s']: w['n'] for w in order}
def is_var(t):  return t in starts and kind[t] == 'data' and info[t] in DOVAR
def is_const(t):
    if t not in starts or kind[t] != 'code': return False
    o = [x for x in info[t] if x[0] != 'ALN']
    return len(o) == 1 and o[0][0] == 'LITX' or (len(o) == 2 and o[0][0] in ('LIT', 'LITOFF') and o[1] == ('P', 'EXIT'))
def tiny(t):
    """a colon word of <= 3 ops, none of them a call or a branch"""
    if t not in starts or kind[t] != 'code' or is_const(t): return False
    o = [x for x in info[t] if x[0] not in ('ALN',)]
    return 1 <= len(o) <= 3 and all(k in ('P', 'PX', 'LIT', 'LITX') for k, _ in o)

# walk every code op with its static position and dynamic count
ops = []           # (word, j, kind, payload, dyn)
seen = 0
for w in order:
    if kind[w['s']] != 'code': continue
    o = info[w['s']]
    _, cs, ts, _, _ = layout(o)
    base = new_off[w['s']]['body']
    for j, (k, pl) in enumerate(o):
        if k == 'ALN': continue
        d = ipc.get(base + ts[j], 0); seen += d
        ops.append((w['n'], j, k, pl, d))
tot = sum(ipc.values())
print("dispatches profiled %.1fM, %.1f%% attributed to code-body op starts"
      % (tot / 1e6, 100 * seen / max(tot, 1)))

def label(k, pl):
    if k == 'C': return 'call ' + ('VAR' if is_var(pl) else name.get(pl, 'tail'))
    if k in ('P', 'PX'): return pl + (';X' if k == 'PX' else '')
    if k in ('LIT', 'LITX'): return 'LIT'
    return k

byw = collections.defaultdict(list)
for r in ops: byw[r[0]].append(r)

def report(title, pred):
    st = dy = 0
    for w, rs in byw.items():
        for i in range(len(rs)):
            n = pred(rs, i)
            if n: st += 1; dy += rs[i][4]
    print("  %-46s static %5d   dynamic %6.1fM (%4.1f%%)" % (title, st, dy / 1e6, 100 * dy / tot))

print("\n-- candidate specialisations (dynamic = executions of the FIRST op) --")

lrt = {}
for nm in ('LSAVE', 'LRESTORE', 'L!', 'LZERO'):
    ws = [w for w in order if w['n'] == nm]
    if ws: lrt[ws[-1]['s']] = nm
for nm in ('LSAVE', 'LRESTORE', 'L!', 'LZERO'):
    report("locals: LITOFF + call %s" % nm, lambda rs, i, nm=nm: rs[i][2] == 'LITOFF'
           and i + 1 < len(rs) and rs[i + 1][2] == 'C' and lrt.get(rs[i + 1][3]) == nm)
report("variable ref followed by @", lambda rs, i: rs[i][2] == 'C' and is_var(rs[i][3])
       and i + 1 < len(rs) and rs[i + 1][2] in ('P', 'PX') and rs[i + 1][3] == '@')
report("variable ref followed by !", lambda rs, i: rs[i][2] == 'C' and is_var(rs[i][3])
       and i + 1 < len(rs) and rs[i + 1][2] in ('P', 'PX') and rs[i + 1][3] == '!')
report("variable ref, other", lambda rs, i: rs[i][2] == 'C' and is_var(rs[i][3])
       and not (i + 1 < len(rs) and rs[i + 1][2] in ('P', 'PX') and rs[i + 1][3] in ('@', '!')))
report("call to a CONSTANT", lambda rs, i: rs[i][2] == 'C' and is_const(rs[i][3]))
report("call to a tiny colon word (<=3 prim ops)", lambda rs, i: rs[i][2] == 'C' and tiny(rs[i][3]))
report("compare/0= then ?BRANCH", lambda rs, i: i + 1 < len(rs) and rs[i + 1][2] == 'QBR' and (
       (rs[i][2] == 'P' and rs[i][3] in ('=', '<', 'U<')) or (rs[i][2] == 'C' and name.get(rs[i][3]) in ('0=', '<>', '>', '0<'))))
report("LIT 0..3 (one-byte small-int candidates)", lambda rs, i: rs[i][2] in ('LIT', 'LITX') and 0 <= rs[i][3] <= 3)

print("\n-- hottest call targets (dynamic) --")
cc, cs_ = collections.Counter(), collections.Counter()
for w, j, k, pl, d in ops:
    if k == 'C':
        nm = 'VAR ' + name.get(pl, '?') if is_var(pl) else name.get(pl, 'DOES-tail')
        cc[nm] += d; cs_[nm] += 1
for nm, d in cc.most_common(22):
    print("  %-22s dyn %6.1fM  sites %4d  %s" % (nm, d / 1e6, cs_[nm], 'TINY' if any(tiny(w['s']) for w in order if w['n'] == nm) else ''))

print("\n-- hottest dynamic bigrams --")
bg = collections.Counter()
for w, rs in byw.items():
    for i in range(len(rs) - 1):
        bg[(label(rs[i][2], rs[i][3]), label(rs[i + 1][2], rs[i + 1][3]))] += rs[i][4]
for (a, b), d in bg.most_common(18):
    print("  %-24s %-24s %5.1f%%" % (a, b, 100 * d / tot))

print("\n-- LIT values (static sites) --")
lv = collections.Counter(pl for _, _, k, pl, _ in ops if k in ('LIT', 'LITX'))
print("  ", lv.most_common(14))

print("\n-- where the CV8 image's bytes are --")
hdr = sum(C + G['align_up'](len(w['n']) + 1, C) for w in order)
code = sum(G['new_body_bytes'](w) for w in order if kind[w['s']] == 'code')
data = sum(G['new_body_bytes'](w) for w in order if kind[w['s']] == 'data')
print("  headers+names %d   code bodies %d   data bodies %d   total %d"
      % (hdr, code, data, hdr + code + data + G['PROLOGUE']))
