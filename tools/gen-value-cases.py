#!/usr/bin/env python3
"""tools/gen-value-cases.py - the construct matrix's missing dimension.

The matrix (tests/matrix) wraps thirty constructs in fourteen contexts,
but each construct holds ONE fixed value - `case ab in x|a*)` - so no
single-digit case pattern was ever tried, and `case x in 2)` was a
segmentation fault for as long as anyone can tell (found by yash's
suite in Iteration 420). This writes differential cases that hold the
construct still and vary the VALUE: the edge values that have bitten
this project, and a few that plausibly could.

    python3 tools/gen-value-cases.py      # rewrites tests/diff/cases/values-*.sh

Each case prints with printf, so the reference (bash) cannot differ over
echo's backslash rules, and runs every value as its own line of literal
source text - the point is what the PARSER sees, not what a variable
holds. Iteration 422.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'tests', 'diff', 'cases')

VALUES = [
    ("a lone digit",           "2"),
    ("zero",                   "0"),
    ("two digits",             "12"),
    ("a negative number",      "-3"),
    ("empty, double-quoted",   '""'),
    ("empty, single-quoted",   "''"),
    ("a blank inside quotes",  "'a b'"),
    ("a glob star, quoted",    "'*'"),
    ("a bracket class",        "'[0-9]'"),
    ("a lone dash",            "-"),
    ("two dashes",             "--"),
    ("a hash, quoted",         "'#'"),
    ("a bang, quoted",         "'!'"),
    ("a backslash, quoted",    "'\\'"),
    ("a dollar, quoted",       "'$'"),
    ("an equals sign",         "a=b"),
    ("a long word",            "w" * 300),
]

TEMPLATES = {
    'case-same': ("the value as its own case pattern",
                  "case @V@ in @V@) printf 'same\\n' ;; *) printf 'other\\n' ;; esac"),
    'case-var': ("a variable holding the value, against the literal pattern",
                 "v=@V@; case \"$v\" in @V@) printf 'match\\n' ;; *) printf 'no\\n' ;; esac"),
    'case-alt': ("the value as the second alternative",
                 "case @V@ in zzz|@V@) printf 'alt\\n' ;; *) printf 'none\\n' ;; esac"),
    'for-list': ("the value in a for list",
                 "for i in @V@; do printf '[%s]' \"$i\"; done; printf '\\n'"),
    'test-eq': ("the value compared with itself by [ = ]",
                "[ @V@ = @V@ ] && printf 'eq\\n' || printf 'ne\\n'"),
    'args': ("the value as positional parameters",
             "set -- @V@; printf '%s|%s\\n' \"$#\" \"$*\""),
    'func-arg': ("the value as a function's argument",
                 "f() { printf '<%s>\\n' \"$1\"; }; f @V@"),
    'assign-len': ("the value assigned, then its length",
                   "x=@V@; printf '%s\\n' \"${#x}\""),
}

def main():
    for name, (what, tmpl) in TEMPLATES.items():
        lines = ["# %s (tools/gen-value-cases.py, Iteration 422)." % what.capitalize(),
                 "# Generated: edit the generator, not this file.", ""]
        for label, v in VALUES:
            lines.append("# %s" % label)
            lines.append(tmpl.replace('@V@', v))
        open(os.path.join(OUT, 'values-%s.sh' % name), 'w').write('\n'.join(lines) + '\n')
    print("wrote %d cases, %d values each" % (len(TEMPLATES), len(VALUES)))

main()
