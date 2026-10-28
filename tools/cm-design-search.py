#!/usr/bin/env python3
"""tools/cm-design-search.py [OUT.tsv] - the command model's design genes, every genome (Iteration 866).

The d genes of cm/genes.tsv change the Forth the front end makes, not the syntax - so a genome's Forth
is not cmc.py's, and the gate is what the scripts do: each genome's image (tools/build-cm-image.sh with
CM_GENES) must run every script in tests/cm/scripts with its .expected output. Then the benchmarks of
tests/cm/compare (loop.cm, calls.cm) are run on CV8's counting engine - tools/rill-profile.py's, built
once here - and their dispatches counted: the same count every run, so no rounds and no noise floor.
Prints image bytes and each benchmark's dispatches per genome, with the ratio to the genome of all 0s;
writes the table to OUT.tsv if given. Exit status 1 if any genome fails the gate.
"""
import array, glob, itertools, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

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
        if src.count(old) != 1: sys.exit('cm-design-search: cv8.c has changed - %r' % old[:40])
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

def main():
    names = [l.split('\t')[0] for l in open('cm/genes.tsv') if l.startswith('d')]
    scripts = sorted(glob.glob('tests/cm/scripts/*.cm'))
    benches = sorted(glob.glob('tests/cm/compare/*.cm'))
    work = tempfile.mkdtemp(prefix='cm-design.')
    engine, counts, slots = counting_engine(work)
    img, rows, bad, base = os.path.join(work, 'cm.img'), [], 0, None
    for bits in itertools.product((0, 1), repeat=len(names)):
        spec = ','.join('%s=%d' % kv for kv in zip(names, bits))
        b = subprocess.run(['sh', 'tools/build-cm-image.sh', './relf64', 'forth/kernel64.img', img], capture_output=True,
                           text=True, env=dict(os.environ, CM_GENES=spec), stdin=subprocess.DEVNULL)
        if b.returncode:
            print('%s: not built: %s' % (spec, b.stderr.strip()[:200])); bad += 1; continue
        fails = []
        for s in scripts:
            p = subprocess.run(['timeout', '60', './relf64', img, s], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               stdin=subprocess.DEVNULL)
            out = p.stdout.decode('utf-8', 'replace').replace('\r', '') + 'status %d\n' % p.returncode
            if out != open(s[:-3] + '.expected').read(): fails.append(os.path.basename(s))
        d = [dispatches(engine, counts, slots, img, x) for x in benches]
        if base is None: base = d
        rows.append((spec, os.path.getsize(img), d, fails))
        if fails or None in d: bad += 1
        print('%s  %6d bytes  %s  %s' % (spec, rows[-1][1], '  '.join(
            '%s %s (%.3f)' % (os.path.basename(x)[:-3], format(n, ','), n / base[i]) if n else '%s failed' % os.path.basename(x)
            for i, (x, n) in enumerate(zip(benches, d))), 'ok' if not fails else 'FAILS: ' + ' '.join(fails)), flush=True)
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'w') as f:
            f.write('# genome\timage bytes\t' + '\t'.join(os.path.basename(x) + ' dispatches' for x in benches) + '\tgate\n')
            for spec, size, d, fails in rows:
                f.write('%s\t%d\t%s\t%s\n' % (spec, size, '\t'.join(map(str, d)), 'ok' if not fails else ' '.join(fails)))
    subprocess.run(['rm', '-rf', work])
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
