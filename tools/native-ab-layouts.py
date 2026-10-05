#!/usr/bin/env python3
"""tools/native-ab-layouts.py BASE [ROUNDS] [PADS] - an A/B of the native
shell taken over several layouts (Iteration 688).

687 found that shrinking the code moves the hot loops, and that the VM's
A/B cannot tell a few percent of layout from a few percent of cost. So
each side is built several times, with NATIVE_LAYOUT_PAD bytes of code
space left empty before the first source (tools/build-native-shell.sh) -
PADS, default 0,16,32,48: the four phases of a 64-byte line - and the
native kernel with as many bytes before its runtime, so the routines and
the kernel's words move too; all of them are timed together by
tools/bench-vm.py, interleaved. Per workload:
the spread of BASE's own layouts (what layout alone does), the spread of
the checkout's, and the ratio of their geometric means - the change with
layout averaged out.

BASE is a revision, built in a scratch worktree; the checkout must have
its native kernel built (make native-kernel).
"""
import math, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
base = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
rounds = sys.argv[2] if len(sys.argv) > 2 else '9'
pads = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else '0,16,32,48').split(',')]
WL = os.environ.get('WL', 'loop fn str arith realistic')
out_dir = tempfile.mkdtemp(prefix='native-ab-layouts-')

def sh(cmd, cwd=ROOT, env=None):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, env=env)

KCUT = r"""python3 tools/gen-native-os.py native-os.4 &&
sed '/^\\ PART 10: TOP LEVEL/,$d' forth/kernel.4 > native-kcut9.4 && echo END-CROSS >> native-kcut9.4 &&
{ echo CROSS-COMPILE; sed -n '/^\\ PART 10: TOP LEVEL/,$p' forth/kernel.4; } > native-kcut10.4"""

def kernel(tree, p):
    """The native kernel with p bytes of target space before its runtime:
    the routines and every word after them land p bytes further on. Built
    as the Makefile builds it, from a copy of native-kernel.4 with the pad
    as its first target action."""
    src = open(os.path.join(tree, 'forth/native-kernel.4')).read()
    mark = 'N>A  S" forth/native-rt.4" INCLUDED  A>N'
    if mark not in src:
        sys.exit('native-ab-layouts: %s: native-kernel.4 has no runtime line to pad before' % tree)
    padded = os.path.join(tree, 'native-kernel-padded.4')
    open(padded, 'w').write(src.replace(mark, '%d DP-T +!   \\ layout pad (688)\n%s' % (p, mark), 1))
    r = sh(KCUT + ' && rm -f native-kernel && ./relf64 forth/kernel64.img < native-kernel-padded.4 > native-kernel.log 2>&1; test -x native-kernel', cwd=tree)
    os.unlink(padded)
    if r.returncode:
        sys.exit('native-ab-layouts: %s: kernel pad %d not built' % (tree, p))

def shells(tree, tag):
    made = []
    for p in pads:
        kernel(tree, p)
        out = os.path.join(out_dir, '%s-p%d' % (tag, p))
        # the checkout's build script for both sides: BASE's may predate the pad
        r = sh('sh %s/tools/build-native-shell.sh %s' % (ROOT, out), cwd=tree, env=dict(os.environ, NATIVE_LAYOUT_PAD=str(p)))
        if r.returncode or not os.path.exists(out):
            sys.exit('native-ab-layouts: %s pad %d not built: %s' % (tag, p, (r.stdout + r.stderr)[-300:]))
        made.append(('%s-p%d' % (tag, p), out))
    return made

wt = tempfile.mkdtemp(prefix='native-ab-base-')
r = sh('git worktree add -q --detach %s %s' % (wt, base))
if r.returncode:
    sys.exit('native-ab-layouts: no worktree for %s: %s' % (base, r.stderr.strip()))
try:
    r = sh('make -s native-kernel', cwd=wt)
    if r.returncode:
        sys.exit('native-ab-layouts: %s: no native kernel: %s' % (base, (r.stdout + r.stderr)[-300:]))
    b = shells(wt, 'base')
    n = shells(ROOT, 'now')
finally:
    sh('rm -f native-kernel && make -s native-kernel')   # the checkout's own kernel back, unpadded: make alone
                                       # would keep the last padded one, newer than its sources
    sh('git worktree remove --force %s' % wt); sh('git worktree prune')

cfg = os.path.join(out_dir, 'cfg')
open(cfg, 'w').write(''.join('%s|/tmp|%s {w}\n' % (name, path) for name, path in b + n))
res = sh('python3 tools/bench-vm.py %s %s' % (rounds, cfg), env=dict(os.environ, SCALE=os.environ.get('SCALE', '25'), WL=WL)).stdout
ratio = {b[0][0]: [1.0] * len(WL.split())}
for line in res.split('\n'):
    m = re.match(r'^(\S+)\s+(.*)$', line)
    if m and m.group(1) in dict(b + n):
        rs = [float(x) for x in re.findall(r'(\d+\.\d+)\s*\[', m.group(2))]
        if len(rs) == len(WL.split()):
            ratio[m.group(1)] = rs
missing = [name for name, _ in b + n if name not in ratio]
if missing:
    sys.exit('native-ab-layouts: no result for %s\n%s' % (missing, res[-600:]))
gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))
print('native A/B over layouts: the checkout against %s, pads %s, %s rounds (SCALE=%s)' % (base, ','.join(map(str, pads)), rounds, os.environ.get('SCALE', '25')))
print('%-11s %-22s %-22s %s' % ('workload', "base's layouts", "checkout's layouts", 'checkout / base'))
for k, w in enumerate(WL.split()):
    bs = [ratio[name][k] for name, _ in b]; ns = [ratio[name][k] for name, _ in n]
    print('%-11s %.3f-%.3f            %.3f-%.3f            %.3f' % (w, min(bs), max(bs), min(ns), max(ns), gm(ns) / gm(bs)))
