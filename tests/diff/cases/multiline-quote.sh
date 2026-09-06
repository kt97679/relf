# A quoted string may span physical lines; the newline is part of it.
echo "a
b"
echo 'p
q'
v="one
two"
echo "[$v]"
echo after
