#!/usr/bin/env python3
"""tools/native-c.py [ROUNDS] [N] - C, the cost of a call that crosses between CV8 and native code, measured.

Iteration 952 (NATIVE.md 18.9): NATIVE.md 18's model takes a crossing at C dispatches beyond what it counts.
On the assembly engine, with tests/native/hybrid.4's mechanism (CODE-MAP, [NATIVE][disp32], cv8_call and
NRET), six loops of N turns, each a Forth file of its own with the same prelude, so the start and the
laying of native code are the same in every one and drop out of the differences:
  base     a CV8 DO LOOP, empty                   cv8call  the same, calling `: CNOP ;`
  base8, cv8call8, native8: N/8 turns of eight different words in turn - CV8 NOPs, or native words that
           only return, whose shared `call rax` in NATIVE then changes its target at every call
  native   the same, calling a native word that only returns (CV8 -> native, and back)
  nempty   a native loop, empty                   n2n      the same, calling a native ret
  n2c      the same, calling CNOP through cv8_call (native -> CV8, and back)
d, a dispatch's time, is (cv8call - base) / 2: a call and an EXIT. In the model's terms a CV8 call of a
native word costs its call's dispatch, the callee's own work at R, and C; a native call of a CV8 word its
call at R, the callee's EXIT, and C. With the callee doing nothing, R's share is a ret's or a call's, taken
as nothing here:
  C in  = (native - base) / d - 1          C out = (n2c - nempty) / d - 1
bench-vm.py's method: every round runs every loop once, shuffled (round 0 a warm-up), the child's CPU time
by wait4, the differences per round, their medians and a bootstrap 95 % interval.
"""
import os, random, statistics as st, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
N = int(sys.argv[2]) if len(sys.argv) > 2 else 50000000
work = tempfile.mkdtemp(prefix='relf-native-c-')
# the prelude's NBODY, lays NATIVE as 122, 0x7A (engine/opcodes.tab), as tests/native/hybrid.4 does
PRELUDE = r'''S" forth/extend.4" INCLUDED  S" forth/asm64.4" INCLUDED
ALSO ASSEMBLER  DECIMAL
: ?MAPPED ( a xt ior --- a xt )   ?DUP IF ." CODE-MAP: " . CR BYE THEN ;
4096 CODE-MAP ?MAPPED  CONSTANT CV8-CALL  CONSTANT CODE
CODE 4096 ASM-BUFFER
: NBODY, ( addr --- )   122 C,  HERE 4 + -  DUP C,  DUP 8 RSHIFT C,  DUP 16 RSHIFT C,  24 RSHIFT C,  NO-PEEP ;
HERE-A CONSTANT N-NOP  ret,
HERE-A CONSTANT N1 ret,  HERE-A CONSTANT N2 ret,  HERE-A CONSTANT N3 ret,  HERE-A CONSTANT N4 ret,
HERE-A CONSTANT N5 ret,  HERE-A CONSTANT N6 ret,  HERE-A CONSTANT N7 ret,  HERE-A CONSTANT N8 ret,
HERE-A CONSTANT N-EMPTY                  \ ( n --- ): n turns of nothing
  rcx r12 mov,  r12 [ r13 ] mov,  r13 8 # add,
  1 L:  rcx rcx test,  2 F jz,  rcx dec,  1 B jmp,  2 L:  ret,
HERE-A CONSTANT N-N2N                    \ ( n --- ): n calls of a native ret
  rcx r12 mov,  r12 [ r13 ] mov,  r13 8 # add,
  1 L:  rcx rcx test,  2 F jz,  rcx push,  N-NOP call,  rcx pop,  rcx dec,  1 B jmp,  2 L:  ret,
HERE-A CONSTANT N-N2C                    \ ( xt n --- ): n calls of a CV8 word through cv8_call
  rcx r12 mov,  rax [ r13 ] mov,  r12 [ r13 8 ] mov,  r13 16 # add,
  1 L:  rcx rcx test,  2 F jz,  rcx push,  rax push,  CV8-CALL call,  rax pop,  rcx pop,  rcx dec,  1 B jmp,
  2 L:  ret,
ABUF @ CODE THERE @ ABUF @ - MOVE  CODE 4096 CODE-SEAL DROP
PREVIOUS
: NNOP [ N-NOP NBODY, ] ;  : NEMPTY [ N-EMPTY NBODY, ] ;  : NN2N [ N-N2N NBODY, ] ;  : NN2C [ N-N2C NBODY, ] ;
: CNOP ;
: W1 [ N1 NBODY, ] ;  : W2 [ N2 NBODY, ] ;  : W3 [ N3 NBODY, ] ;  : W4 [ N4 NBODY, ] ;
: W5 [ N5 NBODY, ] ;  : W6 [ N6 NBODY, ] ;  : W7 [ N7 NBODY, ] ;  : W8 [ N8 NBODY, ] ;
: C1 ;  : C2 ;  : C3 ;  : C4 ;  : C5 ;  : C6 ;  : C7 ;  : C8 ;
'''
BODY = {'base': ': T %d 0 DO LOOP ; T', 'cv8call': ': T %d 0 DO CNOP LOOP ; T', 'native': ': T %d 0 DO NNOP LOOP ; T',
        'nempty': '%d NEMPTY', 'n2n': '%d NN2N', 'n2c': "' CNOP %d NN2C",
        # (the shared call rax in NATIVE, its target changing at every call: eight native words in turn)
        'base8': ': T %d 0 DO LOOP ; T',
        'cv8call8': ': T %d 0 DO C1 C2 C3 C4 C5 C6 C7 C8 LOOP ; T', 'native8': ': T %d 0 DO W1 W2 W3 W4 W5 W6 W7 W8 LOOP ; T'}
