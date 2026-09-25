#!/usr/bin/env python3
"""tools/image-budget.py [IMAGE [CELLBYTES]] - where an image's bytes go.

Walks the dictionary of a CV8 image (default kernel64-shell.img, 8-byte
cells) and splits its bytes into headers (link fields and names), colon
code (with any data laid down after a definition), data words by kind -
DOVAR (VARIABLE, CREATE) and DODOES (BUFFER:, DEFER, ...) - and the
alignment padding inside data bodies. Written for Iteration 509's space
audit (GOALS.md "What comes next", item 10); see PROGRESS.md.
"""
import struct, sys, collections
path = sys.argv[1] if len(sys.argv) > 1 else 'kernel64-shell.img'
C = int(sys.argv[2]) if len(sys.argv) > 2 else 8
d = open(path, 'rb').read()
cell = lambda o: struct.unpack_from('<Q' if C == 8 else '<I', d, o)[0]
nth = cell(8)
img = d[8 + C + nth * C + C:]
heads = [cell(8 + C + i * C) for i in range(nth)]

def prev(nfa):
    tag = img[nfa - 1]
    if tag < 128: return (nfa - tag if tag else 0), 1
    if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa - 2]), 2
    return nfa - (((tag & 63) << 16) | (img[nfa - 2] << 8) | img[nfa - 3]), 3

words = {}
for h in heads:
    n = h
    while n:
        cnt = img[n]
        p, ll = prev(n)
        words[n] = (cnt, ll)
        n = p
nfas = sorted(words)
cats = collections.Counter(); counts = collections.Counter(); pad = 0
for i, n in enumerate(nfas):
    cnt, ll = words[n]
    xt = n + 1 + (cnt & 31)
    end = (nfas[i + 1] - words[nfas[i + 1]][1]) if i + 1 < len(nfas) else len(img)
    cats['headers (links, names)'] += ll + 1 + (cnt & 31)
    body = max(end - xt, 0)
    if cnt & 32 or body == 0:
        cats['opcode words (no body)'] += body
        continue
    op = img[xt]
    if op in (0x24, 0x25):
        pad += ((xt + 4 + C - 1) & ~(C - 1)) - (xt + 4)
        k = 'DOVAR data (VARIABLE, CREATE)' if op == 0x24 else 'DODOES data (BUFFER:, DEFER, ...)'
    else:
        k = 'colon code (and data laid after it)'
    cats[k] += body; counts[k] += 1
tot = sum(cats.values())
print('%s: %d bytes of image, %d words' % (path, len(img), len(words)))
for k, v in cats.most_common():
    print('  %-38s %7d  %5.1f%%  %s' % (k, v, 100.0 * v / tot, counts.get(k, '')))
print('  %-38s %7d  %5.1f%%' % ('... of which data-body alignment padding', pad, 100.0 * pad / tot))
