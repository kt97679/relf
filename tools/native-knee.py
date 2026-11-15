#!/usr/bin/env python3
"""tools/native-knee.py [OUT] - which words a hybrid image should make native, and what they would cost.

Iteration 950, hybrid-native's first step (NATIVE.md 18): price the knee before building anything.
A hybrid image is CV8 bytecode with some words' bodies native code, run by the assembly engine
(QUESTIONS.md A40). A word made native saves most of its own dispatches' time and costs its native
bytes; every call that crosses between a native word and a CV8 one costs a crossing. This counts,
over tools/pair-corpus.py's four families each weighed alike (forth, system, rill3, shell - the
owner's condition that the Forth underneath stays generic), for every word of each image:
  self     the dispatches of its own body (a call's dispatch is the caller's, its EXIT the callee's)
  edges    every call executed, caller word -> callee word: direct calls, EXECUTE (DEFER and CATCH
           go through it) and DOES> tails, recorded by the counting engine as (return address,
           target) pairs - so a native set's crossings are counted, not guessed
  bytes    its CV8 body's bytes, and its native code's bytes in the native build of the same
           sources (relfsh-native for the shell's image, rill3-native for rill3's, native-kernel for
           the kernel and the Forth programs); a word no native build has (a Forth program's own) is
           estimated at the median native/CV8 ratio of the words that have both
Code compiled after an image loads - a CORE test's definitions, a rill3 script - is "(run-time)":
counted, never native (a hybrid made ahead of time cannot reach it), its calls into native words
crossings.

The model, per workload, as a fraction of its CV8 time:  1 - (1 - R) * self(S) / D + C * X(S) / D,
D the dispatches, self(S) those of the native set S, X(S) the calls crossing S's edge, R a native
dispatch's cost against CV8's, C a crossing's in dispatches. Neither is measured here: the report
gives R 0.10, 0.15, 0.25 (950's guesses) and, since 951, R per family as tools/native-r.py measured
it (forth 0.197, system 0.422, rill3 0.259, shell 0.088); C 2 and 8 until the first hybrid build
measures it.

Sets are chosen greedily, never a word that reaches its caller's frame (rstack_flags: those stay CV8):
the word whose modelled gain per net byte - native bytes less the CV8 body
it replaces - is largest, the gain the mean over the four families (each the mean of its programs),
crossings counted against the set as it stands. Also chosen on one family alone and scored on the
others: how stable the choice is. Writes the full report to OUT (default
bench/reports/native-knee-950.txt) and its summary to stdout.
"""
import bisect, collections, os, statistics, struct, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import opcodes
OUT = sys.argv[1] if len(sys.argv) > 1 else 'bench/reports/native-knee-950.txt'
SLOTS = 1 << 22                                   # MEMSIZE: every address the VM has
ESLOTS = 1 << 21                                  # call edges: (return, target, count)
FAMS = ('forth', 'system', 'rill3', 'shell')

def patch(text, old, new):
    if text.count(old) != 1:
        sys.exit('native-knee: the text to patch occurs %d times, not once:\n%s' % (text.count(old), old))
    return text.replace(old, new)

# ---- the counting engine: pair-corpus.py's, and every call's edge -----------
work = tempfile.mkdtemp(prefix='relf-knee-')
engine = os.path.join(work, 'relf-count')
src = open('engine/cv8.c').read()
src = patch(src, '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP',
            '#include <sys/mman.h>\nstatic unsigned int *prof_map, *edge_map;\nstatic UNS64 prof_base;\n'
            '#define PROF(k)\n#define PROFIP(a) (prof_map[((a) - prof_base) & (%d - 1)]++)\n#define PROFDUMP\n'
            'static void edge(UNS64 r, UNS64 t) {\n'
            '    unsigned int ro = (unsigned int)(r - prof_base) + 1, to = (unsigned int)(t - prof_base);\n'
            '    unsigned int h = (ro * 2654435761u ^ to * 40503u) & (%d - 1);\n'
            '    for (;;) { unsigned int *e = edge_map + 3 * h;\n'
            '        if (e[0] == ro && e[1] == to) { e[2]++; return; }\n'
            '        if (e[0] == 0) { e[0] = ro; e[1] = to; e[2] = 1; return; }\n'
            '        h = (h + 1) & (%d - 1); }\n}\n' % (SLOTS, ESLOTS, ESLOTS))
