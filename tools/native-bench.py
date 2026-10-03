#!/usr/bin/env python3
"""native-bench.py - the native kernel against CV8's, on Forth workloads.

tests/native/bench/*.4 run on bare kernels - no shell - so the native
back end (docs/NATIVE.md) can be timed against CV8's engines on the same
source. Each round runs every engine on every workload once, in a
shuffled order; the time is the child's user+sys CPU (wait4), the
summary its median. The workloads print their results, which must agree
across engines - a speed is only worth having for the right answer.
usage: tools/native-bench.py [ROUNDS]     (from the repository's top)
Needs ./native-kernel (`make native-kernel`), ./relf64, ./relfasm64.
Where tests/native/bench/c/W.c exists, it is W in C, built with cc -O2 -
the "c" column, and native's time over it, for A33's exit targets
(Iteration 627).
"""
import os, random, statistics as st, subprocess, sys
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
ENGINES = [('cv8-c', ['./relf64', 'forth/kernel64.img']),
           ('cv8-asm', ['./relfasm64', 'forth/kernel64.img']),
           ('native', ['./native-kernel'])]
D = 'tests/native/bench/'
WL = sorted(f[:-2] for f in os.listdir(D) if f.endswith('.4'))

def run(cmd, wl):
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.dup2(os.open(D + wl + '.4', os.O_RDONLY), 0)
        os.dup2(w, 1); os.dup2(w, 2); os.close(r)
        os.execv(cmd[0], cmd)
    os.close(w)
    out = b''
    while True:
        b = os.read(r, 65536)
        if not b: break
        out += b
    os.close(r)
    _, status, ru = os.wait4(pid, 0)
    res = [l for l in out.decode('latin-1').replace('\r', '').split('\n')
           if l.strip() and 'Welcome' not in l and l.strip() != 'OK']
    return ru.ru_utime + ru.ru_stime, ' '.join(res).strip()

import tempfile
CDIR = tempfile.mkdtemp(prefix='native-bench-c-')
CBIN = {}
for w in WL:
    src = D + 'c/' + w + '.c'
    if os.path.exists(src):
        out = os.path.join(CDIR, w)
        if subprocess.call(['cc', '-O2', '-o', out, src]) == 0:
            CBIN[w] = out
times = {(e, w): [] for e, _ in ENGINES + [('c', None)] for w in WL}
answers = {}
for _ in range(ROUNDS):
    jobs = [(e, c, w) for e, c in ENGINES for w in WL] + [('c', [CBIN[w]], w) for w in CBIN]
    random.shuffle(jobs)
    for e, c, w in jobs:
        t, a = run(c, w)
        times[(e, w)].append(t)
        answers.setdefault(w, {})[e] = a
print('%-8s' % 'workload' + ''.join('%10s' % e for e, _ in ENGINES) + '%10s' % 'c'
      + '   native: vs cv8-asm   / c')
for w in WL:
    med = {e: st.median(times[(e, w)]) for e, _ in ENGINES}
    agree = len(set(answers[w].values())) == 1
    cm = st.median(times[('c', w)]) if times[('c', w)] else None
    print('%-8s' % w + ''.join('%9.3fs' % med[e] for e, _ in ENGINES)
          + ('%9.3fs' % cm if cm is not None else '%10s' % '-')
          + '   %6.2fx faster' % (med['cv8-asm'] / max(med['native'], 1e-9))
          + ('  %5.2fx' % (med['native'] / max(cm, 1e-9)) if cm is not None else '       ')
          + ('' if agree else '  ANSWERS DIFFER: %r' % answers[w]))
