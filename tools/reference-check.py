#!/usr/bin/env python3
"""tools/reference-check.py [DOC] [SCRIPT] - every example in docs/REFERENCE.md is one the suite runs (900).

An example is an indented line of the reference, outside its tables, that is not a usage line (bin/cm,
#!) or a list item; it must be a line of tests/cm/scripts/reference.cm, comments and spacing aside, which
tests/cm/run runs against its expected output. So the reference cannot show code the language no longer
takes. Prints each example missing and exits 1 if any is.
"""
import re, sys
doc = sys.argv[1] if len(sys.argv) > 1 else 'docs/REFERENCE.md'
script = sys.argv[2] if len(sys.argv) > 2 else 'tests/cm/scripts/reference.cm'

def norm(line):
    line = line.strip()
    if line.startswith('#'):
        return ''
    return re.sub(r'\s+', ' ', re.sub(r'\s#\s.*$', '', line)).strip()

ran = {norm(l) for l in open(script).read().split('\n')} - {''}
missing = []
for line in open(doc).read().split('\n'):
    if not line.startswith('    ') or line.lstrip().startswith(('bin/cm', '#!', '-', '|')):
        continue
    n = norm(line)
    if n and n not in ran:
        missing.append(line.strip())
for m in missing:
    print('not in %s: %s' % (script, m))
print('reference-check: %d examples missing' % len(missing))
sys.exit(1 if missing else 0)
