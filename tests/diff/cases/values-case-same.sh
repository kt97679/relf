# The value as its own case pattern (tools/gen-value-cases.py, Iteration 422).
# Generated: edit the generator, not this file.

# a lone digit
case 2 in 2) printf 'same\n' ;; *) printf 'other\n' ;; esac
# zero
case 0 in 0) printf 'same\n' ;; *) printf 'other\n' ;; esac
# two digits
case 12 in 12) printf 'same\n' ;; *) printf 'other\n' ;; esac
# a negative number
case -3 in -3) printf 'same\n' ;; *) printf 'other\n' ;; esac
# empty, double-quoted
case "" in "") printf 'same\n' ;; *) printf 'other\n' ;; esac
# empty, single-quoted
case '' in '') printf 'same\n' ;; *) printf 'other\n' ;; esac
# a blank inside quotes
case 'a b' in 'a b') printf 'same\n' ;; *) printf 'other\n' ;; esac
# a glob star, quoted
case '*' in '*') printf 'same\n' ;; *) printf 'other\n' ;; esac
# a bracket class
case '[0-9]' in '[0-9]') printf 'same\n' ;; *) printf 'other\n' ;; esac
# a lone dash
case - in -) printf 'same\n' ;; *) printf 'other\n' ;; esac
# two dashes
case -- in --) printf 'same\n' ;; *) printf 'other\n' ;; esac
# a hash, quoted
case '#' in '#') printf 'same\n' ;; *) printf 'other\n' ;; esac
# a bang, quoted
case '!' in '!') printf 'same\n' ;; *) printf 'other\n' ;; esac
# a backslash, quoted
case '\' in '\') printf 'same\n' ;; *) printf 'other\n' ;; esac
# a dollar, quoted
case '$' in '$') printf 'same\n' ;; *) printf 'other\n' ;; esac
# an equals sign
case a=b in a=b) printf 'same\n' ;; *) printf 'other\n' ;; esac
# a long word
case wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww in wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww) printf 'same\n' ;; *) printf 'other\n' ;; esac
