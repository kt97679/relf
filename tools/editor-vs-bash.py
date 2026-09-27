#!/usr/bin/env python3
"""tools/editor-vs-bash.py [SHELL] - the line editor against bash's readline.

The same keystrokes, through a pseudo-terminal, into relf and into bash
(no startup files, INPUTRC=/dev/null: readline's default emacs keys);
every line begins `echo `, so what each prints after Enter is the line
its editor made - no screen drawing compared, only the result. Each key
is tried alone first - at the end of the line and in its middle, so a
difference belongs to that key - then in random combinations. A key
relf lacks and a key relf does differently look alike here, and are
told apart by reading. TESTING-IDEAS.md 14; written in Iteration 567.
"""
import os, random, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tests', 'interactive'))
from pty_session import Session

RELF = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, 'relfsh')
BASH = ['/bin/bash', '--norc', '--noprofile', '-i']
ENV = {'PS1': '$ ', 'RELF_PS1': '$ ', 'INPUTRC': '/dev/null', 'TERM': 'xterm', 'HISTFILE': '/dev/null'}
KEYS = {'C-a': '\x01', 'C-e': '\x05', 'C-b': '\x02', 'C-f': '\x06', 'Left': '\x1b[D', 'Right': '\x1b[C',
        'Home': '\x1b[H', 'End': '\x1b[F', 'BS': '\x7f', 'Del': '\x1b[3~', 'C-d': '\x04',
        'C-k': '\x0b', 'C-u': '\x15', 'C-w': '\x17', 'C-y': '\x19', 'M-b': '\x1bb', 'M-f': '\x1bf',
        'M-d': '\x1bd', 'M-BS': '\x1b\x7f', 'C-t': '\x14'}
ANSI = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]|\x1b[=>]|\r')

def result(argv, keys):
    s = Session(argv, env=ENV)
    if not s.wait_prompt():
        s.close(); return '<no prompt>'
    for k in keys:
        s.send(k, wait=False); s._read(0.05)
    mark = len(s.out)
    s.send('\n', wait=True)
    lines = ANSI.sub('', s.out[mark:]).split('\n')
    s.send('exit\n', wait=False); s.close()
    out = [l for l in lines[1:] if l.strip() != '$' and not l.startswith('$ ')]
    # the edit, not the messages: `shell: X: not found` and `bash: X: ...`
    return re.sub(r'^(shell|bash): ', '', '\n'.join(out).strip(), flags=re.M)

def spell(keys):
    inv = {v: k for k, v in KEYS.items()}
    return ' '.join(inv.get(k, repr(k)) for k in keys)

tests = []
base = 'echo alpha beta gamma'
for name, code in KEYS.items():
    tests.append(('%s at the end' % name, [base, code]))
    tests.append(('%s in the middle' % name, [base, '\x1b[D' * 7, code, 'X']))
# C-y after each kind of kill, and after moving elsewhere (Iteration 568)
for label, seq in [('C-k then C-y', ['\x1b[D' * 5, '\x0b', '\x19']),
                   ('C-w then C-y', ['\x17', '\x19']),
                   ('M-d then C-y', ['\x01', '\x1bf', '\x1bd', '\x19']),
                   ('M-BS then C-y', ['\x1b\x7f', '\x19']),
                   ('C-u then C-y', ['\x15', '\x19']),
                   ('C-k, move, C-y', ['\x1b[D' * 6, '\x0b', '\x01', '\x1bf', '\x19']),
                   ('C-w C-w C-y (a ring would append)', ['\x17', '\x17', '\x19']),
                   ('C-y with nothing killed', ['\x19'])]:
    tests.append((label, [base] + seq))
rng = random.Random(567)
for _ in range(40):
    keys = [base]
    for _ in range(rng.randrange(1, 5)):
        keys.append(rng.choice(list(KEYS.values())))
        if rng.random() < 0.5: keys.append(rng.choice(['X', 'yz', ' ']))
    tests.append(('random: ' + spell(keys[1:]), keys))

same, diff = 0, []
for label, keys in tests:
    a, b = result([RELF], keys), result(BASH, keys)
    if a == b: same += 1
    else: diff.append((label, a, b))
print('%d keystroke tests: %d the same as bash, %d different' % (len(tests), same, len(diff)))
for label, a, b in diff:
    print('  %-40s relf %-24r bash %r' % (label[:40], a[:24], b[:30]))
