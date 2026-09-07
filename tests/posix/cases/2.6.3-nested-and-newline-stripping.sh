# XCU 2.6.3 Command Substitution. Trailing newlines are removed, both
# forms nest, and the two forms are equivalent.
printf '[%s]\n' "$(printf 'x\n\n\n')"
printf '[%s]\n' "$(printf 'a b')"
printf '[%s]\n' "`printf 'back'`"
printf '[%s]\n' "$(printf '%s' "$(printf inner)")"
