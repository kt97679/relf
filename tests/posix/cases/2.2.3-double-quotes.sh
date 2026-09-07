# XCU 2.2.3 Double-Quotes. Parameter and command substitution still
# occur; backslash is special only before $ ` " \ and <newline>.
v=set
printf '%s\n' "$v"
printf '%s\n' "a\nb"
printf '%s\n' "\$v"
printf '%s\n' "a\"b"
printf '%s\n' "back\\slash"
