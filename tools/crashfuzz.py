#!/usr/bin/env python3
"""tools/crashfuzz.py [--seconds N] [--out DIR] [--seed S] - look for CRASHES.

Mutates shell snippets - this project's differential cases, and yash's
test inputs when YASH_TESTS points at them - and runs each mutant through
this shell at both cell widths, in an empty scratch directory, under
process, memory and time limits. It compares no output, so it cannot
report a false difference; it reports only:

  CRASH  the engine said so: a segmentation fault, a stack guard, an
         overflow or underflow, an abort;
  HANG   this shell timed out on input dash finishes in well under the
         limit - a mutated `while :` hangs everywhere and is not news.

Each finding is shrunk by deleting lines, then words, while it still
reproduces, and written to --out as a script. Written at Iteration 421,
after three segfaults in twenty iterations had each been found by
accident; this looks for that class on purpose.
"""
import os, random, re, subprocess, sys, tempfile, time, glob, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RELFSH = os.path.join(ROOT, 'relfsh')
WIDTHS = [{}]
if os.path.exists(os.path.join(ROOT, 'relf32')) and os.path.exists(os.path.join(ROOT, 'kernel32.img')):
    WIDTHS.append({'RELF_BIN': os.path.join(ROOT, 'relf32'), 'RELF_IMG': os.path.join(ROOT, 'kernel32.img')})
CRASH = re.compile(r'segmentation fault|stack guard|stack overflow|stack underflow|return stack|Aborted|core dumped|not a RelF image')
DANGER = re.compile(r'\b(rm\s+-r|mkfs|dd|shutdown|reboot|halt|kill|killall|sudo|chmod\s+-R|chown|mount|umount|curl|wget|ssh|nc)\b|/dev/sd|>\s*/(?!dev/null|tmp)')
TOKENS = ['0', '1', '2', '9', '10', '""', "''", '$#', '$@', '"$@"', '$*', '$?', '$$', '$0', '$1', '${x}', '${x-y}',
          '${x#*}', '${#x}', '$((1<<31))', '$((1<<63))', '$((-1))', '$((0-9223372036854775807-1))', '$((x/0))',
          ';', ';;', '&', '&&', '||', '|', '(', ')', '{', '}', '<', '>', '>>', '2>&1', '<&-', '>&-',
          '<<E\nE', '`', '$(', 'esac', 'fi', 'done', 'then', 'do', 'in', '!', '*', '?', '[', ']', '\\', '\n',
          'x=1', 'x=', 'IFS=:', 'set --', 'set -u', 'shift', 'return', 'break', 'continue', 'eval', 'exec',
          'trap : 0', 'case', 'for', 'while', 'until', 'if', 'f()', 'alias a=b', 'unset x', 'read x', 'printf %s',
          'a' * 300, '9' * 25, '-' * 40, '%%', '#', '~', '~/x', '[!a]', '[[:digit:]]', "$'", '${', '$((', ')))']

def seeds():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'tests/diff/cases/*.sh'))):
        t = open(p, errors='replace').read()
        if len(t) < 4000 and not DANGER.search(t):
            out.append(t)
    yt = os.environ.get('YASH_TESTS')
    if yt:
        for p in sorted(glob.glob(os.path.join(yt, '*-p.tst'))):
            for m in re.finditer(r'__IN__\n(.*?)\n__IN__', open(p, errors='replace').read(), re.S):
                t = m.group(1)
                if len(t) < 2000 and not DANGER.search(t):
                    out.append(t)
    return out

