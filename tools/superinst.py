#!/usr/bin/env python3
"""tools/superinst.py [K] - which opcode pairs and triples to fuse.

Iteration 527 (ASM-ENGINE.md Milestone 5): both engines dispatch at the
rate the CPU takes indirect jumps, so speed now means fewer dispatches,
and a superinstruction - two or three operations as one opcode - is the
way to fewer. This finds the candidates on real work:

  1. counts every dispatch by its address, on the shell's workloads (the
     five of tests/bench-vm and the differential suite), with the same
     counting engine tools/profile.py builds, embedded as a shell;
  2. decodes the shell image into instructions - address, opcode, length;
  3. counts each pair of ADJACENT instructions by the executions of the
     first: exact in straight-line code, where an operation that neither
     calls nor branches is always followed by the next. A pair is not a
     candidate if its first is a call, a branch or a return (the second
     would not follow), if either is a call (its target is an operand),
     or if its second is a branch target (a jump cannot land inside a
     fused opcode). Triples likewise;
  4. fuses the K most frequent pairs (default 32, the free opcodes
     0x41-0x60) in a simulation, left to right through every body, and
     reports the dispatches and bytes that would save.
"""
import os, struct, subprocess, sys, tempfile, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import opcodes
K = int(sys.argv[1]) if len(sys.argv) > 1 else 32

def patch(text, old, new):
    if text.count(old) != 1:
        sys.exit('superinst: the text to patch occurs %d times, not once' % text.count(old))
    return text.replace(old, new)

# ---- 1. count dispatches by address ---------------------------------------
work = tempfile.mkdtemp(prefix='relf-super-')
engine, counts, shell = (os.path.join(work, n) for n in ('relf-count', 'counts.bin', 'relfsh'))
SLOTS = 1 << 18
src = open('engine/cv8.c').read()
src = patch(src, '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP',
            '#include <sys/mman.h>\nstatic unsigned int *prof_map;\nstatic UNS64 prof_base;\n'
            '#define PROF(k)\n#define PROFIP(a) (prof_map[((a) - prof_base) & 0x3FFFF]++)\n#define PROFDUMP')
src = patch(src, '    NEXT();\ndo_call:',
            '    prof_base = cbase;\n    { int fd = open("%s", O_RDWR);\n'
            '      prof_map = mmap(0, %d * sizeof(unsigned int), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n'
            '      close(fd); }\n    NEXT();\ndo_call:' % (counts, SLOTS))
