import struct, subprocess, re, tempfile, collections
d = open('/home/claude/relf/relfsh-native', 'rb').read()
phoff, = struct.unpack_from('<Q', d, 32); phnum, = struct.unpack_from('<H', d, 56)
segs = [struct.unpack_from('<IIQQQQQQ', d, phoff + 56 * k) for k in range(phnum)]
segs = [(s[3], s[2], s[5]) for s in segs if s[0] == 1 and s[5]]
N_BASE = 0x401000
(cv, coff, cfz), = [s for s in segs if s[0] <= N_BASE < s[0] + s[2]]
tmp = tempfile.mktemp(); open(tmp, 'wb').write(d[coff + (N_BASE - cv): coff + cfz])
out = subprocess.run(['objdump', '-D', '-b', 'binary', '-m', 'i386:x86-64', '--adjust-vma=%d' % N_BASE, tmp], capture_output=True, text=True).stdout
ins = []
for l in out.split('\n'):
    m = re.match(r'\s+([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*\t(.*)', l)
    if m: ins.append((len(m.group(2).split()), m.group(3)))
def is_stack(t): return 'r15' in t
kinds = collections.Counter(); bytes_ = collections.Counter()
for k, (n, t) in enumerate(ins):
    if not is_stack(t): continue
    nxt = [x[1].split()[0] for x in ins[k + 1:k + 4]]; prv = [x[1].split()[0] for x in ins[max(0, k - 3):k]]
    if 'call' in nxt: c = 'just before a call (3 instructions)'
    elif 'call' in prv: c = 'just after a call'
    elif any(x.startswith('j') for x in nxt + prv): c = 'beside a branch'
    elif 'ret' in nxt or 'ret' in prv: c = 'beside a return'
    else: c = 'in straight code'
    kinds[c] += 1; bytes_[c] += n
tb = sum(bytes_.values())
print('instructions naming r15, the data stack: %d, %d bytes' % (sum(kinds.values()), tb))
for c, b in bytes_.most_common(): print('  %-40s %6d instr %7d bytes %5.1f %%' % (c, kinds[c], b, 100.0 * b / tb))
# the shapes: what a push before a call looks like
shapes = collections.Counter()
for k, (n, t) in enumerate(ins):
    if t.startswith('call'):
        pre = ' ; '.join(re.sub(r'0x[0-9a-f]+', 'N', x[1]) for x in ins[max(0, k - 3):k])
        shapes[pre] += 1
print('the three instructions before a call, most common:')
for s, c in shapes.most_common(8): print('  %5d  %s' % (c, s[:110]))
