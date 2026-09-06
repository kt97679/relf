# An expansion may be longer than the text it replaces, and longer than
# the input line itself. Until Iteration 108 the tokenizer wrote back
# over its own input, so this was bounded by LINE-MAX and guarded by
# ENSURE-ROOM at every single call site - four bugs were one such call
# being missing.
x=0123456789
echo $x in
echo "$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x" | wc -c
echo "start $x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x$x end"

# the exact shape of the original smear (Iteration 26): a value longer
# than its own reference, with more text after it on the same line
v=abc
echo $v in
echo $v $v $v after

# and of the numeric one (46)
false
echo $? x
true
echo "$?-$?-$? done"

# and the two field-splitting ones (99, 103)
set p q r
echo "[$*]"
echo "1  $@  2"
