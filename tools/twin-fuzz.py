#!/usr/bin/env python3
"""tools/twin-fuzz.py [N] [SEED] - the two engines as each other's oracle.

Generates N random Forth programs (default 3000) from arithmetic, logic,
comparison and stack words, runs every one on the C engine (relf64) and
on the assembly engine (relfasm64), and compares what each leaves on the
stack. No expected answers: they run the same image, so any difference
is a bug in one engine. TESTING-IDEAS.md 3; written in Iteration 555.

The generator knows each word's stack effect, so every program is valid;
it keeps out what Forth 2012 leaves undefined - a zero divisor, the most
negative number divided by -1, a shift of 64 or more - which the probes
at the end try on purpose, reporting what each engine does. Values lean
to the edges: 0, 1, -1, the extremes, powers of two and their
neighbours. A difference is printed as the program, shortest first.
"""
import os, random, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 555
rng = random.Random(SEED)
ENGINES = ['./relf64', './relfasm64']
IMAGE = 'forth/kernel64.img'
MIN, MAX = -(1 << 63), (1 << 63) - 1

def literal():
    r = rng.random()
    if r < 0.35:
        v = rng.choice([0, 1, -1, 2, -2, 3, 7, 10, 63, 64, 255, 256, MAX, MIN, MAX - 1, MIN + 1])
    elif r < 0.6:
        v = (1 << rng.randrange(64)) + rng.choice([-1, 0, 1])
    elif r < 0.8:
        v = rng.randrange(-1000, 1000)
    else:
        v = rng.randrange(MIN, MAX)
    v = (v + (1 << 63)) % (1 << 64) - (1 << 63)     # into the signed range
    return '1 63 LSHIFT' if v == MIN else str(v)     # MIN has no safe literal

# (word or phrase, items taken, items left); phrases guard what is undefined
WORDS = [
    ('+', 2, 1), ('-', 2, 1), ('*', 2, 1), ('AND', 2, 1), ('OR', 2, 1), ('XOR', 2, 1),
    ('NEGATE', 1, 1), ('INVERT', 1, 1), ('ABS', 1, 1), ('2*', 1, 1), ('2/', 1, 1),
    ('1+', 1, 1), ('1-', 1, 1), ('0=', 1, 1), ('0<', 1, 1), ('0<>', 1, 1),
    ('=', 2, 1), ('<>', 2, 1), ('<', 2, 1), ('>', 2, 1), ('U<', 2, 1), ('U>', 2, 1),
    ('MIN', 2, 1), ('MAX', 2, 1), ('WITHIN', 3, 1),
    ('DUP', 1, 2), ('DROP', 1, 0), ('SWAP', 2, 2), ('OVER', 2, 3), ('ROT', 3, 3),
    ('NIP', 2, 1), ('TUCK', 2, 3), ('2DUP', 2, 4), ('2DROP', 2, 0), ('2SWAP', 4, 4),
    ('2OVER', 4, 6), ('?DUP 0= IF 0 THEN', 1, 1), ('3 PICK', 4, 5), ('2 ROLL', 3, 3),
    ('63 AND LSHIFT', 2, 1), ('63 AND RSHIFT', 2, 1),
    ('UM*', 2, 2), ('M*', 2, 2), ('D+', 4, 2), ('DNEGATE', 2, 2),
    ('ABS 2 OR /', 2, 1), ('ABS 2 OR MOD', 2, 1), ('ABS 2 OR /MOD', 2, 2),
    ('ABS 2 OR 0 SWAP UM/MOD', 2, 2),              # (lo u) -> 0 as the high cell
    ('ABS 2 OR >R S>D R> SM/REM', 2, 2), ('ABS 2 OR >R S>D R> FM/MOD', 2, 2),
    ('ABS 2 OR */', 3, 1), ('ABS 2 OR */MOD', 3, 2),
    ('S>D', 1, 2), ('D>S', 2, 1), ('IF 1 ELSE 2 THEN', 1, 1),
    ('0 ?DO 1+ LOOP', 2, 1) ,                      # guarded below: count 0..7
]

def defined(word):
    r = subprocess.run([ENGINES[0], IMAGE], input='S" forth/extend.4" INCLUDED\n: T [\'] %s DROP ;\nBYE\n' % word,
                       capture_output=True, text=True, errors='replace', timeout=20)
    return 'Not found' not in r.stdout + r.stderr and 'Undefined' not in r.stdout + r.stderr
missing = sorted({w.split()[-1] for w, _, _ in WORDS for t in [w.split()] if not all(
    defined(x) for x in t if not x.lstrip('-').isdigit() and x not in ('IF', 'ELSE', 'THEN', '?DO', 'LOOP'))})
