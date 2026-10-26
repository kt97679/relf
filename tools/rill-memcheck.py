#!/usr/bin/env python3
"""tools/rill-memcheck.py [--check] - does Rill give back what it no longer needs? (Iteration 778)

Each feature runs in a top-level loop N times and 10 N times, compiled by
the image's own compiler; the peak resident memory of the two runs is
compared. Kept memory grows with the rounds - reported as bytes a round.
The collector (776) should keep every row flat; what lives outside the
arena (the C heap: regex programs, literal texts, the collector's own
blocks) is checked here too. --check: fewer rounds, and exit 1 if any
feature keeps more than LIMIT bytes a round - tests/rill/run calls it.
"""
import os, resource, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
check = '--check' in sys.argv
LIMIT = 48            # bytes a round: well above the measure's noise, far below any real leak
NOISE = 400 * 1024    # what two peaks can differ by with nothing kept: fewer rounds, a larger limit a round

W = [   # name, body (inside: for i in range(N) { ... }), N
    ('texts',      't = "item {$i} of many"; u = trim(" $t "); v = replace($u, "item", "x")', 3000),
    ('lists',      'l = [$i, "two", 3]; push($l, $i); m = slice($l, 1, 3); n = len($m)', 3000),
    ('records',    'r = {a: $i, b: "x"}; r[c] = $i; k = keys($r); h = $r[a]', 3000),
    ('big-record', 'q = {}; for j in range(20) { q["k{$j}"] = $j }; z = $q[k7]', 3000),
    ('words',      'w = words("alpha beta gamma {$i}"); s = join($w, "-")', 3000),
    ('split',      'p = split("a,b,c,{$i}", ","); f = $p[3]', 3000),
    ('regex',      'g = match("abc{$i}def", "c([0-9]+)d"); h = all("x1y22z", "[0-9]+")', 3000),
    ('regex-new',  'g = match("abc", "b{$i}")', 300),       # a new pattern each round: past the cache
    ('sub',        's = sub("a-b-c {$i}", "-", "+")', 3000),
    ('decimals',   'd = 0.5; d = $d + $i * 0.25; e = $d * 2.0', 3000),
    ('sort',       'o = sort([3, 1, 2, $i])', 3000),
    ('comprehend', 'c = [$x * 2 for x in [1, 2, 3, $i] if $x > 1]', 3000),
    ('def-call',   'y = twice($i)', 3000),
    ('capture',    'o = $(echo {$i})', 200),               # forks
]
PRE = 'def twice(x) -> number { t = $x * 2; return $t }\n'

def peak_kb(prog, n):
    probe = ('import resource, subprocess, sys\n'
             'p = subprocess.run(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=240)\n'
             'print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss, p.returncode, repr(p.stdout[-60:]))')
    src = open(prog).read().replace('NROUNDS', str(n))
    one = prog + '.%d.rill' % n
    open(one, 'w').write(src)
    r = subprocess.run([sys.executable, '-c', probe, './relf64', os.environ.get('RILL_IMG', 'kernel64-rill.img'), one], capture_output=True, text=True,
                       env=dict(os.environ, RILL_GC_STRESS='1'))   # collections every 64 KB: the arena stays small,
                                                                    # so what grows is kept for good, not yet collected
    kb, st, out = r.stdout.strip().split(' ', 2)
    return int(kb), int(st), out

work = tempfile.mkdtemp(prefix='rill-mem-')
bad = 0
for name, body, n in W:
    if check: n = max(n // 3, 100)
    prog = os.path.join(work, name)
    open(prog, 'w').write(PRE + 'for i in range(NROUNDS) { %s }\necho done\n' % body)
    a, sa, oa = peak_kb(prog, n)
    b, sb, ob = peak_kb(prog, 10 * n)
    if sa or sb or 'done' not in ob:
        print('%-11s fails: %s' % (name, (ob if sb else oa)[:60])); bad += 1; continue
    per = (b - a) * 1024.0 / (9 * n)
    limit = max(LIMIT, NOISE / (9.0 * n))
    flag = '  KEPT' if per > limit else ''
    bad += per > limit
    print('%-11s %6d -> %6d KB  %7.0f B/round%s' % (name, a, b, per, flag))
if check:
    print('rill-memcheck: %d of %d features keep memory' % (bad, len(W)))
    sys.exit(1 if bad else 0)
