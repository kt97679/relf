#!/usr/bin/env python3
"""port/measure/design-bytes.py OUT.img.map OUT.img HEADER-LEN KERNEL-END - a design's image by part.
OUT.img and its map from MAP=1 port/lab/build.sh; HEADER-LEN port/lab/header.py's (80 on every design);
KERNEL-END the design's own image.img less its header (its kernel: START to its end). A run-time header
is read from the image (a tagged link, the count byte, the name); the strings' bytes are map.4's count;
everything before the port's first file is the kernel and nojit.4 or jit.4 (and map.4's own words)."""
import sys, collections
mapf, imgf, hl, kend = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
img = open(imgf, 'rb').read()[hl:]; bodyend = len(img)
def hdrlen(o, name):   # the design's run-time header: a tagged link of 1-3 bytes, the count byte, the name (CV8's)
    for L in (1, 2, 3):
        if img[o + L] & 31 == len(name) and img[o + L + 1:o + L + 1 + len(name)] == name.encode('latin1'): return L + 1 + len(name)
    return None
bad = 0
ents = []; f = 'scaffold'; strbytes = 0
for l in open(mapf):
    p = l.split()
    if p[0] == 'FILE': f = p[1]
    elif p[0] == 'STRBYTES': strbytes = int(p[1])
    elif p[0] == 'MAP': ents.append((int(p[1]), p[2], p[3] if len(p) > 3 else '', f))
ents.sort()
part = collections.Counter(); byfile = collections.Counter(); words = []
part['kernel (the design\'s, converted)'] = kend
first = ents[0][0]
part['before the port: nojit.4 and the map\'s own words'] = first - kend
for i, (o, kind, name, f) in enumerate(ents):
    end = ents[i + 1][0] if i + 1 < len(ents) else bodyend
    size = end - o
    if f == 'scaffold': part['before the port: nojit.4 and the map\'s own words'] += size; continue
    hdr = hdrlen(o, name)
    if hdr is None: bad += 1; hdr = 2 + len(name)
    body = size - hdr
    part['names and headers'] += hdr
    if kind == ':': part['code'] += body
    elif kind in ('CREATE', 'VARIABLE'): part['data and buffers (CREATE, VARIABLE, their ALLOT)'] += body
    else: part['constants'] += body
    grp = 'port' if f.startswith('port/') else 'relfsh (pool.4, shell/)'
    byfile[(grp, 'code' if kind == ':' else 'data')] += body
    byfile[(grp, 'headers')] += hdr
    words.append((size, name, kind, f))
part['code'] -= strbytes; part['strings (S" and ." in code)'] = strbytes
tot = sum(part.values())
print('image body %d bytes (the file: + a %d-byte header)' % (bodyend, hl))
for k, v in part.most_common(): print('  %-52s %7d  %5.1f%%' % (k, v, 100 * v / tot))
print('  total %d' % tot)
for k in sorted(byfile): print('  %-30s %-8s %7d' % (k[0], k[1], byfile[k]))
print('headers not found exactly:', bad)
print('20 largest:')
for s, n, k, f in sorted(words, reverse=True)[:20]: print('  %6d  %-28s %-8s %s' % (s, n, k, f))
