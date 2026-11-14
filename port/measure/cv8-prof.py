#!/usr/bin/env python3
"""port/measure/cv8-prof.py IMAGE COUNTS - one run on CV8 (relf-count.py's counts: dispatches per instruction address):
by operation, by adjacent pair (static: consecutive instructions of a body, the second not a jump
target, weighted by the second's count - an estimate), calls by target, returns."""
import sys, struct, array, collections
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import opcodes
opname, escname = opcodes.names(); FMT = opcodes.formats(); EXITS = opcodes.returns()
LITOP = opcodes.number('LIT'); NOOPOP = opcodes.number('NOOP')
d = open(sys.argv[1], 'rb').read(); C = 8
cell = lambda o: struct.unpack_from('<Q', d, o)[0]
nth = cell(8); img = d[8 + C + nth * C + C:]; heads = [cell(8 + C + i * C) for i in range(nth)]
cnt = array.array('I'); cnt.frombytes(open(sys.argv[2], 'rb').read())
def prev(nfa):
    tag = img[nfa - 1]
    if tag < 128: return (nfa - tag if tag else 0), 1
    if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa - 2]), 2
    return nfa - (((tag & 63) << 16) | (img[nfa - 2] << 8) | img[nfa - 3]), 3
words = {}
for h in heads:
    n = h
    while n:
        c_ = img[n]; p, ll = prev(n); words[n] = (img[n + 1:n + 1 + (c_ & 31)].decode('latin1'), c_, ll); n = p
nfas = sorted(words); xt_name = {}; bodies = []
for i, n in enumerate(nfas):
    name, c_, ll = words[n]; xt = n + 1 + (c_ & 31)
    end = (nfas[i + 1] - words[nfas[i + 1]][2]) if i + 1 < len(nfas) else len(img)
    xt_name.setdefault(xt, name); bodies.append((name, c_, xt, end))
rx = {v: k for k, v in xt_name.items()}
STRINGS = {rx[k] for k in ('(S")', '(.")', '(ABORT")') if k in rx}; INLINE3 = {rx[k] for k in ('(POSTPONE)',) if k in rx}
ops = collections.Counter(); prs = collections.Counter(); callt = collections.Counter(); rets = 0
for name, c_, xt, end in bodies:
    if c_ & 32 or xt >= end: continue
    if FMT.get(img[xt]) == 'data':
        ops[opname.get(img[xt], '?')] += cnt[xt]; continue
    ins = []; targets = set(); ip = xt; far = xt
    while ip < end:
        op = img[ip]; a = ip; key = opname.get(op, '?%02X' % op) if op < 0x80 else 'CALL'
        f = FMT.get(op, '-') if op < 0x80 else 'call'; tgt = None
        if f in ('b16', 'i8b16'):
            k = 2 if f == 'i8b16' else 1; off = img[ip + k] | img[ip + k + 1] << 8; off = off - 65536 if off >= 32768 else off
            targets.add(ip + k + off); far = max(far, ip + k + off) if off > 0 else far; ip += k + 2
        elif f == 'b8':
            off = img[ip + 1] - 256 if img[ip + 1] >= 128 else img[ip + 1]; targets.add(ip + 1 + off)
            far = max(far, ip + 1 + off) if off > 0 else far; ip += 2
        elif f == 'u16': ip += 3
        elif f in ('u8', 'i8'): ip += 2
        elif f == 'i32': ip += 5
        elif f == 'u64': ip += 9
        elif f == 'sel': key = 'ESC ' + escname.get(img[ip + 1], '?'); ip += 2
        elif f in ('slot', '2slot'):
            ip += 1
            for _ in range(2 if f == '2slot' else 1): ip += 3 if img[ip] & 0x80 else 2
        elif f == 'call':
            ln = 2 if op < 0xC0 else 3
            tgt = ((op & 63) << 8) | img[ip + 1] if ln == 2 else ((op & 63) << 16) | img[ip + 1] << 8 | img[ip + 2]
            ip += ln
            if tgt in INLINE3: ip += 3
            elif tgt in STRINGS: ip = ip + 1 + img[ip]
        else: ip += 1
        ins.append((a, key, tgt)); n_ = cnt[a]; ops[key] += n_
        if tgt is not None: callt[xt_name.get(tgt, '?%d' % tgt)] += n_
        if op < 0x80 and op in EXITS: rets += n_
        if op < 0x80 and op in EXITS and ip > far: break
    for i in range(1, len(ins)):
        a, k1, t1 = ins[i - 1]; b, k2, t2 = ins[i]
        if b in targets or k1 == 'CALL' or k1.startswith('?BRANCH') or k1.startswith('BRANCH'): continue
        prs[(k1, k2)] += cnt[b]
tot = sum(cnt)
print('dispatches %d (decoded %d; the rest: words compiled at run time)  calls %d (%.1f%%)  returns (EXIT and folded) %d' % (tot, sum(ops.values()), ops['CALL'], 100 * ops['CALL'] / tot, rets))
print('by operation:')
for k, n in ops.most_common(30): print('  %10d %5.1f%%  %s' % (n, 100 * n / tot, k))
print('by adjacent pair (static estimate):')
for k, n in prs.most_common(25): print('  %10d %5.1f%%  %s  %s' % (n, 100 * n / tot, k[0], k[1]))
print('hottest words by calls:')
for k, n in callt.most_common(25): print('  %10d  %s' % (n, k))
