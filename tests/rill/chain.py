# tests/rill/chain.rill in Python: its expected output
m = [[1, 2], [3, 4]]
m[1][0] = 9
m[0][1] += 5
print(' '.join(map(str, m[0])), '/', ' '.join(map(str, m[1])))
r = {'a': {'b': 1, 'c': [1, 2, 3]}}
r['a']['b'] = 5
r['a']['c'][2] = 30
r['a']['c'][0] -= 4
print(r['a']['b'], ' '.join(map(str, r['a']['c'])))
grid = []
for i in range(3): grid.append([0, 0, 0])
for i in range(3):
    for j in range(3): grid[i][j] = i * 3 + j
grid[2][2] += 100
for row in grid: print(','.join(map(str, row)))
counts = {}
for w in "a b a c b a".split(): counts[w] = {'n': 0}
for w in "a b a c b a".split(): counts[w]['n'] += 1
for k in sorted(counts): print(k, counts[k]['n'])
deep = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
deep[1][0][1] = 60
deep[0][1][0] += 0.5
print(' '.join(map(str, deep[1][0])), ' '.join(map(str, deep[0][1])))
m[-1][-1] = 44
print(' '.join(map(str, m[1])))
