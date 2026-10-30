#!/usr/bin/env python3
r"""tools/cm-reach.py [--prune OUT] - the runtime's words nothing of the command model reaches (Iteration 873).

rill/rt.4 was Rill's runtime; the command model kept it and, at 873, took out the 80 words it never
reaches - this check keeps it so: exit status 1 if any colon definition in rill/rt.4 is not reached
from the roots, which are rt.4's own code outside definitions, R-BOOT (the image's boot word), and
every word cm/*.4, tests/cm/*.4 and shell/edit.4 name - the strings in cm/*.4 too, since cm/cmc.4's
are the Forth it makes. A name reached is followed into its definition's words. Comments and string
literals are blanked before definitions are found ([CHAR] \ too: a backslash is no comment there).
--prune OUT writes rt.4 without the unreached words to OUT.
"""
import re, glob, sys
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open('rill/rt.4').read()
def blank(text):
    """comments and string literals blanked, positions kept"""
    out = []
    for line in text.split('\n'):
        b = list(line)
        for m in re.finditer(r'(\S*")\s[^"]*"', line):           # S" ...", ." ...": keep the opener, blank the text
            for i in range(m.start() + len(m.group(1)), m.end()): b[i] = ' '
        l2 = ''.join(b)
        for m in re.finditer(r"(?<!\S)(\[CHAR\]|CHAR|'|\[']|POSTPONE)\s+\S+", l2):   # a word's argument: no ; ends a definition there
            if m.group(1) in ('[CHAR]', 'CHAR'): l2 = l2[:m.start()] + m.group(1) + ' ' * (m.end() - m.start() - len(m.group(1))) + l2[m.end():]
        m = re.search(r'(^|\s)\\(\s.*)?$', l2)
        if m: l2 = l2[:m.start()] + ' ' * (len(l2) - m.start())
        for m in re.finditer(r'(^|\s)\(\s[^)]*\)', l2): l2 = l2[:m.start()] + ' ' * (m.end() - m.start()) + l2[m.end():]
        out.append(l2)
    return '\n'.join(out)
bl = blank(src)
spans, defs, top, pos = {}, {}, [], 0
for m in re.finditer(r'(?ms)(?:^|(?<=\s)):\s+(\S+)(.*?)(?:\s;(?=\s|$))', bl):
    top += bl[pos:m.start()].split()
    n = m.group(1).upper()
    defs.setdefault(n, []).extend(t.upper() for t in m.group(2).split()); spans.setdefault(n, []).append((m.start(), m.end()))
    pos = m.end()
top += bl[pos:].split()
data = set(x.upper() for x in re.findall(r'(?:VARIABLE|CONSTANT|CREATE|DEFER|BUFFER:|VALUE|2VARIABLE)\s+(\S+)', bl))
roots = set(t.upper() for t in top) | {'R-BOOT'}
for f in glob.glob('cm/*.4') + glob.glob('tests/cm/*.4') + ['shell/edit.4']:
    roots |= set(t.upper() for t in blank(open(f).read()).split())
    roots |= set(t.upper() for s in re.findall(r'S" ([^"]*)"', open(f).read()) for t in s.split())   # the Forth cmc.4 makes
reach, todo = set(), [r for r in roots if r in defs or r in data]
while todo:
    n = todo.pop()
    if n in reach: continue
    reach.add(n); todo += [t for t in defs.get(n, []) if (t in defs or t in data) and t not in reach]
dead = sorted(n for n in defs if n not in reach)
if '--prune' in sys.argv:                              # rt.4 without them, to OUT
    cut = sorted(sp for n in dead for sp in spans[n])
    out, last = [], 0
    for a, b in cut:
        out.append(src[last:a]); last = b
    out.append(src[last:])
    open(sys.argv[sys.argv.index('--prune') + 1], 'w').write(''.join(out))
print('%d of %d definitions in rill/rt.4 unreached%s' % (len(dead), len(defs), (': ' + ' '.join(dead)) if dead else ''))
sys.exit(1 if dead and '--prune' not in sys.argv else 0)
