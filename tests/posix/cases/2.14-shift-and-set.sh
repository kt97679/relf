# XCU 2.14 shift, set. 'set --' with no further arguments clears the
# positional parameters; shift with no operand shifts by one.
set -- a b c
shift
printf '%s %s\n' "$#" "$1"
set -- x y z
shift 2
printf '%s %s\n' "$#" "$1"
