import os, sys, collections
prims = [l.split()[1] for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kernel.4')) if l.startswith('PRIMITIVE')]
def name(i):
    i=int(i)
    return prims[i] if i < len(prims) else {256:"CALL",257:"<start>",68:"LIT32",69:"DOVAR*",70:"DODOES*"}.get(i, ("X:"+prims[i-128]) if 128<=i<128+len(prims) else str(i))
for f in sys.argv[1:]:
    uni = collections.Counter(); pr = collections.Counter()
    for l in (x for x in open(f) if not x.startswith("C ")):
        a,b,c = l.split(); c=int(c); uni[name(b)] += c; pr[(name(a),name(b))] += c
    tot = sum(uni.values())
    print("==", f, "total dispatches %.2fM" % (tot/1e6))
    print("  top:", ", ".join("%s %.1f%%" % (k, 100*v/tot) for k,v in uni.most_common(16)))
    ex = sum(v for (a,b),v in pr.items() if b=='EXIT')
    print("  before EXIT:", ", ".join("%s %.1f%%" % (a, 100*v/ex) for (a,b),v in sorted(((k,v) for k,v in pr.items() if k[1]=='EXIT'), key=lambda x:-x[1])[:8]))