src = patch(src, '    NEXT();\ndo_call:',
            '    prof_base = cbase;\n    { int fd = open(getenv("COUNTS"), O_RDWR);\n'
            '      prof_map = mmap(0, %d * sizeof(unsigned int), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n'
            '      close(fd);\n      fd = open(getenv("EDGES"), O_RDWR);\n'
            '      edge_map = mmap(0, %d * 3 * sizeof(unsigned int), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n'
            '      close(fd); }\n    NEXT();\ndo_call:' % (SLOTS, ESLOTS))
src = patch(src, 'PROF(256); RPUSH(ip); ip = cbase + (t << SCALE);',
            'PROF(256); RPUSH(ip); edge(ip, cbase + (t << SCALE)); ip = cbase + (t << SCALE);')
src = patch(src, '    RPUSH(ip);\n    ip = x;\n', '    RPUSH(ip);\n    edge(ip, x);\n    ip = x;\n')
src = patch(src, '    ip = cbase + (t << SCALE); NEXT();\nL_branch:',
            '    edge(ip, cbase + (t << SCALE)); ip = cbase + (t << SCALE); NEXT();\nL_branch:')
open(engine + '.c', 'w').write(src)
subprocess.run(['cc', '-O2', '-I', os.path.join(ROOT, 'engine'), '-o', engine, engine + '.c'], check=True)

def run(argv, stdin=None, env=None):
    counts, edges = os.path.join(work, 'counts.bin'), os.path.join(work, 'edges.bin')
    open(counts, 'wb').write(bytes(SLOTS * 4))
    open(edges, 'wb').write(bytes(ESLOTS * 12))
    e = dict(os.environ, COUNTS=counts, EDGES=edges, **(env or {}))
    subprocess.run(argv, input=stdin, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=1800)
    cnt = struct.unpack('<%dI' % SLOTS, open(counts, 'rb').read())
    raw = struct.unpack('<%dI' % (ESLOTS * 3), open(edges, 'rb').read())
    ed = [(raw[i] - 1, raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3) if raw[i]]
    return cnt, ed

# ---- the workloads: pair-corpus.py's four families ----------------------------
def program_image(name, text, run_word):
    img = os.path.join(work, name + '.img')
    stdin = (text + '\n' + 'S" forth/extend.4" INCLUDED S" forth/safety.4" INCLUDED S" forth/pool.4" INCLUDED S" forth/save-system.4" INCLUDED\n'
             ': RUN-BENCH %s BYE ;  \' RUN-BENCH SET-BOOT  S" %s" SAVE-SYSTEM BYE\n' % (run_word, img))
    subprocess.run(['./relf64', 'forth/kernel64.img'], input=stdin.encode(), stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=600)
    if not os.path.exists(img): sys.exit('native-knee: %s was not saved' % name)
    return img
workloads = []                                    # (family, name, image, argv, stdin)
for p in ('fib', 'loop', 'bubble', 'ackermann', 'sieve'):
    t = open('port/measure/inputs/%s.fth' % p).read()
    lines = []
    for l in t.split('\n'):
        if l.startswith(': BX '): l = l[:l.rindex(';') + 1]
        if l.startswith('S" BENCH-DONE"') or l.strip() == 'BYE': continue
        lines.append(l)
    workloads.append(('forth', 'lab ' + p, program_image('lab-' + p, '\n'.join(lines), 'BX'), None, None))
