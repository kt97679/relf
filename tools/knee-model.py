#!/usr/bin/env python3
"""tools/knee-model.py - what portable-knee's mechanisms would save on relf's own workloads, counted.

tools/superinst.py's counting engine and decoder, run on two workloads: the shell's (tests/bench-vm's
five and the differential suite, kernel64-shell.img) and rill3's (tests/cm/bench and the suite's
scripts, kernel64-cm.img). For each, the dispatches each stage of the adoption would remove:
  1. folds: an operation followed by EXIT, the knee's 16 and every other;
  2. one-byte operations: escaped ones made one-byte (a second indirect jump less each), and colon
     words made primitives (their bodies' dispatches, EXIT included);
  3. superinstructions: the knee's three pairs, and I + (rtiplus), SWAP ADDI (swapi);
Exact for the image's code; run-time compiled code (rill3's scripts) is counted but not decoded.
"""
import os, struct, subprocess, sys, tempfile, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import opcodes

def patch(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

work = tempfile.mkdtemp(prefix='knee-model-')
engine = os.path.join(work, 'relf-count')
SLOTS = 1 << 18
src = open('engine/cv8.c').read()
src = patch(src, '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP',
            '#include <sys/mman.h>\nstatic unsigned int *prof_map;\nstatic UNS64 prof_base;\n'
            '#define PROF(k)\n#define PROFIP(a) (prof_map[((a) - prof_base) & 0x3FFFF]++)\n#define PROFDUMP')
src = patch(src, '    NEXT();\ndo_call:',
            '    prof_base = cbase;\n    { int fd = open(getenv("COUNTS"), O_RDWR);\n'
            '      prof_map = mmap(0, %d * sizeof(unsigned int), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n'
            '      close(fd); }\n    NEXT();\ndo_call:' % SLOTS)
open(engine + '.c', 'w').write(src)
subprocess.run(['cc', '-O2', '-I', os.path.join(ROOT, 'engine'), '-o', engine, engine + '.c'], check=True)

def count(runs):
    c = os.path.join(work, 'counts-%d.bin' % len(os.listdir(work)))
    open(c, 'wb').write(bytes(SLOTS * 4))
    for cmd, env in runs:
        e = dict(os.environ, COUNTS=c, **env)
        subprocess.run(cmd, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
    return struct.unpack('<%dI' % SLOTS, open(c, 'rb').read())

shell = os.path.join(work, 'relfsh')
subprocess.run(['sh', 'tools/embed.sh', engine, 'kernel64-shell.img', shell], check=True)
SH = count([([shell, 'tests/bench-vm/%s.sh' % w], dict(THIS_SH=shell, RELFSH=shell))
            for w in ('loop', 'fn', 'str', 'arith', 'realistic')]
           + [(['sh', 'tests/diff/run-all'], dict(THIS_SH=shell, RELFSH=shell))])
cmw = os.path.join(work, 'cm')
open(cmw, 'w').write('#!/bin/sh\nRILL3_PATH=%s/lib exec %s %s/kernel64-cm.img "$@"\n' % (ROOT, engine, ROOT))
os.chmod(cmw, 0o755)
scripts = sorted(f for f in os.listdir('tests/cm/scripts') if f.endswith('.cm'))
CM = count([([cmw, 'tests/cm/bench/%s' % f], {}) for f in ('calls.cm', 'loop.cm', 'for.cm')]
           + [([cmw, 'tests/cm/scripts/' + f], {}) for f in scripts])

N = opcodes.number
EXIT = N('EXIT')
EXITS = opcodes.returns()      # EXIT and the folded returns (939)
opname, escname = opcodes.names()
FMT = opcodes.formats()
def s16(v): return v - 65536 if v >= 32768 else v

def decode(path):
    d = open(path, 'rb').read(); C = 8
    cell = lambda o: struct.unpack_from('<Q', d, o)[0]
    nth = cell(8)
    img = d[8 + C + nth * C + C:]
    heads = [cell(8 + C + i * C) for i in range(nth)]
    def prev(nfa):
        tag = img[nfa - 1]
        if tag < 128: return (nfa - tag if tag else 0), 1
        if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa - 2]), 2
        return nfa - (((tag & 63) << 16) | (img[nfa - 2] << 8) | img[nfa - 3]), 3
    words = {}
    for h in heads:
        n = h
        while n:
            name, c_, ll, st, _ = opcodes.header(img, n)   # [name][link][count] (949)
            p, _ = prev(n); words[n] = (name, c_, n - st); n = p
    nfas = sorted(words)
    xt_of = {}; bodies = []
    for i, n in enumerate(nfas):
        name, c_, ll = words[n]
        xt = n + 1
        end = (nfas[i + 1] - words[nfas[i + 1]][2]) if i + 1 < len(nfas) else len(img)
        xt_of.setdefault(name, xt)
        bodies.append((name, c_, xt, end))
    INLINE3 = {xt_of[k] for k in ('(POSTPONE)',) if k in xt_of}
    STRINGS = {xt_of[k] for k in ('(S")', '(.")', '(ABORT")') if k in xt_of}
    code = []
    for name, c_, xt, end in bodies:
        if c_ & 32 or xt >= end or FMT.get(img[xt]) == 'data':
            continue
        ins, targets = [], set(); ip = xt; far = xt
        while ip < end:
            op = img[ip]; a = ip; kind = 'op'; key = opname.get(op, '?%02X' % op); tgt = None
            f = FMT.get(op, '-') if op < 0x80 else 'call'
            if f in ('b16', 'b8', 'i8b16'):
                k = 2 if f == 'i8b16' else 1            # EQI?BRANCH: its byte, then the offset (940)
                if f == 'b8': off = img[ip + 1] - 256 if img[ip + 1] >= 128 else img[ip + 1]; ln = 2
                else: off = s16(img[ip + k] | img[ip + k + 1] << 8); ln = k + 2
                targets.add(ip + k + off)
                if off > 0: far = max(far, ip + k + off)
                ip += ln; kind = 'branch'
            elif f == 'u16': ip += 3
            elif f in ('u8', 'i8'): ip += 2
            elif f == 'i32': ip += 5
            elif f == 'u64': ip += 9
            elif f == 'sel': key = 'ESC:' + escname.get(img[ip + 1], '?'); ip += 2
            elif f == 'slot': ip += 4 if img[ip + 1] & 0x80 else 3
            elif f == '2slot':                          # 2VAR@ (940)
                ip += 1; ip += 3 if img[ip] & 0x80 else 2; ip += 3 if img[ip] & 0x80 else 2
            elif f == 'call':
                ln = 2 if op < 0xC0 else 3
                tgt = ((op & 63) << 8) | img[ip + 1] if ln == 2 else ((op & 63) << 16) | img[ip + 1] << 8 | img[ip + 2]
                ip += ln; kind = 'call'; key = 'call'
                if tgt in INLINE3: ip += 3
                elif tgt in STRINGS: ip = ip + 1 + img[ip]
            else: ip += 1
            if op in EXITS: kind = 'exit'
            ins.append((a, key, ip - a, kind, tgt))
            if op in EXITS and ip > far: break
        code.append((name, xt, end, ins, targets))
    return code, xt_of

