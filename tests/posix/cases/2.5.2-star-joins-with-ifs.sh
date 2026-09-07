# XCU 2.5.2. "$*" joins the parameters with the FIRST character of
# IFS, not with a space, and with nothing at all when IFS is null.
set -- a b c
IFS=:
printf '%s\n' "$*"
IFS=
printf '%s\n' "$*"
IFS=' '
printf '%s\n' "$*"
