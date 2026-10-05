#!/usr/bin/env python3
"""native-prof.py - where native code spends its time, by Forth word.

docs/NATIVE.md section 11 (N3, Iteration 643): nothing is to be guessed,
and no profiler is installed here. A native binary - relfsh-native, the
native kernel - is a static ELF at a fixed address, so:
- the symbol map comes from the binary's own dictionary: FORTH-WORDLIST's
  header found by its name, its data address read from its stub's mov
  (xt + 11, as N>BODY), the 32 thread heads there (offsets from the image's
  start, as SAVE-SYSTEM leaves them) walked by the links read backward from
  each name - the walker of 616; a word's code runs from its xt to the next;
- the samples come from ptrace: the program runs traced, is stopped about
  every millisecond (SIGSTOP), its rip read (PTRACE_GETREGS), and resumed.
Children it forks run untraced. Prints the words by share of the samples.
usage: tools/native-prof.py BINARY [ARGS...]      e.g. ./relfsh-native tests/bench-vm/fn.sh
NATIVE_PROF_NM=1 takes the symbols from nm instead, for a binary not
relf's, linked where it runs (668). NATIVE_PROF_WORD=NAME adds NAME's own listing (Iteration 660): its
instructions, from objdump, each with the samples that stopped on it - for
where inside a hot word the time goes, which its share cannot say. And
(668) who called it: the word holding the cell on top of the return stack
at each of its samples - the caller, for a routine that pushes nothing
there, as the runtime's string routines do.
"""
import ctypes, os, signal, struct, sys, time, collections

N_BASE = 0x401000                     # native-cross.4's N-BASE: the image's START

def symbols(path):
    d = open(path, 'rb').read()
    # (674) the image as it runs, from its segments: the code at N_BASE, the
    # data where its own PT_LOAD puts it - the word lists' heads among it
    phoff, = struct.unpack_from('<Q', d, 32); phnum, = struct.unpack_from('<H', d, 56)
    segs = [struct.unpack_from('<IIQQQQQQ', d, phoff + 56 * k) for k in range(phnum)]
    segs = [(s[3], s[2], s[5]) for s in segs if s[0] == 1 and s[5]]    # vaddr, offset, filesz
    img = bytearray(max(v + fz for v, _, fz in segs) - N_BASE)
    for v, off, fz in segs:
        lo = max(v, N_BASE)
        img[lo - N_BASE: v + fz - N_BASE] = d[off + lo - v: off + fz]
    name = b'FORTH-WORDLIST'
    syms = {}
    i = img.find(bytes([0x80 | len(name)]) + name)
    if i < 0:
        sys.exit('native-prof: no FORTH-WORDLIST header in %s' % path)
    xt = i + 1 + len(name)
    data = struct.unpack_from('<I', img, xt + 10)[0] - N_BASE      # its stub's mov (+11 until 697)
    heads = struct.unpack_from('<33q', img, data)[1:]
    def prev(nfa):                    # the link, read backward from the name
        tag = img[nfa - 1]
        if tag & 0x80 == 0:
            dist = tag
        elif tag & 0x40 == 0:
            dist = ((tag & 0x3F) << 8) | img[nfa - 2]
        else:
            dist = ((tag & 0x3F) << 16) | (img[nfa - 2] << 8) | img[nfa - 3]
        return nfa - dist if dist else 0
    for h in heads:
        nfa = h
        while nfa:
            n = img[nfa] & 31
            nm = img[nfa + 1:nfa + 1 + n].decode('latin-1')
            syms.setdefault(N_BASE + nfa + 1 + n, nm)
            nfa = prev(nfa)
    return sorted(syms.items())

def routines(path):
    """The map the native kernel's build writes (643): the routines before
    the dictionary, which have no headers - one line each, hex address and
    name. relfsh-native's runtime region is the kernel's, so it serves both."""
    out = []
    for p in (os.environ.get('NATIVE_MAP'), os.path.join(os.path.dirname(os.path.abspath(path)), 'native-kernel.map')):
        if p and os.path.exists(p):
            for line in open(p):
                a, _, n = line.strip().partition(' ')
                if a and n:
                    out.append((int(a, 16), n))
            break
    return out

