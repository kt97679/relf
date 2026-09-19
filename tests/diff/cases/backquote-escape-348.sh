# backquote-escape-348.sh - a backslash inside a backquote substitution.
# POSIX removes it only before a backquote, a backslash or a dollar;
# every other backslash stays. This shell CRASHED on any of the others
# (Iteration 348): the copier re-fetched a character outside the test
# that decides whether to skip one, so each such backslash left an extra
# value on the stack.
x=`echo a\3b`; echo "unquoted=[$x]"
x=`echo "a\\"b"`; echo "escaped-quote=[$x]"
x=`echo "a\$b"`; echo "escaped-dollar=[$x]"
x=`printf "a\tb"`; echo "tab=[$x]"
x=`echo plain`; echo "plain=[$x]"
x=`echo "a\\\\b"`; echo "escaped-backslash=[$x]"
y=set
x=`echo "$y"`; echo "expanded=[$x]"
x=`echo \`echo nested\``; echo "nested=[$x]"
x=`printf 'a\nb'`; echo "newline=[$x]"
f() { echo "in-function"; }
x=`f`; echo "function=[$x]"
x=`echo one; echo two`; echo "two-commands=[$x]"
