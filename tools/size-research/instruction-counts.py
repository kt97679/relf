import struct, subprocess, collections, re, sys, tempfile
def count(path_bin, start, length, vma):
    out = subprocess.run(['objdump', '-D', '-b', 'binary', '-m', 'i386:x86-64', '--adjust-vma=%d' % vma,
                          '--start-address=%d' % vma, '--stop-address=%d' % (vma + length), path_bin],
                         capture_output=True, text=True).stdout
    n = 0; total = 0; mn = collections.Counter()
    for l in out.split('\n'):
        m = re.match(r'\s+[0-9a-f]+:\t((?:[0-9a-f]{2} )+)\s*\t(\S+)', l)
        if m:
            b = len(m.group(1).split()); n += 1; total += b; mn[m.group(2)] += 1
    return n, total, mn
# the native shell: its code segment from N_BASE (as native-budget.py), the whole of it
d = open('/home/claude/relf/relfsh-native', 'rb').read()
phoff, = struct.unpack_from('<Q', d, 32); phnum, = struct.unpack_from('<H', d, 56)
segs = [struct.unpack_from('<IIQQQQQQ', d, phoff + 56 * k) for k in range(phnum)]
segs = [(s[3], s[2], s[5]) for s in segs if s[0] == 1 and s[5]]
N_BASE = 0x401000
(cv, coff, cfz), = [s for s in segs if s[0] <= N_BASE < s[0] + s[2]]
tmp = tempfile.mktemp(); open(tmp, 'wb').write(d[coff + (N_BASE - cv): coff + cfz])
# words' code only would need the headers skipped; count all, headers decode as junk - so use the budget's word code total instead
n, b, mn = count(tmp, 0, cfz - (N_BASE - cv), N_BASE)
print('native code segment: %d bytes disassembled into %d instructions, %.2f bytes each (headers included as junk)' % (b, n, b / n))
print('  most common:', ', '.join('%s %d' % kv for kv in mn.most_common(12)))
# dash's .text
out = subprocess.run(['objdump', '-d', '/tmp/sz/dash-0.5.12/src/dash'], capture_output=True, text=True).stdout
n = 0; total = 0; mn = collections.Counter(); sect = None
for l in out.split('\n'):
    if l.startswith('Disassembly of section'): sect = l.split()[-1].rstrip(':')
    m = sect == '.text' and re.match(r'\s+[0-9a-f]+:\t((?:[0-9a-f]{2} )+)\s*\t(\S+)', l)
    if m: n += 1; total += len(m.group(1).split()); mn[m.group(2)] += 1
print('dash .text: %d bytes in %d instructions, %.2f bytes each' % (total, n, total / n))
print('  most common:', ', '.join('%s %d' % kv for kv in mn.most_common(12)))
