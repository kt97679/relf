# The value compared with itself by [ = ] (tools/gen-value-cases.py, Iteration 422).
# Generated: edit the generator, not this file.

# a lone digit
[ 2 = 2 ] && printf 'eq\n' || printf 'ne\n'
# zero
[ 0 = 0 ] && printf 'eq\n' || printf 'ne\n'
# two digits
[ 12 = 12 ] && printf 'eq\n' || printf 'ne\n'
# a negative number
[ -3 = -3 ] && printf 'eq\n' || printf 'ne\n'
# empty, double-quoted
[ "" = "" ] && printf 'eq\n' || printf 'ne\n'
# empty, single-quoted
[ '' = '' ] && printf 'eq\n' || printf 'ne\n'
# a blank inside quotes
[ 'a b' = 'a b' ] && printf 'eq\n' || printf 'ne\n'
# a glob star, quoted
[ '*' = '*' ] && printf 'eq\n' || printf 'ne\n'
# a bracket class
[ '[0-9]' = '[0-9]' ] && printf 'eq\n' || printf 'ne\n'
# a lone dash
[ - = - ] && printf 'eq\n' || printf 'ne\n'
# two dashes
[ -- = -- ] && printf 'eq\n' || printf 'ne\n'
# a hash, quoted
[ '#' = '#' ] && printf 'eq\n' || printf 'ne\n'
# a bang, quoted
[ '!' = '!' ] && printf 'eq\n' || printf 'ne\n'
# a backslash, quoted
[ '\' = '\' ] && printf 'eq\n' || printf 'ne\n'
# a dollar, quoted
[ '$' = '$' ] && printf 'eq\n' || printf 'ne\n'
# an equals sign
[ a=b = a=b ] && printf 'eq\n' || printf 'ne\n'
# a long word
[ wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww = wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww ] && printf 'eq\n' || printf 'ne\n'
