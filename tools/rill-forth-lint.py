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
- ['], [CHAR] or ." outside a definition, where they leave nothing or
  print nothing, and ' inside one, where it parses its word when the
  definition runs (855, 856, 857: cm's tests, three times).

Also cm/*.4, the command model's runtime, and tests/cm/*.4 - programs,
loaded when they run, like a .fth: they may use ['] in a definition,
may repeat each other's helpers, and may not take a name rill2's image
or cm's runtime has (855: L! and KEY).

Exit status 1 on any finding.
"""
import glob, re, sys
MISSING = {'2>R', '2R@', '2R>', '-ROT', '/STRING', ',"'}
files = sys.argv[1:] or sorted(glob.glob('rill/*.4') + glob.glob('cm/*.4') + glob.glob('tests/cm/*.4'))
def is_program(f): return f.endswith('.fth') or f.startswith('tests/')
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
for g in sorted(glob.glob('rill/*.4') + glob.glob('rill2/*.4') + glob.glob('cm/*.4')):
    runtime |= set(names(open(g).read()))
def ticks(f, s):
    """['], [CHAR] or ." outside a definition, ' inside one - read token by token, a word's argument
    (the name after ' or POSTPONE, the character after CHAR) never taken for a word itself."""
    s = re.sub(r'(?m)(^|\s)\.\(\s[^)]*\)', ' ', s)                       # a .( text ) printed as it is read
    n, inside, name, arg = 0, False, None, False
    for w in words(s):
        u = w.upper()
        if arg:
            arg = False
            if inside and name is None: name = w                        # a colon's name, its argument
            continue
        if u in ("'", "[']", 'CHAR', '[CHAR]', 'POSTPONE', '[COMPILE]'):
            if inside and u == "'":
                print("%s: %s: ' in a definition parses its word when the definition runs - ['] takes it now" % (f, name)); n += 1
            elif not inside and u in ("[']", '[CHAR]'):
                print("%s: %s outside a definition leaves nothing on the stack - %s there" % (f, w, u[1:-1])); n += 1
            arg = True
        elif u == '."' and not inside:
            print('%s: ." outside a definition prints nothing - .( ) there' % f); n += 1
        elif u == ':': inside, name, arg = True, None, True
        elif u == ':NONAME': inside, name = True, ':NONAME'
        elif u == ';': inside = False
        elif inside and name is None: name = w
    return n
found = 0
# a name defined twice in the runtime itself, outside the genes' alternatives: the later one hides the
# earlier from everything after it (776: a VARIABLE R-BASE, hidden by base()'s R-BASE)
seen = {}
for f in sorted(srcs):
    if is_program(f) or f.startswith('cm/'): continue
    plain = re.sub(r'(?ms)^\\ \[gene [^\]]*\]\n.*?^\\ \[/gene\]', '', srcs[f])
    for n in names(plain):
        if n in seen: print('%s: %s is defined again - %s has it (the later hides the earlier)' % (f, n, seen[n])); found += 1
        else: seen[n] = f
# cm's runtime is loaded on rill2's image: a name of its own that the image has, or another cm file has,
# hides one (855) - Rill's compiler, in another image, is no matter
image2 = set()
for g in ['rill/rt.4', 'rill/regex.4'] + sorted(glob.glob('rill2/*.4')):
    image2 |= set(names(open(g).read()))
cm_defined = set(image2)                                            # what cm's files may use: rill2's image and cm (858: -ROT)
for g in glob.glob('cm/*.4'): cm_defined |= {m.upper() for m in re.findall(r'(?m)(?:^|\s):\s+(\S+)', open(g).read())}
cm_seen = {}
def cm_names(text):
    """A cm file's names, each once: a gene's alternatives define the same word each way (865)."""
    blocks = re.findall(r'(?ms)^\\ \[gene [^\]]*\]\n(.*?)^\\ \[/gene\]', text)
    plain = re.sub(r'(?ms)^\\ \[gene [^\]]*\]\n.*?^\\ \[/gene\]', '', text)
    own = names(plain)
    return own + sorted({n for b in blocks for n in names(b)})      # once each - but beside its own words too (867)
for f in sorted(x for x in srcs if x.startswith('cm/')):
    for n in cm_names(srcs[f]):
        if f == 'cm/values.4' and (n in image2 or n == 'D+'): pass   # rill2.4's values, the cm image's own (870): D+ as rill2.4's
        elif n in image2 or n in kernel: print("%s: %s is defined again - rill2's image has it" % (f, n)); found += 1
        elif n in cm_seen: print('%s: %s is defined again - %s has it' % (f, n, cm_seen[n])); found += 1
        else: cm_seen[n] = f
for f, s in srcs.items():
    program = is_program(f)                                  # a program loaded when it runs, not built into the image
    for n in names(s):
        if (n in kernel and (f, n) != ('cm/values.4', 'D+')) or (program and n in runtime):
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
            elif u in MISSING and u not in (cm_defined if f.startswith(('cm/', 'tests/cm/')) else defined):
                print('%s: %s: %s is not in the kernel' % (f, name, u)); found += 1
    found += ticks(f, s)
print('rill-forth-lint: %d findings in %d files' % (found, len(files)))
sys.exit(1 if found else 0)