def mutate(t, rnd):
    lines = t.split('\n')
    for _ in range(rnd.randint(1, 3)):
        op = rnd.randrange(7)
        if op == 0 and len(lines) > 1:                      # delete a line
            del lines[rnd.randrange(len(lines))]
        elif op == 1:                                       # duplicate a line
            i = rnd.randrange(len(lines)); lines.insert(i, lines[i])
        elif op == 2:                                       # truncate
            s = '\n'.join(lines); lines = s[:rnd.randrange(len(s) + 1)].split('\n')
        else:                                               # word-level
            i = rnd.randrange(len(lines)); w = lines[i].split(' ')
            j = rnd.randrange(len(w) + 1)
            if op == 3 and w:
                w[min(j, len(w) - 1)] = rnd.choice(TOKENS)
            elif op == 4:
                w.insert(j, rnd.choice(TOKENS))
            elif op == 5 and len(w) > 1:
                k = min(j, len(w) - 2); w[k], w[k + 1] = w[k + 1], w[k]
            elif op == 6 and w:
                del w[min(j, len(w) - 1)]
            lines[i] = ' '.join(w)
    return '\n'.join(lines)

def run(shell_argv, script, env_extra, limit):
    d = tempfile.mkdtemp(prefix='fuzz-')
    p = os.path.join(d, 's.sh'); open(p, 'w').write(script)
    env = {'PATH': os.environ['PATH'], 'HOME': d, 'LC_ALL': 'C'}
    env.update(env_extra)
    pre = 'ulimit -u 256 2>/dev/null; ulimit -v 1000000 2>/dev/null; ulimit -f 20000 2>/dev/null; exec "$@"'
    t0 = time.time()
    try:
        r = subprocess.run(['sh', '-c', pre, 'sh'] + shell_argv + [p], cwd=d, env=env,
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=limit)
        out = (r.stdout + r.stderr).decode('latin1', 'replace'); kind = 'done'
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b'') + (e.stderr or b'')).decode('latin1', 'replace'); kind = 'timeout'
    shutil.rmtree(d, ignore_errors=True)
    return kind, out, time.time() - t0

def verdict(script, env_extra, limit):
    kind, out, _ = run([RELFSH], script, env_extra, limit)
    m = CRASH.search(out)
    if m:
        return 'CRASH', m.group(0)
    if kind == 'timeout':
        k2, _, t2 = run(['dash'], script, {}, limit)
        if k2 == 'done' and t2 < limit / 4:
            return 'HANG', 'timeout'
    return None, None

def shrink(script, env_extra, want, limit):
    units = script.split('\n'); sep = '\n'
    for _pass in range(2):
        i = 0
        while i < len(units):
            trial = units[:i] + units[i+1:]
            if trial and verdict(sep.join(trial), env_extra, limit)[0] == want:
                units = trial
            else:
                i += 1
        if sep == '\n':
            script = '\n'.join(units); units = script.split(' '); sep = ' '
    return sep.join(units)

def main():
    a = sys.argv[1:]
    seconds = int(a[a.index('--seconds') + 1]) if '--seconds' in a else 120
    outdir = a[a.index('--out') + 1] if '--out' in a else '/tmp/crashfuzz'
    rnd = random.Random(int(a[a.index('--seed') + 1]) if '--seed' in a else 421)
    os.makedirs(outdir, exist_ok=True)
    pool = seeds()
    found, tried, seen = [], 0, set()
    end = time.time() + seconds
    while time.time() < end:
        s = mutate(rnd.choice(pool), rnd)
        env_extra = rnd.choice(WIDTHS)
        tried += 1
        v, why = verdict(s, env_extra, 4)
        if not v:
            continue
        small = shrink(s, env_extra, v, 4)
        key = hashlib.sha1((v + small).encode()).hexdigest()[:10]
        if key in seen:
            continue
        seen.add(key)
        width = '4-byte' if env_extra else '8-byte'
        name = os.path.join(outdir, '%s-%s-%s.sh' % (v.lower(), width, key))
        open(name, 'w').write(small + '\n')
        found.append((v, width, why, name))
        print('%s (%s, %s): %s' % (v, width, why, name), flush=True)
    print('%d mutants, %d findings, %d seeds' % (tried, len(found), len(pool)))

main()
