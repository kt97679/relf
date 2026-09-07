# XCU 2.5.1 Positional Parameters. set replaces them, shift discards
# from the front, and ${10} needs braces because $10 is $1 then '0'.
set -- a b c d e f g h i j k
printf '%s\n' "$#"
printf '%s\n' "$1$2"
printf '%s\n' "${10}"
shift 3
printf '%s %s\n' "$#" "$1"
set --
printf '%s\n' "$#"
