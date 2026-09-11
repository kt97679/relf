#!/usr/bin/env python3
"""gen-fold.py ENGINE.c [NAMES] - generate the folded (prim-then-EXIT)
copies of primitive bodies: vm-fold-table.h and vm-fold-bodies.h.
NAMES is a comma-separated list of kernel.4 primitive names, or 'all'."""
import os, re, sys
s = open(sys.argv[1]).read()
V8 = len(sys.argv) > 3 and sys.argv[3] == 'v8'
V8LIST = sys.argv[2].split(',') if len(sys.argv) > 2 else []
want = None if len(sys.argv) < 3 or sys.argv[2] == 'all' else set(sys.argv[2].split(','))
prims = [l.split()[1] for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kernel.4')) if l.startswith('PRIMITIVE')]
fend = s.index("\n}\n\n/*\n *  Program entry point")
fend = s.rindex("#if FOLD", 0, fend) if "#include \"vm-fold-bodies.h\"" in s[fend-300:fend] else fend
sec = s[s.index("L_noop:"):fend]
labs = [(m.start(), m.group(1)) for m in re.finditer(r'^(L_\w+):', sec, re.M)]
tab = s[s.index("static const void *const dispatch[] = {"):]
order = re.findall(r'&&(L_\w+)', tab[:tab.index("};")])
skip = {'L_noop', 'L_exit', 'L_branch', 'L_0branch'}
copies, entries = [], []
for i, (pos, lab) in enumerate(labs):
    if lab in skip or lab not in order[:len(prims)]: continue
    if want is not None and prims[order.index(lab)] not in want: continue
    nxt = labs[i + 1][0] if i + 1 < len(labs) else len(sec)
    body = sec[pos:nxt].replace(lab + ':', 'LX' + lab[1:] + ':', 1)
    body = ''.join(l for l in body.splitlines(True) if not l.lstrip().startswith('#'))
    copies.append(body.replace('NEXT();', 'EXITNEXT();'))
    if V8: entries.append('[73 + %d] = &&LX%s,' % (V8LIST.index(prims[order.index(lab)]), lab[1:]))
    else: entries.append('[FOLDBASE + %d] = &&LX%s,' % (order.index(lab), lab[1:]))
open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'vm-fold-table.h'), 'w').write('\n'.join(entries) + '\n')
open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'vm-fold-bodies.h'), 'w').write(''.join(copies))
print(len(copies), "folded primitives")