WORDS = [(w, a, b) for w, a, b in WORDS if not any(x in missing for x in w.split())]
if missing:
    print('not in this system, left out:', ' '.join(missing))

def program():
    code, depth = [], 0
    for _ in range(rng.randrange(3, 24)):
        w, take, give = rng.choice(WORDS)
        while depth < take:                         # feed it what it takes
            code.append(literal()); depth += 1
        if w == '0 ?DO 1+ LOOP':
            code.append('7 AND')                    # a count of 0..7
        elif w == '2 ROLL' and depth < 3 or w == '3 PICK' and depth < 4:
            continue
        code.append(w); depth += give - take
        if rng.random() < 0.3:
            code.append(literal()); depth += 1
    return ' '.join(code)

def run(engine, progs):
    """One engine, many programs: each defined, run, its stack printed in
    hex and cleared. Output is one line per program."""
    src = ['S" forth/extend.4" INCLUDED', ': CLEAR DEPTH 0 ?DO DROP LOOP ;', ': SHOW DEPTH 0 ?DO U. LOOP CR ;', 'HEX']
    for i, p in enumerate(progs):
        # One definition over several lines: the input buffer holds a
        # limited line, and the first version's long ones were cut
        # mid-word (THEN arrived as THE) - see PROGRESS 555.
        src.append('DECIMAL : P%d' % i)
        line = ''
        for tok in p.split():
            if len(line) + len(tok) > 56:
                src.append(line); line = ''
            line += tok + ' '
        src.append(line + '; P%d HEX SHOW CLEAR' % i)
    src.append('BYE')
    r = subprocess.run([engine, IMAGE], input='\n'.join(src) + '\n', capture_output=True,
                       text=True, errors='replace', timeout=600)
    lines = [l.replace(' OK', '').strip() for l in r.stdout.replace('\r', '').split('\n')]
    return [l for l in lines if l and 'Welcome' not in l and l != 'OK'], r.stderr

progs = [program() for _ in range(N)]
diffs = []
for start in range(0, N, 500):
    batch = progs[start:start + 500]
    (a, ea), (b, eb) = run(ENGINES[0], batch), run(ENGINES[1], batch)
    if a == b and len(a) != len(batch):
        # Both engines printed the same extra lines: compared all the
        # same, and the extra lines shown, since something printed them.
        extra = [l for l in a if not all(c in '0123456789ABCDEF ' for c in l)]
        print('batch %d: %d lines for %d programs, identical on both; not a stack dump: %s'
              % (start, len(a), len(batch), extra[:3]))
        continue
    if len(a) != len(batch) or len(b) != len(batch):
        print('batch %d: output lines %d and %d for %d programs - a crash or an error?'
              % (start, len(a), len(b), len(batch)))
        print('  C:   ', (ea or '').strip()[:200]); print('  asm: ', (eb or '').strip()[:200])
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                print('  first difference at program %d: %s\n    C:   %s\n    asm: %s' % (start + i, batch[i], x, y)); break
        continue
    diffs += [(batch[i], x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
print('%d programs, %d differences (seed %d)' % (N, len(diffs), SEED))
for p, x, y in sorted(diffs, key=lambda d: len(d[0]))[:8]:
    print('  %s\n    C:   %s\n    asm: %s' % (p, x, y))

# What Forth leaves undefined, tried on purpose: not failures, but each
# engine's answer on record - a crash here is worth knowing about.
print('undefined cases, each engine:')
for probe in ['7 0 /', '1 63 LSHIFT -1 /', '1 63 LSHIFT -1 MOD', '1 64 LSHIFT', '1 65 LSHIFT',
              '-1 64 RSHIFT', '5 0 0 UM/MOD', '1 1 1 UM/MOD']:
    outs = []
    for e in ENGINES:
        r = subprocess.run([e, IMAGE], input='S" forth/extend.4" INCLUDED DECIMAL\n: T ." [" %s HEX DEPTH 0 ?DO U. LOOP ." ]" ;\nT BYE\n' % probe,
                           capture_output=True, text=True, errors='replace', timeout=20)
        import re
        m = re.search(r'\[([^\]]*)\]', r.stdout)
        tail = (r.stderr.strip().splitlines() or [''])[-1][:40]
        outs.append(m.group(1).strip() if m else ('no result, exit %d %s' % (r.returncode, tail)).strip())
    print('  %-22s C: %-28s asm: %s%s' % (probe, outs[0], outs[1], '' if outs[0] == outs[1] else '   <- differ'))
