#!/usr/bin/env python3
"""tools/asm-fuzz.py [N] [SEED] - forth/asm64.4 against GNU as, at random.

tools/asm-test.py holds the assembler to GNU as's bytes on the 456 shapes
the engine uses. This generates N random instructions (default 600) in
the families the encoder has - ALU, mov, lea, test, one-operand, imul,
push and pop, movzx/movsx/movsxd, shifts, setcc, xchg, cmovcc, bsr/bsf -
over every register width, r8-r15 and spl/bpl/sil/dil, and the
addressing modes with encodings of their own: rsp and r12 as a base
(SIB), rbp and r13 (a displacement), no base, every scale, 8- and 32-bit
displacements and immediates. GNU as assembles each alone; relf
assembles each with asm-test.py's translator. A MISMATCH - both
assembled, the bytes differ - is the dangerous case: a program that
silently does something else. What relf refuses is counted apart, and
what GNU as refuses is skipped. TESTING-IDEAS.md 4; Iteration 566.
"""
import os, random, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 600
rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 566)
# asm-test.py's translator from GNU's Intel syntax to asm64.4's: its
# definitions, up to where it reads the corpus
src = open('tools/asm-test.py').read()
exec(src[:src.index('lines = [')], globals())

R64 = 'rax rbx rcx rdx rsi rdi rbp rsp r8 r9 r10 r11 r12 r13 r14 r15'.split()
R32 = 'eax ebx ecx edx esi edi ebp esp r8d r9d r10d r11d r12d r13d r14d r15d'.split()
R16 = 'ax bx cx dx si di bp sp r8w r9w r10w r11w r12w r13w r14w r15w'.split()
R8 = 'al bl cl dl sil dil bpl spl r8b r9b r10b r11b r12b r13b r14b r15b'.split()
BYW = {8: R8, 16: R16, 32: R32, 64: R64}
PTR = {8: 'byte', 16: 'word', 32: 'dword', 64: 'qword'}

def reg(w): return rng.choice(BYW[w])
def disp():
    return rng.choice([0, 0, rng.randrange(-128, 128), rng.randrange(-(1 << 31), 1 << 31),
                       127, -128, 128, -129])
def mem(w=None):
    base = rng.choice(R64 + [None]) if rng.random() < 0.9 else None
    index = rng.choice([r for r in R64 if r != 'rsp']) if rng.random() < 0.4 else None
    d = disp()
    if base is None and index is None:
        base = rng.choice(R64)
    parts = []
    if base: parts.append(base)
    if index: parts.append('%s*%d' % (index, rng.choice([1, 2, 4, 8])))
    s = '+'.join(parts)
    if d or not parts or base is None:
        s += ('+%d' % d if d >= 0 else '%d' % d) if parts else '%d' % d
    return ('%s ptr ' % PTR[w] if w else '') + '[' + s + ']'
def imm(w, small=False):
    if small or w == 8 or rng.random() < 0.5:
        return rng.randrange(-128, 128)
    return rng.randrange(-(1 << 31), 1 << 31) if w != 16 else rng.randrange(-32768, 32768)

def instr():
    k = rng.random()
    w = rng.choice([8, 16, 32, 64])
    if k < 0.30:
        mn = rng.choice(['add', 'sub', 'and', 'or', 'xor', 'cmp', 'adc', 'sbb', 'mov', 'test'])
        f = rng.randrange(5)
        if f == 0: return '%s %s, %s' % (mn, reg(w), reg(w))
        if f == 1 and mn != 'test': return '%s %s, %s' % (mn, reg(w), mem())
        if f == 2: return '%s %s, %s' % (mn, mem(), reg(w))
        if f == 3: return '%s %s, %d' % (mn, reg(w), imm(w))
        return '%s %s, %d' % (mn, mem(w), imm(w))
    if k < 0.38:
        return 'lea %s, %s' % (reg(rng.choice([32, 64])), mem())
    if k < 0.50:
        mn = rng.choice(['inc', 'dec', 'neg', 'not', 'mul', 'div', 'imul', 'idiv'])
        return '%s %s' % (mn, reg(w) if rng.random() < 0.5 else mem(w))
    if k < 0.56:
        w = rng.choice([16, 32, 64]); f = rng.randrange(3)
        if f == 0: return 'imul %s, %s' % (reg(w), reg(w) if rng.random() < 0.5 else mem())
        return 'imul %s, %s, %d' % (reg(w), reg(w) if f == 1 else mem(), imm(w))
    if k < 0.62:
        mn = rng.choice(['push', 'pop'])
        f = rng.randrange(3)
        if f == 0: return '%s %s' % (mn, rng.choice(R64))
        if f == 1: return '%s %s' % (mn, mem(64))
        return 'push %d' % imm(32) if mn == 'push' else 'pop %s' % rng.choice(R64)
    if k < 0.72:
        mn = rng.choice(['movzx', 'movsx', 'movsxd'])
        if mn == 'movsxd': return 'movsxd %s, %s' % (reg(64), reg(32) if rng.random() < 0.5 else mem(32))
        src_w = rng.choice([8, 16]); dst_w = rng.choice([32, 64] + ([16] if src_w == 8 else []))
        return '%s %s, %s' % (mn, reg(dst_w), reg(src_w) if rng.random() < 0.5 else mem(src_w))
    if k < 0.82:
        mn = rng.choice(['shl', 'shr', 'sar', 'rol', 'ror'])
        dst = reg(w) if rng.random() < 0.6 else mem(w)
        return '%s %s, %s' % (mn, dst, rng.choice(['1', 'cl', str(rng.randrange(0, 64))]))
    if k < 0.88:
        cc = rng.choice(['e', 'ne', 'l', 'g', 'le', 'ge', 'b', 'a', 'be', 'ae', 's', 'ns', 'z', 'nz'])
        return 'set%s %s' % (cc, reg(8) if rng.random() < 0.6 else mem(8))
    if k < 0.93:
        cc = rng.choice(['a', 'e', 'ne', 'l', 'g', 'b', 'be'])
        w = rng.choice([16, 32, 64])
        return 'cmov%s %s, %s' % (cc, reg(w), reg(w) if rng.random() < 0.5 else mem())
    if k < 0.97:
        return 'xchg %s, %s' % (reg(w), reg(w) if rng.random() < 0.5 else mem())
    w = rng.choice([16, 32, 64])
    return '%s %s, %s' % (rng.choice(['bsr', 'bsf']), reg(w), reg(w) if rng.random() < 0.5 else mem())

