#!/usr/bin/env python3
"""tools/image-where.py IMAGE [CELLBYTES] OFFSET... - which word holds each
offset of a saved image, for turning a crash into a Forth backtrace.

    gdb: print ip - cbase, and the cells on the return stack minus cbase,
    then run this with those numbers.

Written for Iteration 421, when `case x in 2)` segfaulted in a `@` of 0
and the question was which of 1600 words had done it. The dictionary
walk is tools/image-audit.py's."""
import sys, struct
path = sys.argv[1]
args = sys.argv[2:]
C = 8
if args and args[0] in ('4', '8') and len(args) > 1:
    C = int(args[0]); args = args[1:]
d = open(path, 'rb').read()
fmt = '<Q' if C == 8 else '<I'
cell = lambda b, o: struct.unpack_from(fmt, b, o)[0]
nth = cell(d, 8)
hdr = 8 + C + nth * C + C
heads = [cell(d, 8 + C + i*C) for i in range(nth)]
img = d[hdr:]
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
        words[n] = (img[n+1:n+1+ln].decode('latin1'), cnt, prev(n)[1])
        n = prev(n)[0]
nfas = sorted(words)
spans = []
for i, n in enumerate(nfas):
    name, cnt, ll = words[n]
    xt = n + 1 + (cnt & 31)
    end = (nfas[i+1] - words[nfas[i+1]][2]) if i + 1 < len(nfas) else len(img)
    spans.append((xt, end, name))
for a in args:
    off = int(a, 0)
    hit = [s for s in spans if s[0] <= off < s[1]]
    print("%8d  %s" % (off, ("%s +%d" % (hit[0][2], off - hit[0][0])) if hit else "(outside any word)"))
