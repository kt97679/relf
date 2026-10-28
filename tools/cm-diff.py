#!/usr/bin/env python3
"""tools/cm-diff.py IMAGE [SCRIPT.cm ...] - the command model's two front ends, compared (863).

cm/cmc.4, the front end in Forth, is to make the Forth tools/cmc.py makes, word for word. For each
script - tests/cm/scripts/*.cm by default - both make their Forth, and the two are compared as tokens:
an S" ..." string is one token, anything else is cut at blanks, so line breaks do not count. Left out
of cmc.py's: its first line's INCLUDEDs (cm/cmc.4 is loaded with the runtime - as tools/cm-genes.py makes it
for CM_GENES, 865 - and the runtime with it)
and its stack comments, which cm/cmc.4 does not write. IMAGE is rill2's image; cm's runtime and
cm/cmc.4 are loaded on it.

Prints one line per script, and the first difference with its neighbours; exit status 1 on any.
"""
import glob, os, re, subprocess, sys, tempfile

TOKEN = re.compile(r'S" [^"]*"|\S+')
LOAD = ' '.join('S" cm/%s" INCLUDED' % f for f in ('rt-cm.4', 'out.4', 'ctl.4', 'lib.4', 'pipe.4'))

def python_side(script):
    p = subprocess.run(['python3', 'tools/cmc.py', script], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if p.returncode:
        return None, p.stderr.strip()
    text = p.stdout
    text = text[text.index('cm/pipe.4" INCLUDED') + len('cm/pipe.4" INCLUDED'):]
    for c in ('( --- )', '( args --- )', '( --- f )'):
        text = text.replace(c, ' ')
    return TOKEN.findall(text), ''

def forth_side(image, script):
    fd, driver = tempfile.mkstemp(suffix='.4', prefix='cm-diff.')
    with os.fdopen(fd, 'w') as f:
        f.write('%s S" %s" INCLUDED\nS" %s" CM-SHOW\n' % (LOAD, FRONT, script))
    try:
        p = subprocess.run(['timeout', '60', './relf64', image, driver], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
    finally:
        os.unlink(driver)
    out = (p.stdout + p.stderr).replace('\r', '')
    lines = [l for l in out.split('\n') if l.strip() and not l.startswith('Redefining')]
    return TOKEN.findall('\n'.join(lines)), out

def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__); return 2
    global FRONT
    image, scripts = sys.argv[1], sys.argv[2:] or sorted(glob.glob('tests/cm/scripts/*.cm'))
    fd, FRONT = tempfile.mkstemp(suffix='.4', prefix='cm-diff-front.')    # cm/cmc.4 as CM_GENES has it (865)
    with os.fdopen(fd, 'w') as f:
        f.write(subprocess.run(['python3', 'tools/cm-genes.py'], capture_output=True, text=True, check=True).stdout)
    try:
        return compare(image, scripts)
    finally:
        os.unlink(FRONT)

def compare(image, scripts):
    bad = 0
    for s in scripts:
        a, err = python_side(s)
        b, raw = forth_side(image, s)
        if a is None:
            print('%s: cmc.py fails: %s' % (s, err)); bad += 1; continue
        if a == b:
            print('%s: the same, %d tokens' % (s, len(a))); continue
        bad += 1
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        print('%s: differs at token %d of %d and %d' % (s, i, len(a), len(b)))
        print('  cmc.py: %s' % ' '.join(a[max(0, i - 8):i + 8]))
        print('  cmc.4:  %s' % ' '.join(b[max(0, i - 8):i + 8]))
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
