# tests/bench-vm/realistic.sh - a system-shaped script: option-style
# parsing, parameter trims, `case` matching, arithmetic and `set --`,
# 300 times round, with no external commands. The workload
# tools/profile.py and PERFORMANCE.md's figures are measured on
# (added to the tree at Iteration 384; it had been living in /tmp,
# which made every figure in PERFORMANCE.md unreproducible).
# a system-shaped script: option parsing, expansion, case, arithmetic
n=0; total=0
while [ $n -lt 300 ]; do
  n=$((n+1))
  line="key$n=value$n:extra"
  name=${line%%=*}
  rest=${line#*=}
  val=${rest%%:*}
  case $name in
    key1|key2) kind=low ;;
    key1??|key2??) kind=high ;;
    *) kind=other ;;
  esac
  case $val in
    value*) total=$((total + ${#val})) ;;
  esac
  set -- $rest
  if [ $# -gt 0 ] && [ "$kind" != "" ]; then
    out="$name/$kind/$val"
  fi
done
echo "$total $out"
