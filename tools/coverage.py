#!/usr/bin/env python3
"""tools/coverage.py - which instructions of the shell image the tests run.

    tools/coverage.py [COMMAND...]          the suites (or the COMMANDs), then the report
    tools/coverage.py --probe SCRIPT WORD...  one script, on a fresh map: what it runs of each
                                              WORD that the suites' map did not
    tools/coverage.py --show WORD...        each WORD's instructions, + run and - not, from
                                              the suites' map

Builds a coverage engine from engine/cv8.c: every dispatch marks its instruction
in a byte map, a file mapped MAP_SHARED so forked children mark it too. Runs
each COMMAND (default: every suite below) with THIS_SH and RELFSH pointing at
that engine made a shell, then decodes the shell image with tools/image-audit.py
and reports, for every source's colon definitions, which were never entered and
how many instructions ran. Written in Iteration 262; the numbers it gave then
are in PROGRESS.md.

Since Iteration 958: the build and the suites' map are kept in COVERAGE_DIR
(default /tmp/relf-coverage), so --probe and --show need no second run; a suite
that fails says which file; and a word never entered is told by kind -
CALLED (the image calls it: a test is missing), XT (reached by an execution
token, ' or IS: a test is missing), INLINED (no call to it: the inliner copied
its body into its callers, and those ran) or UNUSED (nothing in the image uses
it: a word the forth builtin offers, for a Forth test to check).
"""
import contextlib, glob, io, os, re, subprocess, sys, textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
WORK = os.environ.get('COVERAGE_DIR', '/tmp/relf-coverage')
ENGINE, BITMAP = os.path.join(WORK, 'relf-cov'), os.path.join(WORK, 'cov.bin')
SUITE_MAP, SHELL = os.path.join(WORK, 'cov-suites.bin'), os.path.join(WORK, 'relfsh')
# Every source, in the order the shell image loads them (Iteration 553:
# before, shell.4 and tree.4 only): a word defined twice is credited to
# the later file, whose definition the image's name finds.
SOURCES = ('forth/kernel.4', 'forth/extend.4', 'forth/safety.4', 'forth/pool.4', 'forth/shadow.4',
           'forth/save-system.4', 'shell/shell.4', 'shell/edit.4', 'shell/tree.4')

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

