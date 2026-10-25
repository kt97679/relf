#!/usr/bin/env python3
"""tools/rill-search.py [--report] [--limit N] - every design of Rill's genome, gated and counted (Iteration 749).

docs/RILL-SEARCH.md's first experiment, on forth-vm-evolution's pattern (its lab/evolve):

  genome   rill/genes.tsv: every combination of every gene's values, a design once
           for each expressed genome (dupnip says nothing without purestack)
  build    RILL_GENES=... tools/build-rill-image.sh, the image apart for each design;
           tools/rillc.py reads the same genome
  life     the gate, every test program in tests/rill: compiled by rillc.py, run in
           the design's image, its output the expected one; compiled by the image's
           own compiler, the Forth word for word rillc.py's; every workload's output
           the default design's. Anything else dies, its cause kept.
  counts   CV8's dispatches, from a counting engine (tools/profile.py's patch of
           engine/cv8.c) - deterministic, so no pairing and no winner's curse in the
           search: each workload in tests/rill/search compiled and run by the image,
           end to end, counted in the same run whose output the gate checks
  fitness  kept apart, as a Pareto front: speed (the geometric mean over the w-
           workloads of dispatches against the default's), the image's bytes, the
           generated Forth's words over the tests and workloads, the arena's peak
           summed over the workloads. h- workloads are held out: reported, never
           selected on.

Before any design, two negative controls must die (the lab's rule 1): an image built
with a gene the Python compiler does not see (short=0 against short=1), and an image
whose R-PUSH drops every item. build/rill-search/db.jsonl keeps every design; one
already there is not measured again. --report writes build/rill-search/report.md.
"""
import array, hashlib, itertools, json, math, os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); os.chdir(ROOT)
OUT = os.path.join(ROOT, 'build', 'rill-search'); os.makedirs(OUT, exist_ok=True)
DB = os.path.join(OUT, 'db.jsonl')
SLOTS = 1 << 18

def genes_table():
    rows = []
    for line in open('rill/genes.tsv'):
        if line.startswith('#') or not line.strip(): continue
        name, default, values = line.split('\t')[:3]
        rows.append((name, int(default), [int(v) for v in values.split(',')]))
    return rows
GENES = genes_table()
DEFAULT = {n: d for n, d, v in GENES}
CODEGEN = ('short', 'purestack', 'dupnip', 'rangeloop')

def expressed(g):
    g = dict(g)
    if not g['purestack']: g['dupnip'] = DEFAULT['dupnip']      # nothing to take out
    return g
def gid(g): return hashlib.sha1(json.dumps(sorted(g.items())).encode()).hexdigest()[:10]
def genes_env(g): return ','.join('%s=%d' % kv for kv in sorted(g.items()))

def counting_engine():
    engine, counts = os.path.join(OUT, 'relf-count'), os.path.join(OUT, 'counts.bin')
    if not os.path.exists(engine):
        src = open('engine/cv8.c').read()
        old = '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP'
        assert src.count(old) == 1
        src = src.replace(old, '#include <sys/mman.h>\nstatic unsigned int *prof_map;\nstatic UNS64 prof_base;\n'
                          '#define PROF(k)\n#define PROFIP(a) (prof_map[((a) - prof_base) & 0x3FFFF]++)\n#define PROFDUMP')
        old = '    NEXT();\ndo_call:'
        assert src.count(old) == 1
        src = src.replace(old, '    prof_base = cbase;\n    { int fd = open("%s", O_RDWR);\n      prof_map = mmap(0, %d * sizeof(unsigned int),\n'
                          '                      PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n      close(fd); }\n    NEXT();\ndo_call:' % (counts, SLOTS))
        open(os.path.join(OUT, 'count.c'), 'w').write(src)
        subprocess.run(['cc', '-O2', '-I', 'engine', '-o', engine, os.path.join(OUT, 'count.c')], check=True)
    return engine, counts

def run(cmd, env=None, timeout=120):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env,
                       stdin=subprocess.DEVNULL, timeout=timeout)       # one stream, as tests/rill/run reads it
    return r.returncode, r.stdout

def build(g, img, root=ROOT):
    env = dict(os.environ, RILL_GENES=genes_env(g))
    st, out = run(['sh', 'tools/build-rill-image.sh', './relf64', 'forth/kernel64.img', img], env=dict(env), timeout=300) \
        if root == ROOT else run(['sh', os.path.join(root, 'tools/build-rill-image.sh'), os.path.join(ROOT, 'relf64'),
                                  os.path.join(ROOT, 'forth/kernel64.img'), img], env=env, timeout=300)
    return st == 0, out

