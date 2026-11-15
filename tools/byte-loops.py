#!/usr/bin/env python3
"""tools/byte-loops.py [OUT] - how much of relfsh's bytecode work is inside byte-at-a-time loops (Iteration 954).

The owner's question at 953: could general primitives - inner loops in the engine, the classic Forth
answer - close much of relfsh's gap to dash? This finds the shell image's byte loops and measures how much
of bench-vm's five scripts runs inside them, the work of every word they call included.

A loop is a backward branch within a word's body and the code from its target to it. A **byte loop** is a
leaf loop - no loop inside it, and nothing it calls reaches one (direct calls followed; EXECUTE and DEFER
not) - that touches a byte: C@, C!, COUNT or a superinstruction with C@ in it, in its body or in a
loop-free word it calls. Only such a loop could be one primitive. (A first count, any loop with a byte
operation in it, took in the loops over a tree's nodes and a command's words - 80 % of the dispatches,
and none of it a primitive's to take.) The counting engine (pair-corpus.py's, the C engine)
also takes a snapshot of the return stack:
  SAMPLE_EVERY=n   every n dispatches: shares of the dispatches          (default 997)
  SAMPLE_EVERY=0   on every millisecond of CPU time (ITIMER_PROF): shares of the time, the main
                   process only (bench-vm's five fork nothing)
A sample belongs to the innermost byte loop among its frames - the instruction dispatched, then each
return address - so a loop is charged for the words it calls, and a byte loop inside a line loop is the
byte loop's. Per loop the counts give its iterations (dispatches of its backward branch), its entries
(of the instruction before its first), so the bytes it takes on each entry, and its own dispatches per
iteration. Writes OUT (default bench/reports/byte-loops-954.txt) and prints it.
"""
import bisect, collections, os, struct, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import opcodes
OUT = sys.argv[1] if len(sys.argv) > 1 else 'bench/reports/byte-loops-954.txt'
SLOTS = 1 << 22
IMG = 'kernel64-shell.img'
WORKLOADS = ('loop', 'fn', 'str', 'arith', 'realistic')
SCALE = 5

def patch(text, old, new):
    if text.count(old) != 1:
        sys.exit('byte-loops: the text to patch occurs %d times, not once:\n%s' % (text.count(old), old))
    return text.replace(old, new)
work = tempfile.mkdtemp(prefix='relf-byte-loops-')
engine = os.path.join(work, 'relf-sample')
src = open('engine/cv8.c').read()
src = patch(src, '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP',
    '#include <sys/mman.h>\n#include <sys/time.h>\n'
    'static unsigned int *prof_map; static UNS64 prof_base; static int samp_fd = -1;\n'
    'static long samp_every, samp_ctr; static volatile sig_atomic_t samp_flag;\n'
    'static void samp_alarm(int s) { (void)s; samp_flag = 1; }\n'
    'static void sample(UNS64 ip, UNS64 rp) {\n'
    '    unsigned int buf[2 + 1024], n = 0; UNS64 p, top = prof_base + MEMSIZE;\n'
    '    buf[1] = (unsigned int)(ip - prof_base);\n'
    '    for (p = rp; p < top && n < 1024; p += CELL_BYTES) {\n'
    '        UNS64 v = CELL(p);\n'
    '        if (v >= prof_base && v < prof_base + MEMSIZE) buf[2 + n++] = (unsigned int)(v - prof_base); }\n'
    '    buf[0] = n; if (write(samp_fd, buf, (2 + n) * 4) < 0) {}\n}\n'
    '#define PROF(k)\n'
    '#define PROFIP(a) do { prof_map[((a) - prof_base) & (%d - 1)]++;\\\n'
    '    if (samp_every ? --samp_ctr == 0 : samp_flag) { samp_ctr = samp_every; samp_flag = 0; sample((a), rp); } } while (0)\n'
    '#define PROFDUMP' % SLOTS)
