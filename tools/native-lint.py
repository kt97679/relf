#!/usr/bin/env python3
"""native-lint.py - two slips the native compiler's sources have made, checked.

prompts/15-repeat-slip: on the second occurrence of a mistake, mechanise
the check. Both of these occurred more than once (docs/PROGRESS.md):

1. A word defined inside a word-list section - between a line
   `CURRENT @  X CURRENT !` and a line `CURRENT !` - goes into X (NPRIMS,
   NCTRL, NTRANS), which the host's search order never holds while it
   compiles source. Such a word can be found only by SEARCH-WORDLIST at
   run time; a reference to it BY NAME, anywhere in the source, inside
   the section or out, is "Undefined word" or, worse, the host's word of
   the same name. Iterations 611 (N-LOOP-END), 622 (N-COMPILEC), 623
   (N-STUB24). Names the host defines too - IF, DO, : - are its own and
   exempt.
2. A host word used above its definition in the same file: Forth binds
   at compile time, so the use is "Undefined word". Iteration 627
   (N>BODY in N-SHADOW).

The host's names come from the files it is built of and loads before
these. Target code - N: and NH: bodies, NCODE names, kernel-native.4 -
is the target's and not checked here. Exit status: the number of faults.
usage: tools/native-lint.py [FILES...]     (default: the native sources)
       tools/native-lint.py --self-test   the four slips rebuilt: each caught?
"""
import re, sys

HOST_FILES = ['forth/kernel.4', 'forth/extend.4', 'forth/asm64.4', 'forth/cross-core.4']
CHECKED = ['forth/native.4', 'forth/native-cross.4']
SEC_OPEN = re.compile(r'^CURRENT @\s+(\S+)\s+CURRENT !\s*(\\.*)?$')
SEC_CLOSE = re.compile(r'^CURRENT !\s*(\\.*)?$')
DEFINERS = {':', 'CREATE', 'VARIABLE', 'CONSTANT', 'VOCABULARY', 'DEFER', 'VALUE', 'PRIMITIVE', 'OPCODE'}
TARGET_DEFINERS = {'NCODE', 'N:', 'NH:', 'T:', 'LABEL'}
NAME_TAKERS = {"'", "[']", 'POSTPONE'}          # the next token is a reference
SKIP_NEXT = {'CHAR', '[CHAR]', "N'", 'N-ADDR'}   # the next token is not a host reference
STRINGS = {'."': '"', 'S"': '"', 'ABORT"': '"', '.(': ')', 'C"': '"', 'S\\"': '"'}

def number(t):
    return re.fullmatch(r"-?(\d+|\$[0-9A-Fa-f]+|#\d+|'.')", t) is not None

def tokens(path):
    """(line number, token, section or None) for the code in a file, comments and strings out."""
    sec = None
    for n, line in enumerate(open(path, encoding='utf-8', errors='replace'), 1):
        s = line.rstrip('\n')
        m = SEC_OPEN.match(s)
        if m:
            sec = m.group(1); continue
        if SEC_CLOSE.match(s):
            sec = None; continue
        toks = s.split()
        i = 0
        while i < len(toks):
            t = toks[i]
            if t == '\\':
                break
            if t == '(':
                while i < len(toks) and not toks[i].endswith(')'):
                    i += 1
                i += 1; continue
            if t in STRINGS:
                end = STRINGS[t]; i += 1
                while i < len(toks) and not toks[i].endswith(end):
                    i += 1
                i += 1; continue
            yield n, t, sec
            i += 1

def definitions(path):
    """{name: (line, section)} of the words a file defines at host level or in sections."""
    out = {}
    stream = list(tokens(path))
    target_body = False
    k = 0
    while k < len(stream):
        n, t, sec = stream[k]
        if target_body:
            if t in ('N;', 'T;'):
                target_body = False
            k += 1; continue
        if t in DEFINERS and k + 1 < len(stream):
            out.setdefault(stream[k + 1][1], (stream[k + 1][0], sec))
            k += 2; continue          # the name defined is not a token of the code: `: NH:`
        if t in ('N:', 'NH:', 'T:'):
            target_body = True
        k += 1
    return out

