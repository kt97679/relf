import re, collections, sys
CELL=4
prims=[l.split()[1] for l in open('kernel.4') if l.startswith('PRIMITIVE')]
tokname={i*CELL+1:n for i,n in enumerate(prims)}
LIT   = prims.index('LIT')*CELL+1
BR    = prims.index('BRANCH')*CELL+1
QBR   = prims.index('?BRANCH')*CELL+1
words=[]; cur=None
for l in open('/tmp/dump2.txt',errors='replace'):
    l=l.rstrip('\n')
    m=re.match(r'^N (-?\d+) (-?\d+) ?(.*)$',l)
    if m: cur={'s':int(m.group(1)),'e':int(m.group(2)),'n':m.group(3).strip(),'c':{}}; words.append(cur); continue
    m=re.match(r'^B (-?\d+) (-?\d+)\s*$',l)
    if m and cur: cur['c'][int(m.group(1))]=int(m.group(2))
bystart={w['s']:w['n'] for w in words}
# which words are the inline-string runtimes?
SLIT={w['s'] for w in words if w['n'] in ('(S")','(.")')}
# (LOOP) reads a branch offset from the cell after its own call site,
# through the return stack - the same trick (S") uses for an inline
# string. So the cell after a call to (LOOP) is an OPERAND, not a token.
# Missed until Iteration 141, when a generator that had to resolve every
# call target failed on it. It is the fifth not-a-token case, after LIT,
# BRANCH, ?BRANCH operands and inline strings.
LOOPW={w['s'] for w in words if w['n'] == '(LOOP)'}
print('inline-string runtimes found:',[w['n'] for w in words if w['n'] in ('(S")','(.")')], file=sys.stderr)
kern=set()
for l in open('/tmp/walk_kernel.txt',errors='replace'):
    m=re.match(r'^W \S+ \S+ ?(.*)$',l.rstrip('\n'))
    if m: kern.add(m.group(1).strip())
src="".join(open(f,errors='replace').read() for f in ['shell.4','locals.4','pool.4','save-system.4'])
notcode=set(re.findall(r'CREATE\s+(\S+)[^\n]*ALLOT',src))|set(re.findall(r'BUFFER:\s+(\S+)',src))|set(re.findall(r'^\s*VARIABLE\s+(\S+)',src,re.M))

def decode(w):
    """return list of (addr, kind, name, ncells) and set of branch targets"""
    out=[]; tg=set(); a=w['s']; C=w['c']
    while a < w['e']:
        v=C.get(a)
        if v is None: break
        if v & 1:
            nm=tokname.get(v)
            if nm is None: out.append((a,'?','?',1)); a+=CELL; continue
            if v in (LIT,BR,QBR):
                op=C.get(a+CELL,0)
                if v in (BR,QBR): tg.add(a+CELL+op)
                out.append((a,'op',nm,2)); a+=2*CELL
            else:
                out.append((a,'p',nm,1)); a+=CELL
        else:
            # Call targets are relative to the cell AFTER the call cell,
            # because relf.c's NEXT() advances ip before adding: the
            # engine does RPUSH(ip); ip += t with ip already past the
            # cell. Getting this wrong resolves no targets at all, so
            # the inline-string skip below never fires and every S"
            # body is read as tokens. Iterations 130-134 had this bug.
            tgt=a+CELL+v
            if tgt in LOOPW:
                out.append((a,'op','(LOOP)',2)); a+=2*CELL; continue
            if tgt in SLIT:
                # inline counted string follows the call cell
                sa=a+CELL; ln=C.get(sa,0)&0xff
                n=1+ln; pad=(n+CELL-1)//CELL
                out.append((a,'str','STR',1+pad)); a+=CELL+pad*CELL
            else:
                out.append((a,'c','CALL:'+bystart.get(tgt,'?'),1))
                a+=CELL
    return out,tg

code=[w for w in words if w['n'] not in kern and w['n'] not in notcode]
tot=0; kinds=collections.Counter(); litv=collections.Counter()
grams={n:collections.Counter() for n in (2,3,4,5)}
for w in code:
    seq,tg=decode(w)
    for a,k,nm,nc in seq:
        kinds[k]+=nc; tot+=nc
        if k=='op' and nm=='LIT': litv[w['c'].get(a+CELL,0)]+=1
    # fusable run: consecutive items, cut at any branch target
    runs=[]; cur=[]
    for it in seq:
        if it[0] in tg and cur: runs.append(cur); cur=[]
        cur.append(it)
    if cur: runs.append(cur)
    for r in runs:
        names=[x[2] for x in r]
        for n in grams:
            for i in range(len(names)-n+1):
                g=tuple(names[i:i+n])
                if any(x.startswith('CALL:') or x=='STR' or x=='?' for x in g): continue
                grams[n][g]+=1
print("cells accounted:",tot)
for k,v in kinds.most_common(): print(f"   {k:4s} {v:6d}")
print("\n--- literal value histogram (top 20) ---")
for k,v in litv.most_common(20): print(f"{v:5d}  {k}")
nlit=sum(litv.values()); print("total LIT sites:",nlit)
for n in (2,3,4,5):
    top=grams[n].most_common(10)
    print(f"\n--- top {n}-grams (fusable, no calls/strings, not crossing a branch target) ---")
    for g,v in top: print(f"{v:5d}  {' '.join(g)}")
