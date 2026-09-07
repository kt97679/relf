# XCU 2.2.2 Single-Quotes. Every character is literal; a backslash
# inside single quotes is an ordinary backslash and no expansion of
# any kind happens.
v=set
printf '%s\n' '$v'
printf '%s\n' 'a\nb'
printf '%s\n' '`echo hi`'
printf '%s\n' ''
