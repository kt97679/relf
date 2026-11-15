#!/usr/bin/env python3
"""port/measure/cv8-bytes.py IMAGE KERNEL-IMAGE - a CV8 image by part, as design-bytes.py splits a
design's: tools/image-audit.py's walk and decode (64-bit cells); the kernel part the words below
KERNEL-IMAGE's end (forth/kernel64.img's, which the image was built on)."""
import sys, struct, collections
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import opcodes as _opcodes
C = 8; fmt = '<Q'
def load(p):
    d = open(p, 'rb').read(); cell = lambda o: struct.unpack_from(fmt, d, o)[0]
    nth = cell(8); return d[8 + C + nth * C + C:], [cell(8 + C + i * C) for i in range(nth)]
img, heads = load(sys.argv[1]); kimg, _ = load(sys.argv[2]); KEND = len(kimg)
def prev(nfa):
    tag = img[nfa - 1]
    if tag < 128: return (nfa - tag if tag else 0), 1
    if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa - 2]), 2
    return nfa - (((tag & 63) << 16) | (img[nfa - 2] << 8) | img[nfa - 3]), 3
words = {}
for h in heads:
    n = h
    while n:
        p, _ = prev(n); nm, cnt, ll, st, _ = _opcodes.header(img, n)   # [name][link][count] (949)
        words[n] = (nm, cnt, n - st); n = p
nfas = sorted(words); xt_of = {}
rows = []
for i, n in enumerate(nfas):
    name, cnt, ll = words[n]; xt = n + 1
    end = (nfas[i + 1] - words[nfas[i + 1]][2]) if i + 1 < len(nfas) else len(img)
    xt_of[name] = xt; rows.append((name, cnt, ll, n, xt, end))
STRINGS = {xt_of[k] for k in ('(S")', '(.")', '(ABORT")') if k in xt_of}
INLINE3 = {xt_of[k] for k in ('(POSTPONE)',) if k in xt_of}
FMT = _opcodes.formats(); EXITS = _opcodes.returns()
LITOP = _opcodes.number('LIT'); NOOPOP = _opcodes.number('NOOP')
def strings_in(xt, end):   # bytes of inline strings, call included, in a colon body (image-audit's decode)
    ip = xt; far = xt; sb = 0
    while ip < end:
        op = img[ip]; f = FMT.get(op, '-') if op < 0x80 else 'call'
        if f in ('b16', 'i8b16'):
            k = 2 if f == 'i8b16' else 1; off = img[ip + k] | img[ip + k + 1] << 8
            off = off - 65536 if off >= 32768 else off
            if off > 0: far = max(far, ip + k + off)
            ip += k + 2; continue
        if f == 'b8':
            off = img[ip + 1] - 256 if img[ip + 1] >= 128 else img[ip + 1]
            if off > 0: far = max(far, ip + 1 + off)
            ip += 2; continue
        if f == 'u16' and op == LITOP: ip += 3; continue
        if f == 'u16': ip += 3
        elif f == 'u8': ip += 2
        elif f == 'i32': ip += 5; continue
        elif f == 'u64': ip += 9; continue
        elif f == 'i8': ip += 2
        elif f == 'sel': ip += 2; continue
        elif f in ('slot', '2slot'):
            ip += 1
            for _ in range(2 if f == '2slot' else 1): ip += 3 if img[ip] & 0x80 else 2
            if op in EXITS and ip > far: break
            continue
        elif op == NOOPOP: ip += 1; continue
        elif op >= 0x80:
            ln = 2 if op < 0xC0 else 3
            t = ((op & 63) << 8) | img[ip + 1] if ln == 2 else ((op & 63) << 16) | img[ip + 1] << 8 | img[ip + 2]
            ip += ln
            if t in INLINE3: ip += 3; continue
            if t in STRINGS: sb += ln + 1 + img[ip]; ip = ip + 1 + img[ip]; continue
            continue
        else: ip += 1
        if op in EXITS and ip > far: break
    return sb
part = collections.Counter(); big = []
for name, cnt, ll, n, xt, end in rows:
    hdr = ll + 1; body = max(0, end - xt)
    if n < KEND: part['kernel words (kernel64.img)'] += hdr + body; continue
    part['names and headers'] += hdr
    if cnt & 32 or xt >= end: part['opcode words (no body)'] += body
    elif FMT.get(img[xt]) == 'data': part['data and buffers (DOVAR, DODOES bodies)'] += body
    else:
        sb = strings_in(xt, end); part['strings (S" ." ABORT" in code)'] += sb; part['code'] += body - sb
    big.append((hdr + body, name))
tot = sum(part.values())
print('%s: image %d bytes, %d words, kernel part %d' % (sys.argv[1], len(img), len(rows), KEND))
for k, v in part.most_common(): print('  %-46s %7d  %5.1f%%' % (k, v, 100 * v / tot))
print('  total', tot)
print('20 largest:')
for s, n in sorted(big, reverse=True)[:20]: print('  %6d  %s' % (s, n))