open(engine + '.c', 'w').write(src)
subprocess.run(['cc', '-O2', '-I', os.path.join(ROOT, 'engine'), '-o', engine, engine + '.c'], check=True)
subprocess.run(['sh', 'tools/embed.sh', engine, 'kernel64-shell.img', shell], check=True)
open(counts, 'wb').write(bytes(SLOTS * 4))
env = dict(os.environ, THIS_SH=shell, RELFSH=shell)
for w in ('loop', 'fn', 'str', 'arith', 'realistic'):
    subprocess.run([shell, 'tests/bench-vm/%s.sh' % w], env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
subprocess.run(['sh', 'tests/diff/run-all'], env=env,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
raw = open(counts, 'rb').read()
cnt = struct.unpack('<%dI' % SLOTS, raw)

# ---- 2. decode the shell image into instructions --------------------------
d = open('kernel64-shell.img', 'rb').read(); C = 8
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
        c_ = img[n]; name = img[n + 1:n + 1 + (c_ & 31)].decode('latin1')
        p, ll = prev(n); words[n] = (name, c_, ll); n = p
nfas = sorted(words)
xt_of = {}
bodies = []
for i, n in enumerate(nfas):
    name, c_, ll = words[n]
    xt = n + 1 + (c_ & 31)
    end = (nfas[i + 1] - words[nfas[i + 1]][2]) if i + 1 < len(nfas) else len(img)
    xt_of[name] = xt
    bodies.append((name, c_, xt, end))
INLINE3 = {xt_of[k] for k in ('(POSTPONE)',) if k in xt_of}
STRINGS = {xt_of[k] for k in ('(S")', '(.")', '(ABORT")') if k in xt_of}
N = opcodes.number
EXIT, BR, QBR, B8, QB8 = N('EXIT'), N('BRANCH'), N('?BRANCH'), N('BRANCH8'), N('?BRANCH8')
rows = opcodes.load()
FOLD = set()                            # no folded returns since Iteration 538
opname, escname = opcodes.names()
FMT = opcodes.formats()
def s16(v): return v - 65536 if v >= 32768 else v
code = []                                # per body: [(addr, key, length, kind)]
for name, c_, xt, end in bodies:
    if c_ & 32 or xt >= end:
        continue
    if FMT.get(img[xt]) == 'data':
        # a data word: its entry opcode runs whenever it is called, and
        # the cold-opcode report must see that (527 showed DOVAR and
        # DODOES as never executed, having skipped these bodies)
        code.append((name, [(xt, 'DOVAR' if img[xt] == 0x24 else 'DODOES', 1, 'op')], set()))
        continue
    ins, targets = [], set()
    ip = xt; far = xt
    while ip < end:
        op = img[ip]; a = ip; kind = 'op'; key = opname.get(op, '?%02X' % op)
        # operand lengths from opcodes.tab's fifth column (Iteration 533)
        f = FMT.get(op, '-') if op < 0x80 else 'call'
        if f in ('b16', 'b8'):
            if f == 'b16':
                off = s16(img[ip + 1] | img[ip + 2] << 8); ln = 3
            else:
                off = img[ip + 1] - 256 if img[ip + 1] >= 128 else img[ip + 1]; ln = 2
            targets.add(ip + 1 + off)
            if off > 0: far = max(far, ip + 1 + off)
            ip += ln; kind = 'branch'
        elif f == 'u16': ip += 3
        elif f in ('u8', 'i8'): ip += 2
        elif f == 'i32': ip += 5
        elif f == 'u64': ip += 9
        elif f == 'sel':
            key = 'ESC:' + escname.get(img[ip + 1], '?'); ip += 2
        elif f == 'slot':
            ip += 4 if img[ip + 1] & 0x80 else 3
        elif f == 'call':
            ln = 2 if op < 0xC0 else 3
            t = ((op & 63) << 8) | img[ip + 1] if ln == 2 else ((op & 63) << 16) | img[ip + 1] << 8 | img[ip + 2]
            ip += ln; kind = 'call'; key = 'call'
            if t in INLINE3: ip += 3
            elif t in STRINGS: ip = ip + 1 + img[ip]
        else:
            ip += 1
        if op == EXIT or op in FOLD: kind = 'exit'
        ins.append((a, key, ip - a, kind))
        if (op == EXIT or op in FOLD) and ip > far:
            break
    code.append((name, ins, targets))

# ---- 3. count adjacent pairs and triples ----------------------------------
total = sum(cnt)
pairs = collections.Counter(); triples = collections.Counter()
for name, ins, targets in code:
    for i in range(len(ins) - 1):
        a, k1, l1, t1 = ins[i]
        b, k2, l2, t2 = ins[i + 1]
        if t1 != 'op' or t2 == 'call' or b in targets or cnt[a] == 0:
            continue
        pairs[(k1, k2)] += cnt[a]
        if i + 2 < len(ins) and t2 == 'op':
            c3, k3, l3, t3 = ins[i + 2]
            if t3 != 'call' and c3 not in targets:
                triples[(k1, k2, k3)] += cnt[a]
print('%d dispatches counted; %d bodies decoded' % (total, len(code)))
print('\nthe most executed adjacent pairs:')
for (k1, k2), n in pairs.most_common(30):
    print('  %-26s %12d  %5.2f%%' % (k1 + ' ' + k2, n, 100.0 * n / total))
print('\nthe most executed adjacent triples:')
for (k1, k2, k3), n in triples.most_common(15):
    print('  %-36s %12d  %5.2f%%' % (' '.join((k1, k2, k3)), n, 100.0 * n / total))

# ---- 3b. the other end: one-byte opcodes that are rarely executed ---------
# (the user's correction at 528: the one-byte space is finite, and a cold
# opcode's slot could hold a hot one - the cold one moving to the escape
# band, one byte and one dispatch more a use, or out of the primitives)
dyn = collections.Counter(); stat = collections.Counter()
for name, ins, targets in code:
    for a, key, ln, kind in ins:
        if key == 'call' or key.startswith('ESC:'):
            continue
        dyn[key] += cnt[a]; stat[key] += 1
one_byte = [nm for k, n, nm, h in rows if k != 'escaped' and nm != 'ESC']
cold = sorted(one_byte, key=lambda k: (dyn[k], stat[k]))
print('\nthe coldest one-byte opcodes - candidates to move out:')
print('  %-12s %12s %8s  %s' % ('opcode', 'executed', '% disp', 'static uses'))
for k in cold[:24]:
    print('  %-12s %12d %7.4f%%  %d' % (k, dyn[k], 100.0 * dyn[k] / total, stat[k]))

# ---- 3c. where the dispatches go, by kind of opcode ------------------------
# (Iteration 536: how much is CALL and EXIT - the threading overhead - and
# how much the folded returns save, for the questions of threading
# technique and of fitting the one-byte opcodes into 64)
kind_of = {n: k for k, n, nm, h in rows if k != 'escaped'}
EXITNUM = N('EXIT')
bykind = collections.Counter()
for name, ins, targets in code:
    for a, key, ln, kind in ins:
        op = img[a]
        if op >= 0x80: k = 'call'
        elif op == EXITNUM: k = 'EXIT'
        elif op == N('ESC'): k = 'escaped'
        else: k = kind_of.get(op, '?')
        bykind[k] += cnt[a]
print('\nwhere the dispatches go, by kind:')
for k, n in bykind.most_common():
    print('  %-10s %12d  %5.1f%%' % (k, n, 100.0 * n / total))

# ---- 4. fuse the top K pairs, in a simulation ------------------------------
chosen = {p for p, n in pairs.most_common(K)}
saved = 0; sites = 0
for name, ins, targets in code:
    i = 0
    while i < len(ins) - 1:
        a, k1, l1, t1 = ins[i]; b, k2, l2, t2 = ins[i + 1]
        if t1 == 'op' and t2 != 'call' and b not in targets and (k1, k2) in chosen:
            saved += cnt[a]; sites += 1; i += 2
        else:
            i += 1
print('\nfusing the top %d pairs, left to right through every body:' % K)
print('  %d dispatches saved, %.1f%% of all; %d sites, %d bytes of image'
      % (saved, 100.0 * saved / total, sites, sites))
