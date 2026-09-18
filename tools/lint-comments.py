#!/usr/bin/env python3
"""tools/lint-comments.py - text after a closing `)` on a comment line.

A `( ... )` comment ends at its FIRST `)`, so a stack note written as
`( u addr u )   R: was-start` leaves `R:` to be compiled, and the file
fails to load with "Undefined word R:". That mistake has been made three
times now (Iterations 286, 291 and 302), each costing a build cycle to
find, so it is checked here instead.
"""
import re, sys

# Only the mistake itself: a stack note like "R: was-start" left after a
# closing paren. Ordinary code after a stack comment - `: FOO ( a --- b )
# SWAP ;` - is how every definition is written and is not flagged.
BAD = re.compile(r'\([^)\n]*\)[^\\\n]*?\b([A-Za-z]{1,3}:)(?:\s|$)')
def check(path):
    bad = []
    for n, line in enumerate(open(path), 1):
        if '(' not in line or line.lstrip().startswith('\\'):
            continue
        before_comment = line.split('\\')[0]
        m = BAD.search(before_comment)
        if m:
            bad.append((n, line.rstrip()))
    return bad

status = 0
for path in sys.argv[1:]:
    for n, line in check(path):
        print(f"{path}:{n}: text after a closing ')': {line.strip()}")
        status = 1
print("comment lint: clean" if status == 0 else "comment lint: problems above")
sys.exit(status)
