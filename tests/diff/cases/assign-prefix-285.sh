# assign-prefix-285.sh - every assignment in a command's prefix keeps its
# value whole, not just the first (Iteration 285): field splitting and
# pathname expansion do not apply to an assignment's value, but do apply
# to an ordinary word that merely contains '='.
v="a b"
star='*'
show() { printf '[%s]' "$@"; printf '\n'; }
x=1 y=$v sh -c 'echo "[$x][$y]"'
x=1 y=$v z=$v sh -c 'echo "[$y][$z]"'
a=$v b=$star c=q sh -c 'echo "[$a][$b][$c]"'
y=$v sh -c 'echo "[$y]"'
echo a=$v b
show a=$v
x=1 echo $v
IFS=:
w='p:q'
m=$w n=$w sh -c 'echo "[$m][$n]"'
echo $w
unset IFS
x= y=$v sh -c 'echo "[$x][$y]"'
x=1 y= sh -c 'echo "[$y]"'
d=$(echo "s t") e=$(echo u) sh -c 'echo "[$d][$e]"'
f=~ g=~/p sh -c 'echo "[$f][$g]"' | sed "s|$HOME|H|g"
