#!/usr/bin/env python3
"""tools/parliament.py [SHELL] - a parliament of shells votes on each script.

The differential suite (tests/diff/cases) trusts one oracle, bash; the
POSIX suite scores a case only when every reference shell agrees. This
puts the same 131 scripts to every POSIX shell installed - dash, bash in
POSIX mode, yash, posh, mksh, ksh93, busybox ash - and reports, by
stdout and exit status: where relf differs from a strong majority (at
least 5 votes); where the shells split, so the spec leaves room, which
DASH.md should record as a choice; and where bash, the differential
suite's oracle, is outvoted - there relf passes by agreeing with the
odd one out. TESTING-IDEAS.md 5; written in Iteration 558.
"""
import os, shutil, subprocess, sys, tempfile
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELF = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, 'relfsh')
CASES = os.path.join(ROOT, 'tests', 'diff', 'cases')
CANDIDATES = [('dash', ['dash']), ('bash', ['bash', '--posix']), ('yash', ['yash', '--posix']),
              ('posh', ['posh']), ('mksh', ['mksh', '-o', 'posix']), ('ksh93', ['ksh93']),
              ('ash', ['busybox', 'ash'])]
SHELLS = [(n, a) for n, a in CANDIDATES if shutil.which(a[0])]
STRONG = 5

def run(argv, path, work):
    try:
        r = subprocess.run(argv + [path], cwd=work, stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
        return (r.stdout, r.returncode)
    except subprocess.TimeoutExpired:
        return (b'<timeout>', -1)

against, splits, bash_out, agree = [], [], [], 0
names = sorted(f for f in os.listdir(CASES) if f.endswith('.sh'))
for name in names:
    with tempfile.TemporaryDirectory() as work:
        path = os.path.join(work, 'case.sh')
        shutil.copy(os.path.join(CASES, name), path)
        votes = {n: run(a, path, work) for n, a in SHELLS}
        mine = run([RELF], path, work)
    tally = Counter(votes.values())
    top, n = tally.most_common(1)[0]
    who = sorted(k for k, v in votes.items() if v == top)
    if n < STRONG:
        splits.append((name, n, len(SHELLS), mine == top, sorted(tally.values(), reverse=True)))
        continue
    if mine != top:
        against.append((name, n, mine, top))
    else:
        agree += 1
    if 'bash' in votes and votes['bash'] != top:
        bash_out.append((name, n, mine == votes['bash']))

print('%d scripts, %d shells: %s' % (len(names), len(SHELLS), ' '.join(n for n, _ in SHELLS)))
print('a strong majority (%d+ votes) and relf with it: %d' % (STRONG, agree))
print('relf against a strong majority: %d' % len(against))
for name, n, mine, top in against:
    a = mine[0].decode(errors='replace').splitlines(); b = top[0].decode(errors='replace').splitlines()
    i = next((k for k in range(max(len(a), len(b))) if (a[k:k+1] or [None]) != (b[k:k+1] or [None])), 0)
    print('  %-32s %d votes: status %s vs %s; line %d: relf %r, majority %r'
          % (name, n, mine[1], top[1], i + 1, (a[i:i+1] or [''])[0][:36], (b[i:i+1] or [''])[0][:36]))
print('splits - no strong majority, the spec leaves room: %d' % len(splits))
for name, n, tot, with_top, sizes in splits:
    print('  %-32s largest bloc %d of %d, blocs %s; relf %s it' % (name, n, tot, sizes, 'in' if with_top else 'outside'))
print('bash outvoted by a strong majority: %d' % len(bash_out))
for name, n, relf_with_bash in bash_out:
    print('  %-32s majority %d; relf %s' % (name, n, 'sides with bash - passes the suite by that' if relf_with_bash else 'sides with the majority'))