def word_at(syms, addrs, rip):
    import bisect
    k = bisect.bisect_right(addrs, rip) - 1
    return syms[k][1] if k >= 0 else '(runtime routines)'

def main():
    prog = sys.argv[1:]
    if os.environ.get('NATIVE_PROF_NM'):
        # (668) any binary with a symbol table, linked where it runs (not
        # PIE): its text symbols from nm - dash, built so, for the
        # function-against-function table (docs/NATIVE.md 11.3)
        import subprocess
        syms = sorted((int(a, 16), n) for a, k, n in
                      (l.split() for l in subprocess.run(['nm', '-n', '--defined-only', prog[0]],
                                                         capture_output=True, text=True).stdout.splitlines()
                       if len(l.split()) == 3) if k in 'tTwW')
    else:
        syms = sorted(dict(symbols(prog[0]) + routines(prog[0])).items())
    addrs = [a for a, _ in syms]
    libc = ctypes.CDLL(None, use_errno=True)
    libc.ptrace.restype = ctypes.c_long
    libc.ptrace.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
    TRACEME, CONT, GETREGS = 0, 7, 12
    pid = os.fork()
    if pid == 0:
        libc.ptrace(TRACEME, 0, None, None)
        os.execv(prog[0], prog)
    os.waitpid(pid, 0)                # stopped at the exec
    regs = (ctypes.c_ulonglong * 27)()
    counts = collections.Counter()
    focus = os.environ.get('NATIVE_PROF_WORD')
    rips = collections.Counter()
    callers = collections.Counter()
    libc.ptrace(CONT, pid, None, None)
    while True:
        time.sleep(0.001)
        try:
            os.kill(pid, signal.SIGSTOP)
        except ProcessLookupError:
            break
        _, status = os.waitpid(pid, 0)
        if os.WIFEXITED(status) or os.WIFSIGNALED(status):
            break
        if os.WIFSTOPPED(status):
            sig = os.WSTOPSIG(status)
            if libc.ptrace(GETREGS, pid, None, ctypes.byref(regs)) == 0:
                w = word_at(syms, addrs, regs[16])               # rip: the 17th register
                counts[w] += 1
                if w == focus:
                    rips[regs[16]] += 1
                    ret = libc.ptrace(2, pid, ctypes.c_void_p(regs[19]), None)   # PEEKDATA at rsp
                    callers[word_at(syms, addrs, ret & 0xffffffffffffffff)] += 1
            pass_sig = 0 if sig == signal.SIGSTOP else sig
            libc.ptrace(CONT, pid, None, ctypes.c_void_p(pass_sig))
    total = sum(counts.values()) or 1
    print('native-prof: %d samples, %d words in the map' % (total, len(syms)))
    for w, c in counts.most_common(25):
        print('%6.1f%%  %s' % (100.0 * c / total, w))
    if focus:
        import subprocess
        k = [n for _, n in syms].index(focus)
        lo, hi = syms[k][0], syms[k + 1][0]
        out = subprocess.run(['objdump', '-D', '-b', 'binary', '-mi386:x86-64',
                              '--start-address=%d' % (lo - N_BASE + 4096), '--stop-address=%d' % (hi - N_BASE + 4096),
                              prog[0]], capture_output=True, text=True).stdout
        own = sum(rips.values()) or 1
        print('%s, %d samples, by instruction (a sample names the instruction about to run):' % (focus, sum(rips.values())))
        for line in out.splitlines()[7:]:
            f = line.split('\t')
            if len(f) < 3 or not f[0].strip().endswith(':'):
                continue
            a = int(f[0].strip()[:-1], 16) + N_BASE - 4096
            n = rips.get(a, 0)
            print('  %5.1f%%  %x  %s' % (100.0 * n / own, a, f[2].strip()) if n else '          %x  %s' % (a, f[2].strip()))
        print('%s, its callers (the word at the top of the return stack, %d samples):' % (focus, sum(callers.values())))
        for w, c in callers.most_common(12):
            print('  %5.1f%%  %s' % (100.0 * c / own, w))

if __name__ == '__main__':
    main()
