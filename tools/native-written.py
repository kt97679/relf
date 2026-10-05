#!/usr/bin/env python3
"""native-written.py - which pages of the native shell's image a started
shell has written, and whose data is on them (Iteration 653).

docs/NATIVE.md 11.1: tools/mem-profile.py counts the executable's resident
pages, and smaps calls every one of them private - but a page that was only
read is private there too, when no other process maps the file. This runs
BINARY -c 'sleep 2; :' (the `:` keeps sleep a child: a shell may exec its
last command), reads the image from /proc/PID/mem while the shell waits,
and compares it with the file: a page that differs was written. The words
whose bytes differ are named from the binary's own dictionary and
native-kernel.map, as tools/native-prof.py names them. And smaps' own
count of the mapping's written pages: Anonymous - a page this process
wrote was copied, and is its own - with Private_Dirty and Private_Clean
beside it. Those said 536 and 0 kB in both of a pack's runs on this VM
(657), each right after the build had written a new file - where the
bytes said 72 pages written and Anonymous 328 kB; on an older file they
say about 328 and 208. So Anonymous is the count, the bytes the check.
usage: tools/native-written.py [BINARY]          default ./relfsh-native
"""
import bisect, collections, importlib.util, os, subprocess, sys, time

BASE = 0x400000                 # the header page, then the image at N-BASE
binp = sys.argv[1] if len(sys.argv) > 1 else './relfsh-native'
spec = importlib.util.spec_from_file_location(
    'native_prof', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'native-prof.py'))
np = importlib.util.module_from_spec(spec)
spec.loader.exec_module(np)
syms = sorted(np.symbols(binp) + np.routines(binp))
addrs = [a for a, _ in syms]

def who(a):
    i = bisect.bisect_right(addrs, a) - 1
    return syms[i][1] if i >= 0 else '(before the first word)'

f = open(binp, 'rb').read()
# the file's PT_LOAD segments (672: the code's, and the data's region)
import struct
phoff, = struct.unpack_from('<Q', f, 32); phnum, = struct.unpack_from('<H', f, 56)
segs = []
for i in range(phnum):
    ptype, flags, off, vaddr, paddr, filesz, memsz, align = struct.unpack_from('<IIQQQQQQ', f, phoff + 56 * i)
    if ptype == 1:
        segs.append((vaddr, off, filesz, memsz))
p = subprocess.Popen([binp, '-c', 'sleep 2; :'])
time.sleep(0.7)
maps = []     # (lo, hi, rss, anon, dirty, clean) of each mapping inside a segment
with open('/proc/%d/smaps' % p.pid) as sm:
    cur = None
    for line in sm:
        fs = line.split()
        if '-' in fs[0] and len(fs) >= 5:
            lo, hi = (int(x, 16) for x in fs[0].split('-'))
            cur = [lo, hi, 0, 0, 0, 0] if any(v <= lo < v + m for v, _, _, m in segs) else None
            if cur: maps.append(cur)
        elif cur is not None:
            k = {'Rss:': 2, 'Anonymous:': 3, 'Private_Dirty:': 4, 'Private_Clean:': 5}.get(fs[0])
            if k: cur[k] = int(fs[1])
pages = collections.OrderedDict()
with open('/proc/%d/mem' % p.pid, 'rb') as m:
    for vaddr, off, filesz, memsz in segs:
        if not filesz:
            continue
        m.seek(vaddr)
        mem = m.read(filesz)
        for i in range(len(mem)):
            if mem[i] != f[off + i]:
                pages.setdefault((vaddr + i) // 4096, set()).add(who(vaddr + i))
p.wait()
rss = sum(x[2] for x in maps); anon = sum(x[3] for x in maps)
size = sum(m for _, _, _, m in segs)
print('%s: the image mapped %d kB, resident %d kB; written, so copied (Anonymous) %d kB, the file\'s pages %d kB'
      % (binp, sum(x[1] - x[0] for x in maps) // 1024, rss, anon, rss - anon))
print('  segments: %s' % ', '.join('%x file %d kB' % (v, fz // 1024) for v, _, fz, _ in segs))
nfile = sum((fz + 4095) // 4096 for _, _, fz, _ in segs)
print('pages whose bytes differ from the file: %d of %d (%d kB)' % (len(pages), nfile, len(pages) * 4))
words = collections.Counter(w for v in pages.values() for w in v)
print('words with bytes written: %d; words per written page: %s'
      % (len(words), ' '.join('%d:%d' % kv for kv in sorted(collections.Counter(len(v) for v in pages.values()).items()))))
for pg, v in pages.items():
    print('  %x  %s' % (pg * 4096, ' '.join(sorted(v))))
