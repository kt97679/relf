#!/usr/bin/env python3
"""port/measure/design-ops.py [SRC] - a design's opcode numbers (as its PROFILE=1 dump has them) and
names, from its src/vm.c and the tables it includes: SRC its src directory (DESIGN_SRC, default
portable-knee's). Written for portable-knee's genes - ENC=3 ESCAPE=1 SPEC=1 FOLD=1 SUPER=1 OPS10=1;
another design's need checking (DEF below, and ESCAPE 2's other band). An escaped op k is k after ESC."""
import re, os, sys
S = os.environ.get('DESIGN_SRC', '/tmp/fve/designs/portable-knee/src').rstrip('/') + '/'
src = open(S + 'vm.c').read()
a = src.index('static const void *const dispatch[] = {'); b = src.index('    };', a)
body = src[a:b]
DEF = dict(ENC=3, ESCAPE=1, SPEC=1, FOLD=1, SUPER=1, OPS10=1)
disp = {}; idx = 0; stack = [True, True, True]
def cond(expr):
    e = expr.split('/*')[0].replace('&&', ' and ').replace('||', ' or ').replace('!=', '!=')
    for k, v in DEF.items(): e = re.sub(r'\b%s\b' % k, str(v), e)
    try: return bool(eval(e))
    except Exception: return False
def take(text):
    global idx
    for m in re.finditer(r'(\[([^\]]+)\]\s*=\s*)?(DSP|FSX|FSX2|FSX3|SYSX)\((\w+)\)|(\[([^\]]+)\]\s*=\s*)?\bSYSF\b', text):
        if m.group(3):
            if m.group(2): idx = eval(m.group(2))
            disp[idx] = m.group(4); idx += 1
        else:
            if m.group(6): idx = eval(m.group(6))
            disp[idx] = 'L_fork'; idx += 1
for line in body.split('\n')[1:]:
    s = line.strip()
    if s.startswith('#if'): stack.append(stack[-1] and cond(s[3:].strip())); continue
    if s.startswith('#else'): stack[-1] = (not stack[-1]) and stack[-2]; continue
    if s.startswith('#endif'): stack.pop(); continue
    if s.startswith('#include'):
        if stack[-1]: take(open(S + s.split('"')[1]).read())
        continue
    if stack[-1] and not s.startswith('/*') and not s.startswith('*'): take(s)
n = max(disp) + 1
cv8 = {i: disp.get(i, 'L_noop') for i in range(128)}
for i in range(32): cv8[i] = disp.get(i)
for i in range(32, 36): cv8[i] = disp.get(i + 1)
for i in range(36, 68): cv8[i] = 'L_noop'
for f in ('vm-super-esc.h', 'vm-ops10-esc.h'):
    for m in re.finditer(r'cv8_tab\[(\d+)\]\s*=\s*&&(\w+);', open(S + f).read()): cv8[int(m.group(1))] = m.group(2)
esc_k = [32] + list(range(37, 68))
esc = {i: disp.get(k) for i, k in enumerate(esc_k)}
# superinstruction and ops10 bodies' own words, from their comments
desc = {}
for f in ('vm-super-bodies.h', 'vm-fold-bodies.h'):
    for m in re.finditer(r'^(\w+):\s*/\*\s*(.*?)\s*\*/', open(S + f).read(), re.M): desc[m.group(1)] = m.group(2)
def name(op):
    if op == 256: return 'CALL'
    if op >= 128: return 'call-byte'
    l = cv8.get(op) or '?'
    if l.startswith('LX_'): return l[3:] + ';EXIT'
    if l.startswith('LS_'): return desc.get(l, l)
    return l[2:]
def esc_name(k): l = esc.get(k) or '?'; return 'ESC ' + l[2:]
if __name__ == '__main__':
    for i in range(128):
        if cv8[i] != 'L_noop' or i == 0: print(i, name(i))
    for k in range(32): print('esc', k, esc_name(k))
