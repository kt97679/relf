#!/usr/bin/env python3
"""tools/gen-case.py > cm/case.4 - Unicode's simple case mapping, packed, for upper and lower (913).

From Python's own tables (unicodedata's version is named in the file made): a code point maps to one code
point, or it is left as it is - the full mappings that change a text's length (ß to SS) are not simple
ones. Each table is ranges, sorted: a range a run of code points with one delta, or with alternation, every
other one from its start (Latin Extended-A's Āā Ăă ...). A range is one cell: bits 0-20 its start, 21-31 its
length less one, 32 alternation, 33 up its delta plus 2^19. Run it again when Python's Unicode moves on.
"""
import sys, unicodedata
def table(f):
    def simple(c):
        s = f(chr(c))
        return ord(s) if len(s) == 1 else c
    pts = [(c, simple(c)) for c in range(0x110000) if not 0xD800 <= c <= 0xDFFF and simple(c) != c]
    rs = []
    for c, m in pts:
        d = m - c
        if rs and not rs[-1][3] and rs[-1][1] == c - 1 and rs[-1][2] == d:
            rs[-1][1] = c; continue
        if rs and rs[-1][2] == d and rs[-1][1] + 2 == c and (rs[-1][3] or rs[-1][0] == rs[-1][1]):
            rs[-1][1] = c; rs[-1][3] = 1; continue
        rs.append([c, c, d, 0])
    out = []
    for lo, hi, d, alt in rs:
        while hi - lo > 2047:
            step = 2048 if not alt else 2048
            out.append((lo, lo + 2047 - (alt and 1), d, alt)); lo += 2048
        out.append((lo, hi, d, alt))
    return out
def cells(rs):
    for lo, hi, d, alt in rs:
        assert 0 <= hi - lo <= 2047 and -(1 << 19) <= d < (1 << 19)
        yield lo | (hi - lo) << 21 | alt << 32 | (d + (1 << 19)) << 33
up, lo = table(str.upper), table(str.lower)
print('\\ cm/case.4 - Unicode %s\'s simple case mapping, for upper and lower: made by tools/gen-case.py - edit that, not this.' % unicodedata.unidata_version)
print('\\ Each cell a range: bits 0-20 its start, 21-31 its length less one, 32 every other point only, 33 up its delta + 2^19.')
for name, rs in (('CASE-UP', up), ('CASE-LO', lo)):
    cs = list(cells(rs))
    print('CREATE %s %d ,' % (name, len(cs)))
    for i in range(0, len(cs), 6):
        print('  ' + ' '.join('%d ,' % c for c in cs[i:i+6]))
