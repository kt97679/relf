#!/usr/bin/env python3
"""tools/pair-corpus.py [N] - adjacent operation pairs over a corpus of Forth, not the shell's alone.

Iteration 946: superinstructions for the Forth, chosen so that no one program decides them - the
owner's condition, "the underlying forth generic and not skewed towards relfsh". tools/superinst.py
counts the shell's workloads only; this counts four families, each program's pairs as a share of
that program's own dispatches, each family the mean of its programs, and ranks a pair by the mean of
the four families:

  forth   the Forth programs: five of the lab's (port/measure/inputs: fib loop bubble ackermann
          sieve) and four of bench/langs/bench.4's seven (fib loopsum fannkuch collatz: its sieve,
          bubble and matrix allocate their arrays as they load, which a saved image does not keep),
          each loaded on the bare kernel, then saved as an image that runs it
  system  the Forth system at work: the CORE suite (tests/tester.fr, core-extra.fth,
          coreplus-loop.fth) and the lab's parse.fth (4,000 lines of interpreted arithmetic) on
          kernel64.img - the interpreter, the compiler, number conversion
  rill3   rill3's runtime: tests/cm/bench's loop, calls and for on kernel64-cm.img
  shell   relfsh: bench-vm's five on kernel64-shell.img

Counts are per address, by a counting engine built from cv8.c (as tools/profile.py's), so only
code in an image's own file is decoded and paired; code compiled after it loads - a CORE test's
definitions, a rill3 script's - counts in the program's total and nowhere else. A pair is two
adjacent instructions of a body, weighted by the second's executions: the first not a call, a
branch or a return; neither a call; the second not a branch target. Prints the top N (40).
"""
import os, struct, subprocess, sys, tempfile, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import opcodes
TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 40
SLOTS = 1 << 22                                   # MEMSIZE: every address the VM has

def patch(text, old, new):
    if text.count(old) != 1:
        sys.exit('pair-corpus: the text to patch occurs %d times, not once' % text.count(old))
    return text.replace(old, new)

work = tempfile.mkdtemp(prefix='relf-pairs-')
engine = os.path.join(work, 'relf-count')
src = open('engine/cv8.c').read()
src = patch(src, '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP',
            '#include <sys/mman.h>\nstatic unsigned int *prof_map;\nstatic UNS64 prof_base;\n'
            '#define PROF(k)\n#define PROFIP(a) (prof_map[((a) - prof_base) & (%d - 1)]++)\n#define PROFDUMP' % SLOTS)
src = patch(src, '    NEXT();\ndo_call:',
            '    prof_base = cbase;\n    { int fd = open(getenv("COUNTS"), O_RDWR);\n'
            '      prof_map = mmap(0, %d * sizeof(unsigned int), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n'
            '      close(fd); }\n    NEXT();\ndo_call:' % SLOTS)
open(engine + '.c', 'w').write(src)
subprocess.run(['cc', '-O2', '-I', os.path.join(ROOT, 'engine'), '-o', engine, engine + '.c'], check=True)

def run(argv, stdin=None, env=None):
    counts = os.path.join(work, 'counts.bin')
    open(counts, 'wb').write(bytes(SLOTS * 4))
    e = dict(os.environ, COUNTS=counts, **(env or {}))
    subprocess.run(argv, input=stdin, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=1800)
    raw = open(counts, 'rb').read()
    return struct.unpack('<%dI' % SLOTS, raw)

# ---- the Forth programs, each saved as an image that runs it ---------------
def program_image(name, text, run_word):
    img = os.path.join(work, name + '.img')
    stdin = (text + '\n' + 'S" forth/extend.4" INCLUDED S" forth/safety.4" INCLUDED S" forth/pool.4" INCLUDED S" forth/save-system.4" INCLUDED\n'
             ': RUN-BENCH %s BYE ;  \' RUN-BENCH SET-BOOT  S" %s" SAVE-SYSTEM BYE\n' % (run_word, img))
    subprocess.run(['./relf64', 'forth/kernel64.img'], input=stdin.encode(), stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=600)
    if not os.path.exists(img): sys.exit('pair-corpus: %s was not saved' % name)
    return img
