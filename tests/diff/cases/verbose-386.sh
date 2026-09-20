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