b4 = open('bench/langs/bench.4').read()
for w, word in (('fib', '30 FIB'), ('loopsum', '10000000 LOOPSUM'), ('fannkuch', 'FANNKUCH'), ('collatz', 'COLLATZ')):
    workloads.append(('forth', 'bench.4 ' + w, program_image('b4-' + w, b4, word + ' DROP'), None, None))
core = b''.join(open(f, 'rb').read() for f in ('tests/tester.fr', 'tests/core-extra.fth', 'tests/coreplus-loop.fth')) + b'\nBYE\n'
workloads.append(('system', 'CORE', 'forth/kernel64.img', None, core))
workloads.append(('system', 'lab parse', 'forth/kernel64.img', None, open('port/measure/inputs/parse.fth', 'rb').read()))
for w in ('loop', 'calls', 'for'):
    workloads.append(('rill3', 'rill3 ' + w, 'kernel64-cm.img', ['tests/cm/bench/%s.cm' % w], None))
for w in ('loop', 'fn', 'str', 'arith', 'realistic'):
    workloads.append(('shell', 'shell ' + w, 'kernel64-shell.img', ['tests/bench-vm/%s.sh' % w], None))
NATIVE_OF = {'kernel64-shell.img': 'relfsh-native', 'kernel64-cm.img': 'rill3-native'}   # else native-kernel

# ---- a CV8 image's words: name, k-th of that name, body span, R-stack use -----
FMT = opcodes.formats()
opname, escname = opcodes.names()
def s16(v): return v - 65536 if v >= 32768 else v
def words_of(path):
    d = open(path, 'rb').read(); C = 8
    cell = lambda o: struct.unpack_from('<Q', d, o)[0]
    nth = cell(8); ntails = cell(8 + C + nth * C)
    img = d[8 + C + nth * C + C + ntails * 2 * C:]
    heads = [cell(8 + C + i * C) for i in range(nth)]
    def prev(nfa):
        tag = img[nfa - 1]
        if tag < 128: return (nfa - tag if tag else 0)
        if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa - 2])
        return nfa - (((tag & 63) << 16) | (img[nfa - 2] << 8) | img[nfa - 3])
    hdr = {}
    for h in heads:
        n = h
        while n:
            name, c_, ll, st, _ = opcodes.header(img, n)
            hdr[n] = (name, c_, n - st); n = prev(n)
    nfas = sorted(hdr)
    seen = collections.Counter(); out = []; xt_of = {}   # (key, xt, end, flags)
    for i, n in enumerate(nfas):
        name, c_, ll = hdr[n]
        end = (nfas[i + 1] - hdr[nfas[i + 1]][2]) if i + 1 < len(nfas) else len(img)
        key = (name, seen[name]); seen[name] += 1
        out.append((key, n + 1, end, c_)); xt_of.setdefault(name, n + 1)
    return img, out, xt_of
def is_data(img, xt, end):
    """a variable, a constant's DOVAR, a DOES> child: data, which native code reads by its address -
    never a candidate, and a native word's use of one is no crossing"""
    return xt >= end or FMT.get(img[xt]) == 'data'
