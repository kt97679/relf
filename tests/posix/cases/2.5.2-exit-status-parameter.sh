# XCU 2.5.2. '$?' is the exit status of the most recent pipeline, and
# reading it does not change it.
true
printf '%s\n' "$?"
false
printf '%s\n' "$?"
printf '%s\n' "$?"
(exit 42)
printf '%s\n' "$?"
