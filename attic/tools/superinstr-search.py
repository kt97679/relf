# tools/superinstr-search.py - greedy superinstruction selection over
# the decoded stream, cutting patterns at branch targets so no fusion
# can hide a jump destination. Reports cells saved for a range of
# dictionary sizes and maximum pattern lengths.
import re, collections, sys
exec(open('/tmp/an.py').read().split("code=[w for w")[0])
code=[w for w in words if w['n'] not in kern and w['n'] not in notcode]
# build token sequences (runs), cut at branch targets; only fusable tokens
runs=[]
for w in code:
    seq,tg=decode(w)
    cur=[]
    for a,k,nm,nc in seq:
        fus = k in ('p','op')
        if a in tg and cur: runs.append(cur); cur=[]
        if fus: cur.append(nm)
        else:
            if cur: runs.append(cur); cur=[]
    if cur: runs.append(cur)
ntok=sum(len(r) for r in runs)
print(f"fusable token positions: {ntok} in {len(runs)} runs")

def greedy(maxn, K):
    rs=[list(r) for r in runs]; chosen=[]; saved=0
    for _ in range(K):
        cnt=collections.Counter()
        for r in rs:
            for n in range(2,maxn+1):
                for i in range(len(r)-n+1):
                    g=tuple(r[i:i+n])
                    if any(x is None for x in g): continue
                    cnt[g]+=1
        best=None;bv=0
        for g,c in cnt.items():
            v=c*(len(g)-1)
            if v>bv: bv=v; best=g
        if not best or bv<=0: break
        chosen.append((best,cnt[best],bv)); saved+=bv
        # apply non-overlapping left-to-right
        n=len(best)
        for r in rs:
            i=0
            while i<=len(r)-n:
                if tuple(r[i:i+n])==best:
                    r[i]='<'+'+'.join(best)+'>'
                    for j in range(i+1,i+n): r[j]=None
                    r[i+1:i+n]=[]
                    i+=1
                else: i+=1
    return chosen,saved

for maxn in (2,3,4,6):
    for K in (16,32,64,128):
        ch,sv=greedy(maxn,K)
        print(f"maxn={maxn} K={K:3d}: saves {sv:5d} cells = {sv*4:6d} B (i386), {sv*8:6d} B (x86-64)")
    print()
ch,sv=greedy(4,32)
print("--- the 12 best superinstructions at maxn=4,K=32 ---")
for g,c,v in ch[:12]: print(f"  saves {v:4d}  x{c:4d}  {' '.join(g)}")