FOLDS = {n for k, n, nm, h in opcodes.load() if k == 'fold'} | {opcodes.number('EXIT')}
UNCOND = {opcodes.number('BRANCH'), opcodes.number('BRANCH8')}
def rstack_flags(img, xt, end, xt_of):
    """the return stack in a body, followed along every branch: an R> or R@ with nothing of the body's
    own pushed on that path, an R>;EXIT there, or a >R;EXIT (a jump to a pushed address) reaches the
    caller's frame - a word a native caller cannot call as CV8 does, and that stays CV8"""
    INLINE3 = {xt_of[k] for k in ('(POSTPONE)',) if k in xt_of}
    STRINGS = {xt_of[k] for k in ('(S")', '(.")', '(ABORT")') if k in xt_of}
    def step(ip):                      # (name, length, branch target or None)
        op = img[ip]
        f = FMT.get(op, '-') if op < 0x80 else 'call'
        if f == 'data': return None
        nm = escname.get(img[ip + 1], '') if f == 'sel' else opname.get(op, '')
        tgt = None
        if f in ('b16', 'b8', 'i8b16'):
            k = 2 if f == 'i8b16' else 1
            if f == 'b8': off = img[ip + 1] - 256 if img[ip + 1] >= 128 else img[ip + 1]; ln = 2
            else: off = s16(img[ip + k] | img[ip + k + 1] << 8); ln = k + 2
            tgt = ip + k + off
        elif f == 'u16': ln = 3
        elif f in ('u8', 'i8'): ln = 2
        elif f == 'i32': ln = 5
        elif f == 'u64': ln = 9
        elif f == 'sel': ln = 2
        elif f == 'slot': ln = 4 if img[ip + 1] & 0x80 else 3
        elif f == '2slot':
            ln = 1; ln += 3 if img[ip + ln] & 0x80 else 2; ln += 3 if img[ip + ln] & 0x80 else 2
        elif f == 'call':
            ln = 2 if op < 0xC0 else 3
            t = ((op & 63) << 8) | img[ip + 1] if ln == 2 else ((op & 63) << 16) | img[ip + 1] << 8 | img[ip + 2]
            if t in INLINE3: ln += 3
            elif t in STRINGS: ln += 1 + img[ip + ln]
        else: ln = 1
        return nm, ln, tgt
    seen, work = set(), [(xt, 0)]
    while work:
        ip, depth = work.pop()
        if (ip, depth) in seen or not (xt <= ip < end) or depth > 16: continue
        seen.add((ip, depth))
        st = step(ip)
        if st is None: continue
        nm, ln, tgt = st
        if nm == '>R;EXIT': return True
        if nm in ('R>', 'R>;EXIT', 'R@') and depth == 0: return True
        if nm in ('>R', 'DUP>R'): depth += 1
        elif nm == 'R>': depth -= 1
        op = img[ip]
        if op in FOLDS and op < 0x80: continue
        if tgt is not None: work.append((tgt, depth))
        if op not in UNCOND: work.append((ip + ln, depth))
    return False

# ---- a native build's words: bytes of code by the same keys -------------------
N_BASE = 0x401000
def native_sizes(path):
    d = open(path, 'rb').read()
    phoff, = struct.unpack_from('<Q', d, 32); phnum, = struct.unpack_from('<H', d, 56)
    segs = [struct.unpack_from('<IIQQQQQQ', d, phoff + 56 * k) for k in range(phnum)]
    segs = [(s[3], s[2], s[5]) for s in segs if s[0] == 1 and s[5]]
    (cv, coff, cfz), = [s for s in segs if s[0] <= N_BASE < s[0] + s[2]]
    code_end = cv + cfz
    img = bytearray(max(v + fz for v, _, fz in segs) - N_BASE)
    for v, off, fz in segs:
        lo = max(v, N_BASE)
        img[lo - N_BASE: v + fz - N_BASE] = d[off + lo - v: off + fz]
    i = opcodes.find_header(img, 'FORTH-WORDLIST')
    heads = struct.unpack_from('<33q', img, struct.unpack_from('<I', img, i + 1 + 8)[0] - N_BASE)[1:]
    def link(nfa):
        tag = img[nfa - 1]
        if tag & 0x80 == 0: dist = tag
        elif tag & 0x40 == 0: dist = ((tag & 0x3F) << 8) | img[nfa - 2]
        else: dist = ((tag & 0x3F) << 16) | (img[nfa - 2] << 8) | img[nfa - 3]
        return nfa - dist if dist else 0
    hs = {}
    for h in heads:
        nfa = h
        while nfa:
            nm, _, _, st, xt = opcodes.header(img, nfa)
            hs.setdefault(st, (nm, xt)); nfa = link(nfa)
    starts = sorted(hs); seen = collections.Counter(); out = {}
    for k, st in enumerate(starts):
        nm, xt = hs[st]
        end = starts[k + 1] if k + 1 < len(starts) else code_end - N_BASE
        out[(nm, seen[nm])] = max(0, end - xt); seen[nm] += 1
    return out

