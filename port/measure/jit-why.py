#!/usr/bin/env python3
"""port/measure/jit-why.py KMAP MAP PROF JITLOG [N] - on a JIT design: the N words the interpreter ran most,
each with the JIT's reason down to the word it could not take (its root): KMAP kdump.4's, MAP a MAP=1
build's map (its MAP lines), PROF its PROFILE=1 dump (VMPROF), JITLOG its JITLOG=1 engine's log (JITLOG=file).
The reasons are jit.c's: 1 an operation without a stencil, 2 the return stack out of order, 3 a stencil it
cannot use, 4 a word it calls (followed), 5 its memory full, 6 too long, 7 too deep."""
import sys, bisect, collections
kmap, mapf, proff, logf = sys.argv[1:5]; N = int(sys.argv[5]) if len(sys.argv) > 5 else 40
ents = []
for l in open(kmap):
    _, o, n = l.split(None, 2); ents.append((int(o), n.strip() + '(k)'))
for l in open(mapf):
    p = l.split()
    if p[0] == 'MAP' and len(p) > 3: ents.append((int(p[1]), p[3]))
ents.sort(); starts = [e[0] for e in ents]
def name(o):
    i = bisect.bisect_right(starts, o) - 1; return ents[i][1] if i >= 0 else '?'
ipc = {}
for l in open(proff):
    p = l.split()
    if l.startswith('I '): ipc[int(p[1])] = int(p[2])
by = collections.Counter()
for o, n in ipc.items(): by[name(o)] += n
tot = sum(ipc.values())
why = {}   # word offset -> (why, at, op)
for l in open(logf):
    p = l.split()
    if p[0] == "R": why[int(p[1])] = (int(p[3]), int(p[2]), int(p[4]))
byname = {}
for o, w in why.items(): byname.setdefault(name(o), o)
WH = {1: 'no stencil op', 2: 'R-stack order', 3: 'stencil unusable', 4: 'callee', 5: 'mem', 6: 'too long', 7: 'depth?'}
def chain(o, seen=()):
    if o not in why or o in seen: return name(o) + ('' if o in why else ' [not refused?]')
    w, at, op = why[o]
    s = name(o)
    if w == 4: return s + ' > ' + chain(at, seen + (o,))
    return s + ' [%s%s @+%d]' % (WH.get(w, w), ' op %d' % op if op >= 0 else '', at - o)
for w, n in by.most_common(N):
    o = byname.get(w)
    print('%9d %5.1f%%  %s' % (n, 100 * n / tot, chain(o) if o is not None else w + ' (no R line)'))
