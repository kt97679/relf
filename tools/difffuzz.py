#!/usr/bin/env python3
"""tools/difffuzz.py [--seconds N] [--out DIR] [--seed S] - look for DIFFERENCES.

Where tools/crashfuzz.py mutates existing scripts and looks only for
crashes and hangs, this GENERATES well-formed scripts from a small
grammar of the constructs this shell's bugs have lived in - parameter
expansions, quoting, field splitting, patterns, here-documents,
redirections, loops, functions, traps - and compares this shell with
dash: standard output and exit status. Standard error is not compared,
since the two word their messages differently; nor are the behaviours
GOALS.md records as deliberate divergences, which the grammar avoids.

Every value a script prints goes through printf '[%s]', so a field
boundary is visible and a splitting difference cannot hide. Each finding
is shrunk by deleting lines while the difference persists, and written
to --out with both outputs. Written at Iteration 471: the bugs of 444 to
470 were each found by hand, one test at a time, and nearly all of them
are shapes a generator reaches in seconds.
"""
import os, random, subprocess, sys, tempfile, time, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RELFSH = os.path.join(ROOT, 'relfsh')
DASH = shutil.which('dash')

VALUES = ['', 'a', 'a b', ' lead', 'trail ', 'a  b', '*', 'x*', '[ab]', 'a:b:c', '1', '10', '-n',
          'x\ty', 'a,b', '$x', "it's", 'q"q', '~', 'a/b/c', '.', '..', '?']
PATTERNS = ['*', '?', 'a*', '*b', '[ab]*', '[!a]*', '*[0-9]', '"*"', "'a'*", 'a\\*', '[[:alpha:]]*', '']
IFSES = [None, '', ':', ' :', ',', 'a', ' \t\n', ':,']

def word(r, depth=0):
    """a word that expands to something - as arguments, most of it quoted or not"""
    v = r.choice(['x', 'y', 'z'])
    forms = ['$' + v, '"$' + v + '"', '${' + v + '-dflt}', '"${' + v + ':-d f}"', '${' + v + ':+set}',
             '${#' + v + '}', '${' + v + '#' + r.choice(PATTERNS) + '}', '"${' + v + '%%' + r.choice(PATTERNS) + '}"',
             '$(( ' + str(r.randint(0, 9)) + ' ' + r.choice(['+', '-', '*', '%', '<<', '&', '|', '^']) + ' ' + str(r.randint(1, 9)) + ' ))',
             '"$@"', '$@', '"$*"', '$*', '$#', 'lit', "'s q'", '"d q"', 'a\\ b', '*.none']
    if depth < 2 and r.random() < 0.25:
        forms.append('"$(printf %s ' + word(r, depth + 1) + ')"')
        forms.append('$(printf "%s " ' + word(r, depth + 1) + ')')
    return r.choice(forms)

def quote(v):
    return "'" + v.replace("'", "'\\''") + "'"

def statement(r, depth=0):
    k = r.randrange(16)
    v = r.choice(['x', 'y', 'z'])
    if k == 0:
        return v + '=' + quote(r.choice(VALUES))
    if k == 1:
        return 'unset ' + v
    if k == 2:
        ifs = r.choice(IFSES)
        return 'unset IFS' if ifs is None else 'IFS=' + quote(ifs)
    if k == 3:
        return 'set -- ' + ' '.join(quote(r.choice(VALUES)) for _ in range(r.randint(0, 3)))
    if k in (4, 5, 6):
        return "printf '[%s]' " + ' '.join(word(r) for _ in range(r.randint(1, 3))) + '; echo'
    if k == 7:
        pats = ' | '.join(r.choice(PATTERNS) or '""' for _ in range(r.randint(1, 2)))
        return 'case ' + word(r) + ' in ' + pats + ') echo hit;; *) echo miss;; esac'
    if k == 8 and depth < 2:
        return 'for i in ' + ' '.join(word(r) for _ in range(r.randint(1, 3))) + "; do printf '<%s>' \"$i\"; done; echo"
    if k == 9:
        return 'test -n ' + word(r) + ' && echo yes || echo no'
    if k == 10 and depth < 2:
        return 'f() { ' + statement(r, depth + 1) + '; return ' + str(r.randint(0, 3)) + '; }; f ' + word(r) + '; echo "st=$?"'
    if k == 11:
        return 'cat <<' + r.choice(['EOF', "'EOF'"]) + '\n' + r.choice(['a $x b', 'lit', '${y-none}', '$(printf in)', 'c\\', '\t tab']) + '\nEOF'
    if k == 12:
        return ('printf \'%s\\n\' ' + word(r) + ' > "$T/f"; cat "$T/f"; printf \'%s\\n\' ' + word(r) +
                ' >> "$T/f"; wc -l < "$T/f" | tr -d " "')
    if k == 13 and depth < 2:
        return 'if ' + r.choice(['true', 'false', 'test -z "$x"', '[ "$y" = a ]']) + '; then ' + statement(r, depth + 1) + '; else echo else; fi'
    if k == 14:
        return 'read -r ' + ' '.join(r.sample(['p', 'q', 's'], r.randint(1, 3))) + " <<'EOF'\n" + r.choice(VALUES + ['a b c d']) + "\nEOF\nprintf '[%s]' \"$p\" \"$q\" \"$s\"; echo"
    return '(' + statement(r, depth + 1) + '); echo "sub=$?"' if depth < 2 else 'echo end'

