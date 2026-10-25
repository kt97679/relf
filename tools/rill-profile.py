#!/usr/bin/env python3
"""tools/rill-profile.py [--calls] PROGRAM [ARGS...] - where a Rill program's dispatches go (Iteration 768).

PROGRAM is a .rill - compiled by tools/rillc.py first, so the compiler's
own work is not counted - or a .4 already compiled. It runs on CV8 with
the counting engine tools/profile.py builds (every dispatch counted per
instruction, in a file mapped MAP_SHARED so forked children count too),
in kernel64-rill.img. The image is decoded with tools/image-audit.py and
the counts attributed to its words: each word's own instructions, not
its callees'. The program's own words - R-MAIN, its defs, compiled when
it runs - are not in the image file; their dispatches are one line, "the
program's own code", with the outer interpreter's work on its text in
the kernel's words above it.

--calls adds how often each word is called: every call site's
dispatches, summed by the word called.

Phase 4 of docs/RILL-ROADMAP.md starts here: 766 and 767 each guessed a
cost and were wrong; this measures it.
"""
import array, collections, contextlib, io, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
args = sys.argv[1:]
calls_too = '--calls' in args
args = [a for a in args if a != '--calls']
if not args:
    sys.exit(__doc__)
prog, rest = args[0], args[1:]
IMG = os.environ.get('RILL_IMG', 'kernel64-rill.img')

def patch(text, old, new):
    if text.count(old) != 1:
        sys.exit('rill-profile: %d places for %r' % (text.count(old), old[:80]))
    return text.replace(old, new)

work = tempfile.mkdtemp(prefix='rill-profile-')
engine, counts, SLOTS = os.path.join(work, 'relf-count'), os.path.join(work, 'counts.bin'), 1 << 18
src = open('engine/cv8.c').read()
src = patch(src, '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP',
            '#include <sys/mman.h>\nstatic unsigned int *prof_map;\nstatic UNS64 prof_base;\n'
            '#define PROF(k)\n#define PROFIP(a) (prof_map[((a) - prof_base) & 0x3FFFF]++)\n#define PROFDUMP')
src = patch(src, '    NEXT();\ndo_call:',
            '    prof_base = cbase;\n    { int fd = open("%s", O_RDWR);\n      prof_map = mmap(0, %d * sizeof(unsigned int),\n'
            '                      PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n      close(fd); }\n    NEXT();\ndo_call:' % (counts, SLOTS))
open(os.path.join(work, 'prof.c'), 'w').write(src)
subprocess.run(['cc', '-O2', '-I', 'engine', '-o', engine, os.path.join(work, 'prof.c')], check=True)

if prog.endswith('.rill'):
    compiled = os.path.join(work, 'prog.4')
    with open(compiled, 'w') as out:
        subprocess.run(['python3', 'tools/rillc.py', prog], stdout=out, check=True)
    prog = compiled
open(counts, 'wb').write(bytes(SLOTS * 4))
r = subprocess.run([engine, IMG, prog] + rest, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
print('ran: %s %s  (status %d)' % (args[0], ' '.join(rest), r.returncode))

audit = open('tools/image-audit.py').read()
audit = patch(audit, "    ip = xt; far_target = xt\n    while ip < end:\n        op = img[ip]",
              "    ip = xt; far_target = xt\n    STARTS[name] = []\n    while ip < end:\n        STARTS[name].append(ip)\n        op = img[ip]")
audit = patch(audit, "CALLS=[]; SLOTS=[];", "CALLS=[]; SLOTS=[]; STARTS={};")
g = {'__file__': os.path.join(ROOT, 'tools', 'image-audit.py')}
sys.argv = ['image-audit', IMG, '8']
with contextlib.redirect_stdout(io.StringIO()):
    exec(audit, g)

c = array.array('I'); c.frombytes(open(counts, 'rb').read())
total = sum(c)
defline = {}
for f in ['forth/kernel.4'] + sorted(f for f in os.listdir('rill') if f.endswith('.4')):
    path = f if '/' in f else os.path.join('rill', f)
    for i, l in enumerate(open(path).read().split('\n')):
        m = re.match(r'^: (\S+)', l)
        if m and m.group(1) not in defline:
            defline[m.group(1)] = '%s:%d' % (path, i + 1)
mine = set()
rows = []
for n, starts in g['STARTS'].items():
    mine.update(starts)
    t = sum(c[s] for s in starts)
    if t:
        rows.append((t, n, defline.get(n, '-')))
image = sum(r[0] for r in rows)
print('%s dispatches: %s in the image\'s words (%d of them), %s the program\'s own code\n'
      % (format(total, ','), format(image, ','), len(rows), format(total - image, ',')))
print('%12s  %6s  word' % ('dispatches', 'share'))
for t, n, where in sorted(rows, reverse=True)[:30]:
    print('%12s  %5.1f%%  %-22s %s' % (format(t, ','), t * 100.0 / total, n, where))
print('%12s  %5.1f%%  %s' % (format(total - image, ','), (total - image) * 100.0 / total, "(the program's own code)"))
if calls_too:
    xt2name = {s[0]: n for n, s in g['STARTS'].items() if s}
    called = collections.Counter()
    for ip, nxt, tgt in g['CALLS']:
        if tgt in xt2name:
            called[xt2name[tgt]] += c[ip]
    print('\nthe most called, from the image\'s own words (the program\'s calls are not decoded):')
    for w, v in called.most_common(25):
        print('  %12s  %s' % (format(v, ','), w))
