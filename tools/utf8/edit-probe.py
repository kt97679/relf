import sys, os, time
sys.path.insert(0, '/home/claude/relf/tests/interactive')
from pty_session import Session
shell = sys.argv[1]
cases = [
  ('^T swaps two Cyrillic letters', ['echo аб', '\x14', '\n'], 'ба'),
  ('backspace over a 4-byte emoji', ['echo x😀', '\x7f', '\n'], 'x'),
  ('^W then ^Y over multibyte words', ['echo привет мир', '\x17', '\x19', '!', '\n'], 'привет мир!'),
  ('history recall of a UTF-8 line', ['echo ёлка', '\n', '\x1b[A', '\n'], 'ёлка\r\nёлка'),
  ('a stray 0xFF typed, then backspace', [b'echo a\xff', '\x7f', '\n'], 'a'),
  ('a stray 0xFF passed through', [b'echo a\xffb', '\n'], 'a\ufffdb'),
  ('TAB completes a UTF-8 file name', ['cd /tmp/u8\n', 'echo g/a', '\t', '\n'], 'g/aé'),
  ('cursor right over Cyrillic', ['echo где', '\x01', '\x1b[C' * 6, 'X', '\n'], 'гXде'),
]
bad = 0
for name, keys, want in cases:
    env = {'PS1': '$ ', 'RELF_PS1': '$ ', 'HOME': '/tmp', 'TERM': 'xterm', 'PATH': '/usr/bin:/bin', 'LC_ALL': 'C.UTF-8'}
    s = Session([shell], env=env); s.wait_prompt()
    for k in keys:
        if k == '\n': s.send('\n')
        elif isinstance(k, str) and k.endswith('\n'): s.send(k)
        else: s.send(k, wait=False); time.sleep(0.15)
    s.send('exit\n', wait=False); s.drain(0.4); s.close()
    out = s.out
    ok = want in out
    if not ok: bad += 1
    tail = out[-90:].replace('\r', '').replace('\n', '~')
    print('%-38s %s%s' % (name, 'ok' if ok else 'DIFFERS', '' if ok else '   ...' + repr(tail)))
print('%d of %d differ' % (bad, len(cases)))
