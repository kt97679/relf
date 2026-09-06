# Operations whose internal loop count can be zero. This kernel's DO
# with start = limit runs the entire unsigned range, so each of these
# is a hang or a segfault without an explicit guard.
p=/usr/local/bin
echo "trim-all [${p%%/*}] [${p##*}] [${p%%*}]"
echo "trim-part [${p#/usr}] [${p##*/}] [${p%bin}]"
set -- a b
shift 0
echo "shift0 n=$#"
shift 2
echo "shift2 n=$#"
echo "emptysub [$(true)]"
echo "zero [$((0))] [$((5-5))]"
n=""
echo "emptylen [${#n}]"
