#!/usr/bin/env python3
"""tools/asm-translate.py - relfasm64.S into asm64.4's syntax (SELF-HOSTING.md M2).

A one-time, mechanical translation, kept only until the Forth source is
the engine's only source (M5). Line by line, in the source's order - the
bytes must come out in GNU as's order (M3):

  .equ X, expr        expr's postfix form CONSTANT X - names kept, so the
                      result reads as a source, not as a dump
  name: / 1:          name L: / 1 L:
  an instruction      as tools/asm-test.py translates the corpus, but with
                      symbols kept: labels as label words, constants by
                      name; a forward jump GNU as made long gets NEAR
  a macro's use       its colon word (tests/relfasm64-macros.4, by hand)
  .quad .long ...     Q,A L,A ...; a label in one: Q,+ (forward too)

Every line it cannot translate yet is reported, with its number: the
measure of what M2 has left. (Iteration 546, a first version.)
"""
import ast, os, re, subprocess, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
subprocess.run(['make', '-s', 'relfasm-ops.S', 'relfasm-consts.S'], check=True)

def expand(path):                  # the #includes, textually
    out = []
    for n, line in enumerate(open(path), 1):
        m = re.match(r'\s*#include "(.*)"', line)
        if m: out += expand(m.group(1))
        else: out.append((path, n, line.rstrip('\n')))
    return out
src = expand('relfasm64.S')

# GNU as's choices, from its listing: each source line's instruction length
lst = '/tmp/translate.lst'
subprocess.run(['cc', '-c', '-Wa,-alm=' + lst, '-o', '/tmp/translate.o', 'relfasm64.S'], check=True)
REGS = set('''rax rbx rcx rdx rsi rdi rbp rsp r8 r9 r10 r11 r12 r13 r14 r15
eax ebx ecx edx esi edi ebp esp r8d r9d r10d r11d r12d r13d r14d r15d
ax bx cx dx si di bp sp r8w r9w r10w r11w r12w r13w r14w r15w
al bl cl dl sil dil bpl spl ah bh ch dh r8b r9b r10b r11b r12b r13b r14b r15b'''.split())
MACROS = {'NEXT': 'NEXT,', 'POPT': 'POPT,', 'EXITNEXT': 'EXITNEXT,', 'SLOT': 'SLOT,',
          'PUSHT': 'PUSHT,', 'RPUSH': 'RPUSH,', 'FLAG': 'FLAG,', 'SYSCALL1': 'SYSCALL1,'}
CC = {'o': 0, 'no': 1, 'b': 2, 'ae': 3, 'e': 4, 'z': 4, 'ne': 5, 'nz': 5, 'be': 6, 'a': 7,
      's': 8, 'ns': 9, 'l': 12, 'ge': 13, 'le': 14, 'g': 15}
labels = set(); consts = set()
for f, n, line in src:
    for m in re.finditer(r'^\s*([A-Za-z_][\w]*):', line): labels.add(m.group(1))
    m = re.match(r'\s*\.equ\s+([A-Za-z_]\w*)\s*,', line)
    if m: consts.add(m.group(1))

def postfix(expr):
    """An infix expression in Forth's postfix; names kept."""
    e = re.sub(r"'(.)'", lambda m: str(ord(m.group(1))), expr.strip())
    e = re.sub(r'\b0x([0-9a-fA-F]+)\b', lambda m: str(int(m.group(1), 16)), e)
    tree = ast.parse(e, mode='eval').body
    OPS = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.FloorDiv: '/', ast.Div: '/',
           ast.LShift: 'LSHIFT', ast.RShift: 'RSHIFT', ast.BitAnd: 'AND', ast.BitOr: 'OR'}
    def walk(t):
        if isinstance(t, ast.BinOp): return walk(t.left) + [walk_one(t.right)] + [OPS[type(t.op)]] if False else walk(t.left) + walk(t.right) + [OPS[type(t.op)]]
        if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.USub): return walk(t.operand) + ['NEGATE']
        if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Invert): return walk(t.operand) + ['INVERT']
        if isinstance(t, ast.Constant): return [str(t.value)]
        if isinstance(t, ast.Name): return [t.id]
        raise ValueError('expression: %s' % expr)
    def walk_one(t): return ' '.join(walk(t))
    return ' '.join(walk(tree))

