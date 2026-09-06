# A word is expanded when its command runs, not when its line is read.
# Everything here depends on an assignment earlier on the SAME line
# being visible to a later command on it - the stale-expansion
# limitation recorded since Iteration 18, fixed in 114.
FOO=bar; echo "[$FOO]"
A=1; B=2; echo "$A$B"
X=one; X=two; echo "$X"
unset c
echo ${c=GOOD} $c; echo ${c=BAD} $c; c=""; echo ${c=BAD} $c; unset c
n=0; n=$((n+1)); echo "n=$n"
p=/tmp; echo "${p}/f"
v=set; v=""; echo "[${v:-empty}]"

# and through the other separators
q=1 && echo "and:$q"
r=1; r=2 && echo "chain:$r"
t="a b c"; set -- $t; echo "split:$#"

# a compound command reads its words when it runs, too
w=one
for i in $w $w
do
  printf '%s' "$i"
done
echo
z=x
case $z in
  x) echo "case:$z" ;;
esac
