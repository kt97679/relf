# XCU 2.14 eval. The arguments are concatenated and re-parsed as
# shell input, so a second round of expansion happens.
v=inner
name=v
eval "printf '%s\n' \"\$$name\""
eval 'x=set-by-eval'
printf '%s\n' "$x"
eval 'printf "%s\n" one; printf "%s\n" two'