files = {}
for k, b in BODY.items():
    p = os.path.join(work, k + '.4')
    open(p, 'w').write(PRELUDE + (b % (N // 8 if k.endswith('8') else N)) + '\nDEPTH . CR BYE\n')
    files[k] = p

def run(path):
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.dup2(os.open(path, os.O_RDONLY), 0)
        os.dup2(w, 1); os.dup2(w, 2); os.close(r)
        try: os.execv('./relfasm64', ['./relfasm64', 'forth/kernel64.img'])
        finally: os._exit(127)
    os.close(w)
    out = b''
    while True:
        b = os.read(r, 65536)
        if not b: break
        out += b
    os.close(r)
    _, status, ru = os.wait4(pid, 0)
    lines = [l.strip() for l in out.decode('latin-1').replace('\r', '').split('\n') if l.strip() and l.strip() != 'OK'
             and not l.startswith('Redefining') and 'Welcome' not in l]
    if lines != ['0'] or status != 0:
        sys.exit('native-c: %s did not end with an empty stack: %r' % (path, lines))
    return ru.ru_utime + ru.ru_stime

T = {k: [] for k in BODY}
for rnd in range(ROUNDS + 1):
    ks = list(BODY); random.shuffle(ks)
    for k in ks:
        t = run(files[k])
        if rnd: T[k].append(t)
def boot(xs, k=2000):
    m = sorted(st.median(random.choices(xs, k=len(xs))) for _ in range(k))
    return m[int(.025 * k)], m[int(.975 * k)]
per = lambda a, b: [(x - y) / N * 1e9 for x, y in zip(T[a], T[b])]     # ns a turn, per round
d = [x / 2 for x in per('cv8call', 'base')]
cin = [x / y - 1 for x, y in zip(per('native', 'base'), d)]
cout = [x / y - 1 for x, y in zip(per('n2c', 'nempty'), d)]
print('tools/native-c.py: %d rounds, %d turns a loop, relfasm64 forth/kernel64.img' % (ROUNDS, N))
for k in BODY: print('  %-8s %.3f s (median CPU time)' % (k, st.median(T[k])))
def row(name, xs, unit):
    lo, hi = boot(xs)
    print('%-44s %7.3f [%.3f-%.3f] %s' % (name, st.median(xs), lo, hi, unit))
row('d: a dispatch, (cv8call - base) / 2', d, 'ns')
row('a CV8 call and EXIT, cv8call - base', per('cv8call', 'base'), 'ns')
row('CV8 -> native and back, native - base', per('native', 'base'), 'ns')
row('a native call and ret, n2n - nempty', per('n2n', 'nempty'), 'ns')
row('native -> CV8 and back, n2c - nempty', per('n2c', 'nempty'), 'ns')
row('eight CV8 words in turn: a call and EXIT', per('cv8call8', 'base8'), 'ns')
row('eight native words in turn: CV8 -> native and back', per('native8', 'base8'), 'ns')
row('C in: (native - base) / d - 1', cin, 'dispatches')
row('C out: (n2c - nempty) / d - 1', cout, 'dispatches')

# In the model's units (NATIVE.md 18.9): a family's dispatch is its CV8 time over its dispatches - 951's
# times (bench/reports/native-r-951.txt) over 950's counts (bench/reports/native-knee-951.txt), on the
# workloads both measured at the same size, each less its start - and C its crossing's extra time over that:
# eight native words in turn against eight CV8 words, the case whose shared call changes its target.
import math, re
RR, KR = 'bench/reports/native-r-951.txt', 'bench/reports/native-knee-951.txt'
if os.path.exists(RR) and os.path.exists(KR):
    r, k = open(RR).read(), open(KR).read()
    TT = {m.group(1).strip(): float(m.group(2)) for m in re.finditer(r'^(.{18}) \S+\s+([0-9.]+)s\s+[0-9.]+s', r, re.M)}
    DD = {m.group(1).strip(): int(m.group(2)) for m in re.finditer(r'^(.{18}) \S+\s+D\s+(\d+)', k, re.M)}
    start = {'forth': 'start:forth', 'system': 'start:forth', 'rill3': 'start:rill3', 'shell': 'start:shell'}
    same = {'forth': ['lab fib', 'lab loop', 'lab bubble', 'lab ackermann', 'lab sieve', 'bench.4 fannkuch', 'bench.4 collatz'],
            'system': ['CORE', 'lab parse'], 'rill3': ['rill3 loop', 'rill3 calls'],
            'shell': ['shell loop', 'shell fn', 'shell str', 'shell arith', 'shell realistic']}
    extra = st.median(per('native8', 'base8')) - st.median(per('cv8call8', 'base8'))
    print('\na crossing\'s extra time, eight words in turn: %.3f ns; in each family\'s dispatches:' % extra)
    for f, ws in same.items():
        ds = [(TT[w] - TT[start[f]]) / (DD[w] * (5 if f == 'shell' else 1)) * 1e9 for w in ws]
        g = math.exp(sum(map(math.log, ds)) / len(ds))
        print('  %-7s a dispatch %.3f ns (geometric mean of %d), C %.2f' % (f, g, len(ds), extra / g))
