#!/usr/bin/env python3
"""tools/asm-test.py - M0's test: forth/asm64.4 against tests/asm-corpus.txt

Each corpus line - an instruction as relfasm64.S writes it, its address,
the bytes GNU as made - is translated into forth/asm64.4's syntax, with the
symbols' values from nm and a jump's target from its reference bytes,
and assembled by relf at the same address; the bytes are compared.
(Iteration 541.)
"""
import os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ENGINE = next((a for a in sys.argv[1:] if not a.startswith('-')), './relf64')
# The corpus is FROZEN since Iteration 549: made from GNU as's listing of
# relfasm64.S, which retired when relfasm64.4 became the engine's source
# (SELF-HOSTING.md M5); its symbols' values frozen beside it. The encoder
# is still held to GNU as's bytes, shape by shape.
work = tempfile.mkdtemp(prefix='relf-asmtest-')
sym = {}
for line in open('tests/asm-corpus-symbols.txt'):
    name, value = line.split()
    sym[name] = int(value)
REGS = set('''rax rbx rcx rdx rsi rdi rbp rsp r8 r9 r10 r11 r12 r13 r14 r15
eax ebx ecx edx esi edi ebp esp r8d r9d r10d r11d r12d r13d r14d r15d
ax bx cx dx si di bp sp r8w r9w r10w r11w r12w r13w r14w r15w
al bl cl dl sil dil bpl spl ah bh ch dh r8b r9b r10b r11b r12b r13b r14b r15b'''.split())

def value(expr):
    e = re.sub(r"'(.)'", lambda m: str(ord(m.group(1))), expr)                # 'c'
    e = re.sub(r'0x[0-9a-fA-F]+', lambda m: str(int(m.group(0), 16)), e)      # hex first
    e = re.sub(r'(?<![0-9])[A-Za-z_][\w]*', lambda m: str(sym[m.group(0)]), e)
    return int(eval(e.replace('/', '//')))

def memop(text):
    size = ''
    m = re.match(r'(byte|word|dword|qword)\s+ptr\s+(.*)$', text, re.I)
    if m: size, text = m.group(1).lower() + '-ptr', m.group(2)
    inner = text.strip()[1:-1]
    parts, disp = [], 0
    for sign, term in re.findall(r'([+-]?)\s*([^+-]+)', inner):
        term = term.strip()
        m = re.match(r'^(\w+)\s*\*\s*(\d+)$', term) or re.match(r'^(\d+)\s*\*\s*(\w+)$', term)
        if m and (m.group(1) in REGS or m.group(2) in REGS):
            r, k = (m.group(1), m.group(2)) if m.group(1) in REGS else (m.group(2), m.group(1))
            parts.append('%s *%s' % (r, k)); continue
        if term in REGS:
            parts.append(term); continue
        disp += -value(term) if sign == '-' else value(term)
    if disp: parts.append(str(disp))
    return '[ %s ]%s' % (' '.join(parts), ' ' + size if size else '')

def operand(t):
    t = t.strip()
    if t in REGS: return t
    if '[' in t: return memop(t)
    return '%d #' % value(t)

def forth(addr, hexbytes, text):
    mn, _, ops = text.partition(' ')
    if mn in ('rep', 'repe', 'repne'):                 # a prefix, then its instruction
        return '%s, %s,' % (mn, ops.strip())
    if re.match(r'^(j[a-z]+|call)$', mn) and '[' not in ops and ops.strip() not in REGS:
        n = len(hexbytes) // 2
        rel = int.from_bytes(bytes.fromhex(hexbytes)[-4 if n > 2 else -1:], 'little', signed=True)
        return '%d %s,' % (addr + 0x400000 + n + rel, mn)
    ops = [o for o in re.split(r',(?![^\[]*\])', ops) if o.strip()] if ops else []
    return ' '.join(operand(o) for o in ops) + (' ' if ops else '') + mn + ','

lines = [l.rstrip('\n') for l in open('tests/asm-corpus.txt') if not l.startswith('#')]
cases, src = [], ['S" forth/extend.4" INCLUDED', 'S" forth/asm64.4" INCLUDED', 'ALSO ASSEMBLER',
                  ': CLEAR BEGIN DEPTH WHILE DROP REPEAT ;',
                  ': SHOW ( n --- ) CR ." L" . THERE @ ABUF @ ?DO I C@ . LOOP ;']
