# posix-features.sh - eval, until, for without in, and NAME=value
# assignment words, alone and before a command (Iteration 256); and a
# one-line loop inside a multi-line one, which lost the outer done.
a=1 b=2 c=3
echo "$a$b$c"
X=outer
X=inner sh -c 'echo "child X=$X"'
echo "after X=$X"
Y=tmp env | grep '^Y='
echo "Y=[${Y-unset}]"
f() { echo "f sees Z=$Z"; }
Z=zz f
echo "Z=[${Z-unset}]"
i=0
until [ $i -ge 2 ]; do i=$((i+1)); echo u$i; done
until false; do echo once; break; done
n=0
until [ $n = 3 ]
do
  m=0
  until [ $m = 2 ]; do m=$((m+1)); done
  n=$((n+1))
done
echo "n=$n m=$m"
set -- p q
for w do echo "w=$w"; done
for w
do
  echo "nl=$w"
done
eval 'echo e1'
eval "x=5; y=\$((x+1))"; echo "x=$x y=$y"
cmd='echo multi
echo lines'
eval "$cmd"
eval 'for i in 1 2; do echo ev$i; done'
eval ''; echo "empty st=$?"
eval false; echo "false st=$?"
g() { eval 'return 3'; echo not-here; }
g; echo "g st=$?"
n=0
until [ $n = 3 ]
do
  m=0
  until [ $m = 2 ]; do m=$((m+1)); done
  n=$((n+1))
done
echo "n=$n m=$m"
