#!/usr/bin/env python3
"""tools/dead-words.py [--delete] FILE... - definitions nothing can reach.

Reads the Forth source files in load order and builds a reference graph:
every colon definition and every defining word (VARIABLE, CONSTANT,
CREATE, DEFER, BUFFER:, ARGS-BUFFER:, VALUE) is a node; the words in its
body are its references (comments, stack comments and string literals
excluded). The roots are the boot word MAIN and every top-level line that
is not a definition - builtin registrations, stores, and so on - except
`' X IS Y`, which makes X reachable only if Y is, and only if it is Y's
last such assignment.

Prints the unreachable definitions. With --delete, removes them from the
files, each with the comment lines directly above it, and removes the
superseded or unreachable `IS` lines. Written for Iteration 265, where
it removed the line-based shell once the command-tree path replaced it.
"""
import re, sys

DEFINERS = {'VARIABLE', 'CONSTANT', 'CREATE', 'DEFER', 'BUFFER:',
            'ARGS-BUFFER:', 'VALUE', '2VARIABLE'}
STRINGS = {'S"': '"', '."': '"', 'ABORT"': '"', 'C"': '"', '.(': ')'}

def tokens(line):
    """(token) list of a line, comments and string literals removed."""
    out, toks, i = [], line.split(), 0
    while i < len(toks):
        t = toks[i]
        if t == '\\':
            break
        if t == '(':
            while i < len(toks) and not toks[i].endswith(')'):
                i += 1
            i += 1
            continue
        if t in STRINGS:
            end = STRINGS[t]
            out.append(t)
            i += 1
            while i < len(toks) and not toks[i].endswith(end):
                i += 1
            i += 1
            continue
        out.append(t)
        i += 1
    return out

delete = '--delete' in sys.argv
why = sys.argv[sys.argv.index('--why') + 1] if '--why' in sys.argv else None
args = sys.argv[1:]
if why:
    i = args.index('--why'); del args[i:i + 2]
files = [f for f in args if f != '--delete']
# Each definition is its own node; a name refers to the definition visible
# where it is used, as the Forth compiler resolves it (a redefinition
# shadows the earlier one only for what follows).
nodes = []       # (name, file, first line, last line)
nrefs = []       # set of node ids per node
current = {}     # name -> node id visible now
roots = set()
is_lines = []    # (file, line, xt node, defer node)
lines = {f: open(f).read().split('\n') for f in files}

def resolve(toks):
    return {current[t] for t in toks if t in current}

def new_node(name, f, a, b, body):
    nodes.append((name, f, a, b)); nrefs.append(resolve(body))
    current[name] = len(nodes) - 1

for f in files:
    L = lines[f]
    i = 0
    while i < len(L):
        t = tokens(L[i])
        if t and t[0] == ':' and len(t) > 1:
            name, start, body = t[1], i, t[2:]
            while ';' not in body:
                i += 1
                if i >= len(L):
                    break
                body += tokens(L[i])
            new_node(name, f, start, i, body)
            i += 1
            continue
        if len(t) >= 4 and t[0] == "'" and t[2] == 'IS':
            if t[1] in current and t[3] in current:
                is_lines.append((f, i, current[t[1]], current[t[3]]))
            i += 1
            continue
        named = False
        for k, w in enumerate(t):
            if (w in DEFINERS or w.endswith('BUFFER:')) and k + 1 < len(t):
                roots.update(resolve(t[k + 2:]))
                new_node(t[k + 1], f, i, i, t[:k + 1])   # the definer is used too
                named = True
                break
        if not named:
            roots.update(resolve(t))
        i += 1
if 'MAIN' in current:
    roots.add(current['MAIN'])

last_is = {}
for entry in is_lines:
    last_is[entry[3]] = entry
for (f, ln, x, y) in last_is.values():
    nrefs[y].add(x)

reach, parent, todo = set(), {}, list(roots)
for r in todo:
    parent[r] = None
while todo:
    n = todo.pop(0)
    if n in reach:
        continue
    reach.add(n)
    for r in nrefs[n]:
        if r not in reach and r not in parent:
            parent[r] = n
            todo.append(r)
if why:
    ids = [k for k, nd in enumerate(nodes) if nd[0] == why]
    for k in ids:
        chain = []
        n = k
        while n is not None and n in parent and len(chain) < 40:
            chain.append(f'{nodes[n][0]}@{nodes[n][1]}:{nodes[n][2] + 1}')
            n = parent[n]
        print(' <- '.join(chain) + ('' if k in parent else '  (unreachable)'))
    sys.exit(0)

dead = sorted((nd[1], nd[2], nd[0]) for k, nd in enumerate(nodes) if k not in reach)
for f, ln, n in dead:
    print(f'{f}:{ln + 1}: {n}')
dead_is = [e for e in is_lines if e[3] not in reach or last_is.get(e[3]) is not e]
for f, ln, x, y in dead_is:
    print(f'{f}:{ln + 1}: IS line  {nodes[x][0]} -> {nodes[y][0]}')
print(f'{len(dead)} unreachable definitions, {len(dead_is)} dead IS lines, {len(reach)} reachable', file=sys.stderr)

if delete:
    kill = {f: set() for f in files}
    for k, (n, f, a, b) in enumerate(nodes):
        if k in reach:
            continue
        # the comment block directly above belongs to the definition
        while a > 0 and lines[f][a - 1].lstrip().startswith('\\'):
            a -= 1
        kill[f].update(range(a, b + 1))
    for f, ln, x, y in dead_is:
        kill[f].add(ln)
    for f in files:
        out, blank = [], False
        for k, l in enumerate(lines[f]):
            if k in kill[f]:
                continue
            if l.strip() == '':
                if blank:
                    continue
                blank = True
            else:
                blank = False
            out.append(l)
        open(f, 'w').write('\n'.join(out))
