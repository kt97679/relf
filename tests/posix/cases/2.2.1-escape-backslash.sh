# XCU 2.2.1 Escape Character. An unquoted backslash preserves the
# literal value of the next character, except <newline>, where the
# pair is a line continuation and both are removed.
printf '%s\n' a\ b
printf '%s\n' \$notavar
printf '%s\n' \\
printf '%s\n' a\
b
