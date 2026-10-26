#!/usr/bin/env python3
"""tools/rill-candidates.py - what a feature would save, before it is built (Iteration 747).

Rule 5 (RILL-LEDGER.md, the user at 747): a feature that costs little in
Rill's own source and saves much in Rill's scripts is worth considering.
Each candidate below is a rewrite of the corpus (examples/rill/*.rill)
into the form the feature would allow - a regular expression and its
replacement, applied to code, not to comments - and an estimate of what
it adds to Rill's source: lines in tools/rillc.py, in rill/compile.4 and
in rill/rt.4 together, since both compilers are kept (744). The saving is
measured as rill-measure.py counts characters: code only.
"""
import glob, importlib.util, re, sys
spec = importlib.util.spec_from_file_location('m', 'tools/rill-measure.py'); m = importlib.util.module_from_spec(spec)
sys.argv, argv = sys.argv[:1], sys.argv; spec.loader.exec_module(m); sys.argv = argv
def chars(text): return sum(len(l.strip()) for l in m.code_shell(text))
POST = r'\$\w+(?:\[[^\[\]]+\]|\.\w+)*'              # $x, $x[...], $x.f, chained
CANDIDATES = [
    # name, cost in lines (both compilers + runtime), [(pattern, replacement)]
    ('empty is false: if ($x), not $x for len(...) > 0, == ""', 12, [
        (r'len\((' + POST + r')\) > 0', r'\1'), (r'len\((' + POST + r')\) == 0', r'not \1'),
        (r'(' + POST + r') != ""', r'\1'), (r'(' + POST + r') == ""', r'not \1')]),
    ('def f(x) -> kind = expr (one expression, no return)', 10, [
        (r'(def [^{\n]*-> \w+) \{ return (.*) \}$', r'\1 = \2')]),
    ('$x[i] and $x[i].f in a string without { }', 24, [
        (r'\{(\$\w+(?:\[[^\[\]{}]+\]|\.\w+)+)\}', r'\1')]),
    ('x = if (c) a else b', 20, [
        (r'(\w+) = ("[^"]*"|\'[^\']*\'|\S+); if \(([^{}]+)\) \{ \1 = ([^{};]+) \}', r'\1 = if (\3) \4 else \2')]),
    ('{k: v for x in src} - a record made by a loop', 24, [
        (r'(\w+) = \{\}\n(\s*)for (\w+) in (' + POST + r') \{ \1\[\$\3\] = ([^{}\n]+) \}', r'\1 = {$\3: \5 for \3 in \4}')]),
    ('options(...): flags and values read from $args', 30, [   # dead-words' argument loop, as one call
        (r'delete = "--delete" in \$args\nwhy = ""; files = \[\]\nfor i, a in \$args \{\n.*\n.*\n\}',
         r'o = options([--delete], [--why]); delete = $o["delete"]; why = $o["why"]; files = $o[rest]')]),
    ('m[k] ?= v - set a field only when it is missing', 14, [  # native-by-source's accumulations
        (r'(\w+)\[([^\]]+)\] = add-to\(at\(\$\1, ([^,]+), (\{bytes: 0, n: 0, cls: \[0 0 0 0 0 0\]\})\), \$v\)',
         r'\1[\2] ?= $zero; \1[\2] = add-to($\1[\2], $v)')]),
]
files = sorted(glob.glob('examples/rill/*.rill'))
texts = {f: open(f).read() for f in files}
total = sum(chars(t) for t in texts.values())
print('corpus: %d rewrites, %d code characters\n' % (len(files), total))
print('%-58s %5s %6s %6s %5s %8s' % ('candidate', 'uses', 'saved', '%', 'cost', 'per line'))
rows = []
for name, cost, rules in CANDIDATES:
    uses = saved = 0
    for f, t in texts.items():
        new = t
        for pat, rep in rules:
            new, n = re.subn(pat, rep, new, flags=re.M); uses += n
        saved += chars(t) - chars(new)
    rows.append((saved / cost, name, uses, saved, cost))
    print('%-58s %5d %6d %5.1f%% %5d %8.1f' % (name[:58], uses, saved, 100.0 * saved / total, cost, saved / cost))
