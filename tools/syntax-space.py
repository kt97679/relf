#!/usr/bin/env python3
"""tools/syntax-space.py [N] - the syntax feature table, checked and measured (Iteration 864, docs/SYNTAX-GENES.md).

Reads docs/syntax-features.tsv: axes, their values (who uses each, which front end here has it) and the
rules between values. Then:

1. Checks the table: every rule names values that exist; and every system named in it - sh, fish,
   Elvish, YSH ... - can be given one value per axis it is named on without breaking a rule. A real
   system that breaks a rule means the rule is wrong, not the system: the check the rules must pass.
2. Measures the space: genomes in all, and without the lexical group (renames, chosen apart).
3. Samples it uniformly (N genomes, 200,000 unless given, a fixed seed): how many break no rule, and
   how many rules the rest break - before any search, what a search would wade through (prompts/02).
4. Counts what is built: each front end's values, and the genomes buildable from values one front
   end has - a search needs two or more values of a gene in one front end.

Exit status 1 if the table is inconsistent.
"""
import itertools, os, random, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
axes, values, users, here, rules = [], defaultdict(list), {}, {}, []
for line in open(os.path.join(ROOT, 'docs', 'syntax-features.tsv'), encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    f = line.rstrip('\n').split('\t') + [''] * 6
    if f[0] == 'axis':
        axes.append(f[1])
    elif f[0] == 'value':
        values[f[1]].append(f[2])
        users[(f[1], f[2])] = f[3].split()
        here[(f[1], f[2])] = [h for h in f[4].split() if h != '-']
    elif f[0] == 'rule':
        def alts(t):
            a, vs = t.split('=')
            return a, set(vs.split('|'))
        rules.append((f[1], alts(f[2]), alts(f[3]), f[4]))

bad = 0
for kind, (a, va), (b, vb), _ in rules:
    for ax, vs in ((a, va), (b, vb)):
        for v in vs:
            if v not in values.get(ax, []):
                print('rule names %s=%s, which the table has not' % (ax, v)); bad += 1

def broken(g):
    """The rules genome g (axis -> value) breaks; an axis g leaves out breaks nothing."""
    out = []
    for kind, (a, va), (b, vb), why in rules:
        if a not in g or g[a] not in va or b not in g:
            continue
        if (kind == 'excludes') == (g[b] in vb):
            out.append('%s %s=%s %s=%s' % (kind, a, g[a], b, '|'.join(sorted(vb))))
    return out

systems = defaultdict(lambda: defaultdict(list))
for (a, v), us in users.items():
    for u in us:
        systems[u][a].append(v)
for name in sorted(systems):
    known = systems[name]
    choices = [[(a, v) for v in known[a]] for a in sorted(known)]
    if not any(not broken(dict(c)) for c in itertools.product(*choices)):
        g = {a: vs[0] for a, vs in known.items()}
        print('%s, as the table has it, breaks: %s' % (name, '; '.join(broken(g)))); bad += 1
print('the table: %d axes, %d values, %d rules; %d systems named, %s'
      % (len(axes), sum(len(values[a]) for a in axes), len(rules), len(systems),
         'each consistent with the rules' if not bad else '%d findings' % bad))

def size(axs):
    n = 1
    for a in axs: n *= len(values[a])
    return n
structural = [a for a in axes if not a.startswith('L')]
print('genomes: %d in all; %d without the lexical group (%s), whose values are chosen apart'
      % (size(axes), size(structural), ' '.join(a for a in axes if a.startswith('L'))))

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
rnd, hist = random.Random(864), Counter()
for _ in range(N):
    g = {a: rnd.choice(values[a]) for a in structural}
    hist[len(broken(g))] += 1
print('a uniform sample of %d: %d break no rule (%.2f%%); rules broken: %s'
      % (N, hist[0], 100.0 * hist[0] / N, ', '.join('%d: %d' % (k, hist[k]) for k in sorted(hist))))

for fe in ('relfsh', 'rill2', 'cm'):
    per = [sum(1 for v in values[a] if fe in here[(a, v)]) for a in axes]
    print('%-6s has %2d values on %2d of %d axes; genomes from its own values: %d'
          % (fe, sum(per), sum(1 for p in per if p), len(axes), 0 if 0 in per else eval('*'.join(map(str, per)))))
print('values no front end here has: %d of %d' % (sum(1 for k in here if not here[k]), len(here)))
sys.exit(1 if bad else 0)
