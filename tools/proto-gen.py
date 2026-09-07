import re, collections, sys
exec(open('/tmp/an.py').read().split("code=[w for w")[0])
allw={w['n']:w for w in words}
info={}
for w in words:
    if w['n'] in notcode: continue
    info[w['n']]=(decode(w)[0], w)
def closure(n,seen=None):
    if seen is None: seen=set()
    if n in seen or n not in info: return seen
    seen.add(n)
    for a,k,nm,nc in info[n][0]:
        if k=='c': closure(nm[5:],seen)
    return seen
ROOT='VALID-NAME?'
cl=sorted(closure(ROOT))
# (DO)/(LOOP)/I/UNLOOP become primitives in the prototype. (LOOP) reads
# an inline operand cell through the return stack (R> DUP @ + >R), the
# same trick (S") uses - so it is encoding-specific by nature and a real
# port would have to rewrite it either way. Discovered by this generator
# failing on the unresolvable "call" after (LOOP), which is that operand.
ASPRIM={'(DO)','(LOOP)','I','UNLOOP'}
PRIMS=sorted({nm for n in cl for a,k,nm,nc in info[n][0] if k in ('p','op')} | ASPRIM)
pidx={p:i for i,p in enumerate(PRIMS)}
cl=[n for n in cl if n not in ASPRIM]
widx={n:i for i,n in enumerate(cl)}

# normalise each word into a list of (op, payload) plus branch targets
def norm(n):
    seq=[]; s,w=info[n]; pos={}
    for a,k,nm,nc in s:
        pos[a]=len(seq)
        if k=='op' and nm=='LIT':   seq.append(('LIT', w['c'].get(a+CELL,0)))
        elif k=='op':               seq.append((nm, w['c'].get(a+CELL,0)))  # branch: byte offset
        elif k=='p':                seq.append((nm, None))
        elif k=='c':
            tgt=nm[5:]
            if tgt in ASPRIM:  seq.append((tgt, w['c'].get(a+CELL,0) if tgt=='(LOOP)' else None))
            else:              seq.append(('CALL', tgt))
        else:                       raise SystemExit('unexpected item '+k+' in '+n)
    # resolve branch byte-offsets to token indices
    out=[]
    for a,k,nm,nc in s:
        i=pos[a]
        op,pay=seq[i]
        if op in ('BRANCH','?BRANCH','(LOOP)'):
            tgt=a+CELL+pay              # relf: ip += CELL(ip), ip at operand
            if tgt not in pos: raise SystemExit('branch out of word in '+n)
            out.append((op,pos[tgt]))
        else: out.append((op,pay))
    return out
prog={n:norm(n) for n in cl}

# ---- CELL layout: 1 cell per token, +1 for LIT/BRANCH operand ----
OPERAND={'LIT','BRANCH','?BRANCH','(LOOP)'}
def cellsize(seq): return sum(2 if op in OPERAND else 1 for op,_ in seq)
cstart={}; off=0
for n in cl: cstart[n]=off; off+=cellsize(prog[n])
CELLN=off
cellprog=[('RAW',0)]*CELLN; tokcell={}
for n in cl:
    i=cstart[n]
    for j,(op,pay) in enumerate(prog[n]): tokcell[(n,j)]=i; i+= 2 if op in OPERAND else 1
for n in cl:
    for j,(op,pay) in enumerate(prog[n]):
        i=tokcell[(n,j)]
        # Tagged so an odd cell-count offset cannot be mistaken for a
        # primitive token. RelF's real offsets are BYTE counts and so are
        # always even; this prototype indexes cells, which can be odd.
        if op=='CALL':   cellprog[i]=('CALLREL', ((tokcell[(pay,0)]-(i+1))<<2)|2)
        elif op=='LIT':  cellprog[i]=('PRIM',pidx['LIT']); cellprog[i+1]=('RAW',pay)
        elif op in ('BRANCH','?BRANCH','(LOOP)'):
            cellprog[i]=('PRIM',pidx[op]); cellprog[i+1]=('RAW', tokcell[(n,pay)]-(i+1))
        else: cellprog[i]=('PRIM',pidx[op])

