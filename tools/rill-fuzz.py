#!/usr/bin/env python3
"""tools/rill-fuzz.py [--seconds N] [--out DIR] [--seed S] - look for Rill's crashes and disagreements.

Mutates Rill programs - tests/rill's, its error programs, examples/rill's
rewrites - token by token (deleted, doubled, swapped, replaced by an edge
value, a construct or another program's token), and gives every mutant to
both compilers: tools/rillc.py and the image's own (.RILL). A mutant whose
Forth starts no process and writes no file - no PL-BEGIN, R-WRITE, R-CD,
R-SETENV - is also run, in an empty scratch directory; a mutant that could
run a command (a mutated `rm -rf $t`) never is. It reports:

  CRASH   rillc.py raised (a Traceback), or the engine said so - a fault,
          a stack guard, `rill: error -N` with no Rill message - while
          compiling or running;
  HANG    a compiler did not finish (a run that loops is the program's own);
  DIFFER  one compiler took the mutant and the other refused it, or both
          took it and their Forth differs (blanks aside, as tests/rill/oracle).

Each finding is shrunk by deleting lines, then tokens, while it keeps its
class, and written to --out. Written at Iteration 816, after 805-815 found
two crashes, three refusals and several wrong results by accident.
"""
import os, random, re, subprocess, sys, tempfile, time, glob, hashlib, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE, IMAGE = os.path.join(ROOT, 'relf64'), os.path.join(ROOT, 'kernel64-rill.img')
RILLC = os.path.join(ROOT, 'tools', 'rillc.py')
spec = importlib.util.spec_from_file_location('rillc', RILLC); rillc = importlib.util.module_from_spec(spec)
sys.argv, _argv = ['rillc'], sys.argv
try: spec.loader.exec_module(rillc)
except SystemExit: pass
sys.argv = _argv

ENGINE_SAID = re.compile(r'^relf: |rill: error -\d|Segmentation|core dumped|Aborted|Undefined word|Not found', re.M)
UNSAFE = re.compile(r'\b(PL-BEGIN|R-WRITE|R-CD|R-SETENV|R-CWD-PUSH)\b')
EDGE = ['0', '1', '-1', '2', '9223372036854775807', '-9223372036854775808', '9223372036854775808', '0.5',
        '-0.000001', '9223372036854.775807', '""', "''", '"x"', '[]', '{}', '[1, 2]', '{a: 1}', '[[1], [2]]',
        '$x', '$args', '@args', '$script', '(', ')', '[', ']', '{', '}', ',', ':', ';', '\n', '+', '-', '*',
        '/', '%', '==', '!=', '<', '>=', 'and', 'or', 'not', 'in', 'if', 'else', 'while', 'for', 'return',
        'break', 'continue', 'def', 'echo', 'exit', 'case', '??', '|', 'out>', 'err>', '$(', '"{', '}"', '"$',
        'true', 'false', 'len(', 'range(', 'sum(', 'push(', 'pop(', 'json(', 'from-json(', 'decimal(',
        'number(', 'spawn((', 'wait(', 'code((', 'x =', 'x[0] =', '[$x for x in', 'on EXIT', '\\']

def corpus():
    files = sorted(glob.glob(os.path.join(ROOT, 'tests/rill/*.rill')) + glob.glob(os.path.join(ROOT, 'tests/rill/errors/*.rill'))
                   + glob.glob(os.path.join(ROOT, 'examples/rill/*.rill')))
    return [open(f, encoding='utf-8').read() for f in files]

def spans(src):
    try: return [(t[3], t[4], t[1]) for t in rillc.tokenize(src) if t[0] != 'eof']
    except Exception: return []

def mutate(src, pool, rnd):
    ts = spans(src)
    if not ts: return src
    for _ in range(rnd.choice((1, 1, 1, 2, 3))):
        ts = spans(src) or ts
        a, b, v = ts[rnd.randrange(len(ts))]
        op = rnd.randrange(6)
        if op == 0: src = src[:a] + src[b:]                                   # deleted
        elif op == 1: src = src[:b] + ' ' + v + src[b:]                         # doubled
        elif op == 2: src = src[:a] + rnd.choice(EDGE) + src[b:]                # an edge value or a construct
        elif op == 3: src = src[:a] + rnd.choice(EDGE) + ' ' + src[a:]          # ... put before it
        elif op == 4:                                                           # another program's token
            o = spans(rnd.choice(pool))
            if o: src = src[:a] + rnd.choice(o)[2] + src[b:]
        else:                                                                   # swapped with the next
            i = ts.index((a, b, v))
            if i + 1 < len(ts):
                c, d, w = ts[i + 1]; src = src[:a] + w + src[b:c] + v + src[d:]
    return src

