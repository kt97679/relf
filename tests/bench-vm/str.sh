s=/usr/local/lib/libfoo.so.1.2
i=0
n=0
while [ $i -lt 400 ]
do
  b=${s##*/}
  d=${s%/*}
  case $b in
    lib*.so*) n=$((n+1)) ;;
    *) ;;
  esac
  i=$((i+1))
done
echo $n $b $d
