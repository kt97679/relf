import re, collections, sys
ROOT = '/home/claude/relf/'
files = ['forth/kernel.4', 'forth/kernel-native.4', 'forth/extend.4', 'forth/safety.4', 'forth/pool.4', 'forth/shadow.4',
         'shell/shell.4', 'shell/edit.4', 'shell/tree.4']
eff = {}            # word -> (ins, outs) from its stack comment
bodies = {}         # word -> list of tokens in its body (colon words only)
for f in files:
    text = open(ROOT + f).read()
    for m in re.finditer(r'(?m)^:\s+(\S+)\s+(.*?)(?=^:\s|\Z)', text, re.S):
        name = m.group(1).upper(); body = m.group(2)
        c = re.match(r'\(\s*([^)]*?)\s*---?\s*([^)]*?)\s*\)', body)
        if c:
            ins = [x for x in c.group(1).split() if x not in ('"name"',)]
            outs = c.group(2).split()
            if '|' not in c.group(1) + c.group(2):          # skip alternatives like ( x --- 0 | y )
                eff[name] = (len(ins), len(outs))
        code = re.sub(r'\\ [^\n]*|\\\n', ' ', body)
        code = re.sub(r'\( [^)]*\)', ' ', code)
        code = code.split(';')[0] if ';' in code else code
        bodies[name] = code.upper().split()
print('%d colon words, %d with a stack comment read' % (len(bodies), len(eff)))
ins = collections.Counter(i for i, o in eff.values()); outs = collections.Counter(o for i, o in eff.values())
print('inputs: ', dict(sorted(ins.items())))
print('outputs:', dict(sorted(outs.items())))
# call sites in the source: a token naming another colon word with a known effect
site = collections.Counter(); site_io = collections.Counter(); unknown = 0; total = 0
for w, toks in bodies.items():
    for t in toks:
        if t in bodies and t != w:
            total += 1
            if t in eff: site[eff[t][0]] += 1; site_io[eff[t]] += 1
            else: unknown += 1
print('call sites to colon words in the source: %d, effect known for %d' % (total, total - unknown))
print('  by the callee\'s inputs:', dict(sorted(site.items())))
print('  most common (in, out):', ', '.join('%s %d' % (k, v) for k, v in site_io.most_common(10)))
import json; json.dump({'eff': eff}, open('/tmp/relf-stack-effects.json', 'w'))
