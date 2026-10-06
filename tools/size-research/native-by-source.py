import re, collections, sys
ROOT = '/home/claude/relf/'
# per-word code bytes from native-budget.py's dump
words = {}
on = False
for l in open('/tmp/sz/budget-all.txt'):
    if l.startswith('the 3000 largest words'): on = True; continue
    if not on: continue
    m = re.match(r'\s+(\d+)\s+(\S+)\s+(\d+) (\d+) (\d+) (\d+) (\d+) (\d+)', l)
    if m:
        words[m.group(2).upper()] = (int(m.group(1)), tuple(int(x) for x in m.group(3, 4, 5, 6, 7, 8)))
shell_files = ['forth/extend.4', 'forth/safety.4', 'forth/pool.4', 'forth/shadow.4', 'forth/save-system.4',
               'forth/save-system-native.4', 'shell/shell.4', 'shell/edit.4', 'shell/tree.4']
defre = re.compile(r'(?:^|\s)(:|CODE|NCODE|VARIABLE|2VARIABLE|CONSTANT|VALUE|CREATE|DEFER|BUFFER:)\s+(\S+)')
where = {}   # name -> (file, section)
for f in shell_files:
    lines = open(ROOT + f).read().split('\n')
    section = '(start)'; i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('\\ ====') and i + 2 < len(lines) and lines[i + 2].startswith('\\ ===='):
            section = lines[i + 1].lstrip('\\ ').strip()[:60]; i += 3; continue
        code = re.sub(r'\\ .*$|\\$', '', l)
        code = re.sub(r'\( [^)]*\)', '', code)
        for m in defre.finditer(code):
            where[m.group(2).upper()] = (f, section)
        i += 1
by_file = collections.Counter(); n_file = collections.Counter()
by_sec = collections.Counter(); n_sec = collections.Counter()
cls = collections.defaultdict(lambda: [0] * 6)
for w, (b, c) in words.items():
    f, s = where.get(w, ('kernel', ''))
    if w == '(RUNTIME)': f, s = 'runtime', ''
    by_file[f] += b; n_file[f] += 1
    if f.startswith('shell/'): by_sec[(f, s)] += b; n_sec[(f, s)] += 1
    for k in range(6): cls[f][k] += c[k]
tot = sum(by_file.values())
print('total code %d bytes in %d words' % (tot, len(words)))
for f, b in by_file.most_common():
    c = cls[f]
    print('  %-28s %7d  %5.1f %%  %4d words   stack %4.1f %%  call %4.1f %%' % (f, b, 100.0 * b / tot, n_file[f], 100.0 * c[1] / max(b, 1), 100.0 * c[0] / max(b, 1)))
print('\nshell sections, largest first:')
for (f, s), b in by_sec.most_common(60):
    print('  %7d %4d  %-14s %s' % (b, n_sec[(f, s)], f.split('/')[1], s))