src = patch(src, '    NEXT();\ndo_call:',
    '    prof_base = cbase;\n'
    '    { int fd = open(getenv("COUNTS"), O_RDWR);\n'
    '      prof_map = mmap(0, %d * sizeof(unsigned int), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); close(fd);\n'
    '      samp_fd = open(getenv("SAMPLES"), O_WRONLY | O_CREAT | O_APPEND, 0644);\n'
    '      samp_every = samp_ctr = atol(getenv("SAMPLE_EVERY"));\n'
    '      if (!samp_every) { struct sigaction sa; struct itimerval it;\n'
    '          memset(&sa, 0, sizeof sa); sa.sa_handler = samp_alarm; sa.sa_flags = SA_RESTART;\n'
    '          sigaction(SIGPROF, &sa, 0);\n'
    '          it.it_interval.tv_sec = it.it_value.tv_sec = 0; it.it_interval.tv_usec = it.it_value.tv_usec = 1000;\n'
    '          setitimer(ITIMER_PROF, &it, 0); } }\n'
    '    NEXT();\ndo_call:' % SLOTS)
open(engine + '.c', 'w').write(src)
subprocess.run(['cc', '-O2', '-I', os.path.join(ROOT, 'engine'), '-o', engine, engine + '.c'], check=True)

# ---- the image: words, their bodies decoded, their loops -------------------------
FMT = opcodes.formats(); opname, escname = opcodes.names()
d = open(IMG, 'rb').read(); C = 8
cell = lambda o: struct.unpack_from('<Q', d, o)[0]
nth = cell(8); ntails = cell(8 + C + nth * C)
img = d[8 + C + nth * C + C + ntails * 2 * C:]
heads = [cell(8 + C + i * C) for i in range(nth)]
def prev(nfa):
    tag = img[nfa - 1]
    if tag < 128: return (nfa - tag if tag else 0)
    if tag < 192: return nfa - (((tag & 63) << 8) | img[nfa - 2])
    return nfa - (((tag & 63) << 16) | (img[nfa - 2] << 8) | img[nfa - 3])
hdr = {}
for h in heads:
    n = h
    while n:
        name, c_, ll, st, _ = opcodes.header(img, n); hdr[n] = (name, n - st); n = prev(n)
nfas = sorted(hdr); WORDS = []                   # (xt, end, name)
for i, n in enumerate(nfas):
    end = (nfas[i + 1] - hdr[nfas[i + 1]][1]) if i + 1 < len(nfas) else len(img)
    WORDS.append((n + 1, end, hdr[n][0]))
XTS = [w[0] for w in WORDS]
xt_of = {}
for xt, end, nm in WORDS: xt_of.setdefault(nm, xt)
INLINE3 = {xt_of[k] for k in ('(POSTPONE)',) if k in xt_of}
STRINGS = {xt_of[k] for k in ('(S")', '(.")', '(ABORT")') if k in xt_of}
def s16(v): return v - 65536 if v >= 32768 else v
def decode(xt, end):
    """(address, length, name, branch target or None, call target or None)"""
    out, ip = [], xt
    while ip < end:
        op = img[ip]; f = FMT.get(op, '-') if op < 0x80 else 'call'
        if f == 'data': break
        nm = escname.get(img[ip + 1], '?') if f == 'sel' else opname.get(op, '?')
        tgt = call = None
        if f in ('b16', 'b8', 'i8b16'):
            k = 2 if f == 'i8b16' else 1
            if f == 'b8': off = img[ip + 1] - 256 if img[ip + 1] >= 128 else img[ip + 1]; ln = 2
            else: off = s16(img[ip + k] | img[ip + k + 1] << 8); ln = k + 2
            tgt = ip + k + off
        elif f == 'u16': ln = 3
        elif f in ('u8', 'i8'): ln = 2
        elif f == 'i32': ln = 5
        elif f == 'u64': ln = 9
        elif f == 'sel': ln = 2
        elif f == 'slot': ln = 4 if img[ip + 1] & 0x80 else 3
        elif f == '2slot':
            ln = 1; ln += 3 if img[ip + ln] & 0x80 else 2; ln += 3 if img[ip + ln] & 0x80 else 2
        elif f == 'call':
            ln = 2 if op < 0xC0 else 3
            call = ((op & 63) << 8) | img[ip + 1] if ln == 2 else ((op & 63) << 16) | img[ip + 1] << 8 | img[ip + 2]
            nm = 'call'
            if call in INLINE3: ln += 3
            elif call in STRINGS: ln += 1 + img[ip + ln]
        else: ln = 1
        out.append((ip, ln, nm, tgt, call)); ip += ln
    return out
