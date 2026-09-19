# trap-return-355.sh - `return n` inside a trap. The status it sets
# stands afterwards, where $? is otherwise restored to what it was
# before the trap ran, and the return itself carries on out of the
# enclosing function (Iteration 355). A first attempt cleared the
# pending return as well as keeping the status, which left the function
# spinning in the loop that the return was supposed to end.
f() {
  trap 'echo caught; return 11' USR1
  kill -USR1 $$
  echo "not reached"
}
f; echo "status=$?"
g() {
  trap 'echo plain' USR2
  (exit 42)
  kill -USR2 $$
  echo "after=$?"
}
g
h() {
  trap 'return 7' USR1
  (exit 3)
  kill -USR1 $$
  echo "not reached either"
}
h; echo "second=$?"
trap - USR1 USR2
(exit 5); echo "untouched=$?"
# `return` with no operand inside a trap takes the status the shell had
# when the trap was entered, as `exit` does (Iteration 360).
k() {
  trap 'echo bare; return' USR1
  (exit 42)
  kill -USR1 $$
  echo "not reached"
}
k; echo "bare-return=$?"
trap - USR1
