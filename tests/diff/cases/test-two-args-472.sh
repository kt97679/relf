# POSIX's two-argument rule for test: `!` negates the one-argument test
# of the second, and a unary primary applies to the second WHATEVER it
# looks like (Iteration 472, found by tools/difffuzz.py). `test -n =`
# failed with 2 here: the general parser read `=` as a binary operator
# short of its right side. Reached in scripts by "$@" expanding to
# nothing: `test "$z" = "$@"` with no parameters is `test -n =` when z
# is -n.
test -n =;  echo "1 $?"
test -n !=; echo "2 $?"
test -z =;  echo "3 $?"
[ -n = ];   echo "4 $?"
test ! =;   echo "5 $?"
test -n -a; echo "6 $?"
z=-n
test "$z" = "$@"; echo "7 $?"
test "$z" != "$@"; echo "8 $?"
# ... and the other counts are unchanged
test -n;    echo "9 $?"
test a = a; echo "10 $?"
test -z ""; echo "11 $?"