BYTEOP = lambda nm: 'C@' in nm or 'C!' in nm or nm == 'COUNT'
BODY = {xt: decode(xt, end) for xt, end, nm in WORDS}
NAME = {xt: nm for xt, end, nm in WORDS}
has_byte = {xt: any(BYTEOP(i[2]) for i in b) for xt, b in BODY.items()}
has_loop = {xt: any(i[3] is not None and i[3] <= i[0] for i in b) for xt, b in BODY.items()}
# a word reaches a loop if it has one or calls - directly; EXECUTE and DEFER are not followed - a word that does
reaches = dict(has_loop)
changed = True
while changed:
    changed = False
    for xt, b in BODY.items():
        if not reaches[xt] and any(i[4] in reaches and reaches[i[4]] for i in b if i[4] is not None):
            reaches[xt] = changed = True
# the loop-free words that touch a byte, however deep: a per-byte helper
touches = {xt: has_byte[xt] for xt in BODY}
changed = True
while changed:
    changed = False
    for xt, b in BODY.items():
        if not touches[xt] and not reaches[xt] and any(touches.get(i[4]) and not reaches.get(i[4]) for i in b if i[4] is not None):
            touches[xt] = changed = True
LOOPS = []                                        # (start, end, word xt, branch address, byte?)
for xt, b in BODY.items():
    for a, ln, nm, tgt, call in b:
        if tgt is not None and xt <= tgt <= a:
            body = [i for i in b if tgt <= i[0] <= a]
            # a leaf: no loop of its own inside, nothing called that reaches one
            leaf = not any(i[3] is not None and tgt <= i[3] <= i[0] and i[0] != a for i in body) and \
                   not any(i[4] is not None and reaches.get(i[4]) for i in body)
            byte = leaf and (any(BYTEOP(i[2]) for i in body) or
                             any(i[4] is not None and touches.get(i[4]) for i in body))
            LOOPS.append((tgt, a + ln, xt, a, byte))
BYTE_LOOPS = [l for l in LOOPS if l[4]]
def innermost(addr):
    best = None
    for l in BYTE_LOOPS:                          # few hundred loops: a scan is fine
        if l[0] <= addr < l[1] and (best is None or l[1] - l[0] < best[1] - best[0]): best = l
    return best
# an index by address, for speed: each byte loop's span marks the addresses it covers
cover = {}
for l in sorted(BYTE_LOOPS, key=lambda l: -(l[1] - l[0])):
    for a in range(l[0], l[1]): cover[a] = l       # narrower loops written later win

# ---- run ------------------------------------------------------------------------
def scaled(w):
    import re
    t = open('tests/bench-vm/%s.sh' % w).read()
    t = re.sub(r'-lt (\d+)', lambda m: '-lt %d' % (int(m.group(1)) * SCALE), t)
    p = os.path.join(work, w + '.sh'); open(p, 'w').write(t); return p
