# tests/rill/itemarith.rill in Python: its expected output
b = lambda v: 'true' if v else 'false'
l = [1.5, 2, 7, 0.25]
l[0] += 1
print(l[0])
print(l[0] + 1, l[0] * 2, l[1] + l[0], l[2] - 1, l[2] % 4)
print(b(l[0] < 3), b(l[1] == 2), b(l[3] > 0), b(2 < l[0]), b(l[0] >= 2.5))
r = {'a': 0.25, 'n': 3}
r['a'] += 2; r['n'] += 1; r['n'] -= 0.5
print(r['a'], r['n'])
totals = {}
for w in ["x", "y", "x"]:
    if w in totals: totals[w] += 1.5
    else: totals[w] = 1
print(totals['x'], totals['y'])
k = l[1] + 1
print(k * 10)
