#!/usr/bin/env python3
"""bench/langs/run.py - relf against other languages and other Forths.

Seven small programs, each stressing one kind of work - calls (fib),
the bare loop, byte memory (sieve), cell arrays (bubble), nested
arithmetic (matrix), permutations (fannkuch, from the Benchmarks Game),
branches (collatz) - written the same way in C, Go, Python and Ruby,
and ONCE in Forth (bench.4), the same text for relf, gforth and pforth.
Each run's checksum is checked against C's; times are the best of
three, wall clock, the process's start included. (Iteration 543.)
"""
import os, subprocess, sys, time, math
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
subprocess.run(['gcc', '-O2', '-o', 'bench-c', 'bench.c'], check=True)
subprocess.run(['go', 'build', '-o', 'bench-go', 'bench.go'], check=True)
TESTS = ['fib', 'loop', 'sieve', 'bubble', 'matrix', 'fannkuch', 'collatz']
FWORD = {'fib': '32 FIB', 'loop': '30000000 LOOPSUM'}
def forth_stdin(w): return 'S" bench.4" INCLUDED %s . BYE\n' % FWORD.get(w, w.upper())
IMPL = [  # name, argv for test w, stdin for test w
    ('C (gcc -O2)', lambda w: ['./bench-c', w], None),
    ('Go', lambda w: ['./bench-go', w], None),
    ('relf, assembly engine', lambda w: [ROOT + '/relfasm64', ROOT + '/kernel64.img'], forth_stdin),
    ('relf, C engine', lambda w: [ROOT + '/relf64', ROOT + '/kernel64.img'], forth_stdin),
    ('gforth-fast 0.7.3', lambda w: ['gforth-fast', 'bench.4', '-e', FWORD.get(w, w.upper()) + ' . bye'], None),
    ('gforth 0.7.3', lambda w: ['gforth', 'bench.4', '-e', FWORD.get(w, w.upper()) + ' . bye'], None),
    ('pforth 2.0.1', lambda w: ['pforth', '-q'], forth_stdin),
    ('Ruby 3.2', lambda w: ['ruby', 'bench.rb', w], None),
    ('Python 3.12', lambda w: ['python3', 'bench.py', w], None),
]
def run(argv, stdin):
    t = time.perf_counter()
    out = subprocess.run(argv, input=stdin, capture_output=True, text=True, timeout=300).stdout
    return time.perf_counter() - t, out
ref = {w: run(['./bench-c', w], None)[1].split()[-1] for w in TESTS}
rows = []
for name, argv, stdin in IMPL:
    times = []
    for w in TESTS:
        best = None
        for _ in range(3):
            dt, out = run(argv(w), stdin(w) if stdin else None)
            nums = [x for x in out.replace('\r', ' ').split() if x.lstrip('-').isdigit()]
            if not nums or nums[-1] != ref[w]:
                sys.exit('%s: %s gave %r, not %s' % (name, w, nums[-1:] or out[-60:], ref[w]))
            best = dt if best is None else min(best, dt)
        times.append(best * 1000)
    rows.append((name, times))
relf = dict(rows)['relf, assembly engine']
print('| ms, best of 3 | ' + ' | '.join(TESTS) + ' | vs relf |')
print('|---|' + '---:|' * (len(TESTS) + 1))
for name, t in rows:
    g = math.exp(sum(math.log(a / b) for a, b in zip(t, relf)) / len(t))
    print('| %s | %s | %s |' % (name, ' | '.join('%.0f' % x for x in t), '%.2fx' % g))
