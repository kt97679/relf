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
if __name__ == '__main__':
    g = read_genes()
    for name, v in g.items():
        print('%d CONSTANT G-%s' % (v, name.upper()) if '--forth' in sys.argv else '%s=%d' % (name, v))