def run(argv, cwd, limit):
    try:
        p = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, timeout=limit)
        return p.returncode, (p.stdout + p.stderr).decode('utf-8', 'replace')
    except subprocess.TimeoutExpired:
        return None, ''

def norm(forth): return ' '.join(forth.split())

def verdict(src, tmp):
    """(class, detail) or None: what the two compilers, and a safe run, make of src."""
    path = os.path.join(tmp, 'm.rill'); open(path, 'w', encoding='utf-8').write(src)
    st, py = run([sys.executable, RILLC, path], tmp, 10)
    if st is None: return 'HANG', 'rillc.py'
    if 'Traceback' in py: return 'CRASH', 'rillc.py: ' + py.strip().splitlines()[-1][:120]
    drv = os.path.join(tmp, 'drv.4'); open(drv, 'w').write('S" %s" .RILL\n' % path)
    st2, im = run([ENGINE, IMAGE, drv], tmp, 10)
    if st2 is None: return 'HANG', 'the image compiler'
    if ENGINE_SAID.search(im): return 'CRASH', 'image compiler: ' + ENGINE_SAID.search(im).group(0) + ' ' + im.strip()[-80:]
    py_ok, im_ok = not py.startswith('rillc:'), 'rillc:' not in im
    if py_ok != im_ok: return 'DIFFER', 'rillc.py %s, the image %s' % ('took it' if py_ok else 'refused it', 'took it' if im_ok else 'refused it')
    if not py_ok: return None
    if norm(py) != norm(im): return 'DIFFER', 'both took it; their Forth differs'
    if UNSAFE.search(py): return None
    work = tempfile.mkdtemp(dir=tmp)
    st3, out = run([ENGINE, IMAGE, path], work, 5)
    if st3 is not None and (ENGINE_SAID.search(out) or (st3 < 0 and st3 not in (-15, -2))):
        return 'CRASH', 'run: ' + (ENGINE_SAID.search(out).group(0) if ENGINE_SAID.search(out) else 'signal %d' % -st3) + ' ' + out.strip()[-80:]
    return None

def shrink(src, want, tmp):
    def same(s): v = verdict(s, tmp); return v is not None and v[0] == want
    lines = src.split('\n'); i = 0
    while i < len(lines):
        t = lines[:i] + lines[i + 1:]
        if t and same('\n'.join(t)): lines = t
        else: i += 1
    src = '\n'.join(lines); i = 0
    while True:
        ts = spans(src)
        if i >= len(ts): return src
        a, b, _ = ts[i]; t = src[:a] + src[b:]
        if same(t): src = t
        else: i += 1

def main():
    secs, out, seed = 60, '/tmp/rill-fuzz', int(time.time())
    a = sys.argv[1:]
    while a:
        k = a.pop(0)
        if k == '--seconds': secs = int(a.pop(0))
        elif k == '--out': out = a.pop(0)
        elif k == '--seed': seed = int(a.pop(0))
        else: sys.exit(__doc__)
    os.makedirs(out, exist_ok=True); rnd = random.Random(seed); pool = corpus()
    tmp = tempfile.mkdtemp(prefix='rill-fuzz.'); end = time.time() + secs; n = 0; seen = {}
    while time.time() < end:
        src = mutate(rnd.choice(pool), pool, rnd); n += 1
        v = verdict(src, tmp)
        if not v: continue
        key = (v[0], re.sub(r'\d+', 'N', v[1])[:60])
        if key in seen: seen[key] += 1; continue
        small = shrink(src, v[0], tmp); seen[key] = 1
        name = os.path.join(out, '%s-%s.rill' % (v[0].lower(), hashlib.sha1(small.encode()).hexdigest()[:8]))
        open(name, 'w', encoding='utf-8').write(small)
        print('%-6s %s\n       %s' % (v[0], v[1], name)); sys.stdout.flush()
    print('seed %d: %d mutants in %d s; %d findings: %s' % (seed, n, secs, len(seen),
          ', '.join('%s %d' % (c, sum(1 for k in seen if k[0] == c)) for c in ('CRASH', 'HANG', 'DIFFER'))))
    sys.exit(1 if seen else 0)

if __name__ == '__main__':
    main()
