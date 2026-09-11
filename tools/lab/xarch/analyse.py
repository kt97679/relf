import re, sys, collections
"""analyse.py INSNS [X86CG] - ratios and instructions per dispatch.
Dispatch counts are constants measured on x86 with vm-lab.c -DPROFILE
(identical on every ISA for the same image)."""
D = {64: {'cell': dict(loop=479288788, fn=309272548, str=368646997, arith=348217888, start=521936),
          'cv8':  dict(loop=375926441, fn=253005886, str=282696953, arith=272895931, start=425527),
          'spec': dict(loop=97475883, fn=95960765, str=62054812, arith=73100789, start=219523)},
     32: {'cell': dict(loop=453066751, fn=297655429, str=361000554, arith=331485467, start=864301),
          'cv8':  dict(loop=350825963, fn=241853808, str=275338639, arith=256850921, start=707181),
          'spec': dict(loop=77929519, fn=87255409, str=56247540, arith=60579161, start=380043)}}
disp = {'relf-old': 'cell', 'relf-new': 'cell', 'cv8t': 'cv8', 'spec': 'spec'}
I = collections.defaultdict(dict)
for l in open(sys.argv[1]):
    m = re.match(r'(\S+) (\S+) (\S+) insns=(\d+)', l)
    if m: I[(m[1], m[2])][m[3]] = int(m[4])
for l in open('/home/claude/x86cg.txt'):
    m = re.match(r'(\S+) (\S+) (\S+) insns=(\d+)', l)
    if m: I[(m[1], m[2])][m[3]] = int(m[4])
W = ['loop', 'fn', 'str', 'arith']
print("instructions relative to relf-old (whole run)")
for a in ('x86_64', 'aarch64', 'arm', 'riscv64'):
    for e in ('relf-new', 'cv8t', 'spec'):
        r = [I[(a, e)].get(w, 0) / I[(a, 'relf-old')][w] if I[(a, e)].get(w) and I[(a, 'relf-old')].get(w) else None for w in W]
        print("  %-8s %-9s" % (a, e) + "".join("  %5.3f" % x if x else "      -" for x in r))
print("\ninstructions per dispatch (startup subtracted; x86 has no start run: whole)")
for a in ('x86_64', 'aarch64', 'arm', 'riscv64'):
    cw = 32 if a == 'arm' else 64
    row = "  %-8s" % a
    for e in ('relf-old', 'relf-new', 'cv8t', 'spec'):
        vals = []
        for w in W:
            i = I[(a, e)].get(w)
            if not i: continue
            d = D[cw][disp[e]]
            s_i = I[(a, e)].get('start', 0); s_d = d['start'] if s_i else 0
            vals.append((i - s_i) / (d[w] - s_d))
        row += "  %s %s" % (e, ("%5.1f-%-5.1f" % (min(vals), max(vals))) if vals else "   -   ")
    print(row)
print("\nstartup (-c true) instructions")
for a in ('aarch64', 'arm', 'riscv64'):
    print("  %-8s" % a + "".join("  %s %5.2fM" % (e, I[(a, e)]['start'] / 1e6) for e in ('relf-old', 'relf-new', 'cv8t', 'spec')))
