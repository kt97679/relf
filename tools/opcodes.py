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

def returns():
    """the opcodes that end a body: EXIT and the folded returns, an
    operation and the EXIT after it as one opcode (Iteration 939)"""
    return {n for k, n, nm, h in load() if nm == 'EXIT' and k != 'escaped' or k == 'fold'}

_SYMS = None

def name_symbols():
    """the name code's 30 symbols (Iteration 949): forth/cross-core.4's
    NAME-SYMBOLS, their one source"""
    global _SYMS
    if _SYMS is None:
        import re
        src = open(os.path.join(ROOT, 'forth/cross-core.4'), encoding='latin1').read()
        _SYMS = re.search(r'^: NAME-SYMBOLS .*?S" (.{30})" ;', src, re.M).group(1)
    return _SYMS

def unpack_name(units, count=0):
    """A header's name as written, from its bytes (count & 31 of them)
    and its count byte: CV8.md 4.2, kernel.4's NAME>STRING - as written
    when bit 7 is set, else packed. Format 14 on (Iteration 949) and
    the native kernels."""
    units = bytes(units)
    if count & 128:
        return units.decode('latin1')
    syms = name_symbols()
    nib = [n for u in units for n in (u >> 4, u & 15)]
    out, i = [], 0
    while i < len(nib) and len(out) < 31:
        n = nib[i]; i += 1
        if n < 15:
            out.append(syms[n]); continue
        if i >= len(nib):
            break                                # the 15 after an odd last nibble
        m = nib[i]; i += 1
        if m:
            out.append(syms[14 + m])
        else:
            out.append(chr(nib[i] << 4 | nib[i + 1])); i += 2
    return ''.join(out)

def pack_name(name):
    """(bytes, count byte) of a header for name, as kernel.4's NAME>BUF lays it"""
    syms = name_symbols(); nib = []
    for c in name.encode('latin1'):
        i = syms.find(chr(c)) if c < 128 else -1
        nib += [i] if 0 <= i < 15 else [15, i - 14] if i >= 15 else [15, 0, c >> 4, c & 15]
    if len(nib) & 1:
        nib.append(15)
    b = bytes(nib[j] << 4 | nib[j + 1] for j in range(0, len(nib), 2))
    if len(b) < len(name):
        return b, len(b)
    return name.encode('latin1'), len(name) | 128

def link_len(img, nfa):
    """the bytes of the link before the name field at nfa: its tag says"""
    tag = img[nfa - 1]
    return 1 if tag < 128 else 2 if tag < 192 else 3

def header(img, nfa):
    """(name, count byte, link bytes, header start, xt) of the header whose
    name field - its count byte - is at nfa: [name][link][count][body]
    (Iteration 949)"""
    c = img[nfa]; k = c & 31; ll = link_len(img, nfa)
    start = nfa - ll - k
    return unpack_name(img[start:start + k], c), c, ll, start, nfa + 1

def find_header(img, name):
    """the name field (count byte) of a header for name in img, found by
    its bytes - the first that a link and the count byte follow - or -1"""
    b, c = pack_name(name); i = img.find(b)
    while i >= 0:
        for ll in (1, 2, 3):
            nfa = i + len(b) + ll
            if nfa < len(img) and img[nfa] & 0x9F == c and link_len(img, nfa) == ll:
                return nfa
        i = img.find(b, i + 1)
    return -1
