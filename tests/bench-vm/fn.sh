f() {
  r=$(( $1 * 2 + 1 ))
}
i=0
while [ $i -lt 600 ]
do
  f $i
  i=$((i+1))
done
echo $r
