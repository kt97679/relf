# POSIX.1-2017 XCU 2.5.2 Special Parameters - $#, $*, $@ and the
# field-splitting difference between "$*" and "$@".
set -- a b c
printf '%s\n' "$#"
printf '%s\n' "$*"
for w in "$@"; do printf '[%s]' "$w"; done
printf '\n'
set -- 'one two' three
printf '%s\n' "$#"
for w in "$@"; do printf '[%s]' "$w"; done
printf '\n'
