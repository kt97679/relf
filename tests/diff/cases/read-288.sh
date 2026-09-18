# read-288.sh - the read builtin (Iteration 288): fields split by IFS
# rather than by blanks, a backslash quoting the next character and
# joining lines unless -r, and status 1 when the line ended at end of
# file. dash and bash agree on every line here.
printf 'a\\ b c\n' | { read x y; echo "B [$x][$y]"; }
printf 'raw\\ x\n' | { read -r p; echo "R [$p]"; }
printf 'no newline' | { read q; echo "E rc=$? [$q]"; }
printf 'x:y:z\n' | { IFS=: read m n; echo "I [$m][$n]"; }
printf 'one  two   three\n' | { read a b; echo "W [$a][$b]"; }
printf 'first\\\nsecond\n' | { read v; echo "C [$v]"; }
printf '  sp  \n' | { read s; echo "T [$s]"; }
printf 'a b\n' | { read only; echo "O [$only]"; }
printf ':x::y:\n' | { IFS=: read f1 f2 f3; echo "N [$f1][$f2][$f3]"; }
printf 'k=v\n' | { IFS== read k v; echo "K [$k][$v]"; }
printf '\n' | { read e; echo "Z rc=$? [$e]"; }
printf 'trail \n' | { read t; echo "S [$t]"; }
