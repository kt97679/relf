# special-length-356.sh - `${#?}` is the length of `$?`, and the same
# for the other special parameters. Two things were wrong (Iteration
# 356): the length form looked names up as ordinary variables, so every
# special answered 0; and `${#?}` parsed as the parameter `#` with a `?`
# operator, because Iteration 339 taught the scanner that an operator
# after `#` means the parameter is `#` - true for `${#+word}` and not
# for `${#?}`, where what follows is the closing brace.
false; echo "status-one=${#?}"
(exit 10); echo "status-two=${#?}"
(exit 100); echo "status-three=${#?}"
true; echo "status-zero=${#?}"
echo "pid-is-numeric=$(case ${#$} in [1-9]) echo yes;; *) echo no;; esac)"
set -- a b c; echo "count=${#} params=${#*}"
x=abcde; echo "name=${#x}"
echo "unset-name=${#nosuch}"
echo "with-operator=[${#+SET}] [${#-D}]"
set --; echo "empty-count=${#}"
