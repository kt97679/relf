#!/usr/bin/env python3
"""tools/rill-genes.py [--forth] - Rill's genes, defaults from rill/genes.tsv and RILL_GENES's
overrides (Iteration 749). --forth prints them as the constants the image is built with
(G-SHORT, G-LISTCAP, ...); without it, name=value lines. tools/rillc.py reads the same
table the same way (read_genes), so the two compilers see one genome."""
import os, sys
def read_genes(root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')):
    genes, values = {}, {}
    for line in open(os.path.join(root, 'rill', 'genes.tsv')):
        if line.startswith('#') or not line.strip(): continue
        name, default, vals = line.split('\t')[:3]
        genes[name], values[name] = int(default), [int(v) for v in vals.split(',')]
    for item in filter(None, os.environ.get('RILL_GENES', '').split(',')):
        name, value = item.split('=')
        if name not in genes: sys.exit('rill-genes: no gene %r' % name)
        if int(value) not in values[name]: sys.exit('rill-genes: %s=%s is not one of %s' % (name, value, values[name]))
        genes[name] = int(value)
    return genes
SOURCES = ('rt.4', 'regex.4', 'compile.4')
def filtered(text, g):
    r"""A Forth source as a genome has it (751): the lines between \ [gene NAME] and \ [/gene] kept only
    when NAME is on, between \ [gene !NAME] and \ [/gene] only when it is off - so a gene's code is
    in the image, and counted in Rill's source, only where the gene is on."""
    out, keep = [], [True]
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith('\\ [gene '):
            name = s[len('\\ [gene '):].split(']')[0]
            on = g[name.lstrip('!')] != 0
            keep.append(keep[-1] and (not on if name.startswith('!') else on)); continue
        if s.startswith('\\ [/gene]'):
            keep.pop(); continue
        if keep[-1]: out.append(line)
    if len(keep) != 1: sys.exit('rill-genes: a [gene] block not closed')
    return '\n'.join(out)
def code_chars(text):
    r"""Characters of code, as rule 3 counts a script: comments, blank lines and indentation out."""
    n = 0
    for line in text.split('\n'):
        line = line.split(' \\ ')[0] if not line.lstrip().startswith('\\') else ''
        line = __import__('re').sub(r'(^|\s)\( [^)]*\)', ' ', line).strip()
        n += len(line)
    return n
if __name__ == '__main__':
    g = read_genes()
    if '--source' in sys.argv:              # the genome's sources, filtered, into DIR
        d = sys.argv[sys.argv.index('--source') + 1]; os.makedirs(d, exist_ok=True)
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rill')
        for f in SOURCES: open(os.path.join(d, f), 'w').write(filtered(open(os.path.join(root, f)).read(), g))
        sys.exit(0)
    if '--size' in sys.argv:                 # Rill's source as the genome has it: code characters
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rill')
        print(sum(code_chars(filtered(open(os.path.join(root, f)).read(), g)) for f in SOURCES)); sys.exit(0)
    for name, v in g.items():
        print('%d CONSTANT G-%s' % (v, name.upper()) if '--forth' in sys.argv else '%s=%d' % (name, v))
