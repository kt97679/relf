# trap-exit-336.sh - entries 13 and 14 of
# tests/from-others/CATALOGUE.md, both fixed in Iteration 336: `exit`
# with no operand inside a trap took the status of the last command the
# trap ran, and an exited background child was never reaped while the
# shell ran builtins, so `kill -0` on it succeeded for ever.
(trap "echo trapped; exit" EXIT; (exit 1)); echo "entry-status=$?"
(trap "exit" EXIT; exit 3); echo "explicit-before=$?"
(trap "echo t; exit 7" EXIT; (exit 1)); echo "explicit-in-trap=$?"
(trap "echo t" EXIT; (exit 4)); echo "no-exit-in-trap=$?"
(trap "true; exit" EXIT; (exit 5)); echo "true-then-exit=$?"
(exit 2); echo "no-trap=$?"
f() { (trap "exit" EXIT; exit 9); }; f; echo "in-function=$?"
sleep 0.1 &
p=$!
n=0
while kill -0 $p 2>/dev/null; do
  n=$((n+1))
  [ $n -gt 2000000 ] && break
done
[ $n -le 2000000 ] && echo "child-reaped"
wait
echo "after-wait=$?"
(exit 6) &
wait $!
echo "background-status=$?"