def main(files):
    host = set()
    for f in HOST_FILES:
        host |= set(definitions(f))
    faults = 0
    defined_so_far = set(host)
    for f in files:
        defs = definitions(f)
        section_only = {nm: (ln, sec) for nm, (ln, sec) in defs.items() if sec and nm not in host}
        host_level = {nm: ln for nm, (ln, sec) in defs.items() if not sec}
        stream = list(tokens(f))
        k = 0
        target_body = False
        while k < len(stream):
            n, t, sec = stream[k]
            if target_body:                       # N: ... N; is target code
                if t in ('N;', 'T;'):
                    target_body = False
                k += 1; continue
            if t in ('N:', 'NH:', 'T:'):
                target_body = True; k += 2; continue
            if t in TARGET_DEFINERS or t in DEFINERS:
                if k + 1 < len(stream):
                    nm = stream[k + 1][1]
                    if not stream[k + 1][2]:
                        defined_so_far.add(nm)
                k += 2; continue
            if t in SKIP_NEXT:
                k += 2; continue
            refs = [t]
            if t in NAME_TAKERS and k + 1 < len(stream):
                refs = [stream[k + 1][1]]; k += 1
            for r in refs:
                if number(r):
                    continue
                if r in section_only:
                    ln, s2 = section_only[r]
                    print('%s:%d: %s is defined inside the %s section (line %d), where no '
                          'source can name it' % (f, n, r, s2, ln))
                    faults += 1
                elif r in host_level and r not in defined_so_far and host_level[r] > n:
                    print('%s:%d: %s is used above its definition (line %d)' % (f, n, r, host_level[r]))
                    faults += 1
            k += 1
        defined_so_far |= set(host_level)
    print('native-lint: %d fault(s) in %s' % (faults, ' '.join(files)))
    return faults

def self_test():
    """The negative controls: the four slips, rebuilt in copies of today's
    sources by moving the very definitions back where they once wrongly
    sat; each must be caught (prompts/16-fail-before-fix). A move that
    finds nothing to move - the sources changed - is reported, not passed."""
    import io, os, tempfile, contextlib
    nat = open('forth/native.4').read(); cross = open('forth/native-cross.4').read()
    def move(src, start, after, end):
        L = src.split('\n')
        a = next(i for i, l in enumerate(L) if re.match(start, l))
        b = a
        while not re.search(end, L[b]): b += 1
        blk = L[a:b + 1]; del L[a:b + 1]
        t = next(i for i, l in enumerate(L) if re.match(after, l))
        L[t + 1:t + 1] = blk
        return '\n'.join(L)
    cases = [
        ('611 N-LOOP-END in NCTRL', 'native.4', 'N-LOOP-END',
         lambda: move(nat, r'^: N-LOOP-END', r'^CURRENT @  NCTRL CURRENT !', r';\s*(\\.*)?$')),
        ('622 N-COMPILEC in NCTRL', 'native-cross.4', 'N-COMPILEC',
         lambda: move(cross, r'^CREATE N-COMPILEC', r'^CURRENT @  NCTRL CURRENT !', r'COMPILE,')),
        ('623 N-STUB24 in NTRANS', 'native-cross.4', 'N-STUB24',
         lambda: move(cross, r'^: N-STUB24', r'^CURRENT @  NTRANS CURRENT !', r'-1 N-DATA-OPEN ! ;')),
        ('627 N>BODY below its use', 'native-cross.4', 'N>BODY',
         lambda: move(cross, r'^: N>BODY', r'^  \?DUP IF NIP EXECUTE ELSE @ call, THEN ;', r'N-BASE - ;')),
    ]
    caught = 0
    for label, which, word, build in cases:
        try:
            text = build()
        except StopIteration:
            print('self-test: %s - could not be rebuilt from today\'s sources' % label); continue
        d = tempfile.mkdtemp(prefix='native-lint-')
        files = [os.path.join(d, 'native.4'), os.path.join(d, 'native-cross.4')]
        open(files[0], 'w').write(text if which == 'native.4' else nat)
        open(files[1], 'w').write(text if which == 'native-cross.4' else cross)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(files)
        hit = any(word in l for l in out.getvalue().split('\n') if not l.startswith('native-lint:'))
        print('self-test: %s - %s' % (label, 'caught' if hit else 'MISSED'))
        caught += hit
    print('native-lint self-test: %d of %d caught' % (caught, len(cases)))
    return len(cases) - caught

if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        sys.exit(self_test())
    sys.exit(min(main(sys.argv[1:] or CHECKED), 100))
