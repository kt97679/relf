# pathname.sh - pathname expansion (XCU 2.6.6; Iteration 267): patterns
# in one directory and across components, dot files, quoting, patterns
# produced by an unquoted expansion, brackets, no match, trailing /, and
# the places where no expansion happens (case, assignments, redirections).
d=$(mktemp -d) || exit 1
cd "$d" || exit 1
mkdir -p d1/sub d2
touch a.txt b.txt c.log .hidden 'we ird.txt' d1/x.c d1/y.c d2/x.c d1/sub/z.c
echo *.txt
echo *
echo .*
echo d*/x.c
echo */*.c
echo d1/*/*.c
echo *.none
echo "*.txt" '*'.txt \*.txt
x='*.log'; echo $x "$x"
for f in d?; do echo "dir $f"; done
echo [ab].txt [!a].txt
echo "$d"/d1/* | sed "s|$d|D|g"
echo d1/
echo */
for w in *.txt; do printf '[%s]\n' "$w"; done
case a.txt in *.txt) echo case-ok;; esac
y=*.txt; echo "$y"
echo a*.txt > out.txt; cat out.txt; rm out.txt
set -- *.log; echo "$# $1"
cd / && rm -rf "$d"
