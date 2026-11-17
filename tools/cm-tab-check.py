#!/usr/bin/env python3
"""tools/cm-tab-check.py [IMAGE] - TAB at the command model's prompt, through a pseudo-terminal (911).

Keystroke sessions against bin/cm's prompt: a builtin's name completed (ech -> echo), a file whose
name holds a blank put in '...' (the language's quoting, not sh's backslashes), a function made at the prompt
completed by name, two TABs listing a directory, and a $name completed - in "..." too (914); a value's operations after it, by its kind (972). Each checks what the line ran or showed. Exits 1 if
any fails. tests/cm/run runs it.
"""
import os, pty, select, sys, time, tempfile
img = sys.argv[1] if len(sys.argv) > 1 else 'kernel64-cm.img'
d = tempfile.mkdtemp(prefix='cm-tab-')
open(os.path.join(d, 'my notes.txt'), 'w').close()
open(os.path.join(d, 'other.txt'), 'w').close()

def run(keys):
    pid, fd = pty.fork()
    if pid == 0:
        eng = os.environ.get('CM_ENGINE', './relf64')   # the engine the suite runs on (923)
        os.execv(eng, [eng, img])
    out = b''
    def drain(t):
        nonlocal out
        end = time.time() + t
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                try: out += os.read(fd, 4096)
                except OSError: return
    drain(0.5)
    for k in keys:
        os.write(fd, k.encode()); drain(0.4)
    os.write(fd, b'exit\r'); drain(0.5)
    try: os.waitpid(pid, 0)
    except ChildProcessError: pass
    return out.decode('utf-8', 'replace')

checks = [
    ('a builtin completed', ['ech\t', 'tab-completed\r'], '\r\ntab-completed\r\n'),
    ("a name with a blank put in '...'", ['echo %s/my\t' % d, '\r'], "\r\n%s/my notes.txt\r\n" % d),   # echo: GNU ls quotes at a terminal (925)
    ('a function completed', ['var greetings { echo hey from a function }\r', 'gree\t', '\r'], '\r\nhey from a function\r\n'),
    ('two TABs list', ['ls %s/\t\t' % d, '\x03'], 'my notes.txt  other.txt'),
    ('a $name completed', ['var greeting hello\r', 'echo $gree\t', '\r'], '\r\nhello\r\n'),
    ('a $name in quotes', ['var greeting hi\r', 'echo "say $gree\t!"\r'], '\r\nsay hi!\r\n'),
    # a value's operations after it (972): its kind's, by the variable's value at the prompt
    ("a list's operation", ['var l [3 1 2]\r', 'echo $($l cou\t)\r'], '\r\n3\r\n'),
    ("a map's operations listed", ['var m [a: 1]\r', '$m \t\t', '\x03'], 'count  get  has  keys  merge'),
    ("a text's operation", ['var t hello\r', 'echo $($t up\t)\r'], '\r\nHELLO\r\n'),
    ("a quoted text's", ["echo $('a,b' spl\t , | wc -l)\r"], '\r\n2\r\n'),
    ("$env's, a map's", ['echo $(( $($env cou\t) > 0 ))\r'], '\r\ntrue\r\n'),
    ("a block's none: its files", ['var b {|f| echo got $f }\r', '$b %s/oth\t\r' % d], '\r\ngot %s/other.txt\r\n' % d),
]
bad = 0
for name, keys, want in checks:
    ok = want in run(keys)
    bad += not ok
    print('%s %s' % ('ok  ' if ok else 'FAIL', name))
for f in os.listdir(d): os.remove(os.path.join(d, f))
os.rmdir(d)
print('cm-tab-check: %d of %d failed' % (bad, len(checks)))
sys.exit(1 if bad else 0)
