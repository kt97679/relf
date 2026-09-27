"""tools/opcodes.py - the opcode map, read from engine/opcodes.tab (Iteration 518).

The tools used to keep their own copies of the numbering - opcode-mix.py
the fold and specialised names, image-audit.py the band positions - and
engine/opcodes.tab is the one source now (CV8.md 2.2). Import it:

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import opcodes
    ops = opcodes.load()        # rows: (kind, number, name, handler)
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(path=None):
    rows = []
    for line in open(path or os.path.join(ROOT, 'engine/opcodes.tab')):
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

def formats(path=None):
    """opcode number -> the operand after it: the table's fifth column
    (Iteration 533) - '-', 'u8', 'i8', 'u16', 'i32', 'u64', 'b8', 'b16',
    'slot', 'sel' or 'data'. Escape selectors are not opcodes, and have
    no entry."""
    out = {}
    for line in open(path or os.path.join(ROOT, 'engine/opcodes.tab')):
        f = line.split()
        if not f or f[0].startswith('#') or f[0] == 'escaped':
            continue
        out[int(f[1], 0)] = f[4] if len(f) > 4 else '-'
    return out
