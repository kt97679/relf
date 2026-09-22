# `${#` followed by an operator, with or without a colon, is the
# parameter `#` - `${#:=x}` printed `0:=x}` (Iteration 434, yash
# param-p.tst:268) - while `${#name}` is a length and `${#?}` the length
# of $?.
set -- p q r
printf '[%s]' ${#-""}; echo
printf '[%s]' ${#?X}; echo
printf '[%s]' ${#+""} "${#:+}"; echo
printf '[%s]' ${#=""} "${#:=}"; echo
echo ${#:=x} ${#:-y} ${#:+z} [${#:?w}]
x=abc; echo ${#x} ${#} ${#?}
