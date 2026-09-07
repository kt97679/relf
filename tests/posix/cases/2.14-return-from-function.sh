# XCU 2.14 return. Returns from the function with the given status,
# and stops executing the rest of the body.
f() {
    printf 'before\n'
    return 3
    printf 'after\n'
}
f
printf 'status=%s\n' "$?"
g() { return; }
true
g
printf 'bare=%s\n' "$?"
