import re, json, collections
ROOT = '/home/claude/relf/'
eff = {k: tuple(v) for k, v in json.load(open('/tmp/relf-stack-effects.json'))['eff'].items()}
prim = {  # (in, out) of the kernel's primitives and common words
 'DUP': (1, 2), 'DROP': (1, 0), 'SWAP': (2, 2), 'OVER': (2, 3), 'ROT': (3, 3), '-ROT': (3, 3), 'NIP': (2, 1), 'TUCK': (2, 3),
 '2DUP': (2, 4), '2DROP': (2, 0), '2SWAP': (4, 4), '2OVER': (4, 6), '?DUP': (1, 1), 'PICK': (1, 1),
 '+': (2, 1), '-': (2, 1), '*': (2, 1), '/': (2, 1), 'MOD': (2, 1), '/MOD': (2, 2), 'AND': (2, 1), 'OR': (2, 1), 'XOR': (2, 1),
 'LSHIFT': (2, 1), 'RSHIFT': (2, 1), 'NEGATE': (1, 1), 'INVERT': (1, 1), 'ABS': (1, 1), 'MIN': (2, 1), 'MAX': (2, 1),
 '1+': (1, 1), '1-': (1, 1), '2*': (1, 1), '2/': (1, 1), 'CELLS': (1, 1), 'CELL+': (1, 1), 'CHARS': (1, 1), 'CHAR+': (1, 1), 'ALIGNED': (1, 1),
 '=': (2, 1), '<>': (2, 1), '<': (2, 1), '>': (2, 1), 'U<': (2, 1), 'U>': (2, 1), '0=': (1, 1), '0<': (1, 1), '0>': (1, 1), '0<>': (1, 1), 'WITHIN': (3, 1),
 '@': (1, 1), '!': (2, 0), 'C@': (1, 1), 'C!': (2, 0), '+!': (2, 0), 'W@': (1, 1), 'L@': (1, 1),
 '>R': (1, 0), 'R>': (0, 1), 'R@': (0, 1), 'I': (0, 1), 'J': (0, 1), 'RDROP': (0, 0), '2>R': (2, 0), '2R>': (0, 2),
 'MOVE': (3, 0), 'CMOVE': (3, 0), 'CMOVE>': (3, 0), 'FILL': (3, 0), 'COMPARE': (4, 1), 'CSTRLEN': (1, 1), 'SCAN': (3, 2),
 'STR=': (4, 1), 'CTABLE-FIND': (4, 1), 'EXECUTE': None, 'CATCH': None, 'THROW': None, 'EXIT': (0, 0), 'HERE': (0, 1), 'ALLOT': (1, 0),
 ',': (1, 0), 'C,': (1, 0), 'COUNT': (1, 2), 'TYPE': (2, 0), 'EMIT': (1, 0), 'CR': (0, 0), 'TRUE': (0, 1), 'FALSE': (0, 1), 'BL': (0, 1),
 'IF': (1, 0), 'WHILE': (1, 0), 'UNTIL': (1, 0), 'ELSE': (0, 0), 'THEN': (0, 0), 'BEGIN': (0, 0), 'REPEAT': (0, 0), 'AGAIN': (0, 0),
 'DO': (2, 0), '?DO': (2, 0), 'LOOP': (0, 0), '+LOOP': (1, 0), 'LEAVE': (0, 0), 'UNLOOP': (0, 0), 'RECURSE': None,
 'S"': (0, 2), '."': (0, 0), 'ABORT"': (1, 0), 'C"': (0, 1), "[']": (0, 1), "'": (0, 1), '[CHAR]': (0, 1), 'CHAR': (0, 1), 'LITERAL': (1, 0),
 'ALLOCATE': (1, 2), 'FREE': (1, 1), 'RESIZE': (2, 2), 'UM*': (2, 2), 'UM/MOD': (3, 2), 'M*': (2, 2), 'S>D': (1, 2), 'D>S': (2, 1),
 'ON': (1, 0), 'OFF': (1, 0), 'STATE': (0, 1), 'BASE': (0, 1), 'SP@': (0, 1), 'RP@': (0, 1),
}
words = set(eff) | set(prim)
# variables, constants, buffers: a push of one cell
consts = set()
for f in ['forth/kernel.4', 'forth/kernel-native.4', 'forth/extend.4', 'forth/safety.4', 'forth/pool.4', 'forth/shadow.4', 'shell/shell.4', 'shell/edit.4', 'shell/tree.4']:
    for m in re.finditer(r'(?:^|\s)(?:VARIABLE|CONSTANT|VALUE|CREATE|BUFFER:|2VARIABLE)\s+(\S+)', open(ROOT + f).read()):
        consts.add(m.group(1).upper())
below = collections.Counter(); sites = 0; simulated = 0; bodies = 0; aborted = 0
argsin = collections.Counter()
for f in ['forth/kernel.4', 'forth/kernel-native.4', 'forth/extend.4', 'forth/safety.4', 'forth/pool.4', 'forth/shadow.4', 'shell/shell.4', 'shell/edit.4', 'shell/tree.4']:
    text = open(ROOT + f).read()
    for m in re.finditer(r'(?m)^:\s+(\S+)\s+(.*?)(?=^:\s|\Z)', text, re.S):
        name = m.group(1).upper(); body = m.group(2)
        if name not in eff: continue
        bodies += 1
        code = re.sub(r'\\ [^\n]*|\\\n', ' ', body); code = re.sub(r'\( [^)]*\)', ' ', code)
        code = re.sub(r'(S|\.|C|ABORT)" [^"]*"', r'\1"', code)
        toks = code.split(';')[0].upper().split()
        depth = eff[name][0]; ok = True; local = []
        for t in toks:
            if re.fullmatch(r'-?\d+|\$[0-9A-F]+', t) or t in consts: depth += 1; continue
            e = prim.get(t, eff.get(t, 'unknown'))
            if e is None or e == 'unknown': ok = False; break
            if t in eff and t not in prim:          # a call to a colon word
                live = depth - e[0]
                if live < 0: ok = False; break
                local.append((live, e[0]))
            depth += e[1] - e[0]
            if depth < 0: ok = False; break
        if ok:
            simulated += 1
            for live, a in local: below[min(live, 6)] += 1; argsin[min(a, 4)] += 1; sites += 1
        else: aborted += 1
print('%d words with effects; %d simulated to their end, %d stopped (an unknown word, EXECUTE, a depth below zero)' % (bodies, simulated, aborted))
print('%d call sites in them; cells live below the callee\'s arguments (kept across the call):' % sites)
acc = 0
for k in sorted(below):
    acc += below[k]; print('  %s%d: %5d  %5.1f %%  (cumulative %5.1f %%)' % ('>=' if k == 6 else '  ', k, below[k], 100.0 * below[k] / sites, 100.0 * acc / sites))
print('the callee\'s inputs at those sites:', dict(sorted(argsin.items())))
