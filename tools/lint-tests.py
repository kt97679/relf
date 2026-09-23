#!/usr/bin/env python3
"""tools/lint-tests.py - tests that ask the HOST a question.

An assertion about this shell must not run whatever `sh` the machine
has: in Iteration 465 one ran `sh -c "kill -QUIT $$"`, which is dash here
and bash on an ARMv7 Gentoo box - and bash ignores SIGQUIT when it is not
interactive, so the assertion passed here and failed there. The shell
under test is "$THIS_SH", or "$0" inside a -c string given it as the
command name. A line that means to use the host shell says why with
`# host-sh:` on the line.
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(os.path.dirname(HERE), 'tests', 'shell')
BARE = re.compile(r'(^|[\s;(&|`])sh\s+-c\b')
bad = 0
for name in sorted(os.listdir(TESTS)):
    if not name.startswith('run-'):
        continue
    with open(os.path.join(TESTS, name)) as f:
        for n, line in enumerate(f, 1):
            if line.lstrip().startswith('#') or '# host-sh:' in line:
                continue
            if BARE.search(line):
                bad += 1
                print('tests/shell/%s:%d: runs the host sh: %s' % (name, n, line.strip()[:90]))
print('test lint: clean' if not bad else 'test lint: %d host-dependent line(s)' % bad)
sys.exit(1 if bad else 0)
