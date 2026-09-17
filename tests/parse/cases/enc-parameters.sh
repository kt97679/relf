echo $x ${y} ${#n} $1 $@ $* $# $? $$ $! $-
echo ${z:-def} ${z-d} ${z:=as} ${z=a} ${z:?msg} ${z?m} ${z:+alt} ${z+a}
echo ${p#a*} ${p##a*} ${p%z} ${p%%z} "${v}post" "pre${v:-x}"
