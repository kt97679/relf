#!/usr/bin/env python3
"""tools/cm-bench.py [ROUNDS] - the command model measured (871; tools/cm-compare.py's, which set it beside
Rill and Rill 2 at 865-870 - their numbers stay in docs/SYNTAX-GENES.md).

Builds kernel64-cm.img (tools/build-cm-image.sh) and prints its bytes; then for each program - the
benchmarks in tests/cm/bench and tests/cm/scripts/side.cm - its text (non-blank characters and words,
comment lines left out), its time to run, compiling included (ROUNDS rounds, 9 unless given: the median
and the range, in ms), and its dispatches on CV8's counting engine (tools/rill-profile.py's, built once
here): the same every run. Each program's output is checked against its .expected first.
"""
import array, glob, os, re, statistics, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 9

def counting_engine(work):
    """cv8.c with every dispatch counted into a shared file - rill-profile.py's two patches."""
    counts, slots = os.path.join(work, 'counts.bin'), 1 << 18
    src = open('engine/cv8.c').read()
    for old, new in (('#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP',
                      '#include <sys/mman.h>\nstatic unsigned int *prof_map;\nstatic UNS64 prof_base;\n'
                      '#define PROF(k)\n#define PROFIP(a) (prof_map[((a) - prof_base) & 0x3FFFF]++)\n#define PROFDUMP'),
                     ('    NEXT();\ndo_call:',
                      '    prof_base = cbase;\n    { int fd = open("%s", O_RDWR);\n      prof_map = mmap(0, %d * sizeof(unsigned int),\n'
                      '                      PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n      close(fd); }\n    NEXT();\ndo_call:'
                      % (counts, slots))):
        if src.count(old) != 1: sys.exit('cm-bench: cv8.c has changed - %r' % old[:40])
        src = src.replace(old, new)
    open(os.path.join(work, 'prof.c'), 'w').write(src)
    engine = os.path.join(work, 'relf-count')
    subprocess.run(['cc', '-O2', '-I', 'engine', '-o', engine, os.path.join(work, 'prof.c')], check=True)
    return engine, counts, slots

def dispatches(engine, counts, slots, img, prog):
    open(counts, 'wb').write(bytes(slots * 4))
    r = subprocess.run([engine, img, prog], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    c = array.array('I'); c.frombytes(open(counts, 'rb').read())
    return sum(c) if r.returncode == 0 else None

def run(img, prog):
    t0 = time.perf_counter()
    p = subprocess.run(['timeout', '120', './relf64', img, prog], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       stdin=subprocess.DEVNULL)
    return time.perf_counter() - t0, p.stdout.decode('utf-8', 'replace').replace('\r', '') + 'status %d\n' % p.returncode

def main():
    tmp = tempfile.mkdtemp(prefix='cm-bench.')
    img = os.path.join(tmp, 'cm.img')
    subprocess.run(['sh', 'tools/build-cm-image.sh', './relf64', 'forth/kernel64.img', img], check=True,
                   stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    print('kernel64-cm.img: %d bytes' % os.path.getsize(img))
    engine, counts, slots = counting_engine(tmp)
    bad = 0
    for prog in ['tests/cm/scripts/side.cm'] + sorted(glob.glob('tests/cm/bench/*.cm')):
        text = ''.join(l for l in open(prog) if not l.lstrip().startswith('#'))
        _, out = run(img, prog)
        if out != open(prog[:-3] + '.expected').read():
            print('%s: not the expected output' % prog); bad += 1; continue
        t = [run(img, prog)[0] * 1000 for _ in range(ROUNDS)]
        print('%-28s %4d characters %3d words   %7.1f ms (%.1f-%.1f)   %s dispatches' % (
            prog, len(re.sub(r'\s', '', text)), len(text.split()), statistics.median(t), min(t), max(t),
            format(dispatches(engine, counts, slots, img, prog) or 0, ',')))
    subprocess.run(['rm', '-rf', tmp])
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
