#!/usr/bin/env python3
"""port/measure/count-dispatch.py RCOUNT-DIR DESIGN-PROF DESIGN-IMAGE.img OUT.img - every dispatch of the lab's
Forth benchmarks (inputs/, fed on stdin) and of bench-vm's five, on relf (relf-count.py's engines) and on a
design (its engine built with PROFILE=1: DESIGN-PROF; its kernel image for the benchmarks, the shell's OUT.img
for the scripts). A design's DISPATCH256 dump counts a call twice - its first byte and the pseudo-op 256 -
so a call is taken once here (the pairs whose second is 128-255 left out)."""
import os, sys, array, subprocess, tempfile
here = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(here, '..', '..')
rc, kp, kimg, simg = sys.argv[1:5]
def relf(cmd, stdin=None):
    c = tempfile.mktemp(); open(c, 'wb').write(bytes(1 << 20))
    subprocess.run(cmd, stdin=open(stdin) if stdin else subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   cwd='/tmp', env=dict(os.environ, COUNTS=c, THIS_SH=cmd[0]))
    a = array.array('I'); a.frombytes(open(c, 'rb').read()); os.remove(c); return sum(a)
def design(cmd, stdin=None):
    p = tempfile.mktemp()
    subprocess.run(cmd, stdin=open(stdin) if stdin else subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   cwd='/tmp', env=dict(os.environ, VMPROF=p, RELF_ARGV0='x'))
    tot = calls = 0
    for l in open(p):
        q = l.split()
        if len(q) == 3 and q[0].isdigit():
            b, n = int(q[1]), int(q[2])
            if 128 <= b <= 255: continue
            tot += n; calls += n if b == 256 else 0
    os.remove(p); return tot, calls
print('%-14s %12s %12s %10s %7s' % ('program', 'relf64', 'design', 'its calls', 'ratio'))
for w in ['fib', 'loop', 'bubble', 'ackermann', 'sieve', 'parse']:
    f = os.path.join(here, 'inputs', w + '.fth')
    r = relf([os.path.join(rc, 'relf-count'), os.path.join(R, 'forth/kernel64.img')], f); k, c = design([kp, kimg], f)
    print('%-14s %12d %12d %10d %7.2f' % (w, r, k, c, k / r), flush=True)
for w in ['loop', 'fn', 'str', 'arith', 'realistic']:
    sh = os.path.join(R, 'tests/bench-vm', w + '.sh')
    r = relf([os.path.join(rc, 'relfsh-count'), sh]); k, c = design([kp, simg, sh])
    print('%-14s %12d %12d %10d %7.2f' % (w + '.sh', r, k, c, k / r), flush=True)
