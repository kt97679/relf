#!/usr/bin/env python3
"""tools/native-budget.py [SHELL] [TOP] - where a native image's bytes go
(GOALS.md 9, Iteration 686): the first step of asking why the native
shell is as big as it is.

Reads the ELF (default ./relfsh-native): the code segment from N_BASE and
the data segment. Walks the dictionary as tools/native-prof.py does, but
keeps each header's start - its link (one to three bytes, read backward
from the name), the count byte and the name - so the code segment splits
into the runtime before the first header, the headers, and each word's
code, from its xt to the next header. Then objdump disassembles the code
and every instruction is put in one class:
  call     call rel32 - a word or routine not inlined
  stack    any instruction naming rbp - the data stack in memory: the
           pushes and pops a cell in rbx costs, folded or not
  literal  an immediate into rbx or ebx - a pushed constant's load
  branch   jmp and jcc
  return   ret
  data     bytes a forward jmp steps over and a later rip-relative lea
           points into - S" laid inline (666) - not instructions at all
  other    the rest: arithmetic, memory, register moves
Prints the totals, the classes, and the TOP (default 25) words by code
bytes with their classes.
"""
import bisect, collections, os, re, struct, subprocess, sys, tempfile

N_BASE = 0x401000
path = sys.argv[1] if len(sys.argv) > 1 else 'relfsh-native'
top = int(sys.argv[2]) if len(sys.argv) > 2 else 25
d = open(path, 'rb').read()
phoff, = struct.unpack_from('<Q', d, 32); phnum, = struct.unpack_from('<H', d, 56)
segs = [struct.unpack_from('<IIQQQQQQ', d, phoff + 56 * k) for k in range(phnum)]
segs = [(s[3], s[2], s[5]) for s in segs if s[0] == 1 and s[5]]       # vaddr, offset, filesz
(cv, coff, cfz), = [s for s in segs if s[0] <= N_BASE < s[0] + s[2]]
code_end = cv + cfz                                                    # the code's last byte, as laid
data_bytes = sum(fz for v, _, fz in segs if v >= code_end)
img = bytearray(max(v + fz for v, _, fz in segs) - N_BASE)
for v, off, fz in segs:
    lo = max(v, N_BASE)
    img[lo - N_BASE: v + fz - N_BASE] = d[off + lo - v: off + fz]

# the dictionary: FORTH-WORDLIST's 32 heads, each chain followed by links
name = b'FORTH-WORDLIST'
i = img.find(bytes([0x80 | len(name)]) + name)
if i < 0:
    sys.exit('native-budget: no FORTH-WORDLIST header in %s' % path)
xt0 = i + 1 + len(name)
heads = struct.unpack_from('<33q', img, struct.unpack_from('<I', img, xt0 + 11)[0] - N_BASE)[1:]
def link(nfa):                         # (the previous name, the link's bytes)
    tag = img[nfa - 1]
    if tag & 0x80 == 0:
        dist, ln = tag, 1
    elif tag & 0x40 == 0:
        dist, ln = ((tag & 0x3F) << 8) | img[nfa - 2], 2
    else:
        dist, ln = ((tag & 0x3F) << 16) | (img[nfa - 2] << 8) | img[nfa - 3], 3
    return (nfa - dist if dist else 0), ln
words = {}                             # header start -> (name, xt)
for h in heads:
    nfa = h
    while nfa:
        n = img[nfa] & 31
        prv, ln = link(nfa)
        words.setdefault(N_BASE + nfa - ln, (img[nfa + 1:nfa + 1 + n].decode('latin-1'), N_BASE + nfa + 1 + n))
        nfa = prv
hdr_starts = sorted(words)
spans = []                             # (xt, end, name)
for k, hs in enumerate(hdr_starts):
    nm, xt = words[hs]
    end = hdr_starts[k + 1] if k + 1 < len(hdr_starts) else code_end
    spans.append((xt, end, nm))
headers = sum(words[h][1] - h for h in hdr_starts)
runtime = hdr_starts[0] - N_BASE

# S" laid inline (666): a jmp over bytes - EB n, or E9 and four - then a
# lea whose rip-relative operand points back into them. Found by bytes, not
# by the disassembly: linear disassembly runs through the string as code
# and can come out of it out of step. The ranges are masked with NOPs for
# objdump, and counted as data.
code_img = bytearray(img[:code_end - N_BASE])
data_ranges = []
p = hdr_starts[0] - N_BASE
while p < len(code_img) - 8:
    b = code_img[p]
    if b == 0xEB:
        n, hl = code_img[p + 1], 2
    elif b == 0xE9:
        n, hl = struct.unpack_from('<i', code_img, p + 1)[0], 5
    else:
        p += 1; continue
    q = p + hl + n                     # the jmp's target: SLIT,'s sub rbp,16 and mov [rbp+8],rbx,
    l = q + 8                          # then the lea back to the bytes
    if 0 < n < 4096 and l + 7 <= len(code_img) and code_img[q:q + 8] == bytes.fromhex('4883ed1048895d08') \
            and code_img[l] in (0x48, 0x4C) and code_img[l + 1] == 0x8D and code_img[l + 2] & 0xC7 == 0x05:
        disp = struct.unpack_from('<i', code_img, l + 3)[0]
        if p + hl <= l + 7 + disp < q:
            data_ranges.append((N_BASE + p + hl, N_BASE + q))
            code_img[p + hl:q] = b'\x90' * n
            p = q; continue
    p += 1

