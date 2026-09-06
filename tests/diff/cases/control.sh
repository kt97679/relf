# Control flow shapes this shell has had subtle bugs in.
f() if true; then echo braceless; fi
f

# NOTE: the one-line form "g() ( x=1; echo $x )" HANGS this shell -
# found by this harness on its first run, recorded in PROGRESS.md
# Iteration 83. Using the multi-line form here so this file tests what
# it means to; the hang has its own entry rather than being pinned
# down as expected behaviour.
g() (
  x=inner
  echo "sub=$x"
)
x=outer
g
echo "after=[$x]"

h() {
  while :
  do
    echo loop
    return 3
  done
  echo never
}
h
echo "st=$?"

case abc in
  x) echo no ;;
  ab*) echo sameline ;;
esac

printf 'p\nq\n' | while read v
do
  echo "piped=[$v]"
done
echo tail

# A while condition is stored as raw text and re-tokenized every
# iteration; until Iteration 110 that re-tokenize skipped operator
# normalization entirely, so a fused operator in the condition was
# never spaced out.
i=0
while test "$i" != xxx;do
  i="x$i"
done
echo "fused-do: $i"

j=0
while test "$j" != xx; do
  j="x$j"
done
echo "spaced-do: $j"

# an operator fused inside the condition itself
k=0
while [ "$k" != xx ];do k="x$k"; done
echo "fused-both: $k"
