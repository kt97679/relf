#!/usr/bin/env python3
"""tests/interactive/prompt-probe.py - the prompt and ^C's races (Iteration 712).

Three checks on the shell under test (THIS_SH, else ../../relfsh), each a
FAIL line if it does not hold:
- PS1 is expanded once per prompt: a $(...) in it ran on every key the
  line editor redrew, 29 times for one 19-key line, until 712;
- ^C at the prompt with the next line typed straight after it, in one
  write, runs that line (dash loses the whole line, bash its first
  character - 711);
- a SIGINT another process sends while the shell waits at the prompt
  does not reach the next command, forth or plain (GOALS.md 8c's kind).
"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pty_session import Session

shell = os.path.abspath(os.environ.get('THIS_SH', os.path.join(HERE, '..', '..', 'relfsh')).split()[0])
fails = 0
def env_with(ps1):
    return {'PS1': ps1, 'RELF_PS1': ps1, 'HOME': '/tmp', 'TERM': 'xterm', 'PATH': '/usr/bin:/bin'}
def fail(msg):
    global fails; fails += 1; print('FAIL prompt-probe: ' + msg)

# 1. PS1 expanded once per prompt
cnt = '/tmp/relf-prompt-probe.%d' % os.getpid()
open(cnt, 'w').close()
s = Session([shell], env=env_with('$(echo x >> %s)$ ' % cnt)); s.wait_prompt()
for ch in 'echo abcdefghijklmn':
    s.send(ch, wait=False); time.sleep(0.03)
s.send('\n'); s.send('exit\n', wait=False); s.drain(0.4); s.close()
n = len(open(cnt).read().split()); os.unlink(cnt)
if n > 2: fail('PS1 expanded %d times for two prompts and one 19-key line' % n)

# 2. ^C at the prompt, the next line straight after it
s = Session([shell], env=env_with('$ ')); s.wait_prompt()
s.send(b'\x03echo typed-ahead\n')
s.send('exit\n', wait=False); s.drain(0.4); s.close()
if 'typed-ahead' not in s.out.replace('echo typed-ahead', ''):
    fail('the line typed straight after ^C did not run')

# 3. a SIGINT from another process while the shell waits at the prompt
s = Session([shell], env=env_with('$ ')); s.wait_prompt()
s.send('(sleep 0.3; kill -INT $$) &\n')
time.sleep(1.0); s.drain(0.3)
mark = len(s.out)
s.send("forth 'DEPTH . 77 . CR'\n"); s.send('echo plain-ran\n')
s.send('exit\n', wait=False); s.drain(0.4); s.close()
tail = s.out[mark:]
if '0 77' not in tail: fail('a forth command after a SIGINT at the prompt did not run')
if 'plain-ran' not in tail.replace('echo plain-ran', ''): fail('a command after a SIGINT at the prompt did not run')

print('prompt-probe: 3 checks, %d failed' % fails)
sys.exit(1 if fails else 0)
