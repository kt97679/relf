# XCU 2.6.5. A non-whitespace IFS character delimits exactly one
# field each time it appears, so adjacent ones produce empty fields.
IFS=:
v='a::b:'
set -- $v
printf '%s\n' "$#"
for w; do printf '[%s]' "$w"; done; printf '\n'