KNEE_FOLDS = ['!', 'RSHIFT', 'C@', 'C!', 'AND', 'OR', 'XOR', 'LIT', 'U<', 'OVER', 'DROP', 'SWAP', '>R', 'R@', 'NEGATE', '<']
KNEE_OPS10 = ['(LEAVE)', 'I', 'J', '(DO)', '(LOOP)', '(+LOOP)', '(?DO)', 'UNLOOP', '?BRANCH8', 'FILL', 'HASH',
              '2@', '2!', 'BRANCH8', 'OVER?BRANCH', 'CMOVE', '>', '0=']
KNEE_SUPERS = [('OVER', 'C@'), ('+', '@'), ('@', '+')]

def report(title, path, cnt):
    code, xt_of = decode(path)
    total = sum(cnt)
    inbody = sum(cnt[a] for _, _, _, ins, _ in code for a, *_ in ins)
    pct = lambda n: '%6.2f%%' % (100.0 * n / total)
    print('\n==== %s: %d dispatches, %.1f%% of them in the image\'s decoded code' % (title, total, 100.0 * inbody / total))
    folds = collections.Counter(); pairs = collections.Counter()
    for name, xt, end, ins, targets in code:
        for i in range(len(ins) - 1):
            a, k1, l1, t1, _ = ins[i]; b, k2, l2, t2, _ = ins[i + 1]
            if t1 != 'op' or b in targets or cnt[a] == 0: continue
            if k2 == 'EXIT': folds[k1] += cnt[a]
            if t2 == 'op': pairs[(k1, k2)] += cnt[a]
    ex = sum(cnt[a] for _, _, _, ins, _ in code for a, k, *_ in ins if k == 'EXIT')
    kf = sum(folds[k] for k in KNEE_FOLDS)
    print('1. folds: EXIT %s of all; folded by the knee\'s 16: %s; by any operation: %s' % (pct(ex), pct(kf), pct(sum(folds.values()))))
    print('   X;EXIT, the most executed:', ', '.join('%s %s' % (k, pct(n).strip()) for k, n in folds.most_common(14)))
    esc = collections.Counter()
    for name, xt, end, ins, targets in code:
        for a, k, *_ in ins:
            if k.startswith('ESC:'): esc[k[4:]] += cnt[a]
    print('2. escaped: %s of all; the most executed:' % pct(sum(esc.values())),
          ', '.join('%s %s' % (k, pct(n).strip()) for k, n in esc.most_common(12)))
    colon = []
    for w in KNEE_OPS10 + ['PICK', 'MOVE', 'ROLL', 'NIP', 'TUCK', '2SWAP', '2OVER', 'WITHIN', 'MIN', 'MAX', 'ABS', 'LSHIFT']:
        if w in opcodes.names()[0].values() or w in escname.values(): continue
        body = next((ins for name, xt, end, ins, t in code if name == w), None)
        if body is None: continue
        n = sum(cnt[a] for a, *_ in body)
        if n: colon.append((w, n))
    print('   colon words that are the knee\'s one-byte operations (or common words): their bodies\'', ', '.join('%s %s' % (k, pct(n).strip()) for k, n in sorted(colon, key=lambda x: -x[1])))
    print('3. pairs: the knee\'s supers', ', '.join('%s %s %s' % (a, b, pct(pairs[(a, b)]).strip()) for a, b in KNEE_SUPERS),
          '| I + %s | SWAP ADDI %s | DUP ADDI %s' % tuple(pct(pairs[p]).strip() for p in (('I', '+'), ('SWAP', 'ADDI'), ('DUP', 'ADDI'))))
    print('   the most executed pairs:', ', '.join('%s %s %s' % (a, b, pct(n).strip()) for (a, b), n in pairs.most_common(12)))
    calls = sum(cnt[a] for _, _, _, ins, _ in code for a, k, *_ in ins if k == 'call')
    print('   calls %s of all' % pct(calls))

report('the shell (bench-vm and the differential suite)', 'kernel64-shell.img', SH)
report('rill3 (tests/cm/bench and the suite\'s scripts)', 'kernel64-cm.img', CM)
