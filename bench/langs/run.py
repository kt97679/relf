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
# Any machine (Iteration 577): what is not installed is skipped, and said
# so; each row's version is read from the program itself, not written in;
# the relf engine is the native one - relf32 on a 32-bit host - and the
# ratio column is to the assembly engine where there is one.
import shutil, platform, re
def have(p): return shutil.which(p) is not None
def version(argv, pat):
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=20, input='BYE\n')
        m = re.search(pat, out.stdout + out.stderr)
        return m.group(1) if m else ''
    except Exception:
        return ''
subprocess.run(['gcc', '-O2', '-o', 'bench-c', 'bench.c'], check=True)
if have('go'): subprocess.run(['go', 'build', '-o', 'bench-go', 'bench.go'], check=True)
TESTS = ['fib', 'loop', 'sieve', 'bubble', 'matrix', 'fannkuch', 'collatz']
FWORD = {'fib': '32 FIB', 'loop': '30000000 LOOPSUM'}
def forth_stdin(w): return 'S" bench.4" INCLUDED %s . BYE\n' % FWORD.get(w, w.upper())
bits64 = platform.architecture()[0] == '64bit' and os.path.exists(ROOT + '/relf64')
ENG_C = ROOT + ('/relf64' if bits64 else '/relf32')
IMG = ROOT + ('/forth/kernel64.img' if bits64 else '/forth/kernel32.img')
gv = version(['gforth', '--version'], r'gforth ([0-9.]+)') if have('gforth') else ''
IMPL = [  # name, argv for test w, stdin for test w - only what is here
    ('C (gcc -O2)', lambda w: ['./bench-c', w], None),
]
if have('go'): IMPL.append(('Go ' + version(['go', 'version'], r'go([0-9.]+)'), lambda w: ['./bench-go', w], None))
if os.path.exists(ROOT + '/relfasm64'):
    IMPL.append(('relf, assembly engine', lambda w: [ROOT + '/relfasm64', ROOT + '/forth/kernel64.img'], forth_stdin))
if os.path.exists(ENG_C):
    IMPL.append(('relf, C engine', lambda w: [ENG_C, IMG], forth_stdin))
# the native kernel (Iteration 649): the same bench.4, the same stdin - it is
# a standalone kernel, kernel.4 compiled to x86-64 (docs/NATIVE.md); built by
# `make native-kernel`, x86-64 only
if os.path.exists(ROOT + '/native-kernel'):
    IMPL.append(('relf, native', lambda w: [ROOT + '/native-kernel'], forth_stdin))
if have('gforth-fast'): IMPL.append(('gforth-fast ' + gv, lambda w: ['gforth-fast', 'bench.4', '-e', FWORD.get(w, w.upper()) + ' . bye'], None))
if have('gforth'): IMPL.append(('gforth ' + gv, lambda w: ['gforth', 'bench.4', '-e', FWORD.get(w, w.upper()) + ' . bye'], None))
if have('pforth'): IMPL.append(('pforth ' + version(['pforth'], r'V([0-9.]+)'), lambda w: ['pforth', '-q'], forth_stdin))
if have('ruby'): IMPL.append(('Ruby ' + version(['ruby', '--version'], r'ruby ([0-9.]+)'), lambda w: ['ruby', 'bench.rb', w], None))
if have('python3'): IMPL.append(('Python ' + version(['python3', '--version'], r'Python ([0-9.]+)'), lambda w: ['python3', 'bench.py', w], None))
for n, prog in (('Go', 'go'), ('gforth', 'gforth'), ('pforth', 'pforth'), ('Ruby', 'ruby'), ('Python', 'python3')):
    if not have(prog): print('skipped: %s (%s not installed)' % (n, prog))
def run(argv, stdin):
    t = time.perf_counter()
    out = subprocess.run(argv, input=stdin, capture_output=True, text=True, timeout=300).stdout
    return time.perf_counter() - t, out
ref = {w: run(['./bench-c', w], None)[1].split()[-1] for w in TESTS}
rows = []
for name, argv, stdin in IMPL:
    times = []
    try:
        for w in TESTS:
            best = None
            for _ in range(3):
                dt, out = run(argv(w), stdin(w) if stdin else None)
                nums = [x for x in out.replace('\r', ' ').split() if x.lstrip('-').isdigit()]
                if not nums or nums[-1] != ref[w]:
                    raise ValueError('%s gave %r, not %s' % (w, nums[-1:] or out[-60:], ref[w]))
                best = dt if best is None else min(best, dt)
            times.append(best * 1000)
        rows.append((name, times))
    except Exception as e:           # a row that fails is reported, the rest still run
        print('failed: %s: %s' % (name, e))
d = dict(rows)
relf = d.get('relf, assembly engine') or d.get('relf, C engine')
print('| ms, best of 3 | ' + ' | '.join(TESTS) + ' | vs relf |')
print('|---|' + '---:|' * (len(TESTS) + 1))
for name, t in rows:
    g = math.exp(sum(math.log(a / b) for a, b in zip(t, relf)) / len(t))
    print('| %s | %s | %s |' % (name, ' | '.join('%.0f' % x for x in t), '%.2fx' % g))
