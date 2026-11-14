#!/usr/bin/env python3
"""port/measure/design-prof.py PROF OUT.img.map OUT.img KMAP - a design's PROFILE=1 dump (VMPROF=PROF) of one
run, by operation, adjacent pair and word entered: OUT.img and its map from MAP=1 port/lab/build.sh, KMAP
kdump.4's; op names design-ops.py's (DESIGN_SRC). A word's entries are the count at its first instruction.
The pair table counts a call twice (its first byte 0x80-0xFF, and the pseudo-op 256): here once, as CALL;
an escaped operation k is the pair (ESC, k) and is named from the escaped band."""
import sys, collections, bisect, importlib.util
import os
spec = importlib.util.spec_from_file_location('ko', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'design-ops.py')); ko = importlib.util.module_from_spec(spec); spec.loader.exec_module(ko)
prof, mapf, imgf, kmap = sys.argv[1:5]
ESC = 125
pair = collections.Counter(); calls_by = collections.Counter()
for l in open(prof):
    p = l.split()
    if p[0].isdigit() and len(p) == 3: pair[(int(p[0]), int(p[1]))] += int(p[2])
    elif p[0] == 'R': calls_by[int(p[2])] += int(p[3])
def nm(op, prev=None):
    if 128 <= op <= 256: return 'CALL'
    if prev == ESC: return ko.esc_name(op)
    return ko.name(op)
ops = collections.Counter(); prs = collections.Counter()
for (a, b), n in pair.items():
    if 128 <= b <= 255: continue                      # the call's byte: counted as 256
    ops[nm(b, a)] += n
for (a, b), n in pair.items():
    if 128 <= b <= 255 or (128 <= a <= 255 and b == 256): continue
    if b == ESC: continue
    prs[(nm(a), nm(b, a))] += n
tot = sum(ops.values()); calls = ops['CALL']
rets = sum(n for k, n in ops.items() if k == 'exit' or k.endswith(';EXIT') or k in ('addix', 'eqix'))
print('dispatches %d  calls %d (%.1f%%)  returns: EXIT and its folds %d, DOVAR %d, DODOES %d' % (tot, calls, 100 * calls / tot, rets, ops['dovar'], ops['dodoes']))
print('by operation:')
for k, n in ops.most_common(30): print('  %10d %5.1f%%  %s' % (n, 100 * n / tot, k))
print('by adjacent pair:')
for k, n in prs.most_common(25): print('  %10d %5.1f%%  %s  %s' % (n, 100 * n / tot, k[0], k[1]))
ents = []
for l in open(kmap):
    _, o, n = l.split(None, 2); ents.append((int(o), n.strip() + '(k)'))
for l in open(mapf):
    p = l.split()
    if p[0] == 'MAP': ents.append((int(p[1]), p[3] if len(p) > 3 else '?'))
ents.sort(); st = [e[0] for e in ents]
def wn(o):
    i = bisect.bisect_right(st, o) - 1; return ents[i][1] if i >= 0 else '?'
ipc = {}
for l in open(prof):
    if l.startswith('I '): q = l.split(); ipc[int(q[1])] = int(q[2])
img = open(imgf, 'rb').read()[80:]
byw = collections.Counter()
for l in open(mapf):          # a word's entries: the count at its first instruction (its calls, and any jump back to it)
    p = l.split()
    if p[0] != 'MAP' or len(p) < 4: continue
    o, name = int(p[1]), p[3]
    for L in (1, 2, 3):
        if img[o + L] & 31 == len(name) and img[o + L + 1:o + L + 1 + len(name)] == name.encode('latin1'):
            byw[name] += ipc.get(o + L + 1 + len(name), 0); break
for l in open(kmap):
    _, o, n = l.split(None, 2); byw[n.strip() + '(k)'] += ipc.get(int(o), 0)
print('hottest words by calls:')
for k, n in byw.most_common(25): print('  %10d  %s' % (n, k))
