#!/usr/bin/env python3
"""tests/interactive/run_cases.py [--record SHELL] [--shell SHELL] [case...]

Runs each case in cases.py on a pseudo-terminal and compares the
transcript with expected/<case>.txt. With --record it writes those files
from the shell given, which is how the expectations were taken from dash;
a case whose expectation this shell cannot meet yet is listed in
KNOWN-DIVERGENT so the suite stays green and the gap stays visible.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pty_session import Session
from cases import CASES

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED = os.path.join(HERE, 'expected')
DIVERGENT = os.path.join(HERE, 'KNOWN-DIVERGENT')

DEFAULT_ENV = {'PS1': '$ ', 'PS2': '> '}   # so any shell prompts alike

def run_case(shell, steps, env, raw=False):
    env = dict(DEFAULT_ENV, **(env or {}))
    argv = shell if isinstance(shell, list) else [shell]
    s = Session(argv, env=env)
    s.prompts_from_env(env)
    if not s.wait_prompt():
        s.close(); return None
    for step in steps:
        nowait = False
        if isinstance(step, tuple): step, kind = step; nowait = (kind == 'nowait')
        if isinstance(step, (int, float)):
            time.sleep(step); s.drain(0.2); continue
        if step in ('INTR', 'EOF', 'QUIT', 'SUSP'):
            s.send_signal_char(step, wait=not nowait)
        else:
            s.send(step, wait=not nowait)
    s.drain()
    s.close()
    return s.raw() if raw else s.transcript(env)

def known_divergent():
    if not os.path.exists(DIVERGENT): return {}
    d = {}
    for line in open(DIVERGENT):
        line = line.split('#')[0].strip()
        if line: d[line] = True
    return d

def main():
    args = sys.argv[1:]
    shell = os.environ.get('THIS_SH', os.path.join(HERE, '..', '..', 'relfsh'))
    record = None
    while args and args[0].startswith('--'):
        if args[0] == '--record': record = args[1]; args = args[2:]
        elif args[0] == '--shell': shell = args[1]; args = args[2:]
        else: print("unknown option", args[0]); return 2
    # THIS_SH may carry arguments: bash needs --norc --noprofile before
    # its own startup files will leave PS1 alone.
    parts = shell.split()
    shell, extra = parts[0], parts[1:]
    shell = os.path.abspath(shell)
    only = set(args)
    os.makedirs(EXPECTED, exist_ok=True)
    div = known_divergent()
    passed = failed = skipped = 0
    for case in CASES:
        name, env, steps = case[0], case[1], case[2]
        raw = len(case) > 3 and case[3] == 'raw'
        if only and name not in only: continue
        path = os.path.join(EXPECTED, name + '.txt')
        if record:
            t = run_case(record.split()[:1] + record.split()[1:], steps, env, raw)
            if t is None: print(f"RECORD-FAIL {name}"); failed += 1; continue
            open(path, 'w').write(t)
            print(f"recorded {name} ({len(t)} bytes)")
            continue
        if not os.path.exists(path):
            print(f"NO-EXPECTATION {name}"); failed += 1; continue
        want = open(path).read()
        got = run_case([shell] + extra, steps, env, raw)
        if got == want:
            passed += 1
            if name in div:
                # A listed case counts as divergent whichever way it goes:
                # job-control turns on timing, and a baseline recording one
                # outcome fails whenever the other happens.
                print(f"NOW-PASSES {name} (listed; still counted divergent)")
                passed -= 1
                skipped += 1
        elif name in div:
            skipped += 1
        else:
            failed += 1
            print(f"FAIL {name}\n  want {want!r}\n  got  {got!r}")
    if record: return 0
    print(f"{passed} passed, {failed} failed, {skipped} known-divergent")
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
