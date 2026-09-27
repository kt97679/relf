#!/usr/bin/env python3
"""tools/call-layout.py - how many calls a better word order would make near (FINDINGS.md, Iteration 542)."""
import os, sys, struct, collections
os.chdir('/home/claude/relf'); sys.argv = ['image-audit.py', 'kernel64-shell.img', '8']
g = {'__file__': 'tools/image-audit.py', '__name__': 'audit'}
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('tools/image-audit.py').read(), g)
CALLS = g['CALLS']
d = open('kernel64-shell.img', 'rb').read(); C = 8
cell = lambda o: struct.unpack_from('<Q', d, o)[0]
nth = cell(8); img = d[8 + C + nth * C + C:]
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
        c = img[n]; p, ll = prev(n); words[n] = (img[n+1:n+1+(c & 31)].decode('latin1'), ll, n + 1 + (c & 31)); n = p
nfas = sorted(words)
kern = len(open('forth/kernel64.img', 'rb').read()) - (8 + C + cell(8) * C + C)   # the kernel's dictionary, first in the image
span = []                                      # (start, end, xt, name) for every word
for i, n in enumerate(nfas):
    name, ll, xt = words[n]
    start = n - ll
    end = nfas[i + 1] - words[nfas[i + 1]][1] if i + 1 < len(nfas) else len(img)
    span.append((start, end, xt, name))
by_xt = collections.Counter(t for s, e, t in CALLS)
far_now = sum(1 for s, e, t in CALLS if e - s == 3)
NEAR = 16384
movable = [(s, e, x, nm) for s, e, x, nm in span if s >= kern]
room = NEAR - kern
near_now = sum(by_xt[x] for s, e, x, nm in movable if x < NEAR)
cand = sorted(movable, key=lambda w: -by_xt[w[2]] / max(1, w[1] - w[0]))
used = best = 0; chosen = []
for s, e, x, nm in cand:
    if by_xt[x] == 0: break
    if used + (e - s) <= room:
        used += e - s; best += by_xt[x]; chosen.append((nm, by_xt[x], e - s))
print('call sites %d, far (3 bytes) %d; kernel dictionary %d bytes, so %d of the first 16 KB for the rest'
      % (len(CALLS), far_now, kern, room))
print('calls into that room now: %d; with the most-called words per byte moved there: %d' % (near_now, best))
print('=> %d more calls near: %d bytes (%.1f%% of the %d-byte image)' % (best - near_now, best - near_now,
      100.0 * (best - near_now) / len(d), len(d)))
print('the top of the list:', ', '.join('%s (%d calls, %d B)' % c for c in chosen[:8]))
