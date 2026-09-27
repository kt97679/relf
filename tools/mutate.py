#!/usr/bin/env python3
"""tools/mutate.py [N] [SEED] - mutation testing on the compiled shell.

Does the test corpus notice when the shell is wrong? One opcode in the
shell image is swapped for another of the same size and stack effect -
+ for -, AND for OR, < for >, C@ for @, 1+ for 1-, 0= for 0< - the image
is embedded in the C engine as a shell of its own, and the differential
suite's 131 scripts are run through it. A mutant that changes any
script's stdout or status is killed; one that changes none survives, and
marks behaviour that corpus does not check - the word it lives in is
named. N mutants (default 40), in shell.4 and tree.4, the code scripts
reach (edit.4 is reached only interactively). Mutating threaded code
needs no recompiling: one byte, and the decoder's boundaries stay put.
TESTING-IDEAS.md 7; written in Iteration 558.
"""
import contextlib, io, os, random, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 558)
IMG, ENGINE = 'kernel64-shell.img', './relf64'
KEEP = os.environ.get('MUTANTS_KEEP')   # a directory: the survivors' shells are saved there
CASES = os.path.join(ROOT, 'tests', 'diff', 'cases')

# one-byte opcodes, from the map's one source
op = {}
for line in open('engine/opcodes.tab'):
    f = line.split()
    if len(f) >= 3 and f[0] in ('direct', 'tiny'):
        op[f[2]] = int(f[1], 16)
PAIRS = [('+', '-'), ('AND', 'OR'), ('OR', 'XOR'), ('XOR', 'AND'), ('<', '>'), ('U<', '<'),
         ('0=', '0<'), ('1+', '1-'), ('C@', '@'), ('C!', '!')]
SWAP = {}
for a, b in PAIRS:
    if a in op and b in op:
        SWAP.setdefault(op[a], []).append((b, op[b])); SWAP.setdefault(op[b], []).append((a, op[a]))
NAME = {v: k for k, v in op.items()}

# instruction starts per word, as tools/coverage.py gets them
audit = open('tools/image-audit.py').read()
for old, new in [("    ip = xt; far_target = xt\n    while ip < end:\n        op = img[ip]",
                  "    ip = xt; far_target = xt\n    STARTS[name] = []\n    while ip < end:\n        STARTS[name].append(ip)\n        op = img[ip]"),
                 ("CALLS=[]; SLOTS=[];", "CALLS=[]; SLOTS=[]; STARTS={};")]:
    assert audit.count(old) == 1, 'image-audit.py changed: ' + old[:40]
    audit = audit.replace(old, new)
g = {'__file__': os.path.join(ROOT, 'tools', 'image-audit.py')}
sys.argv = ['image-audit', IMG, '8']
with contextlib.redirect_stdout(io.StringIO()):
    exec(audit, g)
img = g['img']
raw = open(IMG, 'rb').read()
HDR = len(raw) - len(img)                  # the file's header, before offset 0
shellwords = {m.group(1) for src in ('shell/shell.4', 'shell/tree.4')
              for m in re.finditer(r'(?m)^: (\S+)', open(src).read())}
sites = [(name, ip) for name, starts in g['STARTS'].items() if name in shellwords
         for ip in starts if img[ip] in SWAP]
print('%d mutation sites in shell.4 and tree.4 (header %d bytes)' % (len(sites), HDR))

def shell_of(image, work, tag):
    p = os.path.join(work, 'img-' + tag); open(p, 'wb').write(image)
    out = os.path.join(work, 'sh-' + tag)
    subprocess.run(['sh', 'tools/embed.sh', ENGINE, p, out], check=True, capture_output=True)
    return out

def run_all(shell, work, stop_at=None):
    res = {}
    for name in sorted(os.listdir(CASES)):
        if not name.endswith('.sh'):
            continue
        with tempfile.TemporaryDirectory() as d:
            try:
                r = subprocess.run([shell, os.path.join(CASES, name)], cwd=d, stdin=subprocess.DEVNULL,
                                   capture_output=True, timeout=10)
                res[name] = (r.stdout, r.returncode)
            except subprocess.TimeoutExpired:
                res[name] = (b'<timeout>', -1)
        if stop_at is not None and res[name] != stop_at.get(name):
            return res, name
    return res, None

with tempfile.TemporaryDirectory() as work:
    base, _ = run_all(shell_of(raw, work, 'base'), work)
    killed, survived = 0, []
    for k, (word, ip) in enumerate(rng.sample(sites, min(N, len(sites)))):
        new_name, new_op = rng.choice(SWAP[img[ip]])
        m = bytearray(raw); m[HDR + ip] = new_op
        _, by = run_all(shell_of(bytes(m), work, str(k)), work, stop_at=base)
        if by:
            killed += 1
        else:
            survived.append((word, NAME[img[ip]], new_name))
            if KEEP:                           # for a second, fuller trial
                import shutil
                os.makedirs(KEEP, exist_ok=True)
                shutil.copy(os.path.join(work, 'sh-' + str(k)),
                            os.path.join(KEEP, '%02d-%s-%s-to-%s' % (k, word, NAME[img[ip]], new_name)))
    total = killed + len(survived)
    print('%d mutants: %d killed by the corpus, %d survived (%d%% killed)'
          % (total, killed, len(survived), 100 * killed // max(total, 1)))
    for word, a, b in survived:
        print('  survived: %-28s %s -> %s' % (word, a, b))
