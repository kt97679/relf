#!/usr/bin/env python3
"""tools/regex-diff.py [N] [SEED] - rill/regex.4 against Python's re (Iteration 746).

Random patterns from the subset rill/regex.4 takes (literals, . \\s \\S \\d
\\w, classes with ranges and ^, groups, (?: ), |, * + ? and lazy forms,
^ and $) and random texts; for each, match (re.search's groups, an
unmatched group empty), all (re.findall: group 1, or the whole match)
and sub (re.sub with a literal replacement) - in one Forth program run
by Rill's image, compared line by line. A repeat is put only on an atom
that takes one character, never on a group: a group that can match
nothing, repeated, would loop in a backtracking matcher without a guard.
"""
import random, re, subprocess, sys
N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
rnd = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 746)
ALPHA = 'abx12 .'
def atom(depth):
    r = rnd.random()
    if r < 0.30: return rnd.choice('abx12 ')
    if r < 0.40: return '.'
    if r < 0.55: return rnd.choice([r'\d', r'\s', r'\w', r'\S', r'\D', r'\.'])
    if r < 0.68: return rnd.choice(['[ab]', '[^a ]', '[0-9]', '[a-x]', '[^0-9x]', '[.1]'])
    if r < 0.84 and depth < 2: return ('(' if rnd.random() < 0.7 else '(?:') + alt(depth + 1) + ')'
    return rnd.choice('abx')
def piece(depth):
    a = atom(depth)
    if a.startswith('('): return a
    return a + rnd.choice(['', '', '', '*', '+', '?', '*?', '+?', '??'])
def seq(depth): return ''.join(piece(depth) for _ in range(rnd.randint(1, 3)))
def alt(depth): return '|'.join(seq(depth) for _ in range(rnd.choice([1, 1, 1, 2, 3])))
def pattern():
    p = alt(0)
    if rnd.random() < 0.2: p = '^' + p
    if rnd.random() < 0.2: p = p + '$'
    return p
cases = []
for _ in range(N):
    p, t = pattern(), ''.join(rnd.choice(ALPHA) for _ in range(rnd.randint(0, 12)))
    try: re.compile(p)
    except re.error: continue
    cases.append((p, t))
def expect(p, t):
    m = re.search(p, t)
    out = ['M ' + ('-' if not m else ' '.join('[%s]' % (g or '') for g in (m.group(0),) + m.groups()))]
    items = [(m.group(1) or '') if m.re.groups else m.group(0) for m in re.finditer(p, t)]
    out.append('A ' + ' '.join('[%s]' % i for i in items))
    out.append('S [%s]' % re.sub(p, '<>', t))
    return out
forth = [': SHOW ( l --- )   DUP R-LEN 0 ?DO SPACE [CHAR] [ EMIT DUP I R-AT R-ANY>TEXT R-TYPE [CHAR] ] EMIT LOOP DROP ;']
for k, (p, t) in enumerate(cases):
    forth.append(': C%d  S" %s" R-TEXT S" %s" R-TEXT 2DUP R-MATCH ." M" DUP R-LEN IF SHOW ELSE DROP ."  -" THEN R-NL '
                 '2DUP R-ALL ." A" SHOW R-NL  S" <>" R-TEXT R-SUB ." S [" R-TYPE ." ]" R-NL ;  C%d' % (k, t, p, k))
open('/tmp/regex-diff.4', 'w').write('\n'.join(forth) + '\n')
got = subprocess.run(['./relf64', 'kernel64-rill.img', '/tmp/regex-diff.4'], capture_output=True, text=True,
                     stdin=subprocess.DEVNULL, timeout=600).stdout.split('\n')
want = [l for p, t in cases for l in expect(p, t)]
got = [g.replace('M  ', 'M ').rstrip() for g in got]
bad = 0
for k, (p, t) in enumerate(cases):
    w, g = want[3 * k: 3 * k + 3], [x.rstrip() for x in got[3 * k: 3 * k + 3]]
    w = [x.rstrip() for x in w]
    if w != g:
        bad += 1
        if bad <= 6: print('DIFFER pattern %r text %r\n  want %s\n  got  %s' % (p, t, w, g))
print('regex-diff: %d cases, %d different' % (len(cases), bad))
sys.exit(1 if bad else 0)
