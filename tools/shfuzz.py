#!/usr/bin/env python3
"""tools/shfuzz.py [N] [SEED] [SHELL] - grammar-based differential fuzzing.

Random, valid POSIX shell programs - quoting, parameter expansion,
arithmetic, command substitution, here-documents, redirections,
pipelines, and-or lists, if, bounded while loops, for, case, functions,
positional parameters, break, continue, return - with values leaning to
the awkward: empty, spaces, glob characters, backslashes, quotes,
newlines. Each runs on relf, dash and bash --posix; a finding is a
program where dash and bash agree and relf does not, by stdout and exit
status - where the two references disagree the spec may leave room, and
the program is set aside. Findings are shrunk, statement by statement,
to the smallest program that still disagrees. TESTING-IDEAS.md 6;
written in Iteration 559.
"""
import os, random, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 559)
RELF = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(ROOT, 'relfsh')
REFS = [['dash'], ['bash', '--posix']]
VARS = ['a', 'b', 'c']
VALUES = ["''", "x", "'two words'", "'*'", "'a*b'", "' lead'", "'trail '", "'back\\slash'",
          "'q\"uote'", "\"it's\"", "'-n'", "'line1\nline2'", "'[ab]'", "'$x'", "'~'", "0", "7", "-3"]
PATTERNS = ['*', 'x', '?', '[ab]*', '*o*', 'two*', "''", '-*']
depth_limit = 3

def word(d=0):
    r = rng.random()
    v = rng.choice(VARS)
    if r < 0.18: return rng.choice(VALUES)
    if r < 0.30: return '"$%s"' % v
    if r < 0.38: return '$%s' % v
    if r < 0.46: return '"${%s:-%s}"' % (v, rng.choice(['dflt', 'x y', '']))
    if r < 0.52: return '"${%s:+set}"' % v
    if r < 0.58: return '"${%s#%s}"' % (v, rng.choice(PATTERNS))
    if r < 0.63: return '"${%s%%%s}"' % (v, rng.choice(PATTERNS))
    if r < 0.67: return '${#%s}' % v
    if r < 0.73: return '$((%s))' % arith()
    if r < 0.80 and d < depth_limit: return '"$(%s)"' % simple(d + 1)
    if r < 0.84: return '"$@"'
    if r < 0.87: return '"$#"'
    if r < 0.90: return 'pre"$%s"post' % v
    if r < 0.93: return "'lit'\"$%s\"" % v
    return rng.choice(['word', 'a\\ b', '\\$x', '"\\\\"', "''", '""'])

def arith():
    t = [str(rng.randrange(-5, 20)), '${#%s}' % rng.choice(VARS), 'n']
    e = rng.choice(t)
    for _ in range(rng.randrange(0, 3)):
        e = '%s %s %s' % (e, rng.choice(['+', '-', '*', '%', '<', '==', '&&', '||', '<<', '&']),
                          rng.choice(t))
    return e.replace('% 0', '% 1').replace('%s 0' % '%', '% 1')

def simple(d=0):
    r = rng.random()
    if r < 0.30: return 'echo %s' % ' '.join(word(d) for _ in range(rng.randrange(0, 4)))
    if r < 0.42: return "printf '%%s|' %s; echo" % ' '.join(word(d) for _ in range(rng.randrange(1, 4)))
    if r < 0.55: return '%s=%s' % (rng.choice(VARS), word(d))
    if r < 0.62: return 'set -- %s' % ' '.join(word(d) for _ in range(rng.randrange(0, 4)))
    if r < 0.66: return 'shift'
    if r < 0.74: return '[ %s %s %s ]' % (word(d), rng.choice(['=', '!=']), word(d))
    if r < 0.78: return '[ -n %s ]' % word(d)
    if r < 0.82: return rng.choice(['true', 'false', ':'])
    if r < 0.86: return 'n=$((n + 1))'
    if r < 0.90: return 'f %s' % ' '.join(word(d) for _ in range(rng.randrange(0, 3)))
    return 'echo %s > out; cat out' % word(d)

