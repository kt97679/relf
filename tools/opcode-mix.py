#!/usr/bin/env python3
"""tools/opcode-mix.py [--tramp] [--keep N] - what a smaller opcode space would cost.

Iteration 501's experiment for GOALS.md "What comes next", item 2: a
two-bit tag on every byte (00 opcode, 01/10/11 calls of 14, 22 and 30
bits) leaves 64 one-byte opcodes where CV8 has 128, 95 of them in use.
The rest would move behind ESC, costing each one a byte and a second
dispatch. Which ones move decides the price, so this measures it on the
real system rather than guessing:

  1. builds an engine that counts every dispatched byte, and every
     escape selector, into a file shared by all its processes;
  2. runs tests/bench-vm's workloads and the differential suite on it;
  3. counts each opcode's static occurrences in the 64-bit shell image
     (tools/image-audit.py --opcodes);
  4. keeps ESC and the N-1 most executed opcodes (N = 64), and prints
     what the others cost: the share of all dispatches that would gain a
     second dispatch, and the bytes the image would grow by.

With --tramp it also builds relf-tramp: the same engine with the moved
opcodes sent through one more indirect jump, as ESC would send them, so
tools/bench-vm.py can time the difference on real code with no change
to the image format. Everything is built in /tmp/opcode-mix.
"""
import os, re, subprocess, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = '/tmp/opcode-mix'
KEEP = int(sys.argv[sys.argv.index('--keep') + 1]) if '--keep' in sys.argv else 64
TRAMP = '--tramp' in sys.argv

def patch(text, old, new):
    """Replace old, which must occur exactly once (see tools/profile.py)."""
    n = text.count(old)
    if n != 1:
        sys.exit('opcode-mix: the text to patch occurs %d times, not once:\n%s' % (n, old[:300]))
    return text.replace(old, new)

# ---- opcode names, from the sources ----------------------------------
def names():
    k = open(os.path.join(ROOT, 'kernel.4')).read()
    prims = re.findall(r'^PRIMITIVE\s+(\S+)', k, flags=re.M)
    esc_at = k.index('\nESCAPED')
    direct = re.findall(r'^PRIMITIVE\s+(\S+)', k[:esc_at], flags=re.M)
    escaped = re.findall(r'^PRIMITIVE\s+(\S+)', k[esc_at:], flags=re.M)
    nd = len(direct)
    n = {i: direct[i] for i in range(nd)}
    for i, s in enumerate(['LIT32', 'DOVAR', 'DODOES', 'LIT8', 'LIT8;EXIT']):
        n[nd + i] = s
    fold = ['+', '=', '!', '@', 'LSHIFT', 'RSHIFT', 'C@', 'C!', 'AND', 'OR', 'XOR', 'LIT',
            '<', 'U<', 'OVER', 'DROP', 'DUP', 'SWAP', 'ROT', '>R', 'R>', 'R@', 'NEGATE']
    for i, s in enumerate(fold):
        n[nd + 5 + i] = s + ';EXIT'
    n[nd + 5 + len(fold)] = 'BRANCH8'
    n[nd + 6 + len(fold)] = '?BRANCH8'
    spec = ['push0', 'push1', 'push-1', 'VAR@', 'VAR!', 'LSAVE', 'LRESTORE', 'L!', 'LZERO',
            '0=', '-', '<>', '0<', '>', '2DUP', '2DROP', 'CHAR+', '1+', 'CELL+', 'CELLS',
            '1-', 'INVERT', 'COUNT', 'ALIGNED', 'ADDI', 'ADDI;EXIT', 'EQI', 'EQI;EXIT']
    for i, s in enumerate(spec):
        n[0x61 + i] = s
    n[0x7D] = 'LIT64'
    n[0x7E] = 'ESC'
    return n, escaped

# ---- the engines ------------------------------------------------------
HOOKS = '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP'
ENTRY = '    NEXT();\ndo_call:'
ESC_LINE = '    t = BYTE(ip); ip += 1; PROF(t); goto *esc_tab[t];'

def build_counting(src):
    s = patch(src, HOOKS, '''static unsigned int *opmix;
#define PROF(k) (opmix[(k)]++)
#define PROFIP(a)
#define PROFDUMP''')
    s = patch(s, ENTRY, '''    { const char *f_ = getenv("OPMIX"); int fd_ = f_ ? open(f_, O_RDWR) : -1;
      static unsigned int none_[1024];
      opmix = fd_ >= 0 ? mmap(0, 1024 * sizeof(unsigned int), PROT_READ | PROT_WRITE,
                              MAP_SHARED, fd_, 0) : none_;
      if (opmix == MAP_FAILED) opmix = none_; }
''' + ENTRY)
    # Selectors at 512 up: do_call counts every call as PROF(256), so a
    # table that put selectors at 256 up credited each call to BYE -
    # 58 million of them, the first time this ran.
    s = patch(s, ESC_LINE, '    t = BYTE(ip); ip += 1; opmix[512 + t]++; goto *esc_tab[t];')
    return s