# ---- count ---------------------------------------------------------------------
RT = ('(run-time)', 0)
DATA = set()                                      # data words, by key, over every image
prog = []                                         # per workload: dict
images = {}
for fam, name, imgpath, args, stdin in workloads:
    if imgpath not in images:
        img, ws, xt_of = words_of(imgpath)
        nat = native_sizes(NATIVE_OF.get(imgpath, 'native-kernel'))
        images[imgpath] = (img, ws, nat, xt_of)
        for key, xt, end, c_ in ws:
            if is_data(img, xt, end): DATA.add(key)
    img, ws, nat, xt_of = images[imgpath]
    argv = [engine, imgpath] + (args or [])
    env = {'RILL3_PATH': os.path.join(ROOT, 'lib')} if fam == 'rill3' else None
    cnt, ed = run(argv, stdin, env)
    xts = [w[1] for w in ws]
    def word_at(a):
        k = bisect.bisect_right(xts, a) - 1
        return ws[k][0] if k >= 0 and ws[k][1] <= a < ws[k][2] else RT
    total = sum(cnt)
    self_ = collections.Counter()
    for key, xt, end, c_ in ws:
        s = sum(cnt[xt:end])
        if s: self_[key] = s
    self_[RT] = total - sum(self_.values())
    edges = collections.Counter()
    for r, t, c in ed:
        u, v = word_at(r - 1), word_at(t)          # r: the return address, just past the call
        if u != v and v not in DATA: edges[(u, v)] += c
    prog.append(dict(fam=fam, name=name, img=imgpath, D=total, self=self_, edges=edges))
    print('%-18s %-7s %13d dispatches, %6d call edges, run-time code %5.1f %%'
          % (name, fam, total, len(edges), 100.0 * self_[RT] / max(total, 1)), file=sys.stderr)

# ---- bytes per word, over every image it is in ---------------------------------
cv8_bytes, nat_bytes, rflag, images_of = {}, {}, {}, collections.defaultdict(set)
ratios = []
for imgpath, (img, ws, nat, xt_of) in images.items():
    for key, xt, end, c_ in ws:
        images_of[key].add(imgpath)
        b = end - xt
        cv8_bytes.setdefault(key, b)
        rflag.setdefault(key, rstack_flags(img, xt, end, xt_of))
        if key in nat and key not in nat_bytes:
            nat_bytes[key] = nat[key]
            if b >= 4 and nat[key] > 0: ratios.append(nat[key] / b)
RATIO = statistics.median(ratios)
estimated = set()
for key, b in cv8_bytes.items():
    if key not in nat_bytes:
        nat_bytes[key] = int(round(b * RATIO)); estimated.add(key)
cv8_bytes[RT] = nat_bytes[RT] = 0

# ---- the model -----------------------------------------------------------------
def score(S, R, C, progs):
    """each workload's modelled time (fraction of CV8's) for the native set S"""
    out = []
    for p in progs:
        s = sum(c for k, c in p['self'].items() if k in S)
        x = sum(c for (u, v), c in p['edges'].items() if (u in S) != (v in S))
        r = R[p['fam']] if isinstance(R, dict) else R
        out.append((1 - (1 - r) * s / p['D'] + C * x / p['D'], s / p['D'], x / p['D']))
    return out
def fam_mean(vals, progs, fams):
    by = collections.defaultdict(list)
    for v, p in zip(vals, progs): by[p['fam']].append(v)
    return statistics.mean(statistics.mean(by[f]) for f in fams)

