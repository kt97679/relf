#!/usr/bin/env python3
"""tools/rill-forth-lint.py [FILE.4 ...] - Rill's Forth sources, for the slips that came back (Iteration 742).

prompts/15-repeat-slip: a slip fixed by care three times gets a
mechanical guard. Checked in every colon definition of rill/*.4:

- R@ (or R>) inside a DO loop, reading what was put on the return stack
  before the loop - inside DO, the return stack's top is the loop's own
  (739: R-JOIN, R-SLICE, R-RANGE; 741: NM-FIND, HAS-SPECIAL?);
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
found = 0
for f, s in srcs.items():
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
            elif u == "[']":
                print("%s: %s: ['] in a definition - an absolute address, stale after the image is saved" % (f, name)); found += 1
            elif u in MISSING and u not in defined:
                print('%s: %s: %s is not in the kernel' % (f, name, u)); found += 1
print('rill-forth-lint: %d findings in %d files' % (found, len(files)))
sys.exit(1 if found else 0)