def norm(text): return [w for w in text.split() if w]
_rillc = {}
def rillc(path, g):
    key = (path, tuple(g[k] for k in CODEGEN))
    if key not in _rillc:
        st, out = run(['python3', 'tools/rillc.py', path], env=dict(os.environ, RILL_GENES=genes_env(g)))
        _rillc[key] = (st, out)
    return _rillc[key]

def driver(path, measure):
    d = os.path.join(OUT, 'drv-%s.4' % hashlib.sha1((path + str(measure)).encode()).hexdigest()[:8])
    if measure:
        text = ('S" %s" R-SLURP R-COMPILE R-BLANKS EVALUATE\n'     # ." prints only compiled: a word for it
                ': ARENA.  ." ARENA " 16777216 R-END @ R-TOP @ - - . R-NL ;  ARENA.\n' % path)
    else:
        text = 'S" %s" .RILL\n' % path
    open(d, 'w').write(text); return d

TESTS = sorted(f for f in os.listdir('tests/rill') if f.endswith('.rill'))
WORK = sorted(f for f in os.listdir('tests/rill/search') if f.endswith('.rill'))
SEL = [w for w in WORK if w.startswith('w-')]; HELD = [w for w in WORK if w.startswith('h-')]

def evaluate(g, img, reference, engine, counts):
    rec = {'id': gid(g), 'genome': g}
    for t in TESTS:                                   # the gate: tests, as rillc.py compiles them
        st, forth = rillc('tests/rill/' + t, g)
        if st: return dict(rec, alive=False, cause='rillc.py refused %s' % t)
        prog = os.path.join(OUT, 'prog.4'); open(prog, 'w').write(forth)
        st, out = run(['./relf64', img, prog])
        if out != open('tests/rill/' + t[:-5] + '.expected').read():
            return dict(rec, alive=False, cause='%s: not the expected output' % t)
        st, own = run(['./relf64', img, driver(os.path.abspath('tests/rill/' + t), False)])
        if norm(own) != norm(forth):
            return dict(rec, alive=False, cause='%s: the two compilers differ' % t)
    rec['counts'], rec['arena'], gen = {}, {}, 0
    for w in WORK:                                    # the workloads: gated and counted in one run
        path = os.path.abspath('tests/rill/search/' + w)
        st, forth = rillc(path, g)
        if st: return dict(rec, alive=False, cause='rillc.py refused %s' % w)
        gen += len(norm(forth))
        open(counts, 'wb').write(bytes(SLOTS * 4))
        st, out = run([engine, img, driver(path, True)], timeout=600)
        m = re.search(r'ARENA (\d+)', out)
        body = re.sub(r'ARENA \d+ *\n', '', out)
        if not m or (reference is not None and body != reference[w]):
            return dict(rec, alive=False, cause='%s: not the default design\'s output' % w)
        c = array.array('I'); c.frombytes(open(counts, 'rb').read())
        rec['counts'][w], rec['arena'][w] = sum(c), int(m.group(1))
        rec.setdefault('outputs', {})[w] = body
    for t in TESTS: gen += len(norm(rillc('tests/rill/' + t, g)[1]))
    rec.update(alive=True, image=os.path.getsize(img), generated=gen)
    return rec

def controls(engine, counts):
    """Both must die, or the gate checks nothing."""
    img = os.path.join(OUT, 'control.img')
    ok, out = build(dict(DEFAULT, short=0), img)                # an image the Python compiler does not match
    r = evaluate(dict(DEFAULT), img, None, engine, counts) if ok else {'alive': False}
    a = r['alive']
    tree = tempfile.mkdtemp(prefix='rill-broken-')               # an R-PUSH that drops its item
    for d in ('rill', 'tools'): shutil.copytree(d, os.path.join(tree, d))
    p = os.path.join(tree, 'rill', 'rt.4'); t = open(p).read()
    t = t.replace(': R-PUSH ( box l --- )   DUP R-GROW', ': R-PUSH ( box l --- )   2DROP EXIT DUP R-GROW')
    open(p, 'w').write(t)
    st, out = run(['sh', '-c', 'cd %s && ln -s %s/forth forth && sh tools/build-rill-image.sh %s/relf64 forth/kernel64.img %s'
                   % (tree, ROOT, ROOT, img)], timeout=300)
    r2 = evaluate(dict(DEFAULT), img, None, engine, counts) if st == 0 else {'alive': True, 'cause': 'not built'}
    b = r2['alive']
    shutil.rmtree(tree)
    print('negative controls: compilers out of step %s; R-PUSH broken %s'
          % ('caught (%s)' % r.get('cause') if not a else 'NOT CAUGHT', 'caught (%s)' % r2.get('cause') if not b else 'NOT CAUGHT'))
    if a or b: sys.exit('rill-search: BROKEN - a negative control lived')