def memop(text):
    size = ''
    m = re.match(r'(byte|word|dword|qword)\s+ptr\s+(.*)$', text, re.I)
    if m: size, text = m.group(1).lower() + '-ptr', m.group(2)
    inner = text.strip()[1:-1]
    parts, disp = [], []
    for sign, term in re.findall(r'([+-]?)\s*([^+-]+)', inner):
        term = term.strip()
        m = re.match(r'^(\w+)\s*\*\s*(\d+)$', term) or re.match(r'^(\d+)\s*\*\s*(\w+)$', term)
        if m and (m.group(1) in REGS or m.group(2) in REGS):
            r, k = (m.group(1), m.group(2)) if m.group(1) in REGS else (m.group(2), m.group(1))
            parts.append('%s *%s' % (r, k)); continue
        if term in REGS: parts.append(term); continue
        disp.append((sign or '+') + '(' + term + ')')
    if disp:
        parts.append(postfix(''.join(disp).lstrip('+')))
    return '[ %s ]%s' % (' '.join(parts), ' ' + size if size else '')

def operand(t):
    t = t.strip()
    if t in REGS: return t
    if '[' in t: return memop(t)
    return '%s #' % postfix(t)

out, todo = [], []
in_comment = in_macro = False
for f, n, line in src:
    # comments that span lines; macro definitions (written by hand, as
    # colon words in tests/relfasm64-macros.4) skipped whole
    t = line
    if in_comment:
        if '*/' not in t: continue
        t = t.split('*/', 1)[1]; in_comment = False
    t = re.sub(r'/\*.*?\*/', '', t)
    if '/*' in t:
        t = t.split('/*', 1)[0]; in_comment = True
    t = t.strip()
    if in_macro:
        if t.startswith('.endm'): in_macro = False
        continue
    if t.startswith('.macro'):
        in_macro = True; continue
    if not t or t.startswith('#') or t.startswith('//') or t.startswith('*'):
        continue
    words = []
    while True:                                     # labels at the front
        m = re.match(r'^([A-Za-z_][\w]*|\d+):\s*(.*)$', t)
        if not m: break
        words.append('%s L:' % m.group(1)); t = m.group(2).strip()
    try:
        if not t: pass
        elif t.startswith('.equ'):
            name, expr = re.match(r'\.equ\s+(\w+)\s*,\s*(.*)$', t).groups()
            if expr.strip().startswith('.'):
                words.append('HERE-A %s CONSTANT %s' % (postfix(expr.strip()[1:].strip().lstrip('-').strip()) + ' -' if '-' in expr else '', name))
            else:
                words.append('%s CONSTANT %s' % (postfix(expr), name))
        elif re.match(r'\.(quad|long|word|byte)\b', t):
            d, rest = re.match(r'\.(\w+)\s+(.*)$', t).groups()
            w = {'quad': 'Q,A', 'long': 'L,A', 'word': 'W,A', 'byte': 'C,A'}[d]
            for v in [x.strip() for x in rest.split(',')]:
                if v in labels and d == 'quad': words.append('%s 0 Q,+' % v)
                else: words.append('%s %s' % (postfix(v), w))
        elif re.match(r'\.(ascii|asciz)\b', t):
            d, s = re.match(r'\.(\w+)\s+"(.*)"$', t).groups()
            bs = bytes(s, 'latin1').decode('unicode_escape').encode('latin1') + (b'\0' if d == 'asciz' else b'')
            words.append(' '.join('%d C,A' % b for b in bs))
        elif re.match(r'\.(intel_syntax|text|globl|section)\b', t): pass
        elif t.startswith('.'):
            raise ValueError('directive')
        else:
            mn, _, ops = t.partition(' ')
            if mn in MACROS:
                args = [a.strip() for a in ops.split(',') if a.strip()]
                if mn == 'FLAG': words.append('%d FLAG,' % CC[args[0]])
                else: words.append(' '.join(operand(a) if a in REGS else postfix(a) for a in args) + (' ' if args else '') + MACROS[mn])
            elif mn in ('rep', 'repe', 'repne'):
                words.append('%s, %s,' % (mn, ops.strip()))
            elif re.match(r'^(j[a-z]+|call)$', mn) and '[' not in ops and ops.strip() not in REGS:
                tgt = ops.strip()
                m = re.match(r'^(\d+)([fb])$', tgt)
                words.append(('%s %s' % (m.group(1), m.group(2).upper()) if m else tgt) + ' ' + mn + ',')
            else:
                opl = [o for o in re.split(r',(?![^\[]*\])', ops) if o.strip()] if ops else []
                words.append(' '.join(operand(o) for o in opl) + (' ' if opl else '') + mn + ',')
    except Exception as e:
        todo.append((f, n, line.strip(), str(e)))
        words.append('\\ TODO %s' % line.strip())
    if words: out.append('  '.join(words))
open('/tmp/relfasm64.4', 'w').write('\n'.join(out) + '\n')
print('%d source lines -> %d Forth lines; %d not translated yet' % (len(src), len(out), len(todo)))
for f, n, line, e in todo[:25]:
    print('  %s:%d  %-50s %s' % (f, n, line[:50], e[:40]))
print('labels %d, constants %d' % (len(labels), len(consts)))
