# XCU 2.6.2. ${#parameter} is the length in characters, and the word
# in a ${parameter:-word} is itself subject to expansion.
v=hello
printf '%s\n' "${#v}"
unset u
d=fallback
printf '%s\n' "${u:-$d}"
printf '%s\n' "${u:-$(printf sub)}"
set -- a b c
printf '%s\n' "${#}"
