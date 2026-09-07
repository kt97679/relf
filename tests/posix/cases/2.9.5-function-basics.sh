# XCU 2.9.5 Function Definition Command. A function's positional
# parameters are its arguments; the caller's are restored on return.
set -- outer1 outer2
f() {
    printf 'inside %s %s\n' "$#" "$1"
    return 7
}
f a b c
printf 'status %s\n' "$?"
printf 'outside %s %s\n' "$#" "$1"
