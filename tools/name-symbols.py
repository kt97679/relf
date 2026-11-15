#!/usr/bin/env python3
"""tools/name-symbols.py [KERNEL SHELL RILL3] - the name code's symbols (Iteration 949).

Counts the characters of the names in four families - the kernel's, the shell's and rill3's own (those
not the kernel's), and gforth's words, upper-cased, as `gforth -e 'words bye'` lists them - each as a
share of its family's characters, and ranks a character by the mean of the four shares: generic, not
the shell's. The first 15 take 4 bits in a header, the next 15 take 8, any other 16 (CV8.md 4.2);
forth/cross-core.4's NAME-SYMBOLS holds the 30. Then what that code and a few others would make of
each family's names. Images of format 13 (names as written, after the count byte) or 14 (packed,
before the link) - 949 chose the symbols on 948's: forth/kernel64.img, kernel64-shell.img and
kernel64-cm.img, before the change (bench/reports/name-symbols-949.txt)."""
import collections, os, struct, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opcodes

def names(path):
    d = open(path, 'rb').read(); C = d[4]; fmt = '<Q' if C == 8 else '<I'
    cell = lambda o: struct.unpack_from(fmt, d, o)[0]
    nth = cell(8); img = d[8 + C + nth * C + C:]; heads = [cell(8 + C + i * C) for i in range(nth)]
    def prev(nfa):
        tag = img[nfa - 1]
        if tag < 128: return nfa - tag if tag else 0
        if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa - 2])
        return nfa - (((tag & 63) << 16) | (img[nfa - 2] << 8) | img[nfa - 3])
    out = []
    for h in heads:
        n = h
        while n:
            if d[6] >= 14: out.append(opcodes.header(img, n)[0])
            else: out.append(img[n + 1:n + 1 + (img[n] & 31)].decode('latin1'))
            n = prev(n)
    return out

args = sys.argv[1:] or ['forth/kernel64.img', 'kernel64-shell.img', 'kernel64-cm.img']
k = names(args[0]); ks = set(k)
fam = {'kernel': k, 'shell': [n for n in names(args[1]) if n not in ks],
       'rill3': [n for n in names(args[2]) if n not in ks]}
try:
    g = subprocess.run(['gforth', '-e', 'words bye'], capture_output=True, text=True, timeout=60).stdout
    fam['gforth'] = sorted({w.upper() for w in g.split()})
except (OSError, subprocess.TimeoutExpired):
    print('gforth is not installed: three families, not four')
share = collections.Counter()
for v in fam.values():
    cc = collections.Counter(''.join(v)); tot = sum(cc.values())
    for ch, x in cc.items(): share[ch] += x / tot / len(fam)
order = ''.join(ch for ch, _ in sorted(share.items(), key=lambda t: (-t[1], t[0])))
print('families: ' + ', '.join('%s %d names, %d characters' % (f, len(v), sum(map(len, v))) for f, v in fam.items()))
print('ranked:   ' + order[:40])
print('the 30:   %s + %s' % (order[:15], order[15:30]))
print('in cross-core.4: %s' % opcodes.name_symbols())
print('the first 30 by mean share, %%: %s' % ' '.join('%s %.2f' % (c, 100 * share[c]) for c in order[:30]))

def bits(n, t4, t8, raw, syms):
    b = 0
    for ch in n:
        i = syms.find(ch)
        b += 4 if 0 <= i < t4 else 8 if 0 <= i < t4 + t8 else raw
    return b
def size(n, unit, t4, t8, raw, syms):
    k_ = (bits(n, t4, t8, raw, syms) + unit - 1) // unit
    return k_ if k_ < len(n) else len(n)
print('\nbytes of names (% of the characters), each code with these symbols:')
for label, unit, t4, t8, raw in (('8-bit bytes, 15 + 15, others 16 bits (949)', 8, 15, 15, 16),
                                 ('8-bit bytes, 14 + 16, others 12', 8, 14, 16, 12),
                                 ('8-bit bytes, 13 + 32, others 12', 8, 13, 32, 12),
                                 ('7-bit units, 15 + 13, others 16', 7, 15, 13, 16)):
    row = []
    for f, v in fam.items():
        tot = sum(size(n, unit, t4, t8, raw, order) for n in v)
        row.append('%s %d (%.1f%%)' % (f, tot, 100.0 * tot / sum(map(len, v))))
    print('  %-44s %s' % (label, '  '.join(row)))
