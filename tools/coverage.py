#!/usr/bin/env python3
"""tools/coverage.py [COMMAND...] - which parts of shell.4 the tests run.

Builds a coverage engine from cv8.c: every dispatch marks its instruction
in a byte map, a file mapped MAP_SHARED so forked children mark it too.
Runs each COMMAND (default: the shell, differential, POSIX, matrix and
mrsh suites) with RELF_BIN pointing at that engine, then decodes the
shell image with tools/image-audit.py and reports, for shell.4's colon
definitions, which were never entered and how many instructions ran.
Written in Iteration 262; the numbers it gave then are in PROGRESS.md.
"""
import contextlib, io, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
work = tempfile.mkdtemp(prefix='relf-cov-')
engine, bitmap = os.path.join(work, 'relf-cov'), os.path.join(work, 'cov.bin')

src = open('cv8.c').read()
src = src.replace('''#define PROF(k)
#define PROFC(t)
#define PROFIP(a)
#define PROFDUMP''', '''#include <sys/mman.h>
static unsigned char *cov_map;
static UNS64 cov_base;
#define PROF(k)
#define PROFC(t)
#define PROFIP(a) (cov_map[((a) - cov_base) & 0x3FFFF] = 1)
#define PROFDUMP''')
src = src.replace('    NEXT();\ndo_call:', '''    cov_base = cbase;
    { int fd = open("%s", O_RDWR);
      cov_map = mmap(0, 1 << 18, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
      close(fd); }
    NEXT();
do_call:''' % bitmap, 1)
open(os.path.join(work, 'cov.c'), 'w').write(src)
subprocess.run(['cc', '-O2', '-o', engine, os.path.join(work, 'cov.c')], check=True)
open(bitmap, 'wb').write(bytes(1 << 18))

commands = sys.argv[1:] or [
    'cd tests/shell && ./run-all',
    'THIS_SH=./relfsh tests/diff/run-all',
    'sh tests/posix/run.sh',
    'sh tests/matrix/run',
    'bash tests/mrsh-suite/run.sh',
]
env = dict(os.environ, RELF_BIN=engine)
for c in commands:
    r = subprocess.run(c, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(f'ran: {c}  ({r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""})')

# decode the image, recording each body's instruction starts
audit = open('tools/image-audit.py').read()
audit = audit.replace("    ip = xt; far_target = xt\n    while ip < end:\n        op = img[ip]",
                      "    ip = xt; far_target = xt\n    STARTS[name] = []\n    while ip < end:\n        STARTS[name].append(ip)\n        op = img[ip]")
audit = audit.replace("CALLS=[]; SLOTS=[];", "CALLS=[]; SLOTS=[]; STARTS={};")
g = {}
sys.argv = ['image-audit', 'kernel-shell.img', '8']
with contextlib.redirect_stdout(io.StringIO()):
    exec(audit, g)
cov = open(bitmap, 'rb').read()
first = g['xt_of']['LINE-MAX']                     # shell.4's first word
defline = {}
for i, l in enumerate(open('shell.4').read().split('\n')):
    m = re.match(r'^: (\S+)', l)
    if m and m.group(1) not in defline:
        defline[m.group(1)] = i + 1
rows = []
for n, starts in g['STARTS'].items():
    if n in defline and g['xt_of'][n] >= first and starts:
        rows.append((defline[n], n, sum(1 for s in starts if cov[s]), len(starts)))
hit = sum(r[2] for r in rows); tot = sum(r[3] for r in rows)
never = sorted((l, n) for l, n, h, t in rows if cov[g['xt_of'][n]] == 0)
print(f'\nshell.4: {len(rows)} colon words, {len(never)} never entered; '
      f'instructions run {hit}/{tot} = {hit * 100 // tot}%')
for l, n in never:
    print(f'  never entered: line {l:5}  {n}')
print('most instructions never run:')
for l, n, h, t in sorted(rows, key=lambda r: r[3] - r[2], reverse=True)[:15]:
    print(f'  {t - h:4}/{t:4}  line {l:5}  {n}')
