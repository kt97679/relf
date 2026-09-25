#!/usr/bin/env python3
"""tools/dup-scan.py [MIN] [FILE...] - logic repeated across definitions.

Iteration 509's source audit (GOALS.md "What comes next", item 9):
FORTH-STYLE.md 11 says to merge duplicated code because copies drift,
and this finds candidates. Every colon definition is tokenized with its
comments removed - `\\` to the end of a line, `( ... )` - and every run
of at least MIN words (default 12) that appears in two or more
definitions is reported, longest first, overlapping runs merged. A run
is a candidate, not a verdict: two definitions may share words because
they do the same thing, or because Forth has few ways to do a small one.
"""
import re, sys, collections

args = sys.argv[1:]
MIN = int(args.pop(0)) if args and args[0].isdigit() else 12
FILES = args or ['shell.4', 'tree.4', 'edit.4', 'extend.4', 'pool.4', 'shadow.4']

def definitions(path):
    text = open(path).read()
    text = re.sub(r'(?m)(^|\s)\\(\s.*)?$', ' ', text)          # \ comments
    toks = text.split()
    out, i = [], 0
    while i < len(toks):
        if toks[i] == ':' and i + 1 < len(toks):
            name, j, body = toks[i + 1], i + 2, []
            depth = 0
            while j < len(toks) and not (toks[j] == ';' and depth == 0):
                t = toks[j]
                if t == '(' and depth == 0:                        # ( comment )
                    while j < len(toks) and not toks[j].endswith(')'):
                        j += 1
                    j += 1
                    continue
                body.append(t)
                j += 1
            out.append((path, name, body))
            i = j + 1
        else:
            i += 1
    return out

defs = [d for f in FILES for d in definitions(f)]
where = collections.defaultdict(set)
for k, (f, name, body) in enumerate(defs):
    for i in range(len(body) - MIN + 1):
        where[tuple(body[i:i + MIN])].add((k, i))
shared = {s: w for s, w in where.items() if len({k for k, _ in w}) > 1}

# grow each shared shingle into the longest run its definitions share
runs = {}
for s, w in shared.items():
    ks = sorted({k for k, _ in w})
    a, b = ks[0], ks[1]
    ia = min(i for k, i in w if k == a)
    ib = min(i for k, i in w if k == b)
    A, B = defs[a][2], defs[b][2]
    x, y = ia, ib
    while x > 0 and y > 0 and A[x - 1] == B[y - 1]:
        x -= 1; y -= 1
    n = 0
    while x + n < len(A) and y + n < len(B) and A[x + n] == B[y + n]:
        n += 1
    key = (a, x, b, y)
    runs[key] = max(runs.get(key, 0), n)

seen = set(); report = []
for (a, x, b, y), n in sorted(runs.items(), key=lambda kv: -kv[1]):
    sig = tuple(defs[a][2][x:x + n])
    if sig in seen:
        continue
    seen.add(sig)
    users = sorted({'%s %s' % (defs[k][0], defs[k][1]) for k, _ in shared.get(sig[:MIN], [])} |
                   {'%s %s' % (defs[a][0], defs[a][1]), '%s %s' % (defs[b][0], defs[b][1])})
    report.append((n, users, ' '.join(sig)))
print('%d definitions in %s; runs of %d+ words shared by two or more: %d'
      % (len(defs), ' '.join(FILES), MIN, len(report)))
for n, users, text in report[:40]:
    print('\n%3d words, in: %s\n    %s' % (n, ', '.join(users), text[:220]))
