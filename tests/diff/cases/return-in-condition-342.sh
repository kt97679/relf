# return-in-condition-342.sh - `return` in a loop's CONDITION leaves its
# own status. The loop kept a saved status from before it started and
# restored that over the return's, so `while return 2; do :; done`
# reported 0 (Iteration 342).
f1() { while return 2; do :; done; }
f1; echo "condition=$?"
f2() { while :; do return 2; done; }
f2; echo "body=$?"
f3() { until return 3; do :; done; }
f3; echo "until-condition=$?"
f4() { for i in 1 2; do return 4; done; }
f4; echo "for-body=$?"
f5() { while true; do break; done; return 5; }
f5; echo "after-loop=$?"
f6() { while false; do :; done; }
f6; echo "loop-false=$?"
i=0; while [ $i -lt 2 ]; do i=$((i+1)); done; echo "normal=$? i=$i"
f7() { while [ $i -gt 0 ]; do i=$((i-1)); done; return 7; }
f7; echo "counted=$?"
f8() { echo body; return 0; }
while f8 && false; do :; done; echo "condition-list=$?"
