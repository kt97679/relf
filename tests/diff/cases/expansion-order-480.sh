# XCU 2.9.1: a simple command's words are expanded before its
# assignments (Iteration 480, stage 1 of EXPANSION-ORDER.md).
d=${TMPDIR:-/tmp}/relf-480.$$
mkdir -p "$d" && cd "$d" || exit 1
unset a
a=$(echo A 3>|f1) 3>|f1 echo "$(test -f f1 || echo file does not exist $a)"
rm -f f1
# which substitution ran LAST decides an assignment-only command's status
v=`exit 2` `false`; echo "1 $?"
v=`false` `exit 2`; echo "2 $?"
v=`exit 2` `exit 3` `exit 4`; echo "3 $?"
a=$(exit 3) b=$(exit 4); echo "4 $?"
# what a word sees was right before, and stays so
a=old; a=new echo "5 $a"
a=old; a=new b=$a sh -c 'echo "6 $b"'
unset a; a=1 echo "7 ${a-unset}"
# assignments see each other even with a redirection between them
a=x >/dev/null b=$a sh -c 'echo "9 [$b]"'
cd / && rm -rf "$d"
