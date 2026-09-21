# The value as a function's argument (tools/gen-value-cases.py, Iteration 422).
# Generated: edit the generator, not this file.

# a lone digit
f() { printf '<%s>\n' "$1"; }; f 2
# zero
f() { printf '<%s>\n' "$1"; }; f 0
# two digits
f() { printf '<%s>\n' "$1"; }; f 12
# a negative number
f() { printf '<%s>\n' "$1"; }; f -3
# empty, double-quoted
f() { printf '<%s>\n' "$1"; }; f ""
# empty, single-quoted
f() { printf '<%s>\n' "$1"; }; f ''
# a blank inside quotes
f() { printf '<%s>\n' "$1"; }; f 'a b'
# a glob star, quoted
f() { printf '<%s>\n' "$1"; }; f '*'
# a bracket class
f() { printf '<%s>\n' "$1"; }; f '[0-9]'
# a lone dash
f() { printf '<%s>\n' "$1"; }; f -
# two dashes
f() { printf '<%s>\n' "$1"; }; f --
# a hash, quoted
f() { printf '<%s>\n' "$1"; }; f '#'
# a bang, quoted
f() { printf '<%s>\n' "$1"; }; f '!'
# a backslash, quoted
f() { printf '<%s>\n' "$1"; }; f '\'
# a dollar, quoted
f() { printf '<%s>\n' "$1"; }; f '$'
# an equals sign
f() { printf '<%s>\n' "$1"; }; f a=b
# a long word
f() { printf '<%s>\n' "$1"; }; f wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww
