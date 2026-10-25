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
        name, default, values, where = line.split('\t')[:4]
        rows.append((name, int(default), [int(v) for v in values.split(',')], where))
    return rows
GENES_ROWS = genes_table()
GENES = [(n, d, v) for n, d, v, w in GENES_ROWS]
DEFAULT = {n: d for n, d, v in GENES}
# the genes rillc.py reads, from the table's own column - a fixed list here missed littext (750),
# and a cached compilation made under the other littext killed 15 designs as the two compilers differing
CODEGEN = tuple(n for n, d, v, w in GENES_ROWS if w in ('compilers', 'features'))
FEATURES = tuple(n for n, d, v, w in GENES_ROWS if w == 'features')

# a feature gene changes the scripts too (751): the tests, the workloads and the corpus are written
# with the feature where it is on, without it where it is off - the same rewrites rill-candidates.py
# measures, one way or the other
TRUTH_RULES = [(r'len\((\$\w+(?:\[[^\[\]]+\]|\.\w+)*)\) > 0', r'\1'), (r'len\((\$\w+(?:\[[^\[\]]+\]|\.\w+)*)\) == 0', r'not \1'),
               (r'(\$\w+(?:\[[^\[\]]+\]|\.\w+)*) != ""', r'\1'), (r'(\$\w+(?:\[[^\[\]]+\]|\.\w+)*) == ""', r'not \1')]
def written_for(text, g):
    if not g.get('warn', 1): text = re.sub(r'(?m)^(\s*)warn\b(.*)$', r'\1echo\2 out>err', text)   # a bare warn too
    if not g.get('argdefault', 1): text = re.sub(r'arg\((\d+), ', r'default(arg(\1), ', text)
    if g.get('truth', 0):
        for pat, r in TRUTH_RULES: text = re.sub(pat, r, text)
    return text
def source_for(path, g):
    """The script as this genome's features have it - a file of its own when it differs."""
    text = open(path).read(); new = written_for(text, g)
    if new == text: return os.path.abspath(path)
    d = os.path.join(OUT, 'src-' + '-'.join('%s%d' % (f, g[f]) for f in FEATURES)); os.makedirs(d, exist_ok=True)
    out = os.path.join(d, os.path.basename(path)); open(out, 'w').write(new); return out

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
    path = source_for(path, g)
    key = (path, tuple(g[k] for k in CODEGEN))
    if key not in _rillc:
        st, out = run(['python3', 'tools/rillc.py', path], env=dict(os.environ, RILL_GENES=genes_env(g)))
        _rillc[key] = (st, out)
    return _rillc[key]

def driver(path, measure):
    d = os.path.join(OUT, 'drv-%s.4' % hashlib.sha1((path + str(measure)).encode()).hexdigest()[:8])
    if measure:
        text = ('S" %s" R-SLURP R-COMPILE R-BLANKS EVALUATE\n'     # ." prints only compiled: a word for it
                ': ARENA.  ." ARENA " 134217728 R-END @ R-TOP @ - - . R-NL ;  ARENA.\n' % path)
    else:
        text = 'S" %s" .RILL\n' % path
    open(d, 'w').write(text); return d

TESTS = sorted(f for f in os.listdir('tests/rill') if f.endswith('.rill'))
WORK = sorted(f for f in os.listdir('tests/rill/search') if f.endswith('.rill'))
SEL = [w for w in WORK if w.startswith('w-')]; HELD = [w for w in WORK if w.startswith('h-')]

def evaluate(g, img, reference, engine, counts):
    rec = {'id': gid(g), 'genome': g}
    for t in TESTS:                                   # the gate: tests, as rillc.py compiles them
        needs = re.findall(r'(?m)^# needs: (\w+)', open('tests/rill/' + t).read())
        if any(not g.get(f, 1) for f in needs): continue  # a test of a feature the design has not got (752)
        st, forth = rillc('tests/rill/' + t, g)
        if st: return dict(rec, alive=False, cause='rillc.py refused %s' % t)
        prog = os.path.join(OUT, 'prog.4'); open(prog, 'w').write(forth)
        st, out = run(['./relf64', img, prog])
        if out != open('tests/rill/' + t[:-5] + '.expected').read():
            return dict(rec, alive=False, cause='%s: not the expected output' % t)
        st, own = run(['./relf64', img, driver(source_for('tests/rill/' + t, g), False)])
        if norm(own) != norm(forth):
            return dict(rec, alive=False, cause='%s: the two compilers differ' % t)
    rec['counts'], rec['arena'], gen = {}, {}, 0
    for w in WORK:                                    # the workloads: gated and counted in one run
        path = source_for('tests/rill/search/' + w, g)
        st, forth = rillc('tests/rill/search/' + w, g)
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
    for t in TESTS:   # the same programs for every design: a test that needs a feature checks, but is not counted
        if re.findall(r'(?m)^# needs: (\w+)', open('tests/rill/' + t).read()): continue
        gen += len(norm(rillc('tests/rill/' + t, g)[1]))
    st, src = run(['python3', 'tools/rill-genes.py', '--size'], env=dict(os.environ, RILL_GENES=genes_env(g)))
    rec.update(alive=True, image=os.path.getsize(img), generated=gen, source=int(src),
               scripts=sum(corpus_chars(f, g) for f in CORPUS))
    return rec
import importlib.util as _iu
_ms = _iu.spec_from_file_location('m', os.path.join(ROOT, 'tools', 'rill-measure.py')); _m = _iu.module_from_spec(_ms)
_argv = sys.argv; sys.argv = sys.argv[:1]; _ms.loader.exec_module(_m); sys.argv = _argv
CORPUS = sorted('examples/rill/' + f for f in os.listdir('examples/rill') if f.endswith('.rill'))
def corpus_chars(path, g):   # rule 3's count of a rewrite, as this genome's features let it be written
    return sum(len(l.strip()) for l in _m.code_shell(written_for(open(path).read(), g)))

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

def near(g, k):   # within k genes of the default
    return sum(1 for n in DEFAULT if g[n] != DEFAULT[n]) <= k
def search(limit):
    engine, counts = counting_engine()
    controls(engine, counts)
    db = load_db()
    designs, seen = [], set()
    for values in itertools.product(*[v for n, d, v in GENES]):
        g = expressed(dict(zip([n for n, d, v in GENES], values)))
        if PAIRS and not near(g, 2): continue            # --pairs (750): each gene alone and every pair, not the product
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
# The two size criteria weighed by volume (752, the user's): Rill's source is written once, its scripts
# keep coming - SCALE times the corpus, the user's estimate (10). Together they weigh 2, as two criteria,
# split by their share of all the characters: so a feature costing c characters of source and saving s
# of the corpus moves the score by 2 (c - SCALE s) / (S0 + SCALE C0) - characters against characters.
SCALE = float(os.environ.get('RILL_SCRIPTS_SCALE', '10'))
def size_term(r, base):
    return 2.0 * (r['source'] + SCALE * r['scripts']) / (base['source'] + SCALE * base['scripts'])
def score_of(db, r):
    base = db[gid(DEFAULT)]
    speed = gmean([r['counts'][w] / base['counts'][w] for w in SEL])
    return size_term(r, base) + speed + r['generated'] / base['generated']
def climb(limit=12):
    """From the best design known, every design one gene away; to the best of them while it improves (751)."""
    engine, counts = counting_engine()
    for step in range(limit):
        db = load_db(); alive = [r for r in db.values() if r.get('alive')]
        reference = db[gid(DEFAULT)]['outputs']
        best = min(alive, key=lambda r: score_of(db, r)); here = score_of(db, best)
        print('step %d: at %s, score %.4f' % (step, best['id'], here), flush=True)
        moves = []
        for n, d, values in GENES:
            for v in values:
                if v != best['genome'][n]:
                    g = expressed(dict(best['genome'], **{n: v}))
                    if gid(g) not in db: moves.append(g)
        for g in moves:
            img = os.path.join(OUT, 'design.img'); ok, out = build(g, img)
            rec = evaluate(g, img, reference, engine, counts) if ok else {'id': gid(g), 'genome': g, 'alive': False, 'cause': 'build'}
            with open(DB, 'a') as f: f.write(json.dumps(rec) + '\n')
        db = load_db(); alive = [r for r in db.values() if r.get('alive')]
        if min(score_of(db, r) for r in alive) >= here: print('no single change improves it'); return
def report():
    db = load_db(); alive = [r for r in db.values() if r.get('alive')]
    base = db[gid(DEFAULT)]
    for r in alive:
        r['speed'] = gmean([r['counts'][w] / base['counts'][w] for w in SEL])
        r['held'] = gmean([r['counts'][w] / base['counts'][w] for w in HELD])
        r['mem'] = sum(r['arena'].values())
    for r in alive:
        r['score'] = size_term(r, base) + r['speed'] + r['generated'] / base['generated']
    keys = ('source', 'scripts', 'speed', 'generated')   # the user's four (751): Rill's source, its scripts, speed, the Forth made
    def dominates(a, b): return all(a[k] <= b[k] for k in keys) and any(a[k] < b[k] for k in keys)
    front = sorted([r for r in alive if not any(dominates(o, r) for o in alive)], key=lambda r: r['score'])
    lines = ['# rill-search report', '', '%d designs, %d alive, %d dead; the front: %d' %
             (len(db), len(alive), len(db) - len(alive), len(front)), '',
             'source: Rill\'s Forth source as the genome has it, code characters; scripts: the corpus written',
             'as its features allow, code characters; speed and held: dispatches against the default (geometric',
             'means); generated: words of Forth over the tests and workloads; score: speed and generated',
             'against the default\'s, plus the two sizes as 2 (source + %g scripts) / the default\'s - the scripts' % SCALE,
             'counted as %g times the corpus, the user\'s estimate of the Rill to come (752)' % SCALE, '',
             '| design | score | source | scripts | speed | generated | held | image | arena | genome |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    def row(r, tag=''):
        diff = ', '.join('%s=%d' % (k, v) for k, v in sorted(r['genome'].items()) if v != DEFAULT[k]) or 'the default'
        return '| %s%s | %.3f | %d | %d | %.3f | %d | %.3f | %d | %d | %s |' % (r['id'], tag, r['score'], r['source'], r['scripts'],
            r['speed'], r['generated'], r['held'], r['image'], r['mem'], diff)
    lines += [row(r) for r in front]
    lines += ['', '## Each gene alone (a knockout: the default with one gene changed)', '',
              '| design | score | source | scripts | speed | generated | held | image | arena | genome |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|', row(base, ' (default)')]
    for r in sorted(alive, key=lambda r: r['score']):
        if sum(1 for k in DEFAULT if r['genome'][k] != DEFAULT[k]) == 1: lines.append(row(r))
    dead = [r for r in db.values() if not r.get('alive')]
    if dead: lines += ['', '## Deaths', ''] + ['- %s %s: %s' % (r['id'], genes_env(r['genome']), r['cause']) for r in dead]
    open(os.path.join(OUT, 'report.md'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

PAIRS = '--pairs' in sys.argv
if __name__ == '__main__':
    if '--report' in sys.argv: report()
    elif '--climb' in sys.argv: climb()
    else: search(int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 10 ** 9)
