# A backslash-newline goes before anything else is read (XCU 2.2.1), so
# it joins a parameter name, `$` to `(` or `{`, and the two parentheses
# of `$((` (Iteration 429; busybox var_unbackslash1, yash quote-p.tst).
# Inside single quotes and a quoted here-document it is text.
ad=Ok; a=Ba
echo $a\
d
echo "$a\
d"
echo ${a\
d}
echo $\
(echo sub)
echo $\
((1+\
2))
echo $(\
(2+2))
ec\
ho word
x=1\
2; echo $x
echo 'q\
q'
echo a\\
echo b
cat <<"E"
$a\
d
E
cat <<E
$a\
d
E
echo ${a\
:-z} ${u\
:-dflt}
