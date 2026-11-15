#!/usr/bin/env python3
"""tools/native-r.py [ROUNDS] - R, the cost of native code per CV8 dispatch it replaces, measured per family.

Iteration 951 (NATIVE.md 18.8): NATIVE.md 18's model guessed R. A hybrid's native words are what the
native back end makes of the same sources, so for a workload whose every word is native, R is its CPU
time native over its CPU time on the assembly engine - the engine a hybrid runs on (A47). Measured on
tools/native-knee.py's workloads, each family on the native build of its sources:
  forth   the lab's five programs and bench.4's four, as source on stdin: native-kernel against
          relfasm64 forth/kernel64.img
  system  the CORE suite and the lab's parse.fth, the same
  rill3   tests/cm/bench's three: rill3-native against relfasm64 kernel64-cm.img (rill3-native compiles
          a script's own code natively too, so its R covers that code as well)
  shell   tests/bench-vm's five at SCALE copies (default 5, as bench-vm.py's figures): relfsh-native
          against relfshasm64
bench-vm.py's method: every round runs every pair once, shuffled (round 0 a warm-up); the child's user and
system CPU time by wait4; the ratio taken per round; its median and a bootstrap 95 % interval. A
workload's outputs on the two must agree, or it is reported and not counted. Prints a row per workload and
each family's geometric mean of its medians - the R the model takes for it.
"""
import math, os, random, statistics as st, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
SCALE = int(os.environ.get('SCALE', '5'))
work = tempfile.mkdtemp(prefix='relf-native-r-')

def src(name, text):
    p = os.path.join(work, name)
    open(p, 'w', encoding='latin-1').write(text)
    return p
W = []                                            # (family, name, (cmd, stdin) cv8, (cmd, stdin) native)
FK = ['./relfasm64', 'forth/kernel64.img']
for p in ('fib', 'loop', 'bubble', 'ackermann', 'sieve'):
    f = 'port/measure/inputs/%s.fth' % p
    W.append(('forth', 'lab ' + p, (FK, f), (['./native-kernel'], f)))
b4 = open('bench/langs/bench.4').read()
b4 = b4[:b4.rindex('BYE')] if b4.rstrip().endswith('BYE') else b4
# fib and loopsum sized up from pair-corpus.py's counts (30 FIB, 10,000,000): their native runs were 5 ms
for w, word in (('fib', '32 FIB'), ('loopsum', '100000000 LOOPSUM'), ('fannkuch', 'FANNKUCH'), ('collatz', 'COLLATZ')):
    f = src('b4-%s.4' % w, b4 + '\n%s . CR BYE\n' % word)
    W.append(('forth', 'bench.4 ' + w, (FK, f), (['./native-kernel'], f)))
core = src('core.4', ''.join(open(x, encoding='latin-1').read() for x in ('tests/tester.fr', 'tests/core-extra.fth', 'tests/coreplus-loop.fth')) + '\nBYE\n')
W.append(('system', 'CORE', (FK, core), (['./native-kernel'], core)))
W.append(('system', 'lab parse', (FK, 'port/measure/inputs/parse.fth'), (['./native-kernel'], 'port/measure/inputs/parse.fth')))
for w in ('loop', 'calls', 'for'):
    f = 'tests/cm/bench/%s.cm' % w
    if w == 'for':                                # 900 by 900, as 943 measured it (300 by 300 is 12 ms)
        f = src('for.cm', open(f).read().replace('range 300', 'range 900'))
    W.append(('rill3', 'rill3 ' + w, (['./relfasm64', 'kernel64-cm.img', f], None), (['./rill3-native', f], None)))
for w in ('loop', 'fn', 'str', 'arith', 'realistic'):
    t = open('tests/bench-vm/%s.sh' % w).read()
    f = src('%s.sh' % w, '\n'.join([t] * SCALE) if SCALE > 1 else t)
    W.append(('shell', 'shell ' + w, (['./relfshasm64', f], None), (['./relfsh-native', f], None)))

