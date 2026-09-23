# A line continuation may stand inside an IO number or between it and
# its operator: `3\`+newline+`>f` redirects descriptor 3 (Iteration 456,
# yash quote-p.tst:225). The digit was left as an argument.
d=${TMPDIR:-/tmp}/ionum456.$$
mkdir -p "$d" && cd "$d" || exit 1
echo b 3\
>f2
cat f2; echo "[$?]"
exec 3\
>f3
echo via3 >&3
cat f3
exec 3>&-
cd / && rm -rf "$d"
