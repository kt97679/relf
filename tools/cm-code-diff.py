#!/usr/bin/env python3
"""tools/cm-code-diff.py OLD.img [NEW.img] - the code two images make of every tests/cm/scripts/*.cm compared (927).

A review of a front-end change by what it makes, not only by what the scripts print: CM-SHOW of each script
on both images, made words renumbered by first appearance, a def's record (an address) as REC; before 926
the code was Forth text - its named words, DEFERs and VARIABLEs mapped onto the tokens' forms. 926 against
925: 163 compiled, the same but one, the def-call with @, the same code in another order. Exit 1 if any
differ. NEW defaults to kernel64-cm.img.
"""
import sys
import subprocess, re, glob, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD = sys.argv[1]; NEW = sys.argv[2] if len(sys.argv) > 2 else 'kernel64-cm.img'
def show(img, f):
    open('/tmp/ds.4','w').write('S" %s" CM-SHOW BYE\n' % f)
    r=subprocess.run(['./relf64', img, '/tmp/ds.4'], capture_output=True, timeout=30)
    return r.stdout.decode('utf-8','replace')
def norm_old(t):
    strs=[]
    t=re.sub(r'S" [^"]*"', lambda m: (strs.append(m.group(0)), 'STR%d'%(len(strs)-1))[1], t)
    t=t.replace('CM-WORDS ','')
    t=re.sub(r'DEFER (\S+) VARIABLE \S+ VARIABLE \S+ ','',t)
    # names of made words -> G
    names={}
    for m in re.finditer(r': (\S+) ', t):
        n=m.group(1)
        if n not in names: names[n]='G%d'%len(names)
    t=re.sub(r"' (\S+) IS (\S+) (\S+) \S+# ! (\S+) \S+% ! ", lambda m: "['] %s %s %s REC DEF-SET " % (names.get(m.group(1),m.group(1)), m.group(3), m.group(4)), t)
    t=re.sub(r"(\S+)# @ \S+% @ \['\] \S+ (S\" [^\"]*\" CALLING 2! )?DEF-CALL-([PSM])", lambda m: "REC %sDEF-R-%s" % (m.group(2) or '', m.group(3)), t)
    t=re.sub(r"' CM.MAIN", "['] CM.MAIN", t)
    for n,g in sorted(names.items(), key=lambda x:-len(x[0])):
        t=re.sub(r'(?<!\S)'+re.escape(n)+r'(?!\S)', g, t)
    t=re.sub(r'STR(\d+)', lambda m: strs[int(m.group(1))], t)
    return ' '.join(t.split())
def renum(t):
    m={}
    def f(x):
        k=x.group(0)
        if k not in m: m[k]='G%d'%len(m)
        return m[k]
    return re.sub(r'(?<!\S)G\d+(?!\S)', f, t)
def norm_new(t):
    if 'CM-WORDS' in t: return norm_old(t)
    t=re.sub(r'(?<!\S)\d{12,} (?=DEF-SET|DEF-R-|S" [^"]*" CALLING)', 'REC ', t)
    t=re.sub(r"\['\] (G\d+) (\d+ \d+) REC DEF-SET", r"['] \1 \2 REC DEF-SET", t)
    return renum(' '.join(t.split()))
bad=0; n=0
for f in sorted(glob.glob('tests/cm/scripts/*.cm')):
    a=show(OLD, f); b=show(NEW, f)
    if 'error' in a.lower()[:200] and 'error' in b.lower()[:200]: continue
    n+=1
    if norm_new(a)!=norm_new(b):
        bad+=1
        if bad<=4:
            na,nb=norm_old(a).split(),norm_new(b).split()
            i=next((k for k in range(min(len(na),len(nb))) if na[k]!=nb[k]), min(len(na),len(nb)))
            print('DIFF', f, 'at', i, '\n  old:', ' '.join(na[max(0,i-6):i+10]), '\n  new:', ' '.join(nb[max(0,i-6):i+10]))
print(n,'compared,',bad,'differ')
sys.exit(1 if bad else 0)