def greedy(R, C, fams, budget, cands):
    """words added one at a time by gain per net byte, gain the families' mean of
    (1-R)*self/D - C*(new crossings - removed crossings)/D, until no word gains or the
    native bytes pass budget"""
    progs = [p for p in prog if p['fam'] in fams]
    nf = {f: sum(1 for p in progs if p['fam'] == f) for f in fams}
    wt = [1.0 / (len(fams) * nf[p['fam']] * p['D']) for p in progs]   # each workload's weight per count
    gself = collections.Counter()                             # (1 - R) * own dispatches, weighted
    nbr = collections.defaultdict(collections.Counter)       # word -> neighbour -> weighted calls
    for p, w in zip(progs, wt):
        r = R[p['fam']] if isinstance(R, dict) else R
        for k, c in p['self'].items(): gself[k] += (1 - r) * c * w
        for (u, v), c in p['edges'].items():
            nbr[u][v] += c * w; nbr[v][u] += c * w
    tot = {k: sum(n.values()) for k, n in nbr.items()}
    inS = collections.Counter()                               # weighted calls between a word and S
    S, order, nbytes = set(), [], 0
    live = [k for k in cands if gself[k] > 0 and k != RT and k not in DATA and not rflag.get(k)]   # those stay CV8
    while True:
        best, bk = 0.0, None
        for k in live:
            if k in S: continue
            g = gself[k] - C * (tot.get(k, 0) - 2 * inS[k])
            if g <= 0: continue
            cost = max(nat_bytes[k] - cv8_bytes[k], 1)
            if g / cost > best: best, bk = g / cost, k
        if bk is None: break
        nbytes += nat_bytes[bk]
        if nbytes > budget: break
        S.add(bk); order.append((bk, nbytes))
        for v, c in nbr[bk].items(): inS[v] += c
    return S, order

def summarise(R, C, fams, label, f, budgets=(1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144)):
    _, order = greedy(R, C, fams, max(budgets), cv8_bytes.keys())
    rs = ('measured (%s)' % ', '.join('%s %.3f' % (g, R[g]) for g in FAMS)) if isinstance(R, dict) else '%.2f' % R
    print('\n== %s: chosen on %s, R %s, C %d ==' % (label, '+'.join(fams), rs, C), file=f)
    print('%8s %6s %8s %8s | %7s %7s %7s %7s | %6s %6s %6s %6s | %s' % (
        'native B', 'words', 'net B', 'cv8 B', 'forth', 'system', 'rill3', 'shell',
        'covF', 'covS', 'covR', 'covSh', 'crossings per 1000 dispatches (shell)'), file=f)
    rows = []
    for b in budgets:
        S = {k for k, nb in order if nb <= b}
        if not S: continue
        nb = sum(nat_bytes[k] for k in S); cb = sum(cv8_bytes[k] for k in S)
        sc = score(S, R, C, prog)
        t = [fam_mean([x[0] for x in sc], prog, [g]) for g in FAMS]
        cov = [fam_mean([x[1] for x in sc], prog, [g]) for g in FAMS]
        xs = fam_mean([x[2] for x in sc], prog, ['shell'])
        rows.append((b, len(S), nb, cb, t, cov))
        print('%8d %6d %8d %8d | %7.3f %7.3f %7.3f %7.3f | %5.1f%% %5.1f%% %5.1f%% %5.1f%% | %.2f' % (
            nb, len(S), nb - cb, cb, *t, *[c * 100 for c in cov], xs * 1000), file=f)
    return order, rows

