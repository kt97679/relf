#!/usr/bin/env python3
"""tools/cm-compare.py [ROUNDS] - Rill, Rill 2 and the command model on the same programs (Iteration 865).

The programs: side (tests/rill2/compare/side.rill and side.r2, 838; tests/cm/scripts/side.cm), loop and
calls (tests/cm/compare/) - each in the three languages, one output each. Builds the images - Rill's,
Rill 2's, the command model's with its front end resident and with it as an overlay loaded per script
(tools/build-cm-image.sh, CM_FRONT=overlay) - and prints: each image's bytes; each program's text,
its non-blank characters and blank-separated words, comment lines left out; and its time to run,
compiling included - ROUNDS rounds (9 unless given), the images taking turns within a round so drift
falls on all alike, the median and the range, in ms. Each run's output is checked against the
program's .expected first; a wrong one is reported and not timed.
"""
import os, re, statistics, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 9
tmp = tempfile.mkdtemp(prefix='cm-compare.')
IMAGES = [('Rill', 'kernel64-rill.img', ['sh', 'tools/build-rill-image.sh'], {}),
          ('Rill 2', tmp + '/rill2.img', ['sh', 'tools/build-rill2-image.sh', './relf64', 'forth/kernel64.img', tmp + '/rill2.img'], {}),
          ('cm', tmp + '/cm.img', ['sh', 'tools/build-cm-image.sh', './relf64', 'forth/kernel64.img', tmp + '/cm.img'], {}),
          ('cm, overlay', tmp + '/cm-lean.img', ['sh', 'tools/build-cm-image.sh', './relf64', 'forth/kernel64.img', tmp + '/cm-lean.img'],
           {'CM_FRONT': 'overlay'})]
SUFFIX = {'Rill': '.rill', 'Rill 2': '.r2', 'cm': '.cm', 'cm, overlay': '.cm'}
PROGRAMS = {'side': {'.rill': 'tests/rill2/compare/side.rill', '.r2': 'tests/rill2/compare/side.r2',
                     '.cm': 'tests/cm/scripts/side.cm', 'expected': 'tests/rill2/compare/side.expected'},
            'loop': {s: 'tests/cm/compare/loop' + s for s in ('.rill', '.r2', '.cm')} | {'expected': 'tests/cm/compare/loop.expected'},
            'calls': {s: 'tests/cm/compare/calls' + s for s in ('.rill', '.r2', '.cm')} | {'expected': 'tests/cm/compare/calls.expected'}}

def text_size(path):
    lines = [l for l in open(path, encoding='utf-8') if not l.lstrip().startswith('#')]
    t = ''.join(lines)
    return len(re.sub(r'\s', '', t)), len(t.split())

def run(img, prog):
    t0 = time.perf_counter()
    p = subprocess.run(['timeout', '120', './relf64', img, prog], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       stdin=subprocess.DEVNULL)
    return time.perf_counter() - t0, p.stdout.decode('utf-8', 'replace').replace('\r', '') + 'status %d\n' % p.returncode

def main():
    for name, img, cmd, env in IMAGES:
        b = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, **env), stdin=subprocess.DEVNULL)
        if b.returncode: sys.exit('cm-compare: %s not built: %s' % (name, b.stderr.strip()[:300]))
    print('image bytes: ' + ', '.join('%s %d' % (n, os.path.getsize(i)) for n, i, _, _ in IMAGES))
    print('\nthe programs\' text (non-blank characters / words):')
    for prog, files in PROGRAMS.items():
        print('  %-6s ' % prog + '   '.join('%s %d / %d' % ((lang,) + text_size(files[SUFFIX[lang]]))
                                           for lang in ('Rill', 'Rill 2', 'cm')))
    times, bad = {}, 0
    for prog, files in PROGRAMS.items():
        expected = open(files['expected']).read()
        for name, img, _, _ in IMAGES:
            _, out = run(img, files[SUFFIX[name]])
            if out != expected:
                print('%s in %s: not the expected output' % (prog, name)); bad += 1; continue
            times[(prog, name)] = []
    for r in range(ROUNDS):
        for prog, files in PROGRAMS.items():
            for name, img, _, _ in (IMAGES if r % 2 == 0 else IMAGES[::-1]):
                if (prog, name) in times: times[(prog, name)].append(run(img, files[SUFFIX[name]])[0] * 1000)
    print('\ntime to run, compiling included (ms: median, and min-max over %d rounds):' % ROUNDS)
    for prog in PROGRAMS:
        print('  %-6s ' % prog + '   '.join('%s %.1f (%.1f-%.1f)' % (n, statistics.median(t), min(t), max(t))
                                           for (p, n), t in times.items() if p == prog))
    subprocess.run(['rm', '-rf', tmp])
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