workloads = []                                    # (family, name, image, argv, stdin)
for p in ('fib', 'loop', 'bubble', 'ackermann', 'sieve'):
    t = open('port/measure/inputs/%s.fth' % p).read()
    # the run is BX: its definition kept, the line's call of it, the banner and the BYEs dropped
    lines = []
    for l in t.split('\n'):
        if l.startswith(': BX '): l = l[:l.rindex(';') + 1]
        if l.startswith('S" BENCH-DONE"') or l.strip() == 'BYE': continue
        lines.append(l)
    img = program_image('lab-' + p, '\n'.join(lines), 'BX')
    workloads.append(('forth', 'lab ' + p, img, None, None))
b4 = open('bench/langs/bench.4').read()
# its sieve, bubble and matrix ALLOCATE their arrays as they load, which a saved image does not
# keep: the lab's sieve and bubble stand for them
for w, word in (('fib', '30 FIB'), ('loopsum', '10000000 LOOPSUM'), ('fannkuch', 'FANNKUCH'), ('collatz', 'COLLATZ')):
    img = program_image('b4-' + w, b4, word + ' DROP')
    workloads.append(('forth', 'bench.4 ' + w, img, None, None))
core = b''.join(open(f, 'rb').read() for f in ('tests/tester.fr', 'tests/core-extra.fth', 'tests/coreplus-loop.fth')) + b'\nBYE\n'
workloads.append(('system', 'CORE', 'forth/kernel64.img', None, core))
workloads.append(('system', 'lab parse', 'forth/kernel64.img', None, open('port/measure/inputs/parse.fth', 'rb').read()))
for w in ('loop', 'calls', 'for'):
    workloads.append(('rill3', 'rill3 ' + w, 'kernel64-cm.img', ['tests/cm/bench/%s.cm' % w], None))
for w in ('loop', 'fn', 'str', 'arith', 'realistic'):
    workloads.append(('shell', 'shell ' + w, 'kernel64-shell.img', ['tests/bench-vm/%s.sh' % w], None))

