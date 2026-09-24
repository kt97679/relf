#!/usr/bin/env python3
"""tools/op-bench.py [ROUNDS] - what one shell operation costs, here and in dash.

Each operation runs in a `while` loop N times; the CPU time of the shell
and its children (wait4), best of ROUNDS, is divided by N, and the empty
loop's cost is subtracted from the others. Written for Iteration 268's
comparison with dash (DASH.md).
"""
import os, sys, tempfile

ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELF = [os.path.join(ROOT, 'relf64'), os.path.join(ROOT, 'kernel64-shell.img')]
DASH = ['/usr/bin/dash']

OPS = [   # name, iterations, loop body
    ('empty', 20000, ':'),
    ('assign', 20000, 'x=abc'),
    ('varexp', 20000, 'y=$x$x'),
    ('arith', 20000, 'y=$((i*3+7))'),
    ('trim', 20000, 'y=${PWD#/}'),
    ('func', 20000, 'f'),
    ('true', 1000, 'true'),
    ('echo', 1000, 'echo hello > /dev/null'),
    ('abs-true', 1000, '/usr/bin/true'),
    ('cmdsub', 1000, 'y=$(echo x)'),
    ('cmdsub-ext', 1000, 'y=$(/bin/true)'),
    ('pipe-ext', 1000, '/bin/true | /bin/true'),
]

def cpu(argv):
    best = 1e9
    for _ in range(ROUNDS):
        pid = os.fork()
        if pid == 0:
            fd = os.open('/dev/null', os.O_WRONLY)
            os.dup2(fd, 1)
            os.execv(argv[0], argv)
        _, _, ru = os.wait4(pid, 0)
        best = min(best, ru.ru_utime + ru.ru_stime)
    return best

d = tempfile.mkdtemp()
per = {}
for name, n, body in OPS:
    path = os.path.join(d, name + '.sh')
    with open(path, 'w') as f:
        f.write('f() { :; }\ni=0\nwhile [ $i -lt %d ]; do\n%s\ni=$((i+1))\ndone\n' % (n, body))
    per[name] = (cpu(DASH + [path]) / n, cpu(RELF + [path]) / n)

print('%-11s %10s %10s %8s' % ('operation', 'dash us', 'relf us', 'ratio'))
e_d, e_r = per['empty']
for name, _, _ in OPS:
    dd, rr = per[name]
    if name != 'empty':
        dd, rr = dd - e_d, rr - e_r
    print('%-11s %10.2f %10.2f %8.1f' % (name, dd * 1e6, rr * 1e6, rr / dd if dd > 1e-8 else float('inf')))
print('(per operation, CPU of the shell and its children; the empty loop is subtracted from the rest)')