# each family's start alone, measured in the same rounds and taken off both sides for R' (the model's R is per
# dispatch; a start is not)
bye = src('bye.4', 'BYE\n'); nop = src('nop.cm', 'echo\n')
START = {'forth': ((FK, bye), (['./native-kernel'], bye)), 'system': ((FK, bye), (['./native-kernel'], bye)),
         'rill3': ((['./relfasm64', 'kernel64-cm.img', nop], None), (['./rill3-native', nop], None)),
         'shell': ((['./relfshasm64', '-c', 'true'], None), (['./relfsh-native', '-c', 'true'], None))}
for f in ('forth', 'rill3', 'shell'):
    W.append((f, 'start:' + f, START[f][0], START[f][1]))
ENV = dict(os.environ, RILL3_PATH=os.path.join(ROOT, 'lib'))
def run(cmd, stdin):
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.dup2(os.open(stdin or '/dev/null', os.O_RDONLY), 0)
        os.dup2(w, 1); os.dup2(w, 2); os.close(r)
        try: os.execve(cmd[0], cmd, ENV)
        finally: os._exit(127)
    os.close(w)
    out = b''
    while True:
        b = os.read(r, 65536)
        if not b: break
        out += b
    os.close(r)
    _, status, ru = os.wait4(pid, 0)
    lines = [l for l in out.decode('latin-1').replace('\r', '').split('\n')
             if l.strip() and 'Welcome' not in l and l.strip() != 'OK']
    return ru.ru_utime + ru.ru_stime, '\n'.join(lines)

times = {(i, k): [] for i in range(len(W)) for k in (0, 1)}
outs = {}
for rnd in range(ROUNDS + 1):
    jobs = [(i, k) for i in range(len(W)) for k in (0, 1)]
    random.shuffle(jobs)
    for i, k in jobs:
        t, o = run(*W[i][2 + k])
        outs.setdefault(i, {})[k] = o
        if rnd: times[(i, k)].append(t)
def boot(xs, k=2000):
    m = sorted(st.median(random.choices(xs, k=len(xs))) for _ in range(k))
    return m[int(.025 * k)], m[int(.975 * k)]
starts = {f: [None, None] for f in START}
for i, (f, name, _, _) in enumerate(W):
    if name.startswith('start:'):
        starts[f] = [times[(i, 0)], times[(i, 1)]]
starts['system'] = starts['forth']
print('%-18s %-7s %10s %10s  %-26s %s' % ('workload', 'family', 'cv8-asm', 'native', 'R: native / cv8-asm [95 %]',
                                         "R': each side less its start [95 %]"))
fam, famp = {}, {}
for i, (f, name, _, _) in enumerate(W):
    a, b = times[(i, 0)], times[(i, 1)]
    agree = outs[i][0] == outs[i][1] or name.startswith('start:')
    rat = [y / x for x, y in zip(a, b)]
    lo, hi = boot(rat)
    row = '%-18s %-7s %9.4fs %9.4fs  %.3f [%.3f-%.3f]' % (name, f, st.median(a), st.median(b), st.median(rat), lo, hi)
    if not name.startswith('start:'):
        sa, sb = starts[f]
        ratp = [(y - t) / (x - s) for x, y, s, t in zip(a, b, sa, sb)]
        lp, hp = boot(ratp)
        row += '        %.3f [%.3f-%.3f]' % (st.median(ratp), lp, hp)
        if agree:
            fam.setdefault(f, []).append(st.median(rat)); famp.setdefault(f, []).append(st.median(ratp))
    print(row + ('' if agree else '   OUTPUTS DIFFER - not counted'))
print()
g = lambda v: math.exp(sum(map(math.log, v)) / len(v))
for f in ('forth', 'system', 'rill3', 'shell'):
    if fam.get(f):
        print("%-7s R %.3f, R' %.3f (geometric means of %d medians; R' %.3f-%.3f)"
              % (f, g(fam[f]), g(famp[f]), len(fam[f]), min(famp[f]), max(famp[f])))
