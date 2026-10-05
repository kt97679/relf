#!/usr/bin/env python3
"""tools/cv8-ledger.py BASE [ROUNDS] - what a change to CV8 gained and cost,
against the revision BASE, for docs/CV8-LEDGER.md (Iteration 679).

Builds BASE in a scratch worktree, then measures the checkout's build
against it, interleaved, on this machine:
  - the shell: tools/bench-vm.py's five workloads, SCALE=5, the asm
    engine's shell and the C engine's, each against BASE's (ratios: under
    1 is faster);
  - the engine: bench/langs/bench.4's seven kernels on each engine with
    its kernel image, best of 3 per round, BASE's and this one's
    alternated, and their geometric mean;
  - the cost: the engines', the shells' and the images' bytes;
  - the baseline: the asm engine's shell against the native shell
    (relfsh-native), as times the native's - how far CV8 is from relf's
    fastest.
Prints a Markdown block for the ledger. From the repository's top, after
`make all relfasm64 relfshasm64 relfsh-native`.
"""
import math, os, re, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
base = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
rounds = sys.argv[2] if len(sys.argv) > 2 else '7'
WL = 'loop fn str arith realistic'
TESTS = ['fib', 'loop', 'sieve', 'bubble', 'matrix', 'fannkuch', 'collatz']
FWORD = {'fib': '32 FIB', 'loop': '30000000 LOOPSUM'}   # bench/langs/run.py's

def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)

wt = tempfile.mkdtemp(prefix='cv8-ledger-')
r = sh('git worktree add -q --detach %s %s' % (wt, base))
if r.returncode:
    sys.exit('cv8-ledger: no worktree for %s: %s' % (base, r.stderr.strip()))
try:
    r = sh('make -s all relfasm64 relfshasm64 relfsh-native', cwd=wt)
    if r.returncode:
        sys.exit('cv8-ledger: %s did not build: %s' % (base, (r.stdout + r.stderr).strip()[-300:]))

    def benchvm(cfg, scale):
        p = tempfile.mktemp(prefix='cv8-ledger-cfg-')
        open(p, 'w').write(cfg)
        out = sh('python3 tools/bench-vm.py %s %s' % (rounds, p), env=dict(os.environ, SCALE=str(scale), WL=WL)).stdout
        os.unlink(p)
        rows = [l for l in out.splitlines() if l.strip()]
        return rows[-1].split(None, 1)[1] if rows else '(no result)'

    shell_asm = benchvm('base|/tmp|%s/relfshasm64 {w}\nnow|/tmp|%s/relfshasm64 {w}\n' % (wt, ROOT), 5)
    shell_c = benchvm('base|/tmp|%s/relfsh64 {w}\nnow|/tmp|%s/relfsh64 {w}\n' % (wt, ROOT), 5)
    vs_native = benchvm('native|/tmp|%s/relfsh-native {w}\nasm|/tmp|%s/relfshasm64 {w}\n' % (ROOT, ROOT), 5)

    def langs(engine, image, wd):
        best = {}
        for t in TESTS:
            stdin = 'S" bench.4" INCLUDED %s . BYE\n' % FWORD.get(t, t.upper())
            ts = []
            for _ in range(3):
                t0 = time.perf_counter()
                subprocess.run([engine, image], input=stdin, capture_output=True, text=True, cwd=wd, timeout=300)
                ts.append(time.perf_counter() - t0)
            best[t] = min(ts)
        return best
    lang = {}
    for name, eng, img in [('asm', 'relfasm64', 'forth/kernel64.img'), ('C', 'relf64', 'forth/kernel64.img')]:
        b, n = {t: 9e9 for t in TESTS}, {t: 9e9 for t in TESTS}
        for _ in range(int(rounds) // 2 + 1):          # alternated, best of each side
            for t, v in langs(os.path.join(wt, eng), os.path.join(wt, img), os.path.join(ROOT, 'bench/langs')).items(): b[t] = min(b[t], v)
            for t, v in langs(os.path.join(ROOT, eng), os.path.join(ROOT, img), os.path.join(ROOT, 'bench/langs')).items(): n[t] = min(n[t], v)
        ratios = [n[t] / b[t] for t in TESTS]
        lang[name] = (ratios, math.exp(sum(math.log(x) for x in ratios) / len(ratios)))

    def size(d, f):
        p = os.path.join(d, f)
        return os.path.getsize(p) if os.path.exists(p) else 0
    files = ['relfasm64', 'relf64', 'relfshasm64', 'relfsh64', 'forth/kernel64.img', 'kernel64-shell.img']
    head = sh('git log -1 --format=%h').stdout.strip()
    based = sh('git log -1 --format=%h ' + base).stdout.strip()
    dirty = ' (and uncommitted changes)' if sh('git status --porcelain --untracked-files=no').stdout.strip() else ''
    print('Measured on %s, %s%s against %s, %s rounds:' % (os.uname().nodename, head, dirty, based, rounds))
    print()
    print('| shell, SCALE=5 | loop | fn | str | arith | realistic |')
    print('|---|---:|---:|---:|---:|---:|')
    for name, row in [('asm engine, against base', shell_asm), ('C engine, against base', shell_c), ('asm engine, times native', vs_native)]:
        cells = re.findall(r'(\d+\.\d+)\s*\[', row)
        print('| %s | %s |' % (name, ' | '.join(cells) if len(cells) == 5 else row))
    print()
    print('| engine, bench.4 | ' + ' | '.join(TESTS) + ' | geomean |')
    print('|---|' + '---:|' * (len(TESTS) + 1))
    for name, (ratios, g) in lang.items():
        print('| %s engine, against base | %s | %.3f |' % (name, ' | '.join('%.3f' % x for x in ratios), g))
    print()
    print('| bytes | ' + ' | '.join(files) + ' |')
    print('|---|' + '---:|' * len(files))
    print('| base | ' + ' | '.join(str(size(wt, f)) for f in files) + ' |')
    print('| now | ' + ' | '.join(str(size(ROOT, f)) for f in files) + ' |')
    print('| change | ' + ' | '.join('%+d' % (size(ROOT, f) - size(wt, f)) for f in files) + ' |')
finally:
    sh('git worktree remove --force %s' % wt)
    sh('git worktree prune')
