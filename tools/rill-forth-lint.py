#!/usr/bin/env python3
"""tools/rill-forth-lint.py [FILE.4 ...] - Rill's Forth sources, for the slips that came back (Iteration 742).

prompts/15-repeat-slip: a slip fixed by care three times gets a
mechanical guard. Checked in every colon definition of rill/*.4:

- R@ (or R>) inside a DO loop, reading what was put on the return stack
  before the loop - inside DO, the return stack's top is the loop's own
  (739: R-JOIN, R-SLICE, R-RANGE; 741: NM-FIND, HAS-SPECIAL?);
- a name defined again that the kernel has - or, in a program (.fth), that
  the runtime has: "Redefining" in the output, and the old word hidden
  (762: CURRENT, KILL, BASE and PARSE in the pilots' Forth versions)
- ['] inside a definition: it compiles an absolute address, stale once
  the image is saved and reloaded (737's CATCH at boot) - keep the xt
  with !XT and fetch it with @XT;
- words the kernel does not have, unless rill/ defines them (740-741:
  2>R, 2R@, 2R>; -ROT and /STRING rill/ defines).

Exit status 1 on any finding.
"""
import glob, re, sys
MISSING = {'2>R', '2R@', '2R>', '-ROT', '/STRING', ',"'}
files = sys.argv[1:] or sorted(glob.glob('rill/*.4'))
defined = set()
srcs = {f: open(f).read() for f in files}
for s in srcs.values():
    defined |= {m.upper() for m in re.findall(r'(?m)(?:^|\s):\s+(\S+)', s)}
def words(text):
    out = []
    for line in text.split('\n'):
        line = re.sub(r'(^|\s)\\(\s.*)?$', ' ', line)                  # a \ comment
        line = re.sub(r'(^|\s)\(\s[^)]*\)', ' ', line)                  # a ( comment )
        line = re.sub(r'(\S*")\s[^"]*"', r'\1', line)                   # S" text", ." text", ABORT" text"
        out += line.split()
    return out
DEFINER = r'(?:^|\s)(?::|CODE|PRIMITIVE|VARIABLE|2VARIABLE|CONSTANT|CREATE|VALUE|DEFER|BUFFER:)\s+(\S+)'
def names(text):
    lines = [re.sub(r'(\S*")\s[^"]*"', r'\1', re.sub(r'(^|\s)\\(\s.*)?$', ' ', l)) for l in text.split('\n')]   # comments, string literals out
    lines = [re.sub(r"(?<!\S)(\[CHAR\]|CHAR|'|\[']|POSTPONE)\s+\S+", ' ', l) for l in lines]      # [CHAR] : names no word
    return [m.upper() for m in re.findall(DEFINER, '\n'.join(lines))]
kernel = set(names(open('forth/kernel.4').read()))           # the image's own words (762)
runtime = set()
for g in sorted(glob.glob('rill/*.4')):
    runtime |= set(names(open(g).read()))
found = 0
# a name defined twice in the runtime itself, outside the genes' alternatives: the later one hides the
# earlier from everything after it (776: a VARIABLE R-BASE, hidden by base()'s R-BASE)
seen = {}
for f in sorted(srcs):
    if f.endswith('.fth'): continue
    plain = re.sub(r'(?ms)^\\ \[gene [^\]]*\]\n.*?^\\ \[/gene\]', '', srcs[f])
    for n in names(plain):
        if n in seen: print('%s: %s is defined again - %s has it (the later hides the earlier)' % (f, n, seen[n])); found += 1
        else: seen[n] = f
for f, s in srcs.items():
    program = f.endswith('.fth')                             # a program loaded when it runs, not built into the image
    for n in names(s):
        if n in kernel or (program and n in runtime):
            print('%s: %s is defined again - the %s has it ("Redefining" in the output)' % (f, n, 'kernel' if n in kernel else 'runtime')); found += 1
    for m in re.finditer(r'(?ms)(?:^|\s):\s+(\S+)(.*?)(?:\s;(?:\s|$))', s):
        name, body = m.group(1), words(m.group(2))
        loops = []                                                       # per DO loop: >R pushed inside it, net
        for w in body:
            u = w.upper()
            if u in ('DO', '?DO'): loops.append(0)
            elif u in ('LOOP', '+LOOP') and loops: loops.pop()
            elif u == '>R' and loops: loops[-1] += 1
            elif u in ('R>', 'R@') and loops:
                if loops[-1] <= 0:
                    print('%s: %s: %s inside a DO loop reads the loop\'s own return stack' % (f, name, u)); found += 1
                elif u == 'R>': loops[-1] -= 1
            elif u == "[']" and not program:
                print("%s: %s: ['] in a definition - an absolute address, stale after the image is saved" % (f, name)); found += 1
            elif u in MISSING and u not in defined:
                print('%s: %s: %s is not in the kernel' % (f, name, u)); found += 1
print('rill-forth-lint: %d findings in %d files' % (found, len(files)))
sys.exit(1 if found else 0)