def build():
    os.makedirs(WORK, exist_ok=True)
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
do_call:''' % BITMAP)
    open(os.path.join(WORK, 'cov.c'), 'w').write(src)
    subprocess.run(['cc', '-O2', '-I', os.path.join(ROOT, 'engine'), '-o', ENGINE, os.path.join(WORK, 'cov.c')], check=True)
    # The instrumented engine as a shell of its own (tools/embed.sh): since
    # Iteration 506 relfsh is a binary, so the suites are pointed at this
    # one through THIS_SH and RELFSH, and a command's ./relfsh is replaced.
    subprocess.run(['sh', 'tools/embed.sh', ENGINE, 'kernel64-shell.img', SHELL], check=True)
    # the image the map is for: --probe and --show refuse another
    subprocess.run(['cp', 'kernel64-shell.img', os.path.join(WORK, 'image')], check=True)

def decode():
    """The image's words: their instruction starts, the calls, the names by address."""
    audit = open('tools/image-audit.py').read()
    audit = patch(audit, "    ip = xt; far_target = xt\n    while ip < end:\n        op = img[ip]",
                          "    ip = xt; far_target = xt\n    STARTS[name] = []\n    while ip < end:\n        STARTS[name].append(ip)\n        op = img[ip]")
    audit = patch(audit, "CALLS=[]; SLOTS=[];", "CALLS=[]; SLOTS=[]; STARTS={};")
    # __file__ for image-audit.py, which finds opcodes.tab by it since
    # Iteration 518 - exec'd without it, this failed until 527
    g = {'__file__': os.path.join(ROOT, 'tools', 'image-audit.py')}
    argv, sys.argv = sys.argv, ['image-audit', 'kernel64-shell.img', '8']
    with contextlib.redirect_stdout(io.StringIO()):
        exec(audit, g)
    sys.argv = argv
    return g

def same_image():
    p = os.path.join(WORK, 'image')
    if not os.path.exists(SUITE_MAP) or open(p, 'rb').read() != open('kernel64-shell.img', 'rb').read():
        sys.exit('coverage: no map for this kernel64-shell.img in %s - run tools/coverage.py first' % WORK)

def words_at():
    defline = {}
    for src in SOURCES:
        for i, l in enumerate(open(src).read().split('\n')):
            m = re.match(r'^: (\S+)', l)
            if m:
                defline[m.group(1)] = '%s:%d' % (src, i + 1)
    return defline

def strip_comments(t):
    t = re.sub(r'(?m)(^|\s)\\(\s.*)?$', r'\1', t)
    return re.sub(r'(^|\s)\(\s[^)]*\)', r'\1', t)

if sys.argv[1:2] == ['--show']:
    same_image(); g = decode(); cov = open(SUITE_MAP, 'rb').read()
    ops = {}
    for l in open('engine/opcodes.tab'):
        f = l.split()
        if len(f) >= 3 and not l.startswith('#') and f[1].startswith('0x'):
            ops.setdefault(int(f[1], 16), f[2])
    name_at = {v: k for k, v in g['xt_of'].items()}
    call_at = {ip: t for ip, end, t in g['CALLS']}
    for w in sys.argv[2:]:
        st = g['STARTS'][w]
        print('== %s  %d/%d run' % (w, sum(1 for s in st if cov[s]), len(st)))
        print(textwrap.fill(' '.join(('+' if cov[s] else '-') + (name_at.get(call_at[s], '?') if s in call_at
              else ops.get(g['img'][s], '%02x' % g['img'][s])) for s in st), 150))
    sys.exit(0)

if sys.argv[1:2] == ['--probe']:
    same_image(); g = decode()
    script, words = sys.argv[2], sys.argv[3:]
    open(BITMAP, 'wb').write(bytes(1 << 18))
    subprocess.run([SHELL, script], env=dict(os.environ, THIS_SH=SHELL, RELFSH=SHELL), timeout=600,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    probe, suite = open(BITMAP, 'rb').read(), open(SUITE_MAP, 'rb').read()
    for w in words:
        st = g['STARTS'][w]
        print('%-24s %4d instructions: suites %4d, probe %4d, new %4d -> %4d' % (w, len(st),
              sum(1 for a in st if suite[a]), sum(1 for a in st if probe[a]),
              sum(1 for a in st if probe[a] and not suite[a]), sum(1 for a in st if probe[a] or suite[a])))
    sys.exit(0)

build()
open(BITMAP, 'wb').write(bytes(1 << 18))
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
    # kernel's words are measured too. A file that loads sources is left
    # out (shadow.fth: pool.4 and shadow.4 land at other addresses than
    # the shell image's, and would mark what they do not run there).
    'cat tests/tester.fr %s | {engine} forth/kernel64.img > /dev/null'
        % ' '.join(f for f in sorted(glob.glob('tests/*.fth')) if 'INCLUDED' not in open(f).read()),
    # A shell image built by the instrumented engine (Iteration 554):
    # save-system.4, the locals compiler, the buffer definers and every
    # immediate word run only while an image is built. A build is
    # deterministic, so the code it runs sits where the image has it.
    'sh tools/build-shell-image.sh {engine} forth/kernel64.img {work}/built.img forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 shell/shell.4 shell/edit.4 shell/tree.4 && cmp {work}/built.img kernel64-shell.img && echo built: identical',
]
commands = [c.replace('./relfsh', SHELL).replace('{engine}', ENGINE).replace('{work}', WORK) for c in commands]
# RELF_BIN too (958): the tests that run the bare engine - run-engine-stacks,
# run-coverage-958's KEY - ran relf64, and nothing they reached was counted
env = dict(os.environ, THIS_SH=SHELL, RELFSH=SHELL, RELF_BIN=ENGINE, RELF_IMG=os.path.join(ROOT, 'forth/kernel64.img'))
# HUP, INT and QUIT back to their defaults for the suites (958): run under
# nohup, or in the background, every shell below inherited them ignored - a
# signal ignored on entry cannot be taken back - and run-special-error's
# `kill -HUP $$` and `kill -QUIT $$` did nothing.
import signal
def default_hup():
    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGQUIT):
        signal.signal(sig, signal.SIG_DFL)
for c in commands:
    r = subprocess.run(c, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                       errors='replace', preexec_fn=default_hup)
    out = r.stdout.strip().splitlines()
    print(f'ran: {c}  ({out[-1] if out else ""})')
    # which file failed (958): the shell suite's last line says only how many
    for l in out:
        if re.match(r'^(FAIL|.*[1-9][0-9]* failed \()', l):
            print('    ' + l[:200])
subprocess.run(['cp', BITMAP, SUITE_MAP], check=True)

g = decode(); cov = open(SUITE_MAP, 'rb').read(); defline = words_at()
calls = {}
for ip, end, t in g['CALLS']:
    calls.setdefault(t, 0); calls[t] += 1
text = ' '.join(strip_comments(open(s).read()) for s in SOURCES)
def kind(n):
    xt = g['xt_of'][n]
    if calls.get(xt): return 'CALLED'
    if re.search(r"(?:\['\]|')\s+" + re.escape(n) + r"(?=\s)", text): return 'XT'
    uses = len(re.findall(r'(?<!\S)' + re.escape(n) + r'(?!\S)', text)) - 1
    return 'INLINED' if uses > 0 else 'UNUSED'
rows = []
for n, starts in g['STARTS'].items():
    if n in defline and starts:
        rows.append((defline[n], n, sum(1 for s in starts if cov[s]), len(starts)))
hit = sum(r[2] for r in rows); tot = sum(r[3] for r in rows)
never = sorted((l, n) for l, n, h, t in rows if cov[g['xt_of'][n]] == 0)
kinds = {}
for l, n in never:
    kinds.setdefault(kind(n), []).append((l, n))
print(f'\nall sources: {len(rows)} colon words, {len(never)} never entered '
      f'({", ".join("%s %d" % (k, len(v)) for k, v in sorted(kinds.items()))}); '
      f'instructions run {hit}/{tot} = {hit * 100 // tot}%')
for src in SOURCES:
    rs = [r for r in rows if r[0].startswith(src + ':')]
    if rs:
        h = sum(r[2] for r in rs); t = sum(r[3] for r in rs)
        nv = sum(1 for l, n, _, _ in rs if cov[g['xt_of'][n]] == 0)
        print(f'  {src:20} {len(rs):4} words, {nv:3} never entered, instructions {h}/{t} = {h * 100 // t}%')
for k in ('CALLED', 'XT', 'UNUSED', 'INLINED'):
    for l, n in kinds.get(k, []):
        print(f'  never entered, {k:7}  {l:24}  {n}')
part = sorted(((t - h, t, l, n) for l, n, h, t in rows if 0 < h < t), reverse=True)
print(f'partly run: {len(part)} words, {sum(p[0] for p in part)} instructions in them not run; the most:')
for m, t, l, n in part[:int(os.environ.get('COVERAGE_TOP', '25'))]:
    print(f'  {m:4}/{t:4}  {l:24}  {n}')
