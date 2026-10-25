# tests/rill/flow.rill in Python: its expected output
n = 0
while n < 10:
    n += 1
    if n == 3: break
print('a', n)
s = 0; n = 0
while n < 6:
    n += 1
    if n == 3: continue
    s += n
print('b', s)
for i in range(3):
    m = 0
    while m < 10:
        m += 1
        if m == 2: break
    print('c', i, m)
def first_big(xs):
    for x in xs:
        if x > 5: return x
    return -1
print('d', first_big([1, 7, 3, 9]), first_big([1, 2]))
def find_at(n):
    for i in range(10):
        if i * i > n: return i
    return -1
print('e', find_at(20), find_at(200))
def skip_small(xs):
    for x in xs:
        if x < 5: continue
        return x
    return -1
print('f', skip_small([1, 7, 3, 9]), skip_small([1, 2]))
def pair(xs):
    for x in xs:
        for y in xs:
            if x * y == 12: return '%dx%d' % (x, y)
    return 'none'
print('g', pair([2, 3, 4, 6]), pair([1, 5]))
def wloop(n):
    i = 0
    while i < n:
        i += 1
        if i == 4: return i * 10
    return 0
print('h', wloop(9), wloop(2))
def wcont(n):
    i = 0; t = 0
    while i < n:
        i += 1
        if i % 2 == 0: continue
        if i > 6: return t
        t += i
    return t
print('i', wcont(10), wcont(4))
def deep(xs):
    for x in xs:
        if x == 0: continue
        for k, v in {'a': 1, 'b': x}.items():
            if v == 7: return '%s at %d' % (k, x)
    return 'no'
print('j', deep([0, 3, 7, 9]), deep([1, 2]))
total = 0
for i in range(5):
    j = 0
    while True:
        j += 1
        if j > i: break
        if j == 2: continue
        total += j
print('k', total)
