#!/usr/bin/env python3
"""tools/image-audit.py IMAGE [CELLBYTES] - how a CV8 image (format 6)
encodes its references.

Walks the dictionary, decodes every colon body, and reports branches (and
which of them could use a shorter form), calls and variable slots with
what base-relative, pc-relative or either would cost, inline operands and
padding. Written for Iteration 258's audit; see PROGRESS.md."""
import sys, struct, collections
OPCODES = '--opcodes' in sys.argv                     # per-opcode static counts (Iteration 501)
if OPCODES: sys.argv.remove('--opcodes')
path = sys.argv[1]; C = int(sys.argv[2]) if len(sys.argv) > 2 else 8
d = open(path, 'rb').read()
fmt = '<Q' if C == 8 else '<I'
cell = lambda b, o: struct.unpack_from(fmt, b, o)[0]
nth = cell(d, 8)
hdr = 8 + C + nth * C + C
heads = [cell(d, 8 + C + i*C) for i in range(nth)]
img = d[hdr:]
# walk the threads
def prev(nfa):
    tag = img[nfa-1]
    if tag < 128: return nfa - tag if tag else 0, 1
    if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa-2]), 2
    return nfa - (((tag & 63) << 16) | (img[nfa-2] << 8) | img[nfa-3]), 3
words = {}
for h in heads:
    n = h
    while n:
        cnt = img[n]; ln = cnt & 31
        name = img[n+1:n+1+ln].decode('latin1')
        p, ll = prev(n)
        words[n] = (name, cnt, ll)
        n = p
nfas = sorted(words)
xt_of = {}; bodies = []
for i, n in enumerate(nfas):
    name, cnt, ll = words[n]
    xt = n + 1 + (cnt & 31)
    end = (nfas[i+1] - words[nfas[i+1]][2]) if i + 1 < len(nfas) else len(img)
    xt_of[name] = xt
    bodies.append((name, cnt, xt, end))
