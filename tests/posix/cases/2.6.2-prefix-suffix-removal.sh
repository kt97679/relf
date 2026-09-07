# XCU 2.6.2. '%' and '#' remove the shortest match, '%%' and '##' the
# longest, and the patterns are pattern-matching notation, not
# literals.
p=/one/two/three.tar.gz
printf '%s\n' "${p##*/}"
printf '%s\n' "${p#*/}"
printf '%s\n' "${p%%.*}"
printf '%s\n' "${p%.*}"
printf '%s\n' "${p%%/*}(empty)"
