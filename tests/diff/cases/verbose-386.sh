# verbose-386.sh - `set -v` writes each line of input to standard error
# as the shell reads it (XCU `set`). The option was accepted, reported
# in `$-`, and did nothing at all until Iteration 386.
#
# `$-` itself is not checked here: bash puts its own options in it
# (`hB`), so the flags go to tests/shell/run-options instead.
echo before
set -v
echo one
echo two
set +v
echo three
# PS4 is a prompt too, and was ignored entirely: the trace prefix was
# always "+ " (Iteration 391).
PS4='[trace]'
set -x
echo traced
set +x
PS4="[$(echo T)]"
set -x
echo expanded
set +x
PS4=
set -x
echo empty-prefix
set +x
echo done
