# LINENO (XCU 2.5.3, Iteration 475): the line the running command began
# on, counting every physical line - blank ones, and the ones a command
# substitution, a parameter expansion or an arithmetic expansion spans.
# bash is the reference; the dash installed here does not set it.
echo "1: $LINENO"
echo "2: $LINENO"

echo "4: $LINENO"
: $(echo foo
echo \
baz)
echo "9: $LINENO"
: ${foo#
bar \
baz}
echo "13: $LINENO"
: $((1
+ \
2))
echo "17: $LINENO"
f() {
    echo "in f: $LINENO"
}
f
echo "default form: ${LINENO:-unset}"
x=$(echo "$LINENO"); echo "in a substitution: $x"
