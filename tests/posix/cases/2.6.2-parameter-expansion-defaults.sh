# POSIX.1-2017 XCU 2.6.2 Parameter Expansion - the four
# use-default/assign-default/alternative forms and ${#parameter}.
# The ':'-prefixed variants act on "unset or null"; the plain ones on
# "unset" only, which is the whole distinction being checked here.
unset x
printf '%s\n' "${x:-D1}"
printf '%s\n' "${x-D2}"
x=
printf '%s\n' "${x:-D3}"
printf '%s\n' "${x-D4}"
x=value
printf '%s\n' "${x:+A1}"
printf '%s\n' "${#x}"
unset y
printf '%s\n' "${y:=assigned}"
printf '%s\n' "$y"