INLINE3 = {xt_of[k] for k in ('(POSTPONE)',) if k in xt_of}
STRINGS = {xt_of[k] for k in ('(S")', '(.")', '(ABORT")') if k in xt_of}
# The band positions from opcodes.tab, the map's one source (Iteration
# 518); this file kept its own copy of them until then.
import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import opcodes as _opcodes
_rows = _opcodes.load()
NDIRECT = NSYN = sum(1 for k, n, nm, h in _rows if k == 'direct')
EXITS = {_opcodes.number('EXIT'), _opcodes.number('LIT8;EXIT')} | {n for k, n, nm, h in _rows if k == 'fold'}
B8, QB8 = _opcodes.number('BRANCH8'), _opcodes.number('?BRANCH8')
CALLS=[]; SLOTS=[]; S = collections.Counter(); hist = collections.defaultdict(list)
OPS = collections.Counter(); ESCS = collections.Counter()
def s16(v): return v - 65536 if v >= 32768 else v
for name, cnt, xt, end in bodies:
    if cnt & 32 or xt >= end: continue                 # primitives, opcode words
    if img[xt] in (0x24, 0x25): continue               # data bodies
    ip = xt; far_target = xt
    while ip < end:
        op = img[ip]
        if op < 0x80: OPS[op] += 1
        if op == 0x7E: ESCS[img[ip+1]] += 1
        if op in (0x03, 0x04):                         # BRANCH ?BRANCH, s16 from operand
            off = s16(img[ip+1] | img[ip+2] << 8)
            tgt = ip + 1 + off
            kind = ('back' if off < 0 else 'fwd')
            S['branch '+kind] += 1
            hist['branch '+kind].append(abs(off))
            if off > 0: far_target = max(far_target, tgt)
            ip += 3; continue
        if op in (B8, QB8):
            off = img[ip+1] - 256 if img[ip+1] >= 128 else img[ip+1]
            kind = 'branch8 back' if off < 0 else 'branch8 fwd'
            S[kind] += 1; hist[kind].append(abs(off))
            if off > 0: far_target = max(far_target, ip + 1 + off)
            ip += 2; continue
        if op == 0x02: S['LIT16'] += 1; ip += 3; continue
        if op in (0x26, 0x27): S['LIT8'] += 1; ip += 2
        elif op == 0x23: S['LIT32'] += 1; ip += 5; continue
        elif op == 0x7D: S['LIT64'] += 1; ip += 9; continue
        elif op in (0x79, 0x7A, 0x7B, 0x7C): ip += 2
        elif op == 0x7E: ip += 2; S['ESC'] += 1; continue
        elif 0x64 <= op <= 0x69:
            if img[ip+1] & 0x80:
                v = ((img[ip+1] & 0x7F) << 16) | img[ip+2] << 8 | img[ip+3]
                v = (v ^ 0x400000) - 0x400000              # 23 bits signed, from the operand
                S['slot far'] += 1; SLOTS.append((ip, ip+4, ip + 1 + v)); ip += 4
            else:
                v = (img[ip+1] << 8) | img[ip+2]
                v = (v ^ 0x4000) - 0x4000                  # 15 bits signed, from the operand
                S['slot near'] += 1; SLOTS.append((ip, ip+3, ip + 1 + v)); ip += 3
            continue
        elif op == 0x00: S['NOOP'] += 1; ip += 1; continue
        elif op >= 0x80:
            if op < 0xC0:
                t = ((op & 63) << 8) | img[ip+1]; ln = 2
            else:
                t = ((op & 63) << 16) | img[ip+1] << 8 | img[ip+2]; ln = 3
            S['call near' if ln == 2 else 'call far'] += 1
            CALLS.append((ip, ip + ln, t))
            dist = t - (ip + ln)
            S['  pc-rel would be near' if -8192 <= dist < 8192 else '  pc-rel would be far'] += 1
            ip += ln
            if t in INLINE3:
                S['(POSTPONE) operand'] += 1; ip += 3; continue
            if t in STRINGS:
                S['string'] += 1
                ip = ip + 1 + img[ip]; continue
            continue
        else:
            ip += 1
        if op in EXITS and ip > far_target: break
    S['code bytes'] += ip - xt
if OPCODES:
    for k in sorted(OPS): print('op', k, OPS[k])
    for k in sorted(ESCS): print('esc', k, ESCS[k])
    print('code', S['code bytes'])
    sys.exit(0)
print(f"{path}: {len(words)} words, image {len(img)} bytes")
for k in sorted(S): print(f"  {k:28} {S[k]}")
for k, v in sorted(hist.items()):
    v.sort()
    fit8 = sum(1 for x in v if x < 128); fit16 = sum(1 for x in v if x < 32768)
    print(f"  {k:14} n={len(v):5}  max={max(v):6}  median={v[len(v)//2]:5}  fit int8: {fit8}  fit int16: {fit16}")

def model(name, refs, near_bits, near_len, far_len):
    base_near = sum(1 for s, e, t in refs if t < (1 << near_bits))
    # pc-relative: from the operand (s + 1) for slots, from the next
    # instruction (e) for calls, as each would be encoded
    pc_near = sum(1 for s, e, t in refs if -(1 << (near_bits-1)) <= t - (s + 1 if name == "slots" else e) < (1 << (near_bits-1)))
    # hybrid: one bit less for each, either one may be used
    hb = near_bits - 1
    hyb = sum(1 for s, e, t in refs if t < (1 << hb) or -(1 << (hb-1)) <= t - e < (1 << (hb-1)))
    n = len(refs)
    cost = lambda near: near * near_len + (n - near) * far_len
    print(f"  {name}: n={n}  base-rel near={base_near} ({cost(base_near)} B)  pc-rel near={pc_near} ({cost(pc_near)} B)  either, one bit less={hyb} ({cost(hyb)} B)")
model("calls", CALLS, 14, 2, 3)
model("slots", SLOTS, 15, 3, 4)
