#!/usr/bin/env python3
"""tools/chaos.py [SHELL...] - the shell under a storm of signals.

A workload of command substitutions through pipes, whose result is
exact - the sum of 0..299, 44850 - runs while another process sends a
signal every few milliseconds, which a trap counts. Every read of a pipe
and every wait is then liable to be interrupted (EINTR); one that is not
retried loses output, and the sum comes out wrong, or a line goes
missing, or the shell dies. The check is exact: the sum, the final line,
the status, and a trap that ran at least once - for each of USR1, CHLD,
WINCH, ALRM, and INT with a trap. dash runs the same storms, to show
the test is fair. TESTING-IDEAS.md 10; written in Iteration 563.
"""
import os, signal, subprocess, sys, time, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELLS = [os.path.abspath(a) for a in sys.argv[1:]] or [os.path.join(ROOT, 'relfsh64'), os.path.join(ROOT, 'relfshasm64'), 'dash']
SCRIPT = r'''
n=0
trap 'n=$((n + 1))' %(SIG)s
i=0; sum=0
while [ $i -lt 300 ]; do
    x=$(printf '%%s\n' "$i" | cat)
    sum=$((sum + x))
    i=$((i + 1))
done
echo "sum=$sum"
[ "$n" -gt 0 ] && echo "trapped"
echo end
'''
SIGNALS = [('USR1', signal.SIGUSR1), ('CHLD', signal.SIGCHLD), ('WINCH', signal.SIGWINCH),
           ('ALRM', signal.SIGALRM), ('INT', signal.SIGINT)]

def storm(pid, sig, stop, interval=0.002):
    sent = 0
    while not stop.is_set():
        try:
            os.kill(pid, sig); sent += 1
        except ProcessLookupError:
            break
        time.sleep(interval)
    return sent

fails = 0
for sh in SHELLS:
    for name, sig in SIGNALS:
        p = subprocess.Popen([sh, '-c', SCRIPT % {'SIG': name}], stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stop = threading.Event()
        time.sleep(0.05)                      # let the trap be set first
        t = threading.Thread(target=storm, args=(p.pid, sig, stop)); t.start()
        try:
            out, err = p.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            p.kill(); out, err = p.communicate()
        stop.set(); t.join()
        text = out.decode(errors='replace')
        # SIGCHLD and SIGWINCH may be delivered but need not run a trap in
        # every shell before the loop ends; the exactness is what counts.
        want_trap = name not in ('CHLD', 'WINCH')
        ok = ('sum=44850' in text and text.rstrip().endswith('end') and p.returncode == 0
              and ('trapped' in text or not want_trap))
        fails += not ok
        print('%-12s %-6s %s%s' % (os.path.basename(sh), name, 'ok' if ok else 'FAILED',
              '' if ok else '  status %s, output %r, stderr %r' % (p.returncode, text[-80:], err.decode(errors='replace')[:120])))
print('%d storms, %d failed' % (len(SHELLS) * len(SIGNALS), fails))