# ---- BYTE layout: 1 byte for prims and small literals, 2 for calls
#      and wider operands. Calls are given TWO bytes even though this
#      program has only 9 words, because the real image has 817 call
#      targets and a one-byte call here would flatter the encoding.
def bytesize(seq):
    t=0
    for op,pay in seq:
        if op=='CALL': t+=2
        elif op=='LIT': t+= 1 if 0<=pay<64 else 5   # opcode + int32
        elif op in ('BRANCH','?BRANCH','(LOOP)'): t+=3
        else: t+=1
    return t
bstart={}; off=0
for n in cl: bstart[n]=off; off+=bytesize(prog[n])
BYTEN=off
tokbyte={}
for n in cl:
    i=bstart[n]
    for j,(op,pay) in enumerate(prog[n]):
        tokbyte[(n,j)]=i
        i+= 2 if op=='CALL' else (1 if 0<=(pay or 0)<64 else 5) if op=='LIT' else 3 if op in ('BRANCH','?BRANCH','(LOOP)') else 1
out=[]
B_LIT1, B_LITN, B_BR, B_QBR, B_CALL = 0x70,0x71,0x72,0x73,0x80
for n in cl:
    for j,(op,pay) in enumerate(prog[n]):
        i=tokbyte[(n,j)]
        if op=='CALL':
            w=widx[pay]; out.append((i,[B_CALL|(w>>8), w&0xff]))
        elif op=='LIT':
            if 0<=pay<64: out.append((i,[0x30+pay]))
            else:
                # A fixed 32-bit operand, not a host cell: the point of
                # a byte stream is that it does not scale with cell width.
                b=[B_LITN]+[(pay>>(8*k))&0xff for k in range(4)]
                out.append((i,b))
        elif op in ('BRANCH','?BRANCH','(LOOP)'):
            d=tokbyte[(n,pay)]-(i+3)
            code = B_BR if op=='BRANCH' else B_QBR if op=='?BRANCH' else pidx['(LOOP)']
            out.append((i,[code, d&0xff, (d>>8)&0xff]))
        else: out.append((i,[pidx[op]]))
byteprog=[0]*BYTEN
for i,bs in out:
    for k,b in enumerate(bs): byteprog[i+k]=b

f=open('/tmp/proto_gen.h','w')
f.write("/* generated by tools/proto-gen.py - do not edit */\n")
f.write("#define NPRIMS %d\n#define NWORDS %d\n"%(len(PRIMS),len(cl)))
f.write("#define CELLN %d\n#define BYTEN %d\n"%(CELLN,BYTEN))
f.write("#define ROOT_CELL %d\n#define ROOT_BYTE %d\n"%(cstart[ROOT],bstart[ROOT]))
f.write("#define B_LIT1 0x%02x\n#define B_LITN 0x%02x\n#define B_BR 0x%02x\n#define B_QBR 0x%02x\n#define B_CALL 0x%02x\n"%(B_LIT1,B_LITN,B_BR,B_QBR,B_CALL))
f.write("static const char *primnames[] = {%s};\n"%",".join('"%s"'%p for p in PRIMS))
f.write("static const CELL_T cellprog[CELLN] = {\n")
for i,c in enumerate(cellprog):
    k,v=c
    f.write("  %s,\n"%("(CELL_T)((%d<<2)|1)"%v if k=='PRIM' else "(CELL_T)(%d)"%v))
f.write("};\n")
f.write("static const unsigned char byteprog[BYTEN] = {%s};\n"%",".join(str(b) for b in byteprog))
f.write("static const int wordbyte[NWORDS] = {%s};\n"%",".join(str(bstart[n]) for n in cl))
f.close()
print("words:",cl)
print("primitives:",len(PRIMS))
print("CELL program: %d cells = %d bytes (i386) / %d (x86-64)"%(CELLN,CELLN*4,CELLN*8))
print("BYTE program: %d bytes"%BYTEN)
print("ratio: %.2fx (i386)  %.2fx (x86-64)"%(CELLN*4/BYTEN, CELLN*8/BYTEN))
