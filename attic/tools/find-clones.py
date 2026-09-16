# tools/find-clones.py - find repeated compiled token sequences that
# could be factored into a shared word. Sequences are cut at branch
# targets (a factored-out run must not contain a jump destination) and
# at calls, and scored as k*(L-1)-(L+1): k occurrences of L tokens
# replaced by k calls plus one definition.
import re, collections
exec(open('/tmp/an.py').read().split("code=[w for w")[0])
code=[w for w in words if w['n'] not in kern and w['n'] not in notcode]
# token sequences per word, with branch-target positions marked as cut points
seqs=[]
for w in code:
    s,tg=decode(w)
    toks=[]; cuts=set()
    for a,k,nm,nc in s:
        if a in tg: cuts.add(len(toks))
        if k=='op' and nm=='LIT':
            toks.append(('LIT',w['c'].get(a+CELL,0)))
        elif k=='op':
            toks.append((nm,'*'))          # branch: operand differs, not factorable
        elif k=='p': toks.append((nm,None))
        elif k=='c': toks.append((nm,None))
        else: toks.append(('STR',None))
    seqs.append((w['n'],toks,cuts))
# collect all subsequences of length 4..24 that contain no branch and no cut inside
occ=collections.defaultdict(list)
for wi,(nm,toks,cuts) in enumerate(seqs):
    n=len(toks)
    for i in range(n):
        if any(t[1]=='*' for t in toks[i:i+1]): continue
        for L in range(4,25):
            j=i+L
            if j>n: break
            seg=toks[i:j]
            if any(t[1]=='*' for t in seg): break
            if any(k in cuts for k in range(i+1,j)): break
            if any(t[0]=='STR' for t in seg): break
            occ[tuple(seg)].append((wi,i))
# score: replacing k occurrences of L tokens by a call = k*(L-1) - (L+1) cells saved
cand=[]
for seg,pos in occ.items():
    k=len(pos); L=len(seg)
    if k<2: continue
    save=k*(L-1)-(L+1)
    if save>0: cand.append((save,k,L,seg,pos))
cand.sort(reverse=True, key=lambda x:x[0])
seen=set(); out=[]
for save,k,L,seg,pos in cand:
    key=frozenset(pos)
    if any(len(key & s)>0 for s in seen): continue
    seen.add(key); out.append((save,k,L,seg,pos))
    if len(out)>=25: break
print(f"{'save':>5} {'x':>4} {'len':>4}  sequence")
for save,k,L,seg,pos in out:
    names=' '.join(f"{a}" if b is None else (f"#{b}" if a=='LIT' else a) for a,b in seg)
    print(f"{save:5d} {k:4d} {L:4d}  {names[:95]}")
print("\ntotal saving from these:", sum(o[0] for o in out), "cells =", sum(o[0] for o in out)*4, "B i386")
