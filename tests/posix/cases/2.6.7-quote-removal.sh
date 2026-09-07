# XCU 2.6.7 Quote Removal. Quotes that were not the result of an
# expansion are removed; quotes produced BY an expansion are not.
v='"quoted"'
printf '%s\n' "$v"
printf '%s\n' 'a'b'c'
printf '%s\n' ""a""
printf '%s\n' a""b
