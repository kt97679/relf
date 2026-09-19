# command-306.sh - `command NAME args` runs it as if it were not a
# function, and `command -p` looks in a default PATH (XCU). Until
# Iteration 306 only `command -v` existed: `command echo hi` printed
# nothing at all and returned 0.
command echo one
command -p echo two
f() { echo "the function"; }
f
command f 2>/dev/null || echo "command f: rc=$?"
command -v f
command -v echo
command -v /bin/sh
# The exact status for a name that is not found differs between the
# references: bash says 1, dash and this shell say 127, and POSIX asks
# only for "greater than zero" (Iteration 356).
command -v nosuchthing > /dev/null 2>&1; [ $? -gt 0 ] && echo "missing is an error"
command true; echo "true rc=$?"
command false; echo "false rc=$?"
command command echo nested
g() { command echo "inside a function"; }
g
v=$(command echo substituted); echo "[$v]"
command echo a b c | cat
command -p echo after-p
echo "PATH still works: $(ls /dev/null)"
