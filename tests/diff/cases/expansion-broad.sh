a=hello
n=""
sp='x y'
echo "1 [$a] [${a}] [${a:-D}] [${a-D}] [${nope:-D}] [${nope-D}]"
echo "2 [${a:+P}] [${nope:+P}] [${n:+P}] [${n+P}]"
echo "3 [${#a}] [${#n}]"
p=/usr/local/bin
echo "4 [${p#/usr}] [${p##*/}] [${p%bin}] [${p%%/*}]"
echo "5 [$sp] [\"$sp\"]"
for w in $sp
do
  echo "6 word=[$w]"
done
echo "7 [$((3*4))] [$(echo sub)] [`echo bq`]"
set -- one two three
echo "8 [$#] [$1] [$3]"
# NOTE: "$*" / "$@" / '"$@"' as multiple fields are not implemented -
# a known gap, one of the several word.sh still needs. Left out rather
# than asserted, so this file stays a regression net for what does
# work.
echo "12 [\$a] ['\$a'] [\"\$a\"]"
c=1
echo "13 [${c:=Z}] [$c]"
echo "14 [${a}x] [x${a}] [x${a}x]"

# A line whose NORMALIZED form is longer than LINE-MAX. Until
# Iteration 111 the normalized text was copied back over LINE-BUF, and
# when it did not fit the ORIGINAL line was tokenized instead -
# silently, with every operator left fused to its neighbours. TOKENIZE
# now reads NORM-BUF where it already is.
echo a0>/dev/null;echo b0 a1>/dev/null;echo b1 a2>/dev/null;echo b2 a3>/dev/null;echo b3 a4>/dev/null;echo b4 a5>/dev/null;echo b5
echo tail
