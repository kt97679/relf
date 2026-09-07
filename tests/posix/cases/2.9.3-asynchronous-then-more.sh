# POSIX.1-2017 XCU 2.9.3 Asynchronous Lists.
#
# '&' is a list terminator, not a line terminator. A command may
# follow it on the same line and is a separate command, exactly as if
# ';' had been used - the difference is only that the preceding
# command is not waited for.
#
# The asynchronous command deliberately produces no output, so the
# result does not depend on how the two interleave. Two earlier
# versions of this case were wrong in instructive ways: "sleep 0 &
# wait" put the whole difference on stderr, which this harness ignores
# - a hollow pass of exactly the ulimit.sh shape (Iteration 122) - and
# "echo one & echo two" made the reference shells disagree with each
# other on ordering, which is a race, not a conformance question.
true & echo after
wait
echo done
