# A here-document still waiting for its body belongs to the command
# AROUND a command substitution, not to what is inside it (Iteration
# 461, yash cmdsub-p.tst:139). The inner parse read the pending list at
# the end of the line and took the inner body's lines as the outer's.
cat <<\OUTER; printf '%s\n' "$(cat <<\INNER
inner
INNER
)"
outer
OUTER
# two substitutions on one pending line
cat <<\A; printf '%s %s\n' "$(cat <<\B
one
B
)" "$(cat <<\C
two
C
)"
body-a
A
# a substitution inside a here-document body, and one before a pending body
cat <<A
$(echo sub)
A
x=$(cat <<\D
val
D
); echo "[$x]"
