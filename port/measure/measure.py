#!/usr/bin/env python3
"""port/measure/measure.py CFG WDIR EXT START-SCRIPT OUT.json - every build in CFG (mk-cfg.sh's): its size,
its output on each workload against the first build's, and its memory.
Size: the command's first word (the engine), its images (.img, .fi) and a .fi's .so beside it. Memory:
rsstrace (cc -O2 -o rsstrace rsstrace.c, beside this) on START-SCRIPT and on each workload: Rss at exit,
Anonymous at exit, VmHWM (the peak since exec), KB. WDIR holds the workloads: for relfsh, bench-vm's
five at SCALE=5 (scaled.sh writes them), for rill3 tests/cm/bench's (README.md)."""
import os, sys, json, subprocess
cfgf, wdir, ext, start, outf = sys.argv[1:6]
here = os.path.dirname(os.path.abspath(__file__))
cfg = [l.strip().split('|') for l in open(cfgf) if l.strip()]
WL = sorted(f[:-len(ext)] for f in os.listdir(wdir) if f.endswith(ext) and os.path.join(wdir, f) != os.path.abspath(start))
def argv(cmd, path):
    a = cmd.replace('{w}', path).split()
    env = dict(os.environ)
    while '=' in a[0] and not a[0].startswith('/'): k, v = a.pop(0).split('=', 1); env[k] = v
    return a, env
def run(cmd, path): a, env = argv(cmd, path); return subprocess.run(a, cwd='/tmp', capture_output=True, stdin=subprocess.DEVNULL, env=env).stdout
ref = {w: run(cfg[0][2], os.path.join(wdir, w + ext)) for w in WL}
res = {}
for name, cwd, cmd in cfg:
    a, env = argv(cmd, 'X')
    imgs = [x for x in a[1:] if x.endswith('.img') or x.endswith('.fi')]
    eng = [a[0]] + [x + '.so' for x in imgs if x.endswith('.fi') and os.path.exists(x + '.so')]
    se = sum(os.path.getsize(f) for f in eng); si = sum(os.path.getsize(f) for f in imgs)
    same = {w: run(cmd, os.path.join(wdir, w + ext)) == ref[w] for w in WL}
    mem = {}
    for w, path in [('start', start)] + [(w, os.path.join(wdir, w + ext)) for w in WL]:
        a, env = argv(cmd, path)
        r = subprocess.run([os.path.join(here, 'rsstrace'), '/dev/null'] + a, cwd='/tmp', capture_output=True, text=True, env=env).stdout.split()
        mem[w] = [int(x) for x in r[:3]] if len(r) >= 3 else [-1, -1, -1]
    res[name] = dict(engine=se, image=si, same=same, mem=mem)
    print('%-16s %9d %9d %9d  %s  start rss %5d  peak %5d anon %5d' % (name, se, si, se + si,
          ' '.join('%s:%s' % (w, 'ok' if same[w] else 'DIFF') for w in WL),
          mem['start'][0], max(m[2] for m in mem.values()), max(m[1] for m in mem.values())), flush=True)
json.dump(res, open(outf, 'w'), indent=1)