# ---- decoding an image into bodies of instructions (tools/superinst.py's) --
N = opcodes.number
EXIT, BR, QBR, B8, QB8 = N('EXIT'), N('BRANCH'), N('?BRANCH'), N('BRANCH8'), N('?BRANCH8')
rows = opcodes.load()
FOLD = {n for k, n, nm, h in rows if k == 'fold'}
opname, escname = opcodes.names()
FMT = opcodes.formats()
def s16(v): return v - 65536 if v >= 32768 else v
_decoded = {}
def decode(path):
    if path in _decoded: return _decoded[path]
    d = open(path, 'rb').read(); C = 8
    cell = lambda o: struct.unpack_from('<Q', d, o)[0]
    nth = cell(8); ntails = cell(8 + C + nth * C)
    hdr = 8 + C + nth * C + C + ntails * 2 * C
    img = d[hdr:]
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
            c_ = img[n]; name = img[n + 1:n + 1 + (c_ & 31)].decode('latin1')
            p, ll = prev(n); words[n] = (name, c_, ll); n = p
    nfas = sorted(words)
    xt_of, bodies = {}, []
    for i, n in enumerate(nfas):
        name, c_, ll = words[n]
        xt = n + 1 + (c_ & 31)
        end = (nfas[i + 1] - words[nfas[i + 1]][2]) if i + 1 < len(nfas) else len(img)
        xt_of.setdefault(name, xt); bodies.append((name, c_, xt, end))
    INLINE3 = {xt_of[k] for k in ('(POSTPONE)',) if k in xt_of}
    STRINGS = {xt_of[k] for k in ('(S")', '(.")', '(ABORT")') if k in xt_of}
    code = []
    for name, c_, xt, end in bodies:
        if c_ & 32 or xt >= end or FMT.get(img[xt]) == 'data': continue
        ins, targets = [], set()
        ip = xt
        while ip < end:
            op = img[ip]; a = ip; kind = 'op'; key = opname.get(op, '?%02X' % op)
            f = FMT.get(op, '-') if op < 0x80 else 'call'
            if f in ('b16', 'b8', 'i8b16'):
                k = 2 if f == 'i8b16' else 1
                if f == 'b8': off = img[ip + 1] - 256 if img[ip + 1] >= 128 else img[ip + 1]; ln = 2
                else: off = s16(img[ip + k] | img[ip + k + 1] << 8); ln = k + 2
                targets.add(ip + k + off); ip += ln; kind = 'branch'
            elif f == 'u16': ip += 3
            elif f in ('u8', 'i8'): ip += 2
            elif f == 'i32': ip += 5
            elif f == 'u64': ip += 9
            elif f == 'sel': key = 'ESC:' + escname.get(img[ip + 1], '?'); ip += 2
            elif f == 'slot': ip += 4 if img[ip + 1] & 0x80 else 3
            elif f == '2slot': ip += 1; ip += 3 if img[ip] & 0x80 else 2; ip += 3 if img[ip] & 0x80 else 2
            elif f == 'call':
                ln = 2 if op < 0xC0 else 3
                t = ((op & 63) << 8) | img[ip + 1] if ln == 2 else ((op & 63) << 16) | img[ip + 1] << 8 | img[ip + 2]
                ip += ln; kind = 'call'; key = 'call'
                if t in INLINE3: ip += 3
                elif t in STRINGS: ip = ip + 1 + img[ip]
            else: ip += 1
            if op == EXIT or op in FOLD: kind = 'exit'
            ins.append((a, key, ip - a, kind))
        code.append((name, ins, targets))
    _decoded[path] = code
    return code

# ---- count ------------------------------------------------------------------
LOOPISH = {'(?DO)', 'EXECUTE', 'ESC:EXECUTE'}        # the next instruction does not follow them
fam_rows = collections.defaultdict(list)          # family -> [Counter of pair shares]
totals = {}
for fam, name, img, args, stdin in workloads:
    argv = [engine, img] + (args or [])
    env = {'RILL3_PATH': os.path.join(ROOT, 'lib')} if fam == 'rill3' else None
    cnt = run(argv, stdin, env)
    total = sum(cnt)
    pairs = collections.Counter()
    for bname, ins, targets in decode(img):
        for (a1, k1, l1, kd1), (a2, k2, l2, kd2) in zip(ins, ins[1:]):
            if kd1 != 'op' or kd2 == 'call' or a2 in targets or k1 in LOOPISH: continue
            pairs[(k1, k2)] += cnt[a2]
    totals[name] = total
    fam_rows[fam].append({p: c / total for p, c in pairs.items()} if total else {})
    print('%-18s %-7s %13d dispatches' % (name, fam, total), file=sys.stderr)
FAMS = ('forth', 'system', 'rill3', 'shell')
famshare = {}
for fam in FAMS:
    acc = collections.Counter()
    for r in fam_rows[fam]:
        for p, s in r.items(): acc[p] += s / len(fam_rows[fam])
    famshare[fam] = acc
allp = set().union(*[set(famshare[f]) for f in FAMS])
score = {p: sum(famshare[f].get(p, 0) for f in FAMS) / len(FAMS) for p in allp}
print('%-26s %7s  %7s %7s %7s %7s  %s' % ('pair', 'mean %', 'forth', 'system', 'rill3', 'shell', 'families >= 0.3 %'))
for p in sorted(allp, key=lambda p: -score[p])[:TOP]:
    fs = [famshare[f].get(p, 0) * 100 for f in FAMS]
    print('%-26s %7.2f  %7.2f %7.2f %7.2f %7.2f  %d' % (' '.join(p), score[p] * 100, *fs, sum(1 for x in fs if x >= 0.3)))
