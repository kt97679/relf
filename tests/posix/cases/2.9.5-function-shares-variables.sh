# XCU 2.9.5. A function runs in the current environment, so variables
# it sets persist, unlike a subshell.
v=before
f() { v=after; }
f
printf '%s\n' "$v"
v=before
(v=insub)
printf '%s\n' "$v"
