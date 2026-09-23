# wait-job-status-345.sh - two behaviours from busybox's suite
# (Iteration 345). `wait %1` names a job, as `kill %1` does; it was
# parsed as a number, came out 0, and waited for nothing. And an
# assignment made only of command substitutions takes the status of the
# FIRST of them, which is what bash and dash both report; this kept the
# last.
#
# The unknown-job status follows BASH (127): dash answers 2. POSIX says
# an error, without fixing the number.
#
# The jobs a job SPEC names sleep a moment first (Iteration 470). A job
# that has already finished is one bash drops from its table in a
# non-interactive shell - `wait %%` then says "no such job", 127 - while
# dash and this shell still hold its status. So bash's own answer raced:
# 5 when it waited before reaping the job, 127 when it reaped first,
# which under load was about one run in ten, and this case was the
# intermittent failure first seen in 429. The finished-job reading is
# asserted in tests/shell instead, where it can be this shell's own.
v=`exit 2` `false`; echo "first-wins=$?"
v=`false` `exit 2`; echo "first-wins-2=$?"
v=`exit 2` `exit 3` `exit 4`; echo "three=$?"
v=`exit 5`; echo "single=$?"
v=`true`; echo "true-sub=$?"
w=plain; echo "no-sub=$?"
( (sleep 0.1; exit 3) & wait %1; echo "job-spec=$?" )
( (exit 4) & wait $!; echo "by-pid=$?" )
( (sleep 0.1; exit 5) & wait %%; echo "current-job=$?" )
( sleep 0.05 | (exit 6) & wait %1; echo "pipeline-job=$?" )
( (sleep 0.1; exit 7) & (exit 8) & wait %1; echo "first-of-two=$?" )
( (exit 7) & wait; echo "wait-all=$?" )
( wait %9 2>/dev/null; echo "no-such-job=$?" )
command -p -V echo
command -v -p echo
