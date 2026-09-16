# positional.sh - positional parameters past nine (Iteration 250). Until
# then there were nine slots: `set -- 1 ... 12` gave $# = 9, and "$@"
# and function arguments were cut without a word.
set -- 1 2 3 4 5 6 7 8 9 10 11 12
echo "$# $1 $9 ${10} ${12} $10"
shift 3
echo "$# $1 ${9}"
f() { echo "f: $# $1 ${11}"; g "$@" x; echo "f again: $# $1"; }
g() { echo "g: $# ${13}"; }
f a b c d e f g h i j k l m
echo "top: $# $1"
set -- "$@" tail
echo "$# ${10}"
for a in "$@"; do n=$a; done; echo "last=$n"
set --
echo "empty: $#"
h() { set -- one two; echo "h: $#"; }
h p q r
set -- -a -bc -d val x y z w v u t s r q p o n
while getopts "abcd:" o; do echo "o=$o OPTARG=$OPTARG"; done
shift $((OPTIND - 1)); echo "rest: $# $1 ${12}"
OPTIND=1
