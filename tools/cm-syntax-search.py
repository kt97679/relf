#!/usr/bin/env python3
"""tools/cm-syntax-search.py [OUT.tsv] - the first syntax-genes experiment (Iteration 865, docs/SYNTAX-GENES.md).

Every genome of cm/genes.tsv - all 16 - enumerated, not sampled. For each: its image built
(tools/build-cm-image.sh with CM_GENES), and each script in tests/cm/scripts rendered in its syntax
(tools/cm-render.py), then gated twice: the genome's front end must make of the rendered script the
Forth tools/cmc.py makes of the original, token for token, and the rendered script must print the
original's .expected when run in the genome's image. Measured: the image's bytes; the rendered
scripts' non-blank characters and blank-separated words, comments left out of both; and their
escapes - characters the syntax made special that a writer must escape. Prints a table; writes it to
OUT.tsv if given. Exit status 1 if any genome fails a gate.
"""
import glob, importlib.util, itertools, os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location('cm_render', os.path.join(ROOT, 'tools', 'cm-render.py'))
cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)
TOKEN = re.compile(r'S" [^"]*"|\S+')

def canonical(script):
    text = subprocess.run(['python3', 'tools/cmc.py', script], capture_output=True, text=True, check=True).stdout
    text = text[text.index('cm/pipe.4" INCLUDED') + len('cm/pipe.4" INCLUDED'):]
    for c in ('( --- )', '( args --- )', '( --- f )'):
        text = text.replace(c, ' ')
    return TOKEN.findall(text)

def run(args):
    p = subprocess.run(['timeout', '60'] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       stdin=subprocess.DEVNULL)       # one stream, as 2>&1; bytes, as tr -d '\r' reads them -
    return p.stdout.decode('utf-8', 'replace').replace('\r', ''), p.returncode   # text mode made \r a line end

def main():
    names = [l.split('\t')[0] for l in open('cm/genes.tsv') if l.strip() and not l.startswith('#')]
    scripts = sorted(glob.glob('tests/cm/scripts/*.cm'))
    canon = {s: canonical(s) for s in scripts}
    tmp = tempfile.mkdtemp(prefix='cm-syntax.')
    rows, bad = [], 0
    for bits in itertools.product((0, 1), repeat=len(names)):
        g = dict(zip(names, bits)); spec_ = ','.join('%s=%d' % kv for kv in g.items())
        img = os.path.join(tmp, 'cm.img')
        b = subprocess.run(['sh', 'tools/build-cm-image.sh', './relf64', 'forth/kernel64.img', img],
                           capture_output=True, text=True, env=dict(os.environ, CM_GENES=spec_), stdin=subprocess.DEVNULL)
        if b.returncode:
            print('%s: the image is not built: %s' % (spec_, b.stderr.strip()[:200])); bad += 1; continue
        size, chars, words, escapes, fails = os.path.getsize(img), 0, 0, 0, []
        for s in scripts:
            try:
                text, esc = cr.render(open(s, encoding='utf-8').read(), g)
            except cr.Unrenderable as e:
                fails.append('%s: not renderable: %s' % (os.path.basename(s), e)); continue
            path = os.path.join(tmp, os.path.basename(s))
            open(path, 'w', encoding='utf-8').write(text)
            chars += len(re.sub(r'\s', '', text)); words += len(text.split()); escapes += esc
            drv = os.path.join(tmp, 'show.4')
            open(drv, 'w').write('S" %s" CM-SHOW\n' % path)
            out, _ = run(['./relf64', img, drv])
            if TOKEN.findall(out) != canon[s]:
                a, c = TOKEN.findall(out), canon[s]
                i = next((k for k in range(min(len(a), len(c))) if a[k] != c[k]), min(len(a), len(c)))
                fails.append('%s: Forth differs at token %d: %s | %s' % (os.path.basename(s), i,
                             ' '.join(c[max(0, i - 3):i + 4]), ' '.join(a[max(0, i - 3):i + 4])))
                continue
            out, status = run(['./relf64', img, path])
            if out + 'status %d\n' % status != open(s[:-3] + '.expected').read():
                fails.append('%s: its output is not the expected' % os.path.basename(s))
        rows.append((spec_, size, chars, words, escapes, 'ok' if not fails else '; '.join(fails)))
        if fails: bad += 1
        print('%s  %6d bytes  %5d chars  %5d words  %3d escapes  %s' % rows[-1], flush=True)
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'w') as f:
            f.write('# genome\timage bytes\tnon-blank characters\twords\tescapes\tgates\n')
            for r in rows: f.write('\t'.join(map(str, r)) + '\n')
    subprocess.run(['rm', '-rf', tmp])
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
