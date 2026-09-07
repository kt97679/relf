# XCU 2.6.4 Arithmetic Expansion. The operators and precedence are
# those of the ISO C language, signed long arithmetic.
printf '%s\n' "$((1 + 2 * 3))"
printf '%s\n' "$(((1 + 2) * 3))"
printf '%s\n' "$((7 / 2))"
printf '%s\n' "$((7 % 3))"
printf '%s\n' "$((-7 / 2))"
printf '%s\n' "$((1 < 2))"
printf '%s\n' "$((0 || 3))"
printf '%s\n' "$((5 & 3))"
