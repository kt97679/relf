a=1; b=0; i=0
while [ $i -lt 700 ]
do
  t=$(( (a + b) % 1000003 )); a=$b; b=$t
  i=$((i+1))
done
echo $b
