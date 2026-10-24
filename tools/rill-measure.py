#!/usr/bin/env python3
"""tools/rill-measure.py - a Rill rewrite against its original, in code (Iteration 726).

RILL-LEDGER.md's rule: a Rill version is never longer than the original.
Length is code: comments, blank lines, the #! line and a Python module's
docstring are not counted, nor indentation; trailing comments are cut.
Lines and characters both.

    python3 tools/rill-measure.py ORIGINAL REWRITE.rill ...   (pairs)
    python3 tools/rill-measure.py --oneliners FILE            (sh ||| rill a line)
"""
import io, sys, tokenize

def strip_hash(line):
    q = None
    for i, c in enumerate(line):
        if q:
            if c == q: q = None
        elif c in '\'"': q = c
        elif c == '#' and (i == 0 or line[i - 1] in ' \t'): return line[:i]
    return line

def code_shell(text):
    return [l.strip() for l in (strip_hash(l) for l in text.split('\n')[(1 if text.startswith('#!') else 0):]) if l.strip()]

def code_python(text):
    out, prev, first = [], tokenize.INDENT, True
    toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    keep = []
    for t in toks:
        if t.type == tokenize.COMMENT: continue
        if t.type == tokenize.STRING and prev in (tokenize.INDENT, tokenize.NEWLINE, tokenize.NL, tokenize.DEDENT) and first:
            first = False; prev = t.type; continue          # the module docstring
        if t.type not in (tokenize.NL, tokenize.ENCODING): first = first and t.type in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT)
        keep.append(t); prev = t.type
    src = tokenize.untokenize(keep)
    return [l.strip() for l in src.split('\n') if l.strip()]

def measure(path):
    text = open(path, encoding='utf-8').read()
    lines = code_python(text) if path.endswith('.py') else code_shell(text)
    return len(lines), sum(len(l) for l in lines)

if sys.argv[1:2] == ['--oneliners']:
    tot = [0, 0]
    for l in open(sys.argv[2], encoding='utf-8'):
        if l.startswith('#') or '|||' not in l: continue
        a, b = (x.strip() for x in l.split('|||'))
        tot[0] += len(a); tot[1] += len(b)
        print('%4d %4d %s  %s' % (len(a), len(b), 'ok ' if len(b) <= len(a) else 'LONGER', b))
    print('%4d %4d  total, sh then Rill' % tuple(tot))
else:
    args = sys.argv[1:]
    for orig, rill in zip(args[::2], args[1::2]):
        (ol, oc), (rl, rc) = measure(orig), measure(rill)
        print('%-32s %4d lines %6d chars | Rill %4d lines %6d chars | %s' % (orig, ol, oc, rl, rc,
              'ok' if rl <= ol and rc <= oc else 'LONGER'))
