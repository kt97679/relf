# quoted-in-word-363.sh - quoting inside a ${...} word. Within double
# quotes a single quote is literal text in a VALUE word, so
# "${x:+'b c' d}" is one field with the quotes in it, while in a trim
# PATTERN it still quotes, so "${x##*'*'}" matches a literal star. Both
# references agree on the pair; this shell treated every single quote as
# quoting (Iteration 363).
f() { for i; do echo "|$i|"; done; }
x=a
f "${x:+'b c' d}"
f "${x:+"q w"}"
f ${x:+'b c' d}
f ${x:+'lit'}
y='a*b*c'
echo "trim-long=[${y##*'*'}]"
echo "trim-short=[${y%'*'*}]"
echo "trim-escaped=[${y#a\*}]"
z='[ab]c?d'
echo "class=[${z%'?'d}]"
echo "bracket=[${z#'[ab]'}]"
echo "alt-empty=[${x:+''}]"
f ${x:+'' b}
u=
echo "default=[${u:-'q'}]"
echo "default-quoted=[${u:-"q"}]"
# A `~` at the START of a ${...} word is a tilde prefix, as it is at the
# start of any other word (Iteration 381). Inside double quotes, and
# anywhere but the first character, it stays literal.
HOME=/tmp/relf-home
unset a
echo "default=${a-~}"
echo "default-slash=${a-~/x}"
b=b; echo "alternate=${b+~}"
unset c; echo "assign=${c=~}"; echo "assigned=$c"
echo "escaped=${a-\~}"
echo "quoted=\"${a-~}\""
echo "middle=${a-x~y}"
echo "plain-word=$(cd /; echo ~)"
