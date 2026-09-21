#!/usr/bin/env python3
"""tools/lint-comments.py - text after a closing `)` on a comment line,
and a control word swallowed by a `\\` comment.

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

# The mirror image: CODE swallowed by a `\` comment, which runs to the
# end of the line. `2 LAST-STATUS !  \ the status the caller reports EXIT`
# compiles no EXIT at all, so printf with no arguments printed its usage
# and fell through into formatting, and segfaulted; kill did the same and
# reported "no such process". Both came from one edit in Iteration 357
# that appended a comment to lines ending in EXIT; the fuzzer found the
# first in 424, and this check found the second (Iteration 426). Flagged
# only after code, and only for a control word, since a comment line of
# prose can end in "LOOP" legitimately.
SWALLOWED = re.compile(r'\\\s.*\s(EXIT|THEN|ELSE|REPEAT|UNTIL|AGAIN|LOOP|\+LOOP|UNLOOP)\s*$')
def check_swallowed(path):
    bad = []
    for n, line in enumerate(open(path), 1):
        i = line.find('\\ ')
        if i <= 0 or not line[:i].strip():
            continue                              # a whole-line comment
        if line[:i].rstrip().endswith('S"') or '."' in line[:i]:
            continue                              # a backslash inside a string
        if SWALLOWED.search(line[i:]):
            bad.append((n, line.rstrip()))
    return bad

status = 0
for path in sys.argv[1:]:
    for n, line in check(path):
        print(f"{path}:{n}: text after a closing ')': {line.strip()}")
        status = 1
    for n, line in check_swallowed(path):
        print(f"{path}:{n}: a control word inside a \\ comment: {line.strip()}")
        status = 1
print("comment lint: clean" if status == 0 else "comment lint: problems above")
sys.exit(status)
