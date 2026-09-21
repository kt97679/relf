# The value as positional parameters (tools/gen-value-cases.py, Iteration 422).
# Generated: edit the generator, not this file.

# a lone digit
set -- 2; printf '%s|%s\n' "$#" "$*"
# zero
set -- 0; printf '%s|%s\n' "$#" "$*"
# two digits
set -- 12; printf '%s|%s\n' "$#" "$*"
# a negative number
set -- -3; printf '%s|%s\n' "$#" "$*"
# empty, double-quoted
set -- ""; printf '%s|%s\n' "$#" "$*"
# empty, single-quoted
set -- ''; printf '%s|%s\n' "$#" "$*"
# a blank inside quotes
set -- 'a b'; printf '%s|%s\n' "$#" "$*"
# a glob star, quoted
set -- '*'; printf '%s|%s\n' "$#" "$*"
# a bracket class
set -- '[0-9]'; printf '%s|%s\n' "$#" "$*"
# a lone dash
set -- -; printf '%s|%s\n' "$#" "$*"
# two dashes
set -- --; printf '%s|%s\n' "$#" "$*"
# a hash, quoted
set -- '#'; printf '%s|%s\n' "$#" "$*"
# a bang, quoted
set -- '!'; printf '%s|%s\n' "$#" "$*"
# a backslash, quoted
set -- '\'; printf '%s|%s\n' "$#" "$*"
# a dollar, quoted
set -- '$'; printf '%s|%s\n' "$#" "$*"
# an equals sign
set -- a=b; printf '%s|%s\n' "$#" "$*"
# a long word
set -- wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww; printf '%s|%s\n' "$#" "$*"
