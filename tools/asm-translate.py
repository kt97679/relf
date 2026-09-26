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
        if isinstance(t, ast.Compare) and len(t.ops) == 1:
            op = {ast.Gt: '>', ast.Lt: '<', ast.Eq: '='}[type(t.ops[0])]
            return walk(t.left) + walk(t.comparators[0]) + [op]
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

macros_loaded = [False]
def data_item(v, d, w):
    if v in labels:                                  # an address - forward too
        return '%s 0 %s' % (v, 'Q,+' if d == 'quad' else 'L,+')
    if v in equs and v not in defined_consts:        # a constant defined later
        m = re.match(r'^(\w+)\s*-\s*(\w+)$', equs[v])
        if m and m.group(1) in labels:               # FILE_SIZE = file_end - ehdr
            return '%s %s NEGATE %s' % (m.group(1), m.group(2), 'Q,+' if d == 'quad' else 'L,+')
    return '%s %s' % (postfix(v), w)
def translate_data(t):
    d, rest = re.match(r'\.(\w+)\s+(.*)$', t).groups()
    w = {'quad': 'Q,A', 'long': 'L,A', 'word': 'W,A', 'byte': 'C,A'}[d]
    return '  '.join(data_item(v.strip(), d, w) for v in rest.split(','))

def operand(t):
    t = t.strip()
    if t in REGS: return t
    if '[' in t: return memop(t)
    return '%s #' % postfix(t)