# disassembly: the code segment from N_BASE, as raw bytes
raw = tempfile.NamedTemporaryFile(delete=False)
raw.write(bytes(code_img)); raw.close()
out = subprocess.run(['objdump', '-D', '-b', 'binary', '-m', 'i386:x86-64', '--adjust-vma=%#x' % N_BASE, raw.name],
                     capture_output=True, text=True).stdout
os.unlink(raw.name)
ins = []                               # (address, length, text)
for line in out.split('\n'):
    m = re.match(r'^\s*([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*\t?(.*)$', line)
    if m:
        a = int(m.group(1), 16); n = len(m.group(2).split())
        if ins and ins[-1][0] == a:    # a long instruction's bytes go on a second line
            continue
        if ins and ins[-1][2] == '' and ins[-1][0] + ins[-1][1] == a:
            pass
        ins.append((a, n, m.group(3).strip()))
    else:
        m = re.match(r'^\s*([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*$', line)
        if m and ins:                  # continuation: the same instruction's further bytes
            a = int(m.group(1), 16)
            pa, pn, pt = ins[-1]
            if pa + pn == a:
                ins[-1] = (pa, pn + len(m.group(2).split()), pt)

dstarts = [r[0] for r in data_ranges]
def in_data(a):
    k = bisect.bisect_right(dstarts, a) - 1
    return k >= 0 and data_ranges[k][0] <= a < data_ranges[k][1]

def klass(t):
    op = t.split()[0] if t else ''
    if op.startswith('call'): return 'call'
    if op == 'ret' or op.startswith('ret'): return 'return'
    if op.startswith('j'): return 'branch'
    if '%rbp' in t or '%ebp' in t: return 'stack'
    if re.match(r'^(mov|movabs)\s+\$[^,]+,%(rbx|ebx)$', t): return 'literal'
    return 'other'

starts = [s[0] for s in spans]
per = collections.defaultdict(collections.Counter)    # word -> class -> bytes
total = collections.Counter()
for a, n, t in ins:
    if a < hdr_starts[0]:
        w = '(runtime)'
    else:
        k = bisect.bisect_right(starts, a) - 1
        if k < 0 or not (spans[k][0] <= a < spans[k][1]):
            continue                   # a header's bytes, disassembled as if code
        w = spans[k][2]
    c = 'data' if in_data(a) else klass(t)
    per[w][c] += n
    if w != '(runtime)':
        total[c] += n
# encodings: what the shortest form of each literal load and branch would save
enc = collections.Counter(); save = collections.Counter()
for a, n, t in ins:
    if a < hdr_starts[0] or in_data(a):
        continue
    m = re.match(r'^(mov|movabs)\s+\$(0x[0-9a-f]+|[0-9]+),%(rbx|ebx)$', t)
    if m:
        v = int(m.group(2), 0)
        if m.group(3) == 'rbx' and v >= 2 ** 63: v -= 2 ** 64
        enc['literal %d bytes' % n] += 1
        best = 2 if v == 0 else 5 if 0 < v < 2 ** 32 else 7 if -2 ** 31 <= v < 0 else 10
        save['literals at their shortest'] += max(0, n - best)
        continue
    m = re.match(r'^(j[a-z]+)\s+(0x[0-9a-f]+)$', t)
    if m:
        enc['%s %d bytes' % ('jmp' if m.group(1) == 'jmp' else 'jcc', n)] += 1
        off = int(m.group(2), 16) - (a + 2)
        if n > 2 and -128 <= off < 128:
            save['%s branches that fit rel8, as rel8' % ('backward' if off < 0 else 'forward')] += n - 2
    if re.search(r'(^|[^-0-9a-fx])0x0\(%rbp\)|[(,]\(%rbp\)', t) or re.search(r'\b0x0\(%rbp\)', t):
        save['[rbp+0] as a register needing none'] += 1

code = sum(e - x for x, e, _ in spans)
print('%s: %d bytes - the code segment %d (from N_BASE: the runtime %d, headers %d in %d words, '
      'code %d), the data segment %d' % (path, len(d), code_end - cv, runtime, headers, len(spans), code, data_bytes))
seen = sum(total.values())
print('\nthe words\' code by class (%d bytes classed of %d):' % (seen, code))
for c, n in total.most_common():
    print('  %-8s %8d  %5.1f %%' % (c, n, 100.0 * n / seen))
print('\nencodings:')
for k, v in sorted(enc.items()):
    print('  %-22s %6d' % (k, v))
print('saved if:')
for k, v in save.items():
    print('  %-34s %7d bytes' % (k, v))
print('\nthe %d largest words:' % top)
print('  %7s  %-28s %s' % ('bytes', 'word', 'call stack literal branch data other'))
for w, cs in sorted(per.items(), key=lambda kv: -sum(kv[1].values()))[:top]:
    print('  %7d  %-28s %s' % (sum(cs.values()), w[:28], ' '.join('%d' % cs[c] for c in ('call', 'stack', 'literal', 'branch', 'data', 'other'))))
