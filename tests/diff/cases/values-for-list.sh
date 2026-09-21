# The value in a for list (tools/gen-value-cases.py, Iteration 422).
# Generated: edit the generator, not this file.

# a lone digit
for i in 2; do printf '[%s]' "$i"; done; printf '\n'
# zero
for i in 0; do printf '[%s]' "$i"; done; printf '\n'
# two digits
for i in 12; do printf '[%s]' "$i"; done; printf '\n'
# a negative number
for i in -3; do printf '[%s]' "$i"; done; printf '\n'
# empty, double-quoted
for i in ""; do printf '[%s]' "$i"; done; printf '\n'
# empty, single-quoted
for i in ''; do printf '[%s]' "$i"; done; printf '\n'
# a blank inside quotes
for i in 'a b'; do printf '[%s]' "$i"; done; printf '\n'
# a glob star, quoted
for i in '*'; do printf '[%s]' "$i"; done; printf '\n'
# a bracket class
for i in '[0-9]'; do printf '[%s]' "$i"; done; printf '\n'
# a lone dash
for i in -; do printf '[%s]' "$i"; done; printf '\n'
# two dashes
for i in --; do printf '[%s]' "$i"; done; printf '\n'
# a hash, quoted
for i in '#'; do printf '[%s]' "$i"; done; printf '\n'
# a bang, quoted
for i in '!'; do printf '[%s]' "$i"; done; printf '\n'
# a backslash, quoted
for i in '\'; do printf '[%s]' "$i"; done; printf '\n'
# a dollar, quoted
for i in '$'; do printf '[%s]' "$i"; done; printf '\n'
# an equals sign
for i in a=b; do printf '[%s]' "$i"; done; printf '\n'
# a long word
for i in wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww; do printf '[%s]' "$i"; done; printf '\n'