# GNU as's jump lengths, in source order - its macro expansions (marked
# '>') left out: the hand-written macros fix their own
jl = []
for raw in open(lst, encoding='latin1'):
    m = re.match(r'^\s*\d+\s+([0-9a-f]{4})\s+([0-9A-F]+)\s*\t(.*)$', raw.rstrip('\n'))
    if not m or m.group(3).lstrip().startswith('>'): continue
    txt = re.sub(r'^\s*(?:[A-Za-z_.][\w.]*:|\d+:)\s*', '', re.sub(r'/\*.*?\*/', '', m.group(3))).strip()
    mn = txt.split(' ', 1)[0]
    ops = txt[len(mn):].strip()
    # the translator's rule: a jump to a label, not through memory or a
    # register - the first version counted `jmp qword ptr [esc_tab...]`
    # too, and every NEAR after it was taken from the wrong jump
    if re.match(r'^(j[a-z]+|call)$', mn) and '[' not in ops and ops not in REGS:
        jl.append((txt, len(m.group(2)) // 2))
jumps = iter(jl)
defined = set()                                     # labels defined so far
equs = {}                                           # .equ name -> expression
for f, n, line in src:
    m = re.match(r'\s*\.equ\s+(\w+)\s*,\s*(.*?)\s*(/\*.*)?$', line)
    if m: equs[m.group(1)] = m.group(2)
defined_consts = set()
mismatch = []                                       # the first jump the listing disagrees on
rept = None; check_n = 0; pending_if = None
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
        if not macros_loaded[0]:
            out.append('S" engine-macros.4" INCLUDED      \\ the eight macros, by hand')
            macros_loaded[0] = True
        in_macro = True; continue
    if not t or t.startswith('#') or t.startswith('//') or t.startswith('*'):
        continue
    if rept is not None:                            # .rept: collect, then unroll
        if t.startswith('.endr'):
            for _ in range(rept[0]): src_lines_out = rept[1]; out.extend(rept[1])
            rept = None
        elif t: rept[1].append(translate_data(t))
        continue
    words = []
    while True:                                     # labels at the front
        m = re.match(r'^([A-Za-z_][\w]*|\d+):\s*(.*)$', t)
        if not m: break
        words.append('%s L:' % m.group(1)); defined.add(m.group(1)); t = m.group(2).strip()
    try:
        if not t: pass
        elif t.startswith('.rept'):
            rept = (int(t.split()[1]), []); continue
        elif t.startswith('.balign'):
            words.append('%s ALIGN,' % postfix(t.split(None, 1)[1]))
        elif t.startswith('.if '):
            pending_if = postfix(t[4:])
        elif t.startswith('.error'):
            check_n += 1
            msg = re.match(r'\.error\s+"(.*)"', t).group(1)
            words.append(': CHECK-%d %s IF CR ." %s" ABORT THEN ; CHECK-%d' % (check_n, pending_if, msg, check_n))
        elif t.startswith('.endif'): pending_if = None
        elif t.startswith('.equ') and re.search(r'\b(' + '|'.join(re.escape(l) for l in labels) + r')\b', t.split(',', 1)[1]) and not all(
                x in defined for x in re.findall(r'[A-Za-z_]\w*', t.split(',', 1)[1]) if x in labels):
            words.append('\\ ' + t + '   ( a forward label: its uses are rewritten )')
        elif t.startswith('.equ'):
            name, expr = re.match(r'\.equ\s+(\w+)\s*,\s*(.*)$', t).groups()
            if expr.strip().startswith('.'):
                words.append('HERE-A %s CONSTANT %s' % (postfix(expr.strip()[1:].strip().lstrip('-').strip()) + ' -' if '-' in expr else '', name))
            else:
                words.append('%s CONSTANT %s' % (postfix(expr), name))
            defined_consts.add(name)
        elif re.match(r'\.(quad|long|word|byte)\b', t):
            d, rest = re.match(r'\.(\w+)\s+(.*)$', t).groups()
            w = {'quad': 'Q,A', 'long': 'L,A', 'word': 'W,A', 'byte': 'C,A'}[d]
            for v in [x.strip() for x in rest.split(',')]:
                words.append(data_item(v, d, w))
        elif re.match(r'\.(ascii|asciz)\b', t):
            d, s = re.match(r'\.(\w+)\s+"(.*)"$', t).groups()
            bs = bytes(s, 'latin1').decode('unicode_escape').encode('latin1') + (b'\0' if d == 'asciz' else b'')
            words.append(' '.join('%d C,A' % b for b in bs))
        elif re.match(r'\.(intel_syntax|text|globl|section)\b', t): pass
        elif t.startswith('.'):
            raise ValueError('directive')
        else:
            mn, _, ops = t.partition(' ')
            if mn in MACROS and not macros_loaded[0]:
                raise ValueError('a macro used before engine-macros.4 is loaded')
            if mn in MACROS:
                args = [a.strip() for a in ops.split(',') if a.strip()]
                if mn == 'FLAG': words.append('%d FLAG,' % CC[args[0]])
                else: words.append(' '.join(operand(a) if a in REGS else postfix(a) for a in args) + (' ' if args else '') + MACROS[mn])
            elif mn in ('rep', 'repe', 'repne'):
                words.append('%s, %s,' % (mn, ops.strip()))
            elif re.match(r'^(j[a-z]+|call)$', mn) and '[' not in ops and ops.strip() not in REGS:
                tgt = ops.strip()
                want, length = next(jumps)
                if want.split()[:2] != [mn, tgt] and not mismatch:
                    mismatch.append('source %s:%d "%s %s", listing "%s"' % (f, n, mn, tgt, want))
                m = re.match(r'^(\d+)([fb])$', tgt)
                fwd = (m and m.group(2) == 'f') or (not m and tgt not in defined)
                near = 'NEAR ' if fwd and length >= 5 and mn != 'call' else ''
                words.append(near + ('%s %s' % (m.group(1), m.group(2).upper()) if m else tgt) + ' ' + mn + ',')
            else:
                opl = [o for o in re.split(r',(?![^\[]*\])', ops) if o.strip()] if ops else []
                words.append(' '.join(operand(o) for o in opl) + (' ' if opl else '') + mn + ',')
    except Exception as e:
        todo.append((f, n, line.strip(), str(e)))
        words.append('\\ TODO %s' % line.strip())
    if words: out.append('  '.join(words))
head = ['\\ relfasm64.4 - relfasm64.S in asm64.4\'s syntax, made by tools/asm-translate.py',
        '\\ (SELF-HOSTING.md M2). Assembled by relf, it writes the engine.',
        'S" extend.4" INCLUDED  S" asm64.4" INCLUDED', 'ALSO ASSEMBLER',
        ' '.join('LABEL %s' % l for l in sorted(labels)),
        '4194304 65536 ASM-BUFFER                  \\ 0x400000: where the Makefile links it']
tail = ['END-ASM',
        ': WRITE-ENGINE ( c-addr u --- )',
        '  2DUP W/O CREATE-FILE THROW >R  ABUF @ THERE @ OVER - R@ WRITE-FILE THROW',
        '  R> CLOSE-FILE THROW  493 CHMOD THROW ;',
        'S" relfasm64.forth" WRITE-ENGINE', 'BYE']
def wrap(line, width=200):
    # relf reads 256 columns a line (Iteration 514): the first run's one-
    # line list of 189 LABELs was cut there, and every later line failed.
    # Forth breaks anywhere between words - a number left on the stack at a
    # line's end is still there for the next - except inside a quoted
    # string (." S" parse to the quote on the same line): those stay whole.
    if len(line) <= width or '"' in line or line.lstrip().startswith('\\'): return [line]
    lines, cur = [], ''
    for tok in line.split():
        if cur and len(cur) + 1 + len(tok) > width: lines.append(cur); cur = tok
        else: cur = cur + ' ' + tok if cur else tok
    return lines + [cur]
head[4:5] = [' '.join('LABEL %s' % l for l in sorted(labels)[i:i + 6]) for i in range(0, len(labels), 6)]
final = [w for l in head + out + tail for w in wrap(l)]
long = [l for l in final if len(l) > 250]
if long: sys.exit('lines still too long for relf: %d, e.g. %s' % (len(long), long[0][:80]))
open('/tmp/relfasm64.4', 'w').write('\n'.join(final) + '\n')
print('%d source lines -> %d Forth lines; %d not translated yet' % (len(src), len(out), len(todo)))
for f, n, line, e in todo[:25]:
    print('  %s:%d  %-50s %s' % (f, n, line[:50], e[:40]))
print('labels %d, constants %d' % (len(labels), len(consts)))
print('jumps: %d in the listing; ' % len(jl) + ('first mismatch: ' + mismatch[0] if mismatch else 'every one matched'))
