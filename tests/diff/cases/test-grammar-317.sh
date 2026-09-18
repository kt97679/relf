# test-grammar-317.sh - POSIX's `test` grammar: primaries joined by -a
# and -o, negated with !, grouped with ( ). Until Iteration 317 the
# builtin counted arguments and handled at most four, so
# `[ 1 -eq 1 -a 2 -eq 2 ]` was simply false. The file tests -f, -d, -r,
# -w, -x and -s are here too: -f and -d answered "does it exist", and
# -r -w -x did not exist at all.
[ 1 -eq 1 -a 2 -eq 2 ] && echo both
[ 1 -eq 2 -o 2 -eq 2 ] && echo either
[ 1 -eq 2 -a x = x ] || echo and-false
[ 1 -eq 2 -o x = y ] || echo or-false
[ ! -n "" ] && echo bang-unary
[ ! x = y ] && echo bang-binary
[ \( 1 -eq 1 \) -a x = x ] && echo grouped
[ \( 1 -eq 2 -o 3 -eq 3 \) -a x = x ] && echo grouped-or
[ -n "" -o -n x ] && echo or-unary
[ x = x -a ! -n "" ] && echo mixed
[ -f /etc/passwd ] && echo is-file
[ -f /tmp ] || echo dir-not-file
[ -d /tmp ] && echo is-dir
[ -d /etc/passwd ] || echo file-not-dir
[ -r /etc/passwd ] && echo readable
[ -x /bin/sh ] && echo executable
[ -s /etc/passwd ] && echo nonempty
[ -e /etc/passwd -a -e /tmp ] && echo both-exist
[ -f /nonexistent-xyz ] || echo missing
[ 5 -gt 3 -a 3 -gt 1 -a 1 -gt 0 ] && echo chained
test 1 -eq 1 -a 2 -eq 2 && echo test-form
