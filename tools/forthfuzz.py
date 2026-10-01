#!/usr/bin/env python3
"""tools/forthfuzz.py [N] [SEED] [SHELL] - fuzzing the forth builtin's errors.

The articles say an error the Forth system detects fails only the
command it happens in: `$?` is 1, the shell goes on. Four review rounds
in a row (Iterations 586-593) then found a way to break that by hand -
a stack underflow at the prompt, a failing include repeated, a file
including itself, a long command before an include. This does what the
reviewers did, at random and every time: each case is a short shell
script of steps that make such errors - underflow and excess on the
stack, stack overflow, undefined words, THROW and ABORT", division by
zero, addresses outside the shell's memory, compile-only words,
EVALUATE, and includes of generated files (self-inclusion, chains, long
lines, missing files, directories) - at the forth prompt and in loaded
builtins, in pipelines, $(...), subshells, functions, loops and || lists.

After the steps the case checks that the shell is alive, DEPTH is 0, a
variable set first is intact, a good include still works, a loop still
runs, and no file descriptor was left open. A failing case is shrunk,
step by step, to the smallest script that still fails, and printed.

What the articles say is NOT isolated is never generated: a store into
the shell's own memory, a word that takes more than 16 cells from the
stack and then pushes, redefining an existing word. Written in
Iteration 595.
"""
import os, random, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 595
SHELL = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(ROOT, 'relfsh')
TIMEOUT = 30
MISUSE = os.environ.get('FORTHFUZZ_MISUSE') == '1'