def run(w, every, reps):
    cf, sf = os.path.join(work, 'c.bin'), os.path.join(work, 's.bin')
    open(cf, 'wb').write(bytes(SLOTS * 4)); open(sf, 'wb').close()
    for _ in range(reps):
        subprocess.run([engine, IMG, scaled(w)], env=dict(os.environ, COUNTS=cf, SAMPLES=sf, SAMPLE_EVERY=str(every)),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
    cnt = struct.unpack('<%dI' % SLOTS, open(cf, 'rb').read())
    raw = open(sf, 'rb').read(); samples = []; p = 0
    while p + 8 <= len(raw):
        n, ipo = struct.unpack_from('<II', raw, p)
        fr = struct.unpack_from('<%dI' % n, raw, p + 8); p += 8 + 4 * n
        samples.append((ipo, fr))
    return cnt, samples
def attribute(samples):
    by, inside = collections.Counter(), 0
    for ipo, fr in samples:
        hit = cover.get(ipo)
        if hit is None:
            for r in fr:
                hit = cover.get(r - 1)            # a return address: the call just before it
                if hit is not None: break
        if hit is not None: inside += 1; by[hit] += 1
    return inside, by

lines = ['tools/byte-loops.py (Iteration 954): relfsh\'s byte-at-a-time loops, bench-vm\'s five at SCALE %d.' % SCALE,
         '%s: %d words, %d loops, %d of them byte loops.' % (IMG, len(WORDS), len(LOOPS), len(BYTE_LOOPS)), '']
total_by = collections.Counter(); share_d, share_t = {}, {}
for w in WORKLOADS:
    cnt, sd = run(w, 997, 1)
    ins_d, by_d = attribute(sd)
    _, st_ = run(w, 0, 6)
    ins_t, by_t = attribute(st_)
    share_d[w] = 100.0 * ins_d / max(len(sd), 1); share_t[w] = 100.0 * ins_t / max(len(st_), 1)
    for l, c in by_d.items(): total_by[l] += c / max(len(sd), 1) / len(WORKLOADS)
    lines.append('%-10s inside byte loops: %5.1f %% of the dispatches (%d samples), %5.1f %% of the time (%d samples)'
                 % (w, share_d[w], len(sd), share_t[w], len(st_)))
    if w == WORKLOADS[0]: counts0 = cnt
    globals().setdefault('COUNTS_ALL', collections.Counter())
    for a in range(len(img)):
        if cnt[a]: COUNTS_ALL[a] += cnt[a]
lines.append('mean            %5.1f %% of the dispatches, %5.1f %% of the time'
             % (sum(share_d.values()) / len(share_d), sum(share_t.values()) / len(share_t)))
lines += ['', 'the byte loops by their share of the dispatches, the five weighed alike (each with what it calls);',
          'per entry: iterations - about the bytes it takes - and its own dispatches per iteration:']
for l, s in total_by.most_common(30):
    start, end, xt, br, _ = l
    it = COUNTS_ALL[start]                    # the loop's first instruction, once an iteration
    brn = [i for i in BODY[xt] if i[0] == br][0][2]
    if brn in ('BRANCH', 'BRANCH8'): ent = it - COUNTS_ALL[br]   # every turn but the first came back by it
    else:
        before = max([i[0] for i in BODY[xt] if i[0] < start], default=None)
        ent = COUNTS_ALL[before] if before is not None else 0
    own = sum(COUNTS_ALL[a] for a in range(start, end))
    lines.append('  %5.1f %%  %-24s +%-4d  iterations an entry %7s  own dispatches an iteration %5.1f'
                 % (100 * s, NAME[xt], start - xt, '%.1f' % (it / ent) if ent > 0 else '-', own / it if it else 0))
# An upper bound, from the counts alone: every loop with a byte operation in its own body, leaf or not,
# each charged its own dispatches only (not what it calls) - the loops a primitive might take if the
# words they call were folded in too
own_tot = sum(COUNTS_ALL.values())
ub = []
for start, end, xt, br, _ in LOOPS:
    body = [i for i in BODY[xt] if start <= i[0] < end]
    if not any(BYTEOP(i[2]) for i in body): continue
    inner = [l for l in LOOPS if l[2] == xt and start <= l[0] and l[1] <= end and l != (start, end, xt, br, _)]
    own = sum(COUNTS_ALL[a] for a in range(start, end)) - sum(COUNTS_ALL[a] for l in inner for a in range(l[0], l[1]))
    it = COUNTS_ALL[start]
    if own: ub.append((own, NAME[xt], start - xt, it))
ub.sort(reverse=True)
lines += ['', 'an upper bound: every loop with a byte operation in its own body, leaf or not, its own dispatches only:',
          '  %.1f %% of the five\'s dispatches together, in %d loops; the largest:' % (100.0 * sum(u[0] for u in ub) / own_tot, len(ub))]
for own, nm, off, it in ub[:12]:
    lines.append('  %5.1f %%  %-24s +%-4d  iterations %9d  own dispatches an iteration %5.1f' % (100.0 * own / own_tot, nm, off, it, own / max(it, 1)))
open(OUT, 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