def load_db():
    db = {}
    if os.path.exists(DB):
        for line in open(DB): r = json.loads(line); db[r['id']] = r
    return db

def search(limit):
    engine, counts = counting_engine()
    controls(engine, counts)
    db = load_db()
    designs, seen = [], set()
    for values in itertools.product(*[v for n, d, v in GENES]):
        g = expressed(dict(zip([n for n, d, v in GENES], values)))
        if gid(g) not in seen: seen.add(gid(g)); designs.append(g)
    designs.sort(key=lambda g: g != DEFAULT)                    # the default first: its outputs are the reference
    reference = None
    for k, g in enumerate(designs[:limit]):
        if gid(g) in db and db[gid(g)].get('alive'):
            if g == DEFAULT: reference = db[gid(g)]['outputs']
            continue
        img = os.path.join(OUT, 'design.img')
        ok, out = build(g, img)
        rec = evaluate(g, img, reference, engine, counts) if ok else {'id': gid(g), 'genome': g, 'alive': False, 'cause': 'build: ' + out[-200:]}
        if g == DEFAULT:
            if not rec['alive']: sys.exit('rill-search: the default design dies: %s' % rec['cause'])
            reference = rec['outputs']
        with open(DB, 'a') as f: f.write(json.dumps(rec) + '\n')
        print('%3d/%d %s %s %s' % (k + 1, len(designs), rec['id'], 'alive' if rec['alive'] else 'DEAD ' + rec['cause'], genes_env(g)), flush=True)

def gmean(xs): return math.exp(sum(math.log(x) for x in xs) / len(xs))
def report():
    db = load_db(); alive = [r for r in db.values() if r.get('alive')]
    base = db[gid(DEFAULT)]
    for r in alive:
        r['speed'] = gmean([r['counts'][w] / base['counts'][w] for w in SEL])
        r['held'] = gmean([r['counts'][w] / base['counts'][w] for w in HELD])
        r['mem'] = sum(r['arena'].values())
    keys = ('speed', 'image', 'generated', 'mem')
    def dominates(a, b): return all(a[k] <= b[k] for k in keys) and any(a[k] < b[k] for k in keys)
    front = sorted([r for r in alive if not any(dominates(o, r) for o in alive)], key=lambda r: r['speed'])
    lines = ['# rill-search report', '', '%d designs, %d alive, %d dead; the front: %d' %
             (len(db), len(alive), len(db) - len(alive), len(front)), '',
             'speed and held: dispatches against the default design (geometric means); image in bytes;',
             'generated: words of Forth over the tests and workloads; arena: bytes, summed over the workloads', '',
             '| design | speed | held | image | generated | arena | genome |', '|---|---:|---:|---:|---:|---:|---|']
    def row(r, tag=''):
        diff = ', '.join('%s=%d' % (k, v) for k, v in sorted(r['genome'].items()) if v != DEFAULT[k]) or 'the default'
        return '| %s%s | %.3f | %.3f | %d | %d | %d | %s |' % (r['id'], tag, r['speed'], r['held'], r['image'], r['generated'], r['mem'], diff)
    lines += [row(r) for r in front]
    lines += ['', '## Each gene alone (a knockout: the default with one gene changed)', '',
              '| design | speed | held | image | generated | arena | genome |', '|---|---:|---:|---:|---:|---:|---|', row(base, ' (default)')]
    for r in sorted(alive, key=lambda r: r['speed']):
        if sum(1 for k in DEFAULT if r['genome'][k] != DEFAULT[k]) == 1: lines.append(row(r))
    dead = [r for r in db.values() if not r.get('alive')]
    if dead: lines += ['', '## Deaths', ''] + ['- %s %s: %s' % (r['id'], genes_env(r['genome']), r['cause']) for r in dead]
    open(os.path.join(OUT, 'report.md'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

if __name__ == '__main__':
    if '--report' in sys.argv: report()
    else: search(int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 10 ** 9)