with open(OUT, 'w') as f:
    print('tools/native-knee.py (Iteration 950): the knee of a hybrid image, counted on the four families.', file=f)
    print('native/CV8 bytes median ratio, over %d words in both: %.2f; %d words estimated by it'
          % (len(ratios), RATIO, len(estimated)), file=f)
    print('\n== the workloads ==', file=f)
    for p in prog:
        top = [(k, c) for k, c in p['self'].most_common() if k != RT]
        acc, n50, n80, n90 = 0, None, None, None
        for i, (k, c) in enumerate(top):
            acc += c
            if n50 is None and acc >= 0.5 * p['D']: n50 = i + 1
            if n80 is None and acc >= 0.8 * p['D']: n80 = i + 1
            if n90 is None and acc >= 0.9 * p['D']: n90 = i + 1
        print('%-18s %-7s D %12d  run-time %5.1f %%  words for 50/80/90 %% of D: %s/%s/%s  top: %s' % (
            p['name'], p['fam'], p['D'], 100.0 * p['self'][RT] / p['D'], n50, n80, n90,
            ', '.join('%s %.1f' % (k[0], 100.0 * c / p['D']) for k, c in top[:6])), file=f)
    # what a hybrid made ahead of time cannot reach: run-time code, and - in real use - a Forth program's own
    # words, which are compiled when it is loaded (here each program was saved in an image first)
    for p in prog:
        if p['fam'] == 'forth':
            own = sum(c for k, c in p['self'].items() if k in estimated)
            print('%-18s dispatches in words no native build has (its own, and the libraries loaded): %5.1f %%'
                  % (p['name'], 100.0 * own / p['D']), file=f)
    # the knee by self dispatches alone, families weighed alike: the ceiling with no crossing cost
    allw = collections.Counter()
    for p in prog:
        nf = sum(1 for q in prog if q['fam'] == p['fam'])
        for k, c in p['self'].items():
            if k != RT: allw[k] += c / p['D'] / nf / len(FAMS)
    print('\n== words by self dispatches, the four families weighed alike (top 60) ==', file=f)
    print('%-28s %7s %7s %7s %7s %7s %6s %6s %s' % ('word', 'mean %', 'forth', 'system', 'rill3', 'shell',
                                                    'cv8 B', 'nat B', 'flags'), file=f)
    for k, s in allw.most_common(60):
        fs = []
        for g in FAMS:
            ps = [p for p in prog if p['fam'] == g]
            fs.append(statistics.mean(p['self'].get(k, 0) / p['D'] for p in ps) * 100)
        fl = ('data ' if k in DATA else '') + ('R ' if rflag.get(k) else '') + ('est' if k in estimated else '')
        print('%-28s %7.2f %7.2f %7.2f %7.2f %7.2f %6d %6d %s' % (
            k[0] + ('#%d' % k[1] if k[1] else ''), s * 100, *fs, cv8_bytes[k], nat_bytes[k], fl), file=f)
    results = {}
    for R in (0.10, 0.15, 0.25):
        for C in (2, 8):
            results[(R, C, 'all')] = summarise(R, C, FAMS, 'generic', f)
    for g in FAMS:
        results[(0.15, 2, g)] = summarise(0.15, 2, (g,), 'one family', f)
    # (951) R measured per family by tools/native-r.py (bench/reports/native-r-951.txt, R' - each side less
    # its start); C still unmeasured
    RM = dict(forth=0.197, system=0.422, rill3=0.259, shell=0.088)
    for C in (2, 8):
        results[('m', C, 'all')] = summarise(RM, C, FAMS, 'generic, R measured', f)
        for g in FAMS:
            results[('m', C, g)] = summarise(RM, C, (g,), 'one family, R measured', f)
    order = results[(0.15, 2, 'all')][0]
    print('\n== the generic set, R 0.15 C 2, in the order chosen (first 120) ==', file=f)
    for i, (k, nb) in enumerate(order[:120]):
        print('%4d %-28s native %5d  cv8 %5d  cumulative native %7d %s' % (
            i + 1, k[0] + ('#%d' % k[1] if k[1] else ''), nat_bytes[k], cv8_bytes[k], nb,
            ('R' if rflag.get(k) else '') + (' est' if k in estimated else '')), file=f)
    flagged = sorted((k for k in rflag if rflag[k] and allw.get(k)), key=lambda k: -allw[k])
    print('\nwords that reach their caller\'s frame (an R> or R@ on some path with nothing of their own pushed),'
          ' kept CV8, never chosen - %d run here, by share: %s'
          % (len(flagged), ', '.join('%s %.2f' % (k[0], 100 * allw[k]) for k in flagged[:30])), file=f)
print(open(OUT).read())
