# Line continuation. What decides whether a trailing backslash
# continues the line is the PARITY of the backslash run it ends, not
# whether the character before it happens to be a backslash too
# (Iteration 102).

# one: a continuation
printf '[%s]\n' "a\
b"

# two: an escaped backslash, no continuation
printf '[%s]\n' "a\\"
echo after-two

# three: an escaped backslash AND a continuation
printf '[%s]\n' "a\\\
b"

# four: two escaped backslashes, no continuation
printf '[%s]\n' "a\\\\"
echo after-four

# five: two escaped backslashes and a continuation
printf '[%s]\n' "a\\\\\
b"

# outside quotes as well
echo one\
two
echo three\\
echo four\\\
five
