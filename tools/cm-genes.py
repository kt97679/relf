#!/usr/bin/env python3
"""tools/cm-genes.py [--list] - cm/cmc.4 as a genome has it (Iteration 865).

The command model's syntax genes are in cm/genes.tsv; CM_GENES (name=value,...) overrides their
defaults. Prints cm/cmc.4 with each gene's other alternative left out - the lines between
\\ [gene NAME] and \\ [/gene] kept only when NAME is 1, between \\ [gene !NAME] and \\ [/gene] only
when it is 0 - by tools/rill-genes.py's filter, so a genome's image holds its own syntax's code and no
other. --list prints the genome, name=value, one a line.
"""
import importlib.util, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('rill_genes', os.path.join(ROOT, 'tools', 'rill-genes.py'))
rg = importlib.util.module_from_spec(spec); spec.loader.exec_module(rg)

def read_genes(env=None):
    genes, values = {}, {}
    for line in open(os.path.join(ROOT, 'cm', 'genes.tsv')):
        if line.startswith('#') or not line.strip(): continue
        name, default, vals = line.split('\t')[:3]
        genes[name], values[name] = int(default), [int(v) for v in vals.split(',')]
    for item in filter(None, (os.environ.get('CM_GENES', '') if env is None else env).split(',')):
        name, value = item.split('=')
        if name not in genes: sys.exit('cm-genes: no gene %r' % name)
        if int(value) not in values[name]: sys.exit('cm-genes: %s=%s is not one of %s' % (name, value, values[name]))
        genes[name] = int(value)
    return genes

if __name__ == '__main__':
    g = read_genes()
    if '--list' in sys.argv:
        sys.stdout.write(''.join('%s=%d\n' % kv for kv in sorted(g.items())))
    else:
        sys.stdout.write(rg.filtered(open(os.path.join(ROOT, 'cm', 'cmc.4')).read(), g))
