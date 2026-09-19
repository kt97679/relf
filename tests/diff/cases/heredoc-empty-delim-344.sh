# heredoc-empty-delim-344.sh - catalogue entry 21. A here-document
# delimiter that expands to nothing still delimits: the body ends at a
# line matching the delimiter as written. This shell dropped the empty
# word - the operator and its target travel as words - which shifted
# every redirection after it, so the here-document got the wrong file
# descriptor and anything reading it hung (Iteration 344).
a=
cat <<- $a
	one
$a
echo "after-empty=$?"
unset b
cat <<- $b
	two
$b
echo "after-unset=$?"
c=X
cat <<- $c
	three
$c
echo "after-set=$?"
cat <<- ""
	four

echo "after-quoted-empty=$?"
d=
cat <<- $d > /tmp/relf-344-fixed
	five
$d
cat /tmp/relf-344-fixed
rm -f /tmp/relf-344-fixed
e=
read line <<- $e
	six
$e
echo "read=[$line]"
f=
cat <<- $f | tr a-z A-Z
	seven
$f