for i, l in enumerate(lines):
    a, h, t = l.split(None, 2)
    try:
        f = forth(int(a, 16), h, t)
    except Exception as e:
        cases.append((t, h, None, 'untranslated: %s' % e)); continue
    cases.append((t, h, f, None))
    src.append('CLEAR %d 0 ASM-BUFFER %s %d SHOW' % (0x400000 + int(a, 16), f, len(cases) - 1)
               if False else 'ONLY FORTH ALSO ASSEMBLER CLEAR %d 64 ASM-BUFFER %s %d SHOW' % (0x400000 + int(a, 16), f, len(cases) - 1))
    # (each line sets the search order itself: relf's error recovery resets
    # it, so after the first unwritten mnemonic every later line lost the
    # assembler's words - the first run's 8 of 453, Iteration 541)
src.append('CR BYE')
tf = os.path.join(work, 't.4')
open(tf, 'w').write('\n'.join(src) + '\n')
out = subprocess.run([ENGINE, 'forth/kernel64.img'], stdin=open(tf), capture_output=True, text=True, timeout=120).stdout
got = {}
for l in out.split('\n'):
    m = re.match(r'^L(\d+)\s+(.*?)\s*$', l.strip())
    if m:
        toks = [x for x in m.group(2).split() if x != 'OK']    # relf's prompt
        if all(re.match(r'^-?\d+$', x) for x in toks):
            got[int(m.group(1))] = bytes(int(x) & 255 for x in toks).hex()
        else:
            got[int(m.group(1))] = 'garbled: ' + ' '.join(toks)[:30]
ok = 0; bad = []
for i, (t, h, f, err) in enumerate(cases):
    if err: bad.append((t, h, '', err)); continue
    if got.get(i) == h: ok += 1
    else: bad.append((t, h, f, got.get(i, 'no output')))
print('%d of %d shapes assemble to GNU as\'s bytes' % (ok, len(cases)))
if '-v' in sys.argv or len(bad) < 40:
    for t, h, f, g in bad[:60]:
        print('  %-34s want %-18s got %-18s  %s' % (t[:34], h, g, f))

# ---- M1: one-pass labels (Iteration 545) --------------------------------
# tests/asm-labels.S assembled by GNU as, tests/asm-labels.4 by asm64.4 -
# every kind of jump, forward references resolved at their labels.
lo = os.path.join(work, 'l.o'); lb = os.path.join(work, 'l.bin')
subprocess.run(['as', '-o', lo, 'tests/asm-labels.S'], check=True)
subprocess.run(['ld', '-Ttext=0x400000', '--oformat', 'binary', '-o', lb, lo], check=True)
# (linked, as the engine is: an absolute address - the jump through a
# table defined after it - is a placeholder in an object file)
out = subprocess.run([ENGINE, 'forth/kernel64.img'], stdin=open('tests/asm-labels.4'),
                     capture_output=True, text=True, timeout=60).stdout
want = open(lb, 'rb').read()
toks = out.split('BYTES')[1].split() if 'BYTES' in out else []
got = bytes(int(x) & 255 for x in toks if x.lstrip('-').isdigit())   # not relf's OK
print('labels: %s (%d bytes)' % ('identical to GNU as' if got == want else 'DIFFER', len(want)))

# ---- M1: a whole program (Iteration 546) --------------------------------
# tests/asm-exit42.4 writes an ELF executable entirely from Forth, makes it
# executable with CHMOD, and it must exit with status 42.
exe = '/tmp/relf-exit42'
if os.path.exists(exe): os.unlink(exe)
subprocess.run([ENGINE, 'forth/kernel64.img'], stdin=open('tests/asm-exit42.4'), capture_output=True, timeout=60)
st = subprocess.run([exe]).returncode if os.access(exe, os.X_OK) else None
print('program: %s' % ('an ELF from Forth, %d bytes, exits 42' % os.path.getsize(exe) if st == 42
                       else 'FAILED (exit status %r)' % st))
