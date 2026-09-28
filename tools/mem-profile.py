#!/usr/bin/env python3
"""tools/mem-profile.py - where a shell's resident memory goes (Iteration 545).

Each shell dumps its own /proc/PID/smaps - idle, and after running
tests/bench-vm/realistic.sh in the same process - and the resident pages
(Rss) are grouped by what they belong to: the executable, the C library,
the loader, the heap, the stack, and anonymous mappings (for relf: its
memory region - dictionary and stacks - and its allocator's heap).
"""
import os, re, subprocess, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
SHELLS = [('relf, assembly engine', './relfshasm64'), ('relf, C engine', './relfsh64'),
          ('dash', '/usr/bin/dash'), ('busybox ash', '/usr/bin/busybox ash'), ('bash', '/usr/bin/bash')]
# A STATIC dash beside them (Iteration 576): the comparison that is fair
# to relfsh on its own engine, which maps no C library either - a review
# built one with musl and found it about as small. STATIC_DASH=path adds it.
import os as _os
if _os.environ.get('STATIC_DASH'):
    SHELLS.insert(3, ('dash, static (musl)', _os.environ['STATIC_DASH']))
def smaps(cmd, work):
    out = '/tmp/memprof.smaps'
    pre = '. tests/bench-vm/realistic.sh >/dev/null 2>&1; ' if work else ''
    # the trailing : keeps cat a child - a shell may exec its last command,
    # and then cat reports its own memory (the first version's idle rows)
    subprocess.run(cmd.split() + ['-c', pre + 'cat /proc/$$/smaps > %s; :' % out], check=True, timeout=120)
    cats = collections.Counter(); priv = 0; name = ''; size = 0
    for line in open(out):
        m = re.match(r'^[0-9a-f]+-[0-9a-f]+ \S+ \S+ \S+ \S+\s*(.*)$', line)
        if m: name = m.group(1).strip(); continue
        m = re.match(r'^Size:\s+(\d+) kB', line)
        if m: size = int(m.group(1)); continue
        m = re.match(r'^Private_(?:Clean|Dirty):\s+(\d+) kB', line)
        if m: priv += int(m.group(1)); continue
        m = re.match(r'^Rss:\s+(\d+) kB', line)
        if not m: continue
        rss = int(m.group(1))
        if not name: k = 'anonymous, %s' % ('large (%d MB reserved)' % (size // 1024) if size >= 1024 else 'small')
        elif name.startswith('['): k = name
        elif 'libc' in name: k = 'C library'
        elif 'ld-linux' in name: k = 'loader'
        elif '/lib' in name: k = 'other libraries'
        else: k = 'the executable'
        cats[k] += rss
    return cats, priv
for label, cmd in SHELLS:
    for work in (False, True):
        c, priv = smaps(cmd, work)
        print('%-22s %-6s resident %5d kB, private %5d kB: %s' % (label, 'worked' if work else 'idle', sum(c.values()), priv,
              ', '.join('%s %d' % kv for kv in sorted(c.items(), key=lambda kv: -kv[1]) if kv[1])))
