#!/usr/bin/env python3
"""tools/rill-size.py [TOP] - where kernel64-rill.img's bytes go (Iteration 826, at the user's asking).

Builds the image a file at a time, as tools/build-rill-image.sh loads them, and saves it after each:
a file's bytes are the difference - its words' names, code, data and strings together. (The files
before save-system.4 cannot be saved alone; they and it are one layer, the one relfsh shares.)
Then walks the image's dictionary as tools/image-audit.py does, and splits each layer into its
words' headers - the link, the count byte, the name - and their bodies, and names the TOP largest
words (15 unless given). The headers are what the generated Forth's EVALUATE needs of the runtime's
words, and what nothing needs of the compiler's and the editor's own - see docs/RILL-SIZE.md.
"""
import os, re, struct, subprocess, sys, tempfile, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 15
tmp = tempfile.mkdtemp(prefix='rill-size.')
genes = os.path.join(tmp, 'genes.4'); src = os.path.join(tmp, 'src'); widths = os.path.join(tmp, 'widths.4')
subprocess.run(['python3', 'tools/rill-genes.py', '--forth'], stdout=open(genes, 'w'), check=True)
subprocess.run(['python3', 'tools/rill-genes.py', '--source', src], check=True)
text = open('shell/shell.4', encoding='utf-8').read()
a = text.index("\\ Characters' widths on screen"); b = text.index('WIDE-CHARS #WIDE-CHARS CP-IN? IF 2 ELSE 1 THEN ;', a)
open(widths, 'w', encoding='utf-8').write(text[a:text.index('\n', b) + 1])
files = ['forth/extend.4', 'forth/safety.4', 'forth/pool.4', 'forth/shadow.4', 'forth/save-system.4', genes,
         src + '/rt.4', src + '/regex.4', widths, 'rill/edit-shim.4', 'shell/edit.4', src + '/compile.4']
names = ['kernel, shared', 'genes', 'rt.4', 'regex.4', 'widths', 'edit-shim', 'edit.4', 'compile.4']
sizes = []
for k in range(5, len(files) + 1):                   # save-system.4 is the fifth: the first that can save
    img = os.path.join(tmp, 'img%d' % k)
    script = ''.join('S" %s" INCLUDED\n' % f for f in files[:k]) + 'S" %s" SAVE-SYSTEM\nBYE\n' % img
    subprocess.run(['./relf64', 'forth/kernel64.img'], input=script.encode(), capture_output=True, check=True)
    sizes.append(os.path.getsize(img))
d = open(os.path.join(tmp, 'img%d' % len(files)), 'rb').read(); C = 8
cell = lambda o: struct.unpack_from('<Q', d, o)[0]
nth = cell(8); hdr = 8 + C + nth * C + C; heads = [cell(8 + C + i * C) for i in range(nth)]; img = d[hdr:]
def prev(nfa):
    tag = img[nfa - 1]
    if tag < 128: return (nfa - tag if tag else 0), 1
    if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa - 2]), 2
    return nfa - (((tag & 63) << 16) | (img[nfa - 2] << 8) | img[nfa - 3]), 3
words = {}
for h in heads:
    n = h
    while n:
        ln = img[n] & 31; p, ll = prev(n); words[n] = (img[n + 1:n + 1 + ln].decode('latin1'), ln, ll); n = p
nfas = sorted(words); bounds = [s - hdr for s in sizes]
agg = collections.OrderedDict((n, [0, 0, 0]) for n in names); big = []
for i, n in enumerate(nfas):
    name, ln, ll = words[n]; start = n - ll; xt = n + 1 + ln
    end = (nfas[i + 1] - words[nfas[i + 1]][2]) if i + 1 < len(nfas) else len(img)
    layer = next((names[k] for k, b in enumerate(bounds) if start < b), names[-1])
    agg[layer][0] += 1; agg[layer][1] += ll + 1 + ln; agg[layer][2] += end - xt; big.append((end - xt, name, layer))
prev_size = 0                                        # the kernel's own words are in the first layer's counts too
print('%-14s %7s %6s %6s %8s %8s' % ('layer', 'bytes', 'share', 'words', 'headers', 'bodies'))
for (k, (w, h, bd)), s in zip(agg.items(), sizes):
    n = s - prev_size; prev_size = s
    print('%-14s %7d %5.1f%% %6d %8d %8d' % (k, n, 100.0 * n / len(d), w, h, bd))
print('%-14s %7d         %6d %8d %8d' % ('the image', len(d), sum(a[0] for a in agg.values()),
      sum(a[1] for a in agg.values()), sum(a[2] for a in agg.values())))
print('\nthe %d largest words:' % TOP)
for s, n, l in sorted(big, reverse=True)[:TOP]: print('  %6d  %-26s %s' % (s, n, l))
subprocess.run(['rm', '-rf', tmp])