class Case:
    """One generated case: its steps, and the files they include."""
    def __init__(self, rng, d):
        self.rng, self.d, self.n, self.files = rng, d, 0, {}

    def name(self, prefix):
        self.n += 1
        return '%s%d' % (prefix, self.n)

    # -- Forth atoms: text that, interpreted at the forth prompt, makes one
    # -- error the system detects, or does something harmless
    def atom(self, in_word=False):
        r = self.rng
        k = r.choice([1, 2, 3, 15, 16, 17, 18, 19, 20, 30, 60])
        kinds = ['underflow', 'dots', 'excess', 'undefined', 'throw', 'abort', 'div0',
                 'badaddr', 'overflow', 'rec', 'takes', 'fine', 'evaluate']
        if not in_word:
            kinds += ['compileonly', 'include', 'include', 'include', 'rlegal', 'rlegal']
            if MISUSE:
                kinds += ['rmisuse', 'rmisuse']
        kind = r.choice(kinds)
        if kind == 'underflow':
            return 'DROP ' * (1 if in_word else k)
        if kind == 'dots':
            return '. ' * (1 if in_word else k)
        if kind == 'excess':
            return ' '.join(str(i) for i in range(k))
        if kind == 'undefined':
            return 'NOSUCH%d' % r.randrange(1000)
        if kind == 'throw':
            return '%d THROW' % r.choice([1, 42, -1, -2, -3, -4, -5, -9, -10, -13, 0])
        if kind == 'abort':
            return 'ABORT" boom"'
        if kind == 'div0':
            return r.choice(['1 0 /', '1 0 MOD', '7 0 /MOD', '-5 0 /'])
        if kind == 'badaddr':
            return r.choice(['0 @', '0 C@', '8 @', '-8 @', '0 0 !', '1 0 C!', '4096 @'])
        if kind == 'overflow':
            w = self.name('FZP')
            return ': %s BEGIN 0 AGAIN ; %s' % (w, w) if not in_word else '0 0 0'
        if kind == 'rec':
            w = self.name('FZR')
            return ': %s RECURSE ; %s' % (w, w) if not in_word else '1'
        if kind == 'takes':
            # a word that only takes - never takes and then pushes
            w = self.name('FZT')
            return ': %s %d 0 DO DROP LOOP ; %s' % (w, k, w) if not in_word else '%d 0 DO DROP LOOP' % k
        if kind == 'fine':
            return r.choice(['1 2 + DROP', '3 4 2DROP', 'DEPTH DROP', ': %s 5 ; %s DROP' % ((self.name('FZF'),) * 2)])
        if kind == 'evaluate':
            inner = r.choice(['DROP DROP', '1 0 /', 'NOSUCH1', '42 THROW', '1 2', '0 @'])
            return 'S" %s" EVALUATE' % inner
        if kind == 'rlegal':
            # correct Forth on the return stack, with errors thrown from
            # inside it (Iteration 601): it must always come through
            w = self.name('FZL')
            body = r.choice(['1 2 >R >R R> R> 2DROP', '5 0 DO I >R R> DROP LOOP',
                             '10 0 DO I 3 = IF UNLOOP EXIT THEN LOOP', '3 0 DO 4 0 DO J I + DROP LOOP LOOP',
                             '1 >R 42 THROW', '7 >R 0 @', '9 >R 1 0 /', '2 >R RECURSE',
                             '5 0 DO 1 0 / LOOP', '3 0 DO 42 THROW LOOP', '4 0 DO I >R 0 0 ! LOOP'])
            return ': %s %s ; %s' % (w, body, w)
        if kind == 'rmisuse':
            # the return stack misused: a wild return. No guarantee - the
            # jump may run anything - so only with FORTHFUZZ_MISUSE=1, to
            # measure, never in tests/verify
            w = self.name('FZM')
            k = r.randint(1, 10)
            body = r.choice(['%d >R' % r.choice([0, 1, 7, -1, 100000]), 'R> ' * k + 'DROP ' * k,
                             '10 0 DO I 5 = IF EXIT THEN LOOP', '1 0 DO 2 0 DO EXIT LOOP LOOP'])
            return ': %s %s ; %s' % (w, body, w)
        if kind == 'compileonly':
            return r.choice(['>R', 'R>', 'R@', 'I', 'EXIT'])
        return self.include()

    def forth_text(self, max_atoms=4):
        text = ' '.join(self.atom() for _ in range(self.rng.randint(1, max_atoms)))
        if self.rng.random() < 0.15:
            text = ' ' * self.rng.choice([100, 250, 280, 400, 600]) + text
        return text

    # -- files to include
    def include(self):
        r = self.rng
        kind = r.choice(['plain', 'plain', 'self', 'cycle', 'chain', 'long', 'missing', 'dir', 'empty', 'nonl'])
        if kind == 'missing':
            return 'S" %s/none%d.4" INCLUDED' % (self.d, r.randrange(100))
        if kind == 'dir':
            return 'S" %s" INCLUDED' % self.d
        path = os.path.join(self.d, self.name('f') + '.4')
        if kind == 'plain':
            lines = [' '.join(self.atom_in_file() for _ in range(r.randint(1, 3))) for _ in range(r.randint(1, 4))]
        elif kind == 'self':
            lines = [self.atom_in_file(), 'S" %s" INCLUDED' % path]
        elif kind == 'cycle':
            other = os.path.join(self.d, self.name('f') + '.4')
            self.files[other] = 'S" %s" INCLUDED\n' % path
            lines = ['S" %s" INCLUDED' % other]
        elif kind == 'chain':
            lines, nxt = [self.atom_in_file()], None
            for _ in range(r.randint(2, 12)):
                p = os.path.join(self.d, self.name('f') + '.4')
                self.files[p] = (self.atom_in_file() + '\n' + ('S" %s" INCLUDED\n' % nxt if nxt else ''))
                nxt = p
            lines.append('S" %s" INCLUDED' % nxt)
        elif kind == 'long':
            n = r.choice([100, 250, 254, 255, 256, 257, 300, 600])
            lines = ['\\ ' + 'x' * (n - 2), self.atom_in_file()]
        elif kind == 'empty':
            lines = []
        else:   # no newline at the end
            self.files[path] = self.atom_in_file()
            return 'S" %s" INCLUDED' % path
        self.files[path] = ''.join(l + '\n' for l in lines)
        return 'S" %s" INCLUDED' % path

    def atom_in_file(self):
        a = self.atom()
        return a if 'INCLUDED' not in a or self.rng.random() < 0.5 else '1 2 2DROP'

    # -- a loaded builtin, defined from a file, whose body is one atom
    def builtin(self):
        w = self.name('FZB')
        body = self.atom(in_word=True)
        path = os.path.join(self.d, self.name('b') + '.4')
        self.files[path] = ": %s %s ;\n' %s S\" %s\" BUILTIN\n" % (w, body, w, w.lower())
        return ["forth 'S\" %s\" INCLUDED'" % path, w.lower()]

    # -- shell steps
    def step(self):
        r = self.rng
        f = "forth '%s'" % self.forth_text()
        form = r.choice(['plain', 'plain', 'plain', 'subst', 'pipe', 'subshell', 'func',
                         'loop', 'or', 'redir', 'multi', 'builtin'])
        if form == 'plain':
            return [f]
        if form == 'subst':
            return ['x=$(%s 2>&1)' % f]
        if form == 'pipe':
            return ['%s 2>&1 | cat >/dev/null' % f]
        if form == 'subshell':
            return ['(%s)' % f]
        if form == 'func':
            fn = self.name('fn')
            return ['%s() { %s; }' % (fn, f), fn]
        if form == 'loop':
            return ['for i in 1 2 3; do %s; done' % f]
        if form == 'or':
            return ['%s || :' % f]
        if form == 'redir':
            return ['%s 2>/dev/null >/dev/null' % f]
        if form == 'multi':
            return ["forth '%s' '%s' '%s'" % (self.forth_text(1), self.forth_text(1), self.forth_text(1))]
        pre, call = self.builtin()
        return [pre, r.choice([call, '%s | cat' % call, 'y=$(%s)' % call, '%s || :' % call])]


