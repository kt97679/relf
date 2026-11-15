# tests/bench-cmd/subst.sh - command substitution of external tools, 200 rounds (954)
i=0; n=0
while [ $i -lt 200 ]; do
  b=$(basename /usr/lib/file$i.txt .txt)
  d=$(dirname /usr/lib/x/file$i)
  n=$((n + ${#b} + ${#d}))
  i=$((i+1))
done
echo $n
