# loop-control-329.sh - `break n`, `continue n` and the exit status of
# `case`. Found by running busybox's ash test suite (Iteration 329): the
# operand of break and continue was ignored entirely, so `break 2` left
# one loop, and `case` reset $? on entry, so `$?` inside a case body
# reported 0 rather than the status before it.
i=0
while [ $i -lt 3 ]; do
  i=$((i+1))
  while true; do break 2; done
  echo "not reached"
done
echo "break2-while=$i"
i=0
while [ $i -lt 3 ]; do
  i=$((i+1))
  for b in x y; do continue 2; done
  echo "not reached"
done
echo "continue2-while=$i"
for a in 1 2 3; do
  for b in 1 2; do break 2; done
  echo "not reached"
done
echo "break2-for=ok"
i=0
for a in 1 2 3; do
  i=$((i+1))
  for b in 1 2; do continue 2; done
  echo "not reached"
done
echo "continue2-for=$i"
while true; do break; done; echo "plain-break=$?"
i=0; while [ $i -lt 2 ]; do i=$((i+1)); continue; done; echo "plain-continue=$i"
i=0
while [ $i -lt 2 ]; do
  i=$((i+1))
  while true; do
    while true; do break 3; done
  done
done
echo "break3=$i"
false || case a in a) echo "status-in-body=$?";; esac
false; case x in y) ;; esac; echo "no-match=$?"
false; case x in x) true;; esac; echo "matched=$?"
false; case x in x) ;; esac; echo "empty-body=$?"
true; case x in x) false;; esac; echo "body-status=$?"