def build_tramp(src, moved):
    table = 'static const unsigned char MOVED_[] = { %s };' % ', '.join('0x%02X' % m for m in sorted(moved))
    s = patch(src, '    const void *dtab256[256];', table + '\n    const void *dtab256[256];\n    const void *tramp_tab[128];')
    m = re.search(r'dtab256\[i_\] = \(i_ < n_ && i_ < 128\) \? dispatch\[i_\] : &&do_call; }', s)
    if not m:
        sys.exit('opcode-mix: the dispatch table construction was not found')
    s = s[:m.end()] + '''
    for (unsigned k_ = 0; k_ < sizeof MOVED_; k_++) {
        tramp_tab[MOVED_[k_]] = dtab256[MOVED_[k_]];
        dtab256[MOVED_[k_]] = &&L_tramp;
    }''' + s[m.end():]
    # the second dispatch ESC would add: load the selector byte, jump again
    s = patch(s, 'L_esc:', '''L_tramp:
    __asm__ volatile ("" :: "r" (BYTE(ip)));
    goto *tramp_tab[t];
L_esc:''')
    return s

def cc(src, out):
    path = out + '.c'
    open(path, 'w').write(src)
    r = subprocess.run(['cc', '-O2', '-Wall', '-o', out, path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('opcode-mix: %s did not compile:\n%s' % (out, r.stderr[-2000:]))

# ---- run ----------------------------------------------------------------
def main():
    os.makedirs(WORK, exist_ok=True)
    src = open(os.path.join(ROOT, 'cv8.c')).read()
    counter = os.path.join(WORK, 'relf-count')
    cc(build_counting(src), counter)
    mix = os.path.join(WORK, 'opmix.bin')
    open(mix, 'wb').write(bytes(1024 * 4))
    # The counting engine as a shell of its own (tools/embed.sh; relfsh
    # is a binary since Iteration 506).
    shell = os.path.join(WORK, 'relfsh-count')
    subprocess.run(['sh', os.path.join(ROOT, 'tools/embed.sh'), counter,
                    os.path.join(ROOT, 'kernel-shell.img'), shell], check=True)
    env = dict(os.environ, OPMIX=mix, RELFSH=shell)
    for w in ('loop', 'fn', 'str', 'arith', 'realistic'):
        subprocess.run([shell, 'tests/bench-vm/%s.sh' % w], cwd=ROOT, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    subprocess.run(['sh', 'tests/diff/run-all'], cwd=ROOT, env=dict(env, THIS_SH=shell),
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
    raw = open(mix, 'rb').read()
    counts = [int.from_bytes(raw[i*4:i*4+4], 'little') for i in range(1024)]
    dyn = collections.Counter({i: counts[i] for i in range(128) if counts[i]})
    calls = sum(counts[128:256])          # counts[256] is do_call's own count of the same
    escs = collections.Counter({i: counts[512 + i] for i in range(256) if counts[512 + i]})
    total = sum(counts[:256]) + sum(escs.values())
    st_out = subprocess.run([sys.executable, os.path.join(ROOT, 'tools/image-audit.py'),
                             os.path.join(ROOT, 'kernel-shell.img'), '8', '--opcodes'],
                            capture_output=True, text=True).stdout
    stat = collections.Counter(); code = 0
    for line in st_out.splitlines():
        f = line.split()
        if f[0] == 'op': stat[int(f[1])] = int(f[2])
        elif f[0] == 'code': code = int(f[1])
    name, escaped = names()
    used = sorted(name)
    ranked = sorted((o for o in used if o != 0x7E), key=lambda o: (-dyn[o], -stat[o], o))
    keep = set(ranked[:KEEP - 1]) | {0x7E}
    moved = [o for o in used if o not in keep]
    md = sum(dyn[o] for o in moved); ms = sum(stat[o] for o in moved)
    print('dispatches counted: %d (calls %d, %.1f%%; escaped selectors %d)'
          % (total, calls, 100.0 * calls / total, sum(escs.values())))
    print('opcodes in use: %d; kept in one byte: %d (ESC among them); moved behind ESC: %d'
          % (len(used), len(keep), len(moved)))
    print('\nmoved, most executed first:')
    print('  %-4s %-12s %14s %10s %8s' % ('op', 'name', 'dynamic', '% disp', 'static'))
    for o in sorted(moved, key=lambda o: -dyn[o]):
        print('  %02X   %-12s %14d %9.3f%% %8d' % (o, name[o], dyn[o], 100.0 * dyn[o] / total, stat[o]))
    print('\nthe coldest kept:')
    for o in ranked[KEEP - 6:KEEP - 1]:
        print('  %02X   %-12s %14d %9.3f%% %8d' % (o, name[o], dyn[o], 100.0 * dyn[o] / total, stat[o]))
    print('\nthe escaped primitives today, most executed first:')
    for i, n in escs.most_common(6):
        print('  %-16s %12d %9.3f%%' % (escaped[i] if i < len(escaped) else '?', n, 100.0 * n / total))
    print('\nsecond dispatches: %d, %.2f%% of all dispatches' % (md, 100.0 * md / total))
    print('image growth: %d bytes, %.2f%% of the 64-bit image\'s %d code bytes' % (ms, 100.0 * ms / code, code))
    open(os.path.join(WORK, 'moved.txt'), 'w').write(' '.join('%02X' % o for o in moved) + '\n')
    if TRAMP:
        cc(src, os.path.join(WORK, 'relf-base'))
        cc(build_tramp(src, moved), os.path.join(WORK, 'relf-tramp'))
        print('\nbuilt %s/relf-base and %s/relf-tramp for tools/bench-vm.py' % (WORK, WORK))

main()
