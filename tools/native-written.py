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
split of the executable's mapping: Private_Dirty, written; Private_Clean,
only read.
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
p = subprocess.Popen([binp, '-c', 'sleep 2; :'])
time.sleep(0.7)
size = 0; dirty = clean = 0
with open('/proc/%d/smaps' % p.pid) as sm:
    mine = False
    for line in sm:
        fs = line.split()
        if '-' in fs[0] and len(fs) >= 5:                  # a mapping's first line
            lo, hi = (int(x, 16) for x in fs[0].split('-'))
            mine = lo == BASE
            if mine: size = hi - lo
        elif mine and fs[0] == 'Private_Dirty:': dirty = int(fs[1])
        elif mine and fs[0] == 'Private_Clean:': clean = int(fs[1])
with open('/proc/%d/mem' % p.pid, 'rb') as m:
    m.seek(BASE)
    mem = m.read(size)
p.wait()
pages = collections.OrderedDict()
for off in range(len(mem)):
    if mem[off] != (f[off] if off < len(f) else 0):
        pages.setdefault(off // 4096, set()).add(who(BASE + off))
print('%s: the image mapped %d kB; smaps: written (Private_Dirty) %d kB, only read (Private_Clean) %d kB'
      % (binp, size // 1024, dirty, clean))
print('pages whose bytes differ from the file: %d of %d (%d kB)' % (len(pages), size // 4096, len(pages) * 4))
words = collections.Counter(w for v in pages.values() for w in v)
print('words with bytes written: %d; words per written page: %s'
      % (len(words), ' '.join('%d:%d' % kv for kv in sorted(collections.Counter(len(v) for v in pages.values()).items()))))
for pg, v in pages.items():
    print('  %x  %s' % (BASE + pg * 4096, ' '.join(sorted(v))))
