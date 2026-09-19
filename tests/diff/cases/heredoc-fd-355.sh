# heredoc-fd-355.sh - a here-document on a numbered descriptor, and more
# than one on a command. Two faults (Iterations 351 and 355): one buffer
# held one prepared body, so `cmd <<A 3<<B` ran both from the last one;
# and the pipe's read end can land ON the descriptor being redirected -
# fd 3 is the lowest free one for `cat 3<<E` - so the copy was a no-op
# and the close after it destroyed the descriptor.
cat 3<<E <&3
one
E
exec 3<<E
two
E
cat <&3
exec 3<&-
while read a; do read b <&3; echo "$a-$b"; done <<E1 3<<E2
p
q
E1
x
y
E2
cat <<A 4<<B
first
A
{ cat <&4; } 4<&4
second
B
cat <<Z
plain
Z
