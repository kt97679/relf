import sys
sys.setrecursionlimit(10000)
def fib(n): return n if n < 2 else fib(n - 1) + fib(n - 2)
def loopsum(n):
    s = 0
    for i in range(n): s += i
    return s
def sieve():
    N = 5000000; f = bytearray([1]) * N; c = 0
    for i in range(2, N):
        if f[i]:
            c += 1
            for j in range(i * i, N, i): f[j] = 0
    return c
def bubble():
    seed = 74755; NB = 3000; a = []
    for i in range(NB):
        seed = (seed * 1103515245 + 12345) & 2147483647; a.append(seed % 1000000)
    for i in range(1, NB):
        for j in range(NB - i):
            if a[j] > a[j + 1]: a[j], a[j + 1] = a[j + 1], a[j]
    return sum(v * (i + 1) for i, v in enumerate(a))
def matrix():
    NM = 150; A = [[r + c for c in range(NM)] for r in range(NM)]; B = [[c - r for c in range(NM)] for r in range(NM)]
    return sum(sum(A[r][k] * B[k][c] for k in range(NM)) for r in range(NM) for c in range(NM))
def fannkuch():
    n = 9; p1 = list(range(n)); cnt = [0] * n; r = n; maxf = 0; csum = 0; pc = 0
    while True:
        while r != 1: cnt[r - 1] = r; r -= 1
        p = p1[:]; f = 0; k = p[0]
        while k:
            p[:k + 1] = p[k::-1]; f += 1; k = p[0]
        maxf = max(maxf, f); csum += -f if pc & 1 else f
        while True:
            if r == n: return csum * 1000 + maxf
            p0 = p1[0]; p1[:r] = p1[1:r + 1]; p1[r] = p0
            cnt[r] -= 1
            if cnt[r] > 0: break
            r += 1
        pc += 1
def collatz():
    t = 0
    for i in range(1, 100000):
        n = i; s = 0
        while n > 1: n = n * 3 + 1 if n & 1 else n >> 1; s += 1
        t += s
    return t
w = sys.argv[1]
print({'fib': lambda: fib(32), 'loop': lambda: loopsum(30000000), 'sieve': sieve, 'bubble': bubble,
       'matrix': matrix, 'fannkuch': fannkuch, 'collatz': collatz}[w]())
