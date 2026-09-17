# ifs-270.sh - field splitting (XCU 2.6.5; Iteration 270): a non-whitespace IFS
# character ends exactly one field, whitespace next to it is part of it, a
# trailing one adds no field; and "$@" keeps empty parameters.
t() { printf '%s' "$#:"; for w in "$@"; do printf '[%s]' "$w"; done; printf '\n'; }
IFS=:
v='a::b:'; t $v
v=':a'; t $v
v=':'; t $v
v='::'; t $v
v='a:'; t $v
v=''; t $v
IFS=' :'
v='a : b'; t $v
v='  :a'; t $v
v='a  b'; t $v
v=' a:: b '; t $v
v='a :: b'; t $v
IFS=' '
v='  a   b  '; t $v
IFS=
v='a b:c'; t $v
unset IFS
v=' a	b
c '; t $v
IFS=,
set -- x y z
v="$*"; t $v
t "a,b" a,b
w=1,,2; t pre$w,post
unset IFS
set -- "" ""; for w in "$@"; do printf "[%s]" "$w"; done; echo
set -- a ""; for w in "$@"; do printf "[%s]" "$w"; done; echo
set -- "" a; printf "<%s>" "$@"; echo
set --; printf "<%s>" x"$@"y; echo
printf "<%s>" "$@"; echo n
