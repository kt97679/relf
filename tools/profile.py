#!/usr/bin/env python3
"""tools/profile.py [COMMAND] - which words a workload spends its dispatches in.

Builds a counting engine from cv8.c: every dispatch increments a 32-bit
counter for its instruction, in a file mapped MAP_SHARED so forked
children count too. Runs COMMAND (default: the realistic script
PERFORMANCE.md uses) with RELF_BIN pointing at that engine, then decodes
the shell image with tools/image-audit.py and attributes the counts to
shell.4's and tree.4's colon definitions.

Same shape as tools/coverage.py, which marks instructions instead of
counting them (Iteration 365).
"""
import contextlib, io, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
def patch(text, old, new):
    """Replace old, which must occur exactly once. str.replace does nothing
    when its text is missing, and a miss here once built an engine that
    did not compile: Iteration 490 removed an unused macro from cv8.c
    that this tool's pattern still named (found at 495)."""
    n = text.count(old)
    if n != 1:
        sys.exit('%s: the text to patch occurs %d times, not once:\n%s'
                 % (sys.argv[0], n, old[:300]))
    return text.replace(old, new)

work = tempfile.mkdtemp(prefix='relf-prof-')
engine, counts = os.path.join(work, 'relf-prof'), os.path.join(work, 'counts.bin')

SLOTS = 1 << 18
src = open('cv8.c').read()
src = patch(src, '''#define PROF(k)
#define PROFIP(a)
#define PROFDUMP''', '''#include <sys/mman.h>
static unsigned int *prof_map;
static UNS64 prof_base;
#define PROF(k)
#define PROFIP(a) (prof_map[((a) - prof_base) & 0x3FFFF]++)
#define PROFDUMP''')
src = patch(src, '    NEXT();\ndo_call:', '''    prof_base = cbase;
    { int fd = open("%s", O_RDWR);
      prof_map = mmap(0, %d * sizeof(unsigned int),
                      PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
      close(fd); }
    NEXT();
do_call:''' % (counts, SLOTS))
open(os.path.join(work, 'prof.c'), 'w').write(src)
subprocess.run(['cc', '-O2', '-o', engine, os.path.join(work, 'prof.c')], check=True)
open(counts, 'wb').write(bytes(SLOTS * 4))

# The counting engine, made a shell of its own with the shell image in
# it (tools/embed.sh). Until Iteration 506 relfsh was a script, and
# RELF_BIN told it which engine to run; it is a binary now, so the
# command's ./relfsh is this one, and the suites find it in THIS_SH.
shell = os.path.join(work, 'relfsh')
subprocess.run(['sh', 'tools/embed.sh', engine, 'kernel64-shell.img', shell], check=True)
command = (sys.argv[1] if len(sys.argv) > 1 else './relfsh tests/bench-vm/realistic.sh').replace('./relfsh', shell)
env = dict(os.environ, THIS_SH=shell, RELFSH=shell)
open(counts, 'wb').write(bytes(SLOTS * 4))
r = subprocess.run(command, shell=True, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f'ran: {command}  (status {r.returncode})')

audit = open('tools/image-audit.py').read()
audit = patch(audit, "    ip = xt; far_target = xt\n    while ip < end:\n        op = img[ip]",
                      "    ip = xt; far_target = xt\n    STARTS[name] = []\n    while ip < end:\n        STARTS[name].append(ip)\n        op = img[ip]")
audit = patch(audit, "CALLS=[]; SLOTS=[];", "CALLS=[]; SLOTS=[]; STARTS={};")
g = {}
sys.argv = ['image-audit', 'kernel64-shell.img', '8']
with contextlib.redirect_stdout(io.StringIO()):
    exec(audit, g)

import array
c = array.array('I'); c.frombytes(open(counts, 'rb').read())
defline = {}
for f in ('shell.4', 'tree.4', 'edit.4'):
    for i, l in enumerate(open(f).read().split('\n')):
        m = re.match(r'^: (\S+)', l)
        if m and m.group(1) not in defline:
            defline[m.group(1)] = '%s:%d' % (f, i + 1)
rows = []
for n, starts in g['STARTS'].items():
    total = sum(c[s] for s in starts)
    if total:
        rows.append((total, n, defline.get(n, '-')))
grand = sum(r[0] for r in rows)
print(f'{grand:,} dispatches attributed, {len(rows)} words entered\n')
print(f'{"dispatches":>12}  {"share":>6}  word')
for total, n, where in sorted(rows, reverse=True)[:30]:
    print(f'{total:12,}  {total * 100 / grand:5.1f}%  {n:24} {where}')
