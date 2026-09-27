# A backquoted substitution in a here-document holding an escaped
# backquote: the \` is the command's, not the end. relf copied to the
# first backquote, lost the rest of the body, and wrote ncurses's
# config.status broken (Iteration 565). (`echo \"x\"` inside one is left
# out: bash prints "x" and dash x - a split; relf follows dash.)
args=
cat <<EOF
A \\"`echo "$args" | sed 's/[\\""\`\$]/\\\\&/g'`\\"
B line
C line"
EOF
cat <<EOF
t:`echo a\`echo inner\`b`
u:`printf '%s' "x\\y"` v
EOF
echo after
