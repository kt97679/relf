import sys, time, re
sys.path.insert(0, '/home/claude/relf/tests/interactive')
from pty_session import Session
def run(argv, keys):
    env = {'PS1': '$ ', 'RELF_PS1': '$ ', 'HOME': '/tmp', 'TERM': 'xterm', 'PATH': '/usr/bin:/bin', 'LC_ALL': 'C.UTF-8', 'INPUTRC': '/dev/null'}
    s = Session(argv, env=env); s.wait_prompt()
    for k in keys: s.send(k, wait=False); time.sleep(0.25)
    s.send('\n'); s.send('exit\n', wait=False); s.drain(0.4); s.close()
    out = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', s.out.replace('\r', ''))
    m = re.findall(r'\n([^\n$]*)\n\$ ', out)
    return m[0] if m else '?'
cases = [
  ('decomposed é, Backspace', ['echo [xe\u0301', '\x7f', ']']),
  ('decomposed é, Left Left, Z', ['echo [e\u0301x]', '\x1b[D\x1b[D\x1b[D', 'Z']),
  ('Hebrew, Backspace', ['echo [שלום', '\x7f', ']']),
  ('Arabic, Backspace', ['echo [عربي', '\x7f', ']']),
  ('Thai with two marks, Backspace', ['echo [ที่', '\x7f', ']']),
  ('Devanagari, Backspace', ['echo [नमस्ते', '\x7f', ']']),
  ('Hangul syllable, Backspace', ['echo [한국', '\x7f', ']']),
  ('ZWJ family emoji, Backspace', ['echo [\U0001F468\u200d\U0001F469\u200d\U0001F467', '\x7f', ']']),
  ('flag (two indicators), Backspace', ['echo [\U0001F1FA\U0001F1E6', '\x7f', ']']),
]
for name, keys in cases:
    a = run(['/home/claude/relf/relfshasm64'], keys); b = run(['/usr/bin/bash', '--norc', '--noprofile'], keys)
    same = 'same' if a == b else 'DIFFER'
    print('%-34s relf %-22s bash %-22s %s' % (name, ascii(a)[:22], ascii(b)[:22], same))
