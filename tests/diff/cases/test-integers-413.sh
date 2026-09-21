# Integer operands to test's comparisons (Iteration 413). An operand is
# blanks, an optional sign, digits and blanks; anything else is an
# error and the status is 2, not 0 and not 1. Found by the Advanced
# Bash-Scripting Guide corpus: `[ "$UID" -eq 0 ]`, with UID unset,
# told an ordinary user they were root.
for pair in '"" 0' 'abc 0' '1x 2' '" 3" 3' '"3 " 3' '-5 0' '+5 5' '010 10' '"" ""'; do
    eval "set -- $pair"
    [ "$1" -eq "$2" ] 2>/dev/null
    echo "[$1] -eq [$2]: $?"
done
[ 1 -eq ] 2>/dev/null;  echo "missing operand: $?"
[ 2 -gt 1 ];            echo "2 -gt 1: $?"
[ 1 -gt 2 ];            echo "1 -gt 2: $?"
[ -3 -le -3 ];          echo "-3 -le -3: $?"
if [ "$NO_SUCH_VAR_413" -eq 0 ] 2>/dev/null; then echo "root"; else echo "not root"; fi
