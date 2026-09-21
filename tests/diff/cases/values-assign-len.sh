# The value assigned, then its length (tools/gen-value-cases.py, Iteration 422).
# Generated: edit the generator, not this file.

# a lone digit
x=2; printf '%s\n' "${#x}"
# zero
x=0; printf '%s\n' "${#x}"
# two digits
x=12; printf '%s\n' "${#x}"
# a negative number
x=-3; printf '%s\n' "${#x}"
# empty, double-quoted
x=""; printf '%s\n' "${#x}"
# empty, single-quoted
x=''; printf '%s\n' "${#x}"
# a blank inside quotes
x='a b'; printf '%s\n' "${#x}"
# a glob star, quoted
x='*'; printf '%s\n' "${#x}"
# a bracket class
x='[0-9]'; printf '%s\n' "${#x}"
# a lone dash
x=-; printf '%s\n' "${#x}"
# two dashes
x=--; printf '%s\n' "${#x}"
# a hash, quoted
x='#'; printf '%s\n' "${#x}"
# a bang, quoted
x='!'; printf '%s\n' "${#x}"
# a backslash, quoted
x='\'; printf '%s\n' "${#x}"
# a dollar, quoted
x='$'; printf '%s\n' "${#x}"
# an equals sign
x=a=b; printf '%s\n' "${#x}"
# a long word
x=wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww; printf '%s\n' "${#x}"
