# signal-status-299.sh - a child killed by a signal exits 128+n (XCU
# 2.8.2). Only the normal-exit byte was decoded until Iteration 299, so
# `kill $p; wait $p` reported 0 where both references report 143.
sleep 5 & p=$!
kill $p 2>/dev/null
wait $p 2>/dev/null
echo "TERM: $?"
sleep 5 & q=$!
kill -9 $q 2>/dev/null
wait $q 2>/dev/null
echo "KILL: $?"
sh -c 'kill -9 $$' 2>/dev/null; echo "foreground KILL: $?"
sh -c 'kill -TERM $$' 2>/dev/null; echo "foreground TERM: $?"
sh -c 'exit 5'; echo "normal: $?"
sh -c 'exit 0'; echo "zero: $?"
(exit 42) & wait $!; echo "background exit: $?"
x=$(sh -c 'kill -9 $$' 2>/dev/null); echo "in substitution: $?"
if sh -c 'kill -TERM $$' 2>/dev/null; then echo cond-yes; else echo "cond-no: $?"; fi
sh -c 'kill -9 $$' 2>/dev/null | cat; echo "pipeline: $?"
