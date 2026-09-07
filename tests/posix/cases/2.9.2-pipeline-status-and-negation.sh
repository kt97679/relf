# XCU 2.9.2 Pipelines. The status is that of the LAST command, and a
# leading '!' negates it.
true | false
printf '%s\n' "$?"
false | true
printf '%s\n' "$?"
! false
printf '%s\n' "$?"
! true
printf '%s\n' "$?"
