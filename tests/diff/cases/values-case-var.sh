# A variable holding the value, against the literal pattern (tools/gen-value-cases.py, Iteration 422).
# Generated: edit the generator, not this file.

# a lone digit
v=2; case "$v" in 2) printf 'match\n' ;; *) printf 'no\n' ;; esac
# zero
v=0; case "$v" in 0) printf 'match\n' ;; *) printf 'no\n' ;; esac
# two digits
v=12; case "$v" in 12) printf 'match\n' ;; *) printf 'no\n' ;; esac
# a negative number
v=-3; case "$v" in -3) printf 'match\n' ;; *) printf 'no\n' ;; esac
# empty, double-quoted
v=""; case "$v" in "") printf 'match\n' ;; *) printf 'no\n' ;; esac
# empty, single-quoted
v=''; case "$v" in '') printf 'match\n' ;; *) printf 'no\n' ;; esac
# a blank inside quotes
v='a b'; case "$v" in 'a b') printf 'match\n' ;; *) printf 'no\n' ;; esac
# a glob star, quoted
v='*'; case "$v" in '*') printf 'match\n' ;; *) printf 'no\n' ;; esac
# a bracket class
v='[0-9]'; case "$v" in '[0-9]') printf 'match\n' ;; *) printf 'no\n' ;; esac
# a lone dash
v=-; case "$v" in -) printf 'match\n' ;; *) printf 'no\n' ;; esac
# two dashes
v=--; case "$v" in --) printf 'match\n' ;; *) printf 'no\n' ;; esac
# a hash, quoted
v='#'; case "$v" in '#') printf 'match\n' ;; *) printf 'no\n' ;; esac
# a bang, quoted
v='!'; case "$v" in '!') printf 'match\n' ;; *) printf 'no\n' ;; esac
# a backslash, quoted
v='\'; case "$v" in '\') printf 'match\n' ;; *) printf 'no\n' ;; esac
# a dollar, quoted
v='$'; case "$v" in '$') printf 'match\n' ;; *) printf 'no\n' ;; esac
# an equals sign
v=a=b; case "$v" in a=b) printf 'match\n' ;; *) printf 'no\n' ;; esac
# a long word
v=wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww; case "$v" in wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww) printf 'match\n' ;; *) printf 'no\n' ;; esac
