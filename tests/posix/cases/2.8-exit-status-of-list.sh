# XCU 2.8.2 / 2.9.3. The exit status of an AND-OR list is that of the
# last command executed; a list that short-circuits reports the
# status of the command that caused it.
true && false
printf '%s\n' "$?"
false || true
printf '%s\n' "$?"
false && printf 'not reached\n'
printf '%s\n' "$?"
true || printf 'not reached\n'
printf '%s\n' "$?"
