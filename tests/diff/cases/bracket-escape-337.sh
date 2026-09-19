# bracket-escape-337.sh - a backslash inside a bracket expression hides
# the character that follows, so `[\q]` matches q (XCU 2.13.1). The
# scan for the closing bracket and the member test both ignored the
# backslash until Iteration 337, so such a pattern matched nothing.
d=/tmp/relf-337.$$
rm -rf $d; mkdir -p $d; cd $d
: > q; : > a; : > b; : > 'z'
echo [\q]
echo [\a\b]
echo [ab]
echo [a-b]
echo [\q]*
# `case` patterns are left out: a backslash inside a bracket does not
# reach the matcher there, because case patterns are matched with
# escapes turned off. That is catalogued as entry 16 and still open.
cd /tmp; rm -rf $d
