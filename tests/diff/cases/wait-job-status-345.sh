# wait-job-status-345.sh - two behaviours from busybox's suite
# (Iteration 345). `wait %1` names a job, as `kill %1` does; it was
# parsed as a number, came out 0, and waited for nothing. And an
# assignment made only of command substitutions takes the status of the
# FIRST of them, which is what bash and dash both report; this kept the
# last.
#
# The unknown-job status follows BASH (127): dash answers 2. POSIX says
# an error, without fixing the number.
v=`exit 2` `false`; echo "first-wins=$?"
v=`false` `exit 2`; echo "first-wins-2=$?"
v=`exit 2` `exit 3` `exit 4`; echo "three=$?"
v=`exit 5`; echo "single=$?"
v=`true`; echo "true-sub=$?"
w=plain; echo "no-sub=$?"
( (exit 3) & wait %1; echo "job-spec=$?" )
( (exit 4) & wait $!; echo "by-pid=$?" )
( (exit 5) & wait %%; echo "current-job=$?" )
( sleep 0.05 | (exit 6) & wait %1; echo "pipeline-job=$?" )
( (exit 7) & (exit 8) & wait %1; echo "first-of-two=$?" )
( (exit 7) & wait; echo "wait-all=$?" )
( wait %9 2>/dev/null; echo "no-such-job=$?" )
