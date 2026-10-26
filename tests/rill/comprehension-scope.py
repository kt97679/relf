r = {'a': 1, 'b': 2}
names = [k for k, c in r.items()]; x = {'a': {'c': 7}}
print(','.join(names), x['a']['c'])
k = 5; ks = [k for k, v in r.items()]; print(k, ''.join(ks))
y = 'keep'; ys = [y for y in ['p', 'q']]; print(y, ''.join(ys))
m = [[1, 2], [3]]; print(' '.join(str(len([z for z in z])) for z in m))
for i in range(2): print(i, ''.join([i for i in ['s', 't']]))
def double(l): return [w * 2 for w in l]
w = 'w stays'; print(' '.join(str(n) for n in double([1, 2])), w)
q = [q for q in [1]]; print('q', len(q))
print(''.join([e for e in ['u', 'v'] if e != 'u']), 'e')
