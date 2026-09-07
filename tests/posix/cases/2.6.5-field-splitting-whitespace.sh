# XCU 2.6.5 Field Splitting. IFS whitespace is special: leading and
# trailing runs are ignored and interior runs delimit one field.
IFS=' '
v='  a   b  '
set -- $v
printf '%s\n' "$#"
for w; do printf '[%s]' "$w"; done; printf '\n'
