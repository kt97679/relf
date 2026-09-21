# The value as the second alternative (tools/gen-value-cases.py, Iteration 422).
# Generated: edit the generator, not this file.

# a lone digit
case 2 in zzz|2) printf 'alt\n' ;; *) printf 'none\n' ;; esac
# zero
case 0 in zzz|0) printf 'alt\n' ;; *) printf 'none\n' ;; esac
# two digits
case 12 in zzz|12) printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a negative number
case -3 in zzz|-3) printf 'alt\n' ;; *) printf 'none\n' ;; esac
# empty, double-quoted
case "" in zzz|"") printf 'alt\n' ;; *) printf 'none\n' ;; esac
# empty, single-quoted
case '' in zzz|'') printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a blank inside quotes
case 'a b' in zzz|'a b') printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a glob star, quoted
case '*' in zzz|'*') printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a bracket class
case '[0-9]' in zzz|'[0-9]') printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a lone dash
case - in zzz|-) printf 'alt\n' ;; *) printf 'none\n' ;; esac
# two dashes
case -- in zzz|--) printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a hash, quoted
case '#' in zzz|'#') printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a bang, quoted
case '!' in zzz|'!') printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a backslash, quoted
case '\' in zzz|'\') printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a dollar, quoted
case '$' in zzz|'$') printf 'alt\n' ;; *) printf 'none\n' ;; esac
# an equals sign
case a=b in zzz|a=b) printf 'alt\n' ;; *) printf 'none\n' ;; esac
# a long word
case wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww in zzz|wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww) printf 'alt\n' ;; *) printf 'none\n' ;; esac