def command(d=0):
    r = rng.random()
    if d >= depth_limit or r < 0.40: return simple(d)
    if r < 0.48: return '%s | %s' % (simple(d), rng.choice(['cat', 'wc -l | tr -d " "', 'sed s/o/0/']))
    if r < 0.56: return '%s %s %s' % (simple(d), rng.choice(['&&', '||']), simple(d))
    if r < 0.60: return '! %s' % simple(d)
    if r < 0.66: return '{ %s; }' % body(d + 1)
    if r < 0.70: return '( %s )' % body(d + 1)
    if r < 0.77: return 'if %s; then %s; else %s; fi' % (simple(d), body(d + 1), body(d + 1))
    if r < 0.83: return 'for %s in %s; do %s; done' % (rng.choice(VARS), ' '.join(word(d) for _ in range(rng.randrange(0, 4))), body(d + 1, loop=True))
    if r < 0.88: return 'i=0; while [ $i -lt %d ]; do i=$((i + 1)); %s; done' % (rng.randrange(0, 4), body(d + 1, loop=True))
    if r < 0.94: return 'case %s in %s) %s;; %s) %s;; *) %s;; esac' % (word(d), rng.choice(PATTERNS), body(d + 1), rng.choice(PATTERNS), body(d + 1), body(d + 1))
    return "cat <<%s\nline %s\n%s\n" % (rng.choice(['EOF', "'EOF'"]), rng.choice(['$a', '"$b"', '\\$c', '$((1+2))', "'q'"]), 'EOF')

def body(d, loop=False):
    parts = [command(d) for _ in range(rng.randrange(1, 3))]
    if loop and rng.random() < 0.3: parts.append(rng.choice(['break', 'continue']))
    return '; '.join(p for p in parts if not p.endswith('\n')) or ':'

def program():
    lines = ['a=%s b=%s c=%s n=0' % tuple(rng.choice(VALUES) for _ in VARS),
             'f() { echo "f:$#:$1"; %s; return %d; }' % (simple(1), rng.randrange(0, 3))]
    for _ in range(rng.randrange(2, 8)):
        c = command(0)
        lines.append(c.rstrip('\n'))
    lines.append('echo "end:$?:$a:$n"')
    return lines

def run(argv, lines, work):
    path = os.path.join(work, 'p.sh')
    open(path, 'w').write('\n'.join(lines) + '\n')
    for f in os.listdir(work):
        if f != 'p.sh': os.remove(os.path.join(work, f))
    try:
        r = subprocess.run(argv + [path], cwd=work, stdin=subprocess.DEVNULL, capture_output=True, timeout=5)
        return (r.stdout, r.returncode)
    except subprocess.TimeoutExpired:
        return (b'<timeout>', -1)

def verdict(lines, work):
    refs = [run(a, lines, work) for a in REFS]
    if refs[0] != refs[1]: return None                  # the references split
    mine = run([RELF], lines, work)
    return (mine, refs[0]) if mine != refs[0] else False

def shrink(lines, work):
    changed = True
    while changed:
        changed = False
        for i in range(len(lines) - 1, -1, -1):
            trial = lines[:i] + lines[i + 1:]
            if trial and verdict(trial, work):
                lines, changed = trial, True
    return lines

findings, splits = [], 0
with tempfile.TemporaryDirectory() as work:
    for k in range(N):
        prog = program()
        v = verdict(prog, work)
        if v is None: splits += 1
        elif v: findings.append(shrink(prog, work))
    print('%d programs: %d findings, %d set aside where dash and bash disagree' % (N, len(findings), splits))
    seen = set()
    for f in sorted(findings, key=len):
        key = '\n'.join(f)
        if key in seen: continue
        seen.add(key)
        (mo, ms), (ro, rs) = verdict(f, work)
        print('--- finding (%d lines); relf status %s, references %s' % (len(f), ms, rs))
        print('\n'.join('    ' + l for l in f))
        print('    relf: %r\n    refs: %r' % (mo.decode(errors='replace')[:160], ro.decode(errors='replace')[:160]))
