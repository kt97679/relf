#!/usr/bin/env python3
"""bench.py - paired, interleaved CPU-time benchmark of VM builds.

Each round runs every (engine,image) on every workload once, in a
shuffled order, and records user+sys CPU time of the child via wait4
(less noisy than wall clock on a shared 1-vCPU VM). Ratios are computed
PER ROUND against the first configuration (paired), then summarised by
the median and a bootstrap 95% interval of that median.
usage: bench.py ROUNDS cfgfile
cfgfile lines:  name|cwd|command with {w} for the workload path
The command may start with NAME=value words, set in its environment
(Iteration 264: RELF_TREE=1 selects the command-tree path).
"""
import os, sys, random, statistics as st
ROUNDS = int(sys.argv[1]); cfg = []
for l in open(sys.argv[2]):
    l = l.strip()
    if l and not l.startswith('#'):
        n, cwd, cmd = l.split('|'); cfg.append((n, cwd, cmd))
WL = os.environ.get('WL', 'loop fn str arith start').split()
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests', 'bench-vm') + '/'

def run(cwd, cmd, reps=1):
    tot = 0.0
    for _ in range(reps):
        pid = os.fork()
        if pid == 0:
            os.chdir(cwd)
            fd = os.open('/dev/null', os.O_WRONLY); os.dup2(fd, 1); os.dup2(fd, 2)
            a = cmd.split(); env = dict(os.environ)
            while a and '=' in a[0] and not a[0].startswith('/'):
                k, v = a.pop(0).split('=', 1); env[k] = v
            try:
                os.execve(a[0], a, env)
            finally:
                os._exit(127)
        _, status, ru = os.wait4(pid, 0)
        if os.WIFSIGNALED(status) or os.WEXITSTATUS(status) >= 64: raise SystemExit("FAILED: %s in %s" % (cmd, cwd))
        tot += ru.ru_utime + ru.ru_stime
    return tot * 1000

res = {(c[0], w): [] for c in cfg for w in WL}
for r in range(ROUNDS + 1):
    jobs = [(c, w) for c in cfg for w in WL]; random.shuffle(jobs)
    for (n, cwd, cmd), w in jobs:
        if w == 'start':
            t = run(cwd, cmd.replace('{w}', '-c true'), 20)
        else:
            t = run(cwd, cmd.replace('{w}', W + w + '.sh'))
        if r: res[(n, w)].append(t)          # round 0 is warmup

def boot(xs, k=2000):
    m = sorted(st.median(random.choices(xs, k=len(xs))) for _ in range(k))
    return m[int(.025 * k)], m[int(.975 * k)]

base = cfg[0][0]
print("%-16s" % "config" + "".join("%22s" % w for w in WL))
for n, _, _ in cfg:
    row = "%-16s" % n
    for w in WL:
        med = st.median(res[(n, w)])
        if n == base: row += "%14.1fms       " % med
        else:
            rat = [a / b for a, b in zip(res[(n, w)], res[(base, w)])]
            lo, hi = boot(rat)
            row += "  %5.3f [%5.3f-%5.3f]" % (st.median(rat), lo, hi)
    print(row)
