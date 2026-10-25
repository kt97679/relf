# tests/rill/library2.rill in Python: its expected output
import os.path
def dirname(p):                      # Rill's dir(): the shell's dirname, not os.path.dirname
    p = p.rstrip('/') or '/'
    if p == '/': return '/'
    i = p.rfind('/')
    if i < 0: return '.'
    return p[:i].rstrip('/') or '/'
def at(c, k, d):
    if isinstance(c, dict): return c.get(k, d)
    return c[k] if -len(c) <= k < len(c) else d
b = lambda v: 'true' if v else 'false'
print(abs(-7), abs(7), abs(-2.5))
print(os.path.abspath('/a/b/../c/./d'), os.path.abspath('/'), os.path.abspath('/a//b/'), os.path.abspath('/x/..'))
print(dirname('a/b/c'), dirname('c'), dirname('/x'), dirname('/'), dirname('a/'), dirname('a/b/'))
a = [1, 2, [3, 4]]; bb = [1, 2, [3, 4]]; c = [1, 2, [3, 5]]
print(b(a == bb), b(a == c), b(a != c), b([1] == [1.0]), b([] == []))
r = {'x': 1, 'y': [1, 2]}; s = {'y': [1, 2], 'x': 1}
print(b(r == s), b(r == {'x': 1}), b(r != {'x': 2, 'y': [1, 2]}))
w = 'direct 0x02 LIT'.split()
print(at(w, 1, '-'), at(w, 5, '-'), at(w, -1, '-'), at(w, -9, '-'))
item = a[2]
print(at(item, 1, 0), at(item, 2, 0), at({'k': 5}, 'k', 0), at({'k': 5}, 'z', 0))
lines = ['', 'PRIMITIVE DUP', 'other', 'PRIMITIVE SWAP', '']
import re
print(len([l for l in lines if l]), ','.join([l.split()[1] for l in lines if re.match('^PRIMITIVE ', l)]))
long = ['one', 'two', 'three']
print(len(long), '+'.join(long))
print(int('0x1f', 16), -int('0x10', 16), int('12'), int('0X0A', 16))
