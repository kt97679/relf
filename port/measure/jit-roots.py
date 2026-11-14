'''port/measure/jit-roots.py KMAP MAP JITLOG - a JIT design's refusals, each followed down to its root (the
word whose own reason it is), the roots ranked by how many words each left untranslated.'''
import bisect, collections, sys
kmap, mapf, logf = sys.argv[1:4]
ents=[]
for l in open(kmap):
    _,o,n=l.split(None,2); ents.append((int(o),n.strip()+'(k)'))
for l in open(mapf):
    p=l.split()
    if p[0]=='MAP' and len(p)>3: ents.append((int(p[1]),p[3]))
ents.sort(); st=[e[0] for e in ents]
def nm(o):
    i=bisect.bisect_right(st,o)-1; return ents[i][1] if i>=0 else '?'
why={}; T=collections.Counter()
for l in open(logf):
    p=l.split()
    if p[0]=='R': why[int(p[1])]=(int(p[3]),int(p[2]),int(p[4]))
    if p[0]=='T': T['ok' if int(p[3],16)>1 else 'no']+=1
roots=collections.Counter()
def root(o,seen=()):
    if o not in why or o in seen: return (nm(o),'?')
    w,at,op=why[o]
    if w==4: return root(at,seen+(o,))
    return (nm(o), 'why%d op%d'%(w,op))
for o in why: roots[root(o)]+=1
print('translations', dict(T))
for r,n in roots.most_common(20): print(n, r)