# The file descriptors are listed into files: a count through $(...)
# also counts that substitution's own pipe, some of the time. Each
# marker starts a line of its own - `.` prints no newline.
PRELUDE = r'''keep=sentinel
ls /proc/$$/fd > fd0.txt 2>/dev/null
'''
CHECK = r'''echo; echo @@DEPTH; forth 'DEPTH . CR'
echo; echo "@@KEEP $keep"
echo; echo @@INC; forth 'S" %s/good.4" INCLUDED GOODWORD . CR'
echo; echo @@LOOP; for i in a b; do printf $i; done; echo
ls /proc/$$/fd > fd1.txt 2>/dev/null
if cmp -s fd0.txt fd1.txt; then echo "@@FD same"; else echo "@@FD $(tr '\n' ' ' < fd0.txt)-> $(tr '\n' ' ' < fd1.txt)"; fi
echo; echo @@END
'''


def script(d, steps):
    return PRELUDE + ''.join(s + '\n' for s in steps) + CHECK % d


def verdict(out):
    """None if the shell came through; else what went wrong."""
    lines = [l.rstrip('\r') for l in out.split('\n') if not l.startswith('Redefining: ')]
    text = '\n'.join(lines)
    if '@@END' not in lines:
        return 'the shell did not finish'
    if not re.search(r'^@@DEPTH\n0 $', text, re.M):
        return 'DEPTH is not 0'
    if '@@KEEP sentinel' not in lines:
        return 'a variable was lost'
    if not re.search(r'^@@INC\n11 $', text, re.M):
        return 'a good include failed'
    if not re.search(r'^@@LOOP\nab$', text, re.M):
        return 'a loop failed'
    m = re.search(r'^@@FD (.*)$', text, re.M)
    if not m:
        return 'the shell did not finish'
    if m.group(1) != 'same':
        return 'file descriptors changed: ' + m.group(1)
    return None


def run(d, steps, files):
    for p, content in files.items():
        with open(p, 'w') as fh:
            fh.write(content)
    try:
        p = subprocess.run([SHELL, '-c', script(d, steps)], cwd=d, capture_output=True,
                           timeout=TIMEOUT)
        return verdict(p.stdout.decode('utf-8', 'replace'))
    except subprocess.TimeoutExpired:
        return 'hung for %d s' % TIMEOUT


def shrink(d, steps, files, why):
    """Remove steps one at a time while the case still fails."""
    i = 0
    while i < len(steps):
        trial = steps[:i] + steps[i + 1:]
        if trial and run(d, trial, files):
            steps = trial
        else:
            i += 1
    return steps, run(d, steps, files) or why


def main():
    rng = random.Random(SEED)
    base = tempfile.mkdtemp(prefix='forthfuzz.')
    failures = 0
    try:
        for n in range(N):
            d = os.path.join(base, 'c%d' % n)
            os.mkdir(d)
            with open(os.path.join(d, 'good.4'), 'w') as fh:
                fh.write(': GOODWORD 11 ;\n')
            c = Case(rng, d)
            steps = []
            for _ in range(rng.randint(1, 8)):
                steps += c.step()
            why = run(d, steps, c.files)
            if why:
                failures += 1
                small, why2 = shrink(d, steps, c.files, why)
                print('FAIL case %d: %s' % (n, why2))
                for s in small:
                    print('    ' + s)
                for p in sorted(c.files):
                    if any(os.path.basename(p) in s for s in small) or any(p in s for s in small):
                        print('    # %s:' % p)
                        for l in c.files[p].splitlines():
                            print('    #   ' + l)
        print('forthfuzz: %d cases, %d failures (seed %d, %s)' % (N, failures, SEED, os.path.basename(SHELL)))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
