#!/usr/bin/env python3
"""tools/relfsh-memcheck.py [SHELL...] - does relfsh give back what it no longer needs? (Iteration 777)

Each shell feature runs in a loop, once N times and once 10 N times; the
peak resident memory of the two runs is compared. A shell that frees what it
is done with has the same peak either way; memory kept per round shows as a
growth that scales with the rounds - reported as bytes per round. Features
that fork (command substitution, pipelines, subshells) run fewer rounds.
Measures only: nothing of relfsh is changed. Default shells: ./relfsh (on
the VM) and ./relfsh-native; any POSIX shell can be given for comparison.
"""
import os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
shells = sys.argv[1:] or ['./relfsh', './relfsh-native']

LOOP = '%si=0\nwhile [ $i -lt $1 ]; do\n%s\ni=$((i+1))\ndone\necho done $i\n'
PRE = {'func-call': 'f() { z="$1"; }\n', 'local': 'h() { local z="$1 more"; }\n', 'func-bigger': 'k() { a=1; b=2; c=3; d=4; }\n'}
W = [   # name, body, rounds (N), forks
    ('assign',      'x="value number $i"', 2000, False),
    ('arith',       ': $((i * i + 3))', 2000, False),
    ('expand',      'x="abcd$i"; y=${x#a}; z=${#x}; w=${x%?}; v=${x:-none}', 2000, False),
    ('concat',      's=""; for j in 1 2 3 4 5 6 7 8; do s="$s$j$i"; done', 1000, False),
    ('for-words',   'for w in alpha beta gamma delta; do :; done', 2000, False),
    ('case',        'case $i in *5) : ;; *[0-4]) : ;; *) : ;; esac', 2000, False),
    ('func-call',   'f $i', 2000, False),                     # defined once, before the loop
    ('local',       'h $i', 2000, False),
    ('func-redef',  'g() { echo "$i" >/dev/null; }', 2000, False),   # defined again each round, never called
    ('func-redef2', 'g() { :; }', 2000, False),
    ('eval',        'eval "v$((i % 50))=$i"', 2000, False),
    ('unset',       'eval "u$((i % 50))=x$i"; eval "unset u$((i % 50))"', 2000, False),
    ('set-args',    'set -- alpha beta "$i" gamma', 2000, False),
    ('export',      'export E="value $i"', 2000, False),
    ('heredoc',     'cat <<EOF >/dev/null\nline $i\nEOF', 300, True),
    ('trap',        'trap "echo $i" USR1', 2000, False),
    ('alias',       'alias al="echo $i"', 2000, False),
    ('cd',          'cd /tmp; cd /', 2000, False),
    ('printf',      "printf '%s\\n' \"$i\" >/dev/null", 2000, False),
    ('read',        'read line < /etc/hostname', 2000, False),
    ('cmdsubst',    'y=$(echo $i)', 300, True),
    ('pipeline',    'echo $i | cat >/dev/null', 300, True),
    ('subshell',    '( x=$i )', 300, True),
]

def peak_kb(shell, script, n):
    """The shell's peak resident memory, in KB, running script with $1 = n."""
    probe = ('import resource, subprocess, sys\n'
             'p = subprocess.run(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=240)\n'
             'print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss, p.returncode, repr(p.stdout[-80:]))')
    r = subprocess.run([sys.executable, '-c', probe, shell, script, str(n)], capture_output=True, text=True)
    kb, st, out = r.stdout.strip().split(' ', 2)
    return int(kb), int(st), out

work = tempfile.mkdtemp(prefix='relfsh-mem-')
print('%-12s' % 'feature' + ''.join('%28s' % s for s in shells))
for name, body, n, forks in W:
    script = os.path.join(work, name + '.sh')
    open(script, 'w').write(LOOP % (PRE.get(name, ''), body))
    cells = []
    for sh in shells:
        a, sa, oa = peak_kb(sh, script, n)
        b, sb, ob = peak_kb(sh, script, 10 * n)
        if sa or sb or 'done' not in ob:
            cells.append('fails: %s' % (ob if sb else oa)[:22])
            continue
        per = (b - a) * 1024.0 / (9 * n)
        cells.append('%5d->%5d KB %6.0f B/round' % (a, b, per))
    print('%-12s' % name + ''.join('%28s' % c for c in cells))