def gnu(text, work):
    s, o, b = (os.path.join(work, x) for x in ('g.s', 'g.o', 'g.bin'))
    open(s, 'w').write('.intel_syntax noprefix\n' + text + '\n')
    if subprocess.run(['as', '-o', o, s], capture_output=True).returncode: return None
    subprocess.run(['objcopy', '-O', 'binary', '-j', '.text', o, b], check=True)
    return open(b, 'rb').read().hex()

work = tempfile.mkdtemp(prefix='relf-asmfuzz-')
cases = []
seen = set()
while len(cases) < N:
    t = instr()
    if t in seen: continue
    seen.add(t)
    h = gnu(t, work)
    if h is None: continue                       # GNU as refuses: not ours to judge
    try:
        f = forth(0, h, t)
    except Exception as e:
        cases.append((t, h, None)); continue
    cases.append((t, h, f))
lines = ['S" forth/extend.4" INCLUDED', 'S" forth/asm64.4" INCLUDED', 'ALSO ASSEMBLER',
         ': CLEAR BEGIN DEPTH WHILE DROP REPEAT ;',
         ': SHOW ( n --- ) CR ." L" . THERE @ ABUF @ ?DO I C@ . LOOP ;']
for i, (t, h, f) in enumerate(cases):
    if f: lines.append('ONLY FORTH ALSO ASSEMBLER CLEAR %d 64 ASM-BUFFER %s %d SHOW' % (0x400000, f, i))
lines.append('CR BYE')
tf = os.path.join(work, 'r.4'); open(tf, 'w').write('\n'.join(lines) + '\n')
out = subprocess.run(['./relf64', 'forth/kernel64.img'], stdin=open(tf), capture_output=True, text=True, timeout=300).stdout
got = {}
for l in out.split('\n'):
    m = re.match(r'^L(\d+)\s+(.*?)\s*$', l.strip())
    if m:
        toks = [x for x in m.group(2).split() if x != 'OK']
        if toks and all(re.match(r'^-?\d+$', x) for x in toks):
            got[int(m.group(1))] = bytes(int(x) & 255 for x in toks).hex()
def disasm(hexbytes):
    # both byte strings through objdump: the same instruction text is an
    # equivalent encoding - xchg ax, r8w as 90+r by GNU and 87 /r by relf -
    # not a wrong one
    b = os.path.join(work, 'd.bin'); open(b, 'wb').write(bytes.fromhex(hexbytes))
    o = subprocess.run(['objdump', '-D', '-b', 'binary', '-m', 'i386:x86-64', '-M', 'intel', b],
                       capture_output=True, text=True).stdout
    ins = [l.split('\t')[-1].strip() for l in o.splitlines() if re.match(r'^\s+[0-9a-f]+:\t', l)]
    return ' ; '.join(re.sub(r'\s+', ' ', i) for i in ins)
match, mism, unsup, equiv = 0, [], [], []
for i, (t, h, f) in enumerate(cases):
    g = got.get(i)
    if g is None: unsup.append(t)
    elif g == h: match += 1
    elif disasm(g) == disasm(h): equiv.append((t, h, g))
    else: mism.append((t, h, g, f))
print('%d random instructions: %d match GNU as, %d equivalent encodings, %d MISMATCH, %d not supported by asm64.4'
      % (len(cases), match, len(equiv), len(mism), len(unsup)))
for t, h, g in equiv[:4]:
    print('  equivalent %-36s gnu %-18s relf %s' % (t[:36], h, g))
for t, h, g, f in mism[:15]:
    print('  MISMATCH %-38s gnu %-22s relf %s' % (t[:38], h, g))
by = {}
for t in unsup: by[t.split()[0]] = by.get(t.split()[0], 0) + 1
print('  not supported, by mnemonic:', ' '.join('%s:%d' % kv for kv in sorted(by.items(), key=lambda kv: -kv[1])))
