# The two places a hand-written expectation was wrong before:
# "set -- --" (Iteration 61) and field splitting of an unquoted
# multi-line command substitution (Iteration 67).
set -- -x
echo "1=[$1]"
set -- -- -x
echo "1=[$1] 2=[$2]"

p='a b'
q=$p
echo "assign=[$q]"
# A fully one-line "for ...; do ...; done" is not supported (nor the
# while equivalent): DO-FOR reads its body from following lines.
for w in $p
do
  echo "word=[$w]"
done

r=$(printf 'l1\nl2\n')
echo "quoted=[$r]"
echo unquoted=$(printf 'l1\nl2\n')

echo "arith=$((2<<5)) $((3&1|4)) $((2^3^1))"
n=0
echo "assign-in-arith=$((n=7)) then $n"
