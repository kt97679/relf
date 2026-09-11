import sys, bisect, collections
syms = [l.split(None, 3) for l in open(sys.argv[1])]
offs = [int(s[0]) for s in syms]
for f in sys.argv[2:]:
    c = collections.Counter()
    for l in open(f):
        if l.startswith('C '):
            _, t, n = l.split(); off = (int(t) - 256) * 2
            i = bisect.bisect_right(offs, off) - 1
            nm = syms[i][3].strip(); k = syms[i][2]
            c[(nm, k, off - offs[i])] += int(n)
    tot = sum(c.values())
    print("==", f, "calls %.1fM" % (tot / 1e6))
    for (nm, k, d), n in c.most_common(25):
        print("  %6.2f%%  %-22s %s%s" % (100 * n / tot, nm, k, "" if d == 0 else " +%d" % d))
    kinds = collections.Counter()
    for (nm, k, d), n in c.items(): kinds[k] += n
    print("  by kind:", {k: "%.1f%%" % (100 * v / tot) for k, v in kinds.items()})
