#!/usr/bin/env python3
"""tools/rill-audit.py - Rill's features and lengths, monitored (Iteration 732).

The user's rule at 732: a feature a real script needs is added - an
unusable tool helps nobody - but every feature is tracked and audited.
This reads examples/rill/FEATURES.tsv (each feature, its status:
spec, adopted, open or rejected, and a pattern that finds its uses) and
examples/rill/MANIFEST.tsv (each rewrite and its original), and prints:

- every feature's uses, file by file;
- AUDIT lines: an adopted feature no rewrite uses any more; an open or
  rejected one that a rewrite uses all the same;
- every rewrite's length against its original (tools/rill-measure.py's
  count), a LONGER line for each that is.

Exit status 1 if there is an AUDIT or a LONGER line, so a Rill
iteration sees it. Run it at the end of every Rill iteration.
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, 'tools')
import importlib.util
spec = importlib.util.spec_from_file_location('rm', 'tools/rill-measure.py')
rm = importlib.util.module_from_spec(spec)
sys.argv, argv = ['x', '--none'], sys.argv
try: spec.loader.exec_module(rm)
except (IndexError, SystemExit): pass
sys.argv = argv

def rows(path):
    for l in open(path, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            yield l.rstrip('\n').split('\t')

feats = list(rows('examples/rill/FEATURES.tsv'))
manifest = list(rows('examples/rill/MANIFEST.tsv'))
sources = {}
for orig, rew, kind in manifest:
    sources[os.path.basename(rew)] = '\n'.join(rm.code_shell(open(rew, encoding='utf-8').read()))
ol = [l.split('|||')[1].strip() for l in open('examples/rill/oneliners.txt', encoding='utf-8') if '|||' in l and not l.startswith('#')]
sources['oneliners'] = '\n'.join(ol)

problems = 0
print('%-42s %-9s %-5s %5s  %s' % ('feature', 'status', 'since', 'uses', 'where'))
for name, status, since, pat in feats:
    if pat == '-':
        uses = {}
    else:
        r = re.compile(pat, re.M)
        uses = {f: len(r.findall(s)) for f, s in sources.items()}
        uses = {f: n for f, n in uses.items() if n}
    total = sum(uses.values())
    print('%-42s %-9s %-5s %5d  %s' % (name[:42], status, since, total, ', '.join('%s %d' % (f.replace('.rill', ''), n) for f, n in sorted(uses.items()))))
    if status == 'adopted' and total == 0 and pat != '-':
        print('AUDIT: adopted, and no rewrite uses it: %s' % name); problems += 1
    if status in ('open', 'rejected') and total:
        print('AUDIT: %s, and used all the same: %s' % (status, name)); problems += 1

# The rule of 734: a function reads the script's variables and never
# changes them - no assignment, no index assignment, no push, extend or
# shift on a script variable, and no local of a script variable's name;
# nor does a `par for` body. What a function changes it returns. Changes
# to a container passed in as a parameter are allowed, and counted.
def blocks(src):
    """(header, body) of each def and par-for, braces matched outside strings."""
    out, i, n = [], 0, len(src)
    heads = re.compile(r'(?m)^[ \t]*(def\s[^{\n]*|par\s+for\s[^{\n]*)\{')
    for m in heads.finditer(src):
        depth, j, q = 1, m.end(), None
        while j < n and depth:
            c = src[j]
            if q:
                if c == '\\' and q == '"': j += 1
                elif c == q: q = None
            elif c in '"\'': q = c
            elif c == '{': depth += 1
            elif c == '}': depth -= 1
            j += 1
        out.append((m.group(1), src[m.end():j - 1], m.start(), j))
    return out
plain = re.compile(r'(?m)(?:^|[{;])\s*(\w+)\s*=(?!=)\s*([^;\n]*)')
change = re.compile(r'(?m)(?:^|[{;])\s*(\w+)\s*(?:\[[^\]\n]*\]\s*(?:=(?!=)|\+=|-=)|\+=|-=)|\b(?:push|extend|shift)\(\$(\w+)')
stmtfor = re.compile(r'(?m)(?:^|[{;])\s*(?:par\s+)?for\s+(\w+)(?:\s*,\s*(\w+))?\s+in\b')
anyfor = re.compile(r'\bfor\s+(\w+)(?:\s*,\s*(\w+))?\s+in\b')
violations, through_params = 0, 0
for f, src in sources.items():
    if f == 'oneliners': continue
    bl = blocks(src)
    top = src
    for h, b, s, e in sorted(bl, key=lambda x: -x[2]):
        if h.startswith('def'): top = top[:s] + ' ' * (e - s) + top[e:]
    script = set(m.group(1) for m in plain.finditer(top)) | set(m.group(1) or m.group(2) for m in change.finditer(top)) \
           | set(x for m in stmtfor.finditer(top) for x in m.groups() if x)
    for h, b, s, e in bl:
        isdef = h.startswith('def')
        params = set(h.split()[2:]) - {'->', 'list', 'text', 'number', 'record', 'decimal', 'run', 'bool', 'status'} if isdef \
                 else set(x for m in anyfor.finditer(h) for x in m.groups() if x)
        name = ' '.join(h.split()[:2])
        local = set(params) | set(x for m in anyfor.finditer(b) for x in m.groups() if x)
        for m in plain.finditer(b):
            v, rhs = m.group(1), m.group(2)
            if v in script and v not in local and (not isdef or re.search(r'\$' + v + r'\b', rhs)):
                print('AUDIT: %s: %s changes the script variable %s' % (f, name, v)); violations += 1
            local.add(v)
        for m in change.finditer(b):
            v = m.group(1) or m.group(2)
            if v in params: through_params += 1
            elif v in script and v not in local:
                print('AUDIT: %s: %s changes the script variable %s' % (f, name, v)); violations += 1
print('the rule of 734: %d violations; %d changes through a parameter' % (violations, through_params))
problems += violations
print()
for orig, rew, kind in manifest:
    (a, b), (c, d) = rm.measure(orig), rm.measure(rew)
    verdict = 'ok' if c <= a and d <= b else 'LONGER'
    print('%-28s %-6s %4d lines %6d chars | Rill %4d lines %6d chars | chars %+6.1f %% | %s' % (orig, kind, a, b, c, d, 100.0 * (d - b) / b, verdict))
    problems += verdict != 'ok'
sys.exit(1 if problems else 0)
