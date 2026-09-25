"""tools/opcodes.py - the opcode map, read from opcodes.tab (Iteration 518).

The tools used to keep their own copies of the numbering - opcode-mix.py
the fold and specialised names, image-audit.py the band positions - and
opcodes.tab is the one source now (CV8.md 2.2). Import it:

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import opcodes
    ops = opcodes.load()        # rows: (kind, number, name, handler)
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(path=None):
    rows = []
    for line in open(path or os.path.join(ROOT, 'opcodes.tab')):
        f = line.split()
        if not f or f[0].startswith('#'):
            continue
        kind, num, name, handler = f[:4]
        rows.append((kind, int(num, 0), name, handler))
    return rows

def names():
    """(opcode number -> name, escape selector -> name)"""
    rows = load()
    return ({n: nm for k, n, nm, h in rows if k != 'escaped'},
            {n: nm for k, n, nm, h in rows if k == 'escaped'})

def number(name):
    """the opcode numbered by this name (never an escape selector)"""
    for k, n, nm, h in load():
        if nm == name and k != 'escaped':
            return n
    raise KeyError(name)
