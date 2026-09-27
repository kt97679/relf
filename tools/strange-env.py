#!/usr/bin/env python3
"""tools/strange-env.py [SHELL] - the shell in hostile surroundings.

Each probe runs one command under the shell and under dash, in a setting
scripts rarely meet: an empty environment, ten thousand variables, a
working directory deeper than PATH_MAX, HOME unset, umask 777, an
argument holding every byte from 1 to 255, twelve descriptors, a small
address space. Stdout and status are compared with dash's; separately,
any crash - death by a signal, or a message of a segmentation fault - is
a failure whatever dash does. TESTING-IDEAS.md 11; written in Iteration
559.
"""
import os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, 'relfsh')
REF = 'dash'
ALLBYTES = bytes(range(1, 256))

def probe(shell, cmd, env=None, cwd=None, pre='', args=()):
    """Run cmd as `shell -c`, after `pre` (a ulimit, a umask) in the same
    shell process of sh - pre goes through /bin/sh, then exec's the shell."""
    argv = ['sh', '-c', pre + ' exec "$0" -c "$1" sh "$@"', shell, cmd] + list(args) if pre else [shell, '-c', cmd, 'sh'] + list(args)
    try:
        r = subprocess.run(argv, env=env, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, timeout=20)
        return r.stdout, r.returncode, r.stderr
    except subprocess.TimeoutExpired:
        return b'<timeout>', -1, b''

deep = tempfile.mkdtemp(prefix='relf-deep-')
# 90 levels of 50 characters: past PATH_MAX (4096). No single call can
# name such a path - makedirs said "File name too long" - so it is built
# a level at a time, and reached in chunks of 30 levels, each under it.
here = os.getcwd(); os.chdir(deep)
for i in range(90):
    n = 'd' * 49 + str(i % 10)
    os.mkdir(n); os.chdir(n)
os.chdir(here)
levels = ['d' * 49 + str(i % 10) for i in range(90)]
DEEP_CD = ' && '.join('cd ' + '/'.join(levels[k:k + 30]) for k in range(0, 90, 30)) + ' &&'
big_env = dict(os.environ, **{'V%05d' % i: 'x' * 20 for i in range(10000)})
work = tempfile.mkdtemp(prefix='relf-strange-')

PROBES = [
    ('empty environment', 'echo "[$HOME][${PATH+set}][$IFS]" | od -An -c | tr -s " "; echo ok', {}, None, '', ()),
    ('10,000 variables', 'echo "$V09999"; set | grep -c "^V0" ', big_env, None, '', ()),
    ('cwd past PATH_MAX', 'cd .. && cd - >/dev/null && echo ok; pwd | wc -c', None, deep, DEEP_CD, ()),
    ('HOME unset, cd', 'unset HOME; cd; echo "status $?"', None, work, '', ()),
    ('umask 777', 'echo hi > f 2>/dev/null; echo "wrote $?"; cat f 2>/dev/null; echo "read $?"', None, work, 'umask 777;', ()),
    ('every byte in an argument', 'printf %s "$1" | od -An -tx1 | tr -d " \\n"; echo', None, None, '', (ALLBYTES.decode('latin1'),)),
    ('12 descriptors', 'for i in 1 2 3 4 5 6 7 8; do exec 3<&0; done; echo x | cat | cat | cat; echo "ok $?"', None, None, 'ulimit -n 12;', ()),
    ('a small address space', 'echo small; x=$(echo inner); echo "$x"', None, None, 'ulimit -v 65536;', ()),
    ('a deep recursion of functions', 'f() { [ "$1" -gt 0 ] && f $(($1 - 1)); }; f 300; echo "depth $?"', None, None, '', ()),
    ('a long pipeline', 'echo x' + ' | cat' * 60 + '; echo "ok $?"', None, None, '', ()),
]

fails = 0
for name, cmd, env, cwd, pre, args in PROBES:
    if env is not None and 'PATH' not in env and not env:
        env = {}                            # truly empty
    mine = probe(SH, cmd, env, cwd, pre, args)
    ref = probe(REF, cmd, env, cwd, pre, args)
    crash = mine[1] < 0 or mine[1] >= 128 or b'egmentation' in mine[2]
    same = mine[:2] == ref[:2]
    verdict = 'CRASH' if crash else ('same as dash' if same else 'differs from dash')
    fails += crash
    print('%-28s %s' % (name, verdict))
    if crash or not same:
        print('    relf: %r status %d %r' % (mine[0][:90], mine[1], mine[2][:90]))
        print('    dash: %r status %d %r' % (ref[0][:90], ref[1], ref[2][:90]))
print('%d probes, %d crashes' % (len(PROBES), fails))
