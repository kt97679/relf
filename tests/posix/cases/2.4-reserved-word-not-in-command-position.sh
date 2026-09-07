# XCU 2.4 Reserved Words. A reserved word is recognised only where a
# command name is expected. Elsewhere - as an argument, or after an
# assignment - it is an ordinary word.
printf '%s\n' if then fi done esac
v=while
printf '%s\n' "$v"
for x in do done; do printf 'x=%s\n' "$x"; done
