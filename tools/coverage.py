#!/usr/bin/env python3
"""tools/coverage.py [COMMAND...] - which parts of shell/shell.4 and shell/tree.4 the tests run.

Builds a coverage engine from engine/cv8.c: every dispatch marks its instruction
in a byte map, a file mapped MAP_SHARED so forked children mark it too.
Runs each COMMAND (default: the shell, differential, POSIX, matrix and
mrsh suites) with RELF_BIN pointing at that engine, then decodes the
shell image with tools/image-audit.py and reports, for shell/shell.4's colon
definitions, which were never entered and how many instructions ran.
Written in Iteration 262; the numbers it gave then are in PROGRESS.md.
"""
import contextlib, io, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
def patch(text, old, new):
    """Replace old, which must occur exactly once. str.replace does nothing
    when its text is missing, and a miss here once built an engine that
    did not compile: Iteration 490 removed an unused macro from engine/cv8.c
    that this tool's pattern still named (found at 495)."""
    n = text.count(old)
    if n != 1:
        sys.exit('%s: the text to patch occurs %d times, not once:\n%s'
                 % (sys.argv[0], n, old[:300]))
    return text.replace(old, new)

work = tempfile.mkdtemp(prefix='relf-cov-')
engine, bitmap = os.path.join(work, 'relf-cov'), os.path.join(work, 'cov.bin')

src = open('engine/cv8.c').read()
src = patch(src, '''#define PROF(k)
#define PROFIP(a)
#define PROFDUMP''', '''#include <sys/mman.h>
static unsigned char *cov_map;
static UNS64 cov_base;
#define PROF(k)
#define PROFIP(a) (cov_map[((a) - cov_base) & 0x3FFFF] = 1)
#define PROFDUMP''')
src = patch(src, '    NEXT();\ndo_call:', '''    cov_base = cbase;
    { int fd = open("%s", O_RDWR);
      cov_map = mmap(0, 1 << 18, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
      close(fd); }
    NEXT();
do_call:''' % bitmap)
open(os.path.join(work, 'cov.c'), 'w').write(src)
subprocess.run(['cc', '-O2', '-I', os.path.join(ROOT, 'engine'), '-o', engine, os.path.join(work, 'cov.c')], check=True)
open(bitmap, 'wb').write(bytes(1 << 18))

commands = sys.argv[1:] or [
    'cd tests/shell && ./run-all',
    'THIS_SH=./relfsh tests/diff/run-all',
    'sh tests/posix/run.sh',
    'sh tests/matrix/run',
    'sh tests/parse/run',
    'bash tests/mrsh-suite/run.sh',
    # The pty suite, since Iteration 510: without it 18 of the 24 words
    # never entered were prompt escapes and job-control reports, which
    # only an interactive shell reaches - tested, just not counted.
    'sh tests/interactive/run',
    # The Forth suite, since Iteration 553: CORE and the extra files run
    # on kernel64.img - whose code sits at the same addresses in the
    # shell image, which is that image with the rest appended - so the
    # kernel's words are measured too. shadow.fth is left out: it loads
    # pool.4 and shadow.4 at other addresses than the shell image's.
    'cat tests/tester.fr tests/core-extra.fth tests/coreplus-loop.fth | {engine} forth/kernel64.img > /dev/null',
    # A shell image built by the instrumented engine (Iteration 554):
    # save-system.4, the locals compiler, the buffer definers and every
    # immediate word run only while an image is built. A build is
    # deterministic, so the code it runs sits where the image has it.
    'sh tools/build-shell-image.sh {engine} forth/kernel64.img {work}/built.img forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 shell/shell.4 shell/edit.4 shell/tree.4 && cmp {work}/built.img kernel64-shell.img && echo built: identical',
]
# The instrumented engine as a shell of its own (tools/embed.sh): since
# Iteration 506 relfsh is a binary, so the suites are pointed at this
# one through THIS_SH and RELFSH, and a command's ./relfsh is replaced.
shell = os.path.join(work, 'relfsh')
subprocess.run(['sh', 'tools/embed.sh', engine, 'kernel64-shell.img', shell], check=True)
commands = [c.replace('./relfsh', shell).replace('{engine}', engine).replace('{work}', work) for c in commands]
env = dict(os.environ, THIS_SH=shell, RELFSH=shell)
for c in commands:
    r = subprocess.run(c, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(f'ran: {c}  ({r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""})')

# decode the image, recording each body's instruction starts
audit = open('tools/image-audit.py').read()
audit = patch(audit, "    ip = xt; far_target = xt\n    while ip < end:\n        op = img[ip]",
                      "    ip = xt; far_target = xt\n    STARTS[name] = []\n    while ip < end:\n        STARTS[name].append(ip)\n        op = img[ip]")
audit = patch(audit, "CALLS=[]; SLOTS=[];", "CALLS=[]; SLOTS=[]; STARTS={};")
# __file__ for image-audit.py, which finds opcodes.tab by it since
# Iteration 518 - exec'd without it, this failed until 527
g = {'__file__': os.path.join(ROOT, 'tools', 'image-audit.py')}
sys.argv = ['image-audit', 'kernel64-shell.img', '8']
with contextlib.redirect_stdout(io.StringIO()):
    exec(audit, g)
cov = open(bitmap, 'rb').read()
# Every source, in the order the shell image loads them (Iteration 553:
# before, shell.4 and tree.4 only): a word defined twice is credited to
# the later file, whose definition the image's name finds.
SOURCES = ('forth/kernel.4', 'forth/extend.4', 'forth/safety.4', 'forth/pool.4', 'forth/shadow.4', 'forth/save-system.4', 'shell/shell.4', 'shell/edit.4', 'shell/tree.4')
defline = {}
for src in SOURCES:
    for i, l in enumerate(open(src).read().split('\n')):
        m = re.match(r'^: (\S+)', l)
        if m:
            defline[m.group(1)] = '%s:%d' % (src, i + 1)
rows = []
for n, starts in g['STARTS'].items():
    if n in defline and starts:
        rows.append((defline[n], n, sum(1 for s in starts if cov[s]), len(starts)))
hit = sum(r[2] for r in rows); tot = sum(r[3] for r in rows)
never = sorted((l, n) for l, n, h, t in rows if cov[g['xt_of'][n]] == 0)
print(f'\nall sources: {len(rows)} colon words, {len(never)} never entered; '
      f'instructions run {hit}/{tot} = {hit * 100 // tot}%')
for src in SOURCES:
    rs = [r for r in rows if r[0].startswith(src + ':')]
    if rs:
        h = sum(r[2] for r in rs); t = sum(r[3] for r in rs)
        nv = sum(1 for l, n, _, _ in rs if cov[g['xt_of'][n]] == 0)
        print(f'  {src:14} {len(rs):4} words, {nv:3} never entered, instructions {h}/{t} = {h * 100 // t}%')
for l, n in never:
    print(f'  never entered: {l:14}  {n}')
print('most instructions never run:')
for l, n, h, t in sorted(rows, key=lambda r: r[3] - r[2], reverse=True)[:15]:
    print(f'  {t - h:4}/{t:4}  {l:14}  {n}')
