# XCU 2.6.4. A variable inside an arithmetic expression is expanded
# whether or not it is written with a '$', and a null or unset
# variable is treated as zero.
n=6
printf '%s\n' "$((n + 1))"
printf '%s\n' "$(($n + 1))"
unset u
printf '%s\n' "$((u + 5))"
e=
printf '%s\n' "$((e + 5))"
i=0
i=$((i + 1))
printf '%s\n' "$i"
