# tests/rill/pure-params.rill's output, by Python
def size(l): return len(l)
print(size([1, 2, 3]))
for r in [[1, 2], [3]]: print(size(r))
def same(l): return l
print(' '.join(str(x) for x in same([1, 2])))
def first(l): return l[0]
print(first([7, 8]))
def has(l, x): return x in l
print(*['true' if b else 'false' for b in (has([1, 2], 2), has([1, 2], 5))])
def fib(n): return n if n < 2 else fib(n - 1) + fib(n - 2)
def span(n): return len(range(n))
def total(n): return sum(range(n))
print(fib(15), span(4), total(4))
