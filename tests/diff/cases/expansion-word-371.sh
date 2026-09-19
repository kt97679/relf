# expansion-word-371.sh - the word of a ${...} and the result of an
# arithmetic expansion. Three faults (Iteration 371):
#
#   - a backslash in a ${...} word took the DOUBLE-QUOTE rule even when
#     the expansion was not inside quotes, so `${x:+a\*b}` kept it;
#   - the aside capture that evaluates an arithmetic expression emitted
#     its source into the output, recorded glob marks for it, and then
#     took the text back out - leaving marks pointing at offsets the
#     result would reuse;
#   - an unquoted arithmetic result was not a region, so a minus sign in
#     it was not a live range.
x=1
echo "unquoted-escape=${x:+a\*b}"
echo "quoted-escape=${x:+a\*b}"
echo "escaped-dash=${x:+a\-b}"
echo "escaped-letter=${x:+a\qb}"
u=
echo "default-escape=${u:-a\*b}"
echo "plain-escape=a\*b"
d=/tmp/relf-371.$$
rm -rf $d; mkdir -p $d; cd $d
: > f0; : > f1; : > f9
echo "live-range: $(echo f[0$((-9))])"
echo "quoted-member: $(echo f[0"$((-9))"])"
echo "arith-plain: $((2+3)) $((7/2)) $((-4))"
y=-9
echo "var-range: $(echo f[0$y])"
echo "var-member: $(echo f[0"$y"])"
cd /tmp; rm -rf $d
