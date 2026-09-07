# Iterating with an explicit "$@" rather than the implicit "for w; do",
# which is itself unimplemented here - an earlier version used the
# implicit form and so tested two features at once, blaming field
# splitting for a for-loop defect.
#
# XCU 2.6.5 Field Splitting. IFS whitespace is special: leading and
# trailing runs are ignored and interior runs delimit one field.
IFS=' '
v='  a   b  '
set -- $v
printf '%s\n' "$#"
for w in "$@"; do printf '[%s]' "$w"; done; printf '\n'