def script(r):
    lines = ['T=.', 'x=a y=\'a b\' z=']
    lines += [statement(r) for _ in range(r.randint(3, 9))]
    lines.append('echo "last=$?"')
    return '\n'.join(lines) + '\n'

def run(argv, text, scratch):
    p = os.path.join(scratch, 's.sh')
    with open(p, 'w') as f:
        f.write(text)
    try:
        # A relative path and no arguments: anything that differs between
        # the two scratch directories must not reach the output.
        c = subprocess.run(argv + ['s.sh'], cwd=scratch, capture_output=True, timeout=10,
                           env=dict(os.environ, LC_ALL='C'))
        return c.stdout, c.returncode
    except subprocess.TimeoutExpired:
        return b'<timeout>', -1

BASH = shutil.which('bash')

def outputs(text, shells):
    res = []
    for sh in shells:
        d = tempfile.mkdtemp(prefix='dfz-')
        try:
            res.append(run(sh, text, d))
        finally:
            shutil.rmtree(d, ignore_errors=True)
    return res

def differs(text):
    """dash's result and this shell's - equal unless there is a finding"""
    d, s = outputs(text, [[DASH], [RELFSH]])
    # A finding is a difference from BOTH references, which agree with each
    # other. Where dash and bash disagree the question is open, and this
    # shell's answer - whichever side it takes - is not a finding: a
    # leading non-whitespace IFS character inside a parameter is an empty
    # field in bash and here and none in dash, and `$@` in a here-document
    # with IFS empty joins with nothing in dash and with spaces in bash
    # (Iteration 471). GOALS.md records the choices made on purpose.
    if d != s and BASH:
        (b,) = outputs(text, [[BASH, '--posix']])
        if b != d:
            return s, s
    return d, s

def shrink(text):
    lines = text.split('\n')
    i = 2
    while i < len(lines):
        trial = lines[:i] + lines[i + 1:]
        d, s = differs('\n'.join(trial))
        if d != s:
            lines = trial
        else:
            i += 1
    return '\n'.join(lines)

def main():
    a = sys.argv[1:]
    secs = int(a[a.index('--seconds') + 1]) if '--seconds' in a else 60
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(ROOT, 'tests', 'fuzzfinds')
    seed = int(a[a.index('--seed') + 1]) if '--seed' in a else int(time.time())
    if not DASH:
        print('difffuzz: dash is not installed; it is the reference'); return 2
    r = random.Random(seed)
    end = time.time() + secs
    n = found = 0
    seen = set()
    while time.time() < end:
        text = script(r)
        n += 1
        d, s = differs(text)
        if d == s:
            continue
        small = shrink(text)
        key = hashlib.sha1(small.encode()).hexdigest()[:10]
        if key in seen:
            continue
        seen.add(key)
        found += 1
        os.makedirs(out, exist_ok=True)
        d, s = differs(small)
        with open(os.path.join(out, 'diff-' + key + '.sh'), 'w') as f:
            f.write('# difffuzz seed %d: dash %r status %d / this shell %r status %d\n' % (seed, d[0], d[1], s[0], s[1]))
            f.write(small)
        print('DIFF', key, 'dash', d, 'relf', s)
    print('difffuzz: %d scripts, %d difference(s), seed %d' % (n, found, seed))
    return 1 if found else 0

if __name__ == '__main__':
    sys.exit(main())
