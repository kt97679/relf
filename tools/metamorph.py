#!/usr/bin/env python3
"""tools/metamorph.py [SHELL] [REF] - metamorphic testing of the shell.

Every script of the differential suite (tests/diff/cases) is run as it
is, and rewritten in ways that should not change what it prints: its
body in braces, a subshell, eval, `if :; then`, a function, a case arm,
a loop run once, sourced with `.`, piped through cat. The shell is
compared with ITSELF - no expected output. TESTING-IDEAS.md 1; written
in Iteration 557.

A rewriting is not neutral for every script: `exit` inside ( ) ends only
the subshell, $LINENO moves, `break` finds the loop. So a difference is
counted against the shell only when the reference shell (dash by
default) shows no difference between the same two scripts; otherwise the
rewriting was not neutral, and it is tallied as such, not as a finding.
A script whose output differs between two plain runs is set aside.
Stdout and the exit status are compared; stderr is not (line numbers).
"""
import os, subprocess, sys, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, 'relfsh')
REF = sys.argv[2] if len(sys.argv) > 2 else shutil.which('dash')
CASES = os.path.join(ROOT, 'tests', 'diff', 'cases')

def q(s):                     # single-quote s for eval
    return "'" + s.replace("'", "'\\''") + "'"

REWRITES = [
    ('braces',   lambda s, f: '{\n%s\n}\n' % s, True),
    ('subshell', lambda s, f: '(\n%s\n)\n' % s, True),
    ('eval',     lambda s, f: 'eval %s\n' % q(s), True),
    ('if-true',  lambda s, f: 'if :; then\n%s\nfi\n' % s, True),
    ('function', lambda s, f: '__mm() {\n%s\n}\n__mm "$@"\n' % s, True),
    ('case-arm', lambda s, f: 'case x in\nx)\n%s\n;;\nesac\n' % s, True),
    ('loop-once', lambda s, f: 'for __mm in 1; do\n%s\ndone\n' % s, True),
    ('dot',      lambda s, f: '. %s\n' % f, True),
    ('pipe-cat', lambda s, f: '{\n%s\n} | cat\n' % s, False),   # the status is cat's
]

def run(shell, text, work):
    path = os.path.join(work, 'script.sh')
    open(path, 'w').write(text)
    try:
        r = subprocess.run([shell, path], cwd=work, stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
        return r.stdout, r.returncode
    except subprocess.TimeoutExpired:
        return b'<timeout>', -1

findings, neutral_fail, tried, unstable, lineno = [], {}, 0, 0, 0
names = sorted(f for f in os.listdir(CASES) if f.endswith('.sh'))
for name in names:
    src = open(os.path.join(CASES, name)).read()
    if 'LINENO' in src:
        # every rewriting adds lines above the code, so $LINENO moves with
        # it - rightly; the reference cannot vouch for it either, since
        # dash counts from a function's start (the first run's only
        # "findings", all seven in lineno-475.sh)
        lineno += 1
        continue
    with tempfile.TemporaryDirectory() as work:
        orig = os.path.join(work, 'orig.sh')
        open(orig, 'w').write(src)
        base = run(SH, src, work)
        if run(SH, src, work) != base:
            unstable += 1
            continue
        rbase = run(REF, src, work) if REF else None
        for label, rw, keep_status in REWRITES:
            text = rw(src, orig)
            got = run(SH, text, work)
            tried += 1
            same = got[0] == base[0] and (got[1] == base[1] or not keep_status)
            if same:
                continue
            if REF:                               # neutral for the reference?
                rgot = run(REF, text, work)
                rsame = rgot[0] == rbase[0] and (rgot[1] == rbase[1] or not keep_status)
                if not rsame:
                    neutral_fail[label] = neutral_fail.get(label, 0) + 1
                    continue
            findings.append((name, label, base, got))

print('%d scripts (%d set aside as unstable, %d for reading $LINENO), %d rewritings run; reference: %s'
      % (len(names), unstable, lineno, tried, REF or 'none'))
print('not neutral for the reference either (not findings): %s'
      % (', '.join('%s %d' % kv for kv in sorted(neutral_fail.items())) or 'none'))
print('findings - the shell changed its output, the reference did not: %d' % len(findings))
for name, label, (o1, s1), (o2, s2) in findings[:12]:
    a = o1.decode(errors='replace').strip().splitlines(); b = o2.decode(errors='replace').strip().splitlines()
    first = next((i for i in range(max(len(a), len(b))) if (a[i:i+1] or [None]) != (b[i:i+1] or [None])), 0)
    print('  %-34s %-9s status %s -> %s; line %d: %r -> %r'
          % (name, label, s1, s2, first + 1, (a[first:first+1] or [''])[0][:40], (b[first:first+1] or [''])[0][:40]))
