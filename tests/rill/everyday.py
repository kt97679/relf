# tests/rill/everyday.rill in Python: its expected output
b = lambda v: 'true' if v else 'false'
a = [1, 2]; bb = a + [3, 4]
print(','.join(map(str, bb)), len(a))
name = "build"
print(name + ".log", "a" + "b")
def tag(x): return x + "!"
print(tag("hi"))
l = [1, 2, 3, 4]
print(l.pop(), ','.join(map(str, l)))
del l[0]; del l[-1]
print(','.join(map(str, l)))
r = {'a': 1, 'b': 2, 'c': 3}
del r['b']
print(','.join(r.keys()), b('b' in r))
print("hello".find("l"), "hello".find("z"), [10, 20, 30].index(20), -1)
print(b("ell" in "hello"), b("xyz" in "hello"), b("ell" not in "hello"))
rows = [{'n': "c", 'v': 3}, {'n': "a", 'v': 1}, {'n': "b", 'v': 2}, {'n': "d", 'v': 1}]
print(' '.join(x['n'] for x in sorted(rows, key=lambda r: r['v'])))
print(' '.join(x['n'] for x in sorted(rows, key=lambda r: r['n'], reverse=True)))
print(' '.join(str(x) for x in sorted([2, 1.5, 1, 3])))
big = {}
for i in range(20): big['k%d' % i] = i
del big['k3']
print(len(big), big['k19'], b('k3' in big), b('k4' in big))
