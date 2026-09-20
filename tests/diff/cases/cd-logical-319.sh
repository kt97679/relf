# cd-logical-319.sh - `cd` keeps the LOGICAL path (XCU cd), `-P` asks for
# the resolved one, and CDPATH is searched for a relative operand. Until
# Iteration 319 `cd` was chdir plus getcwd, so `cd /tmp/link` left PWD at
# the resolved path and CDPATH was ignored entirely.
d=/tmp/relf-319-fixed
rm -rf $d
mkdir -p $d/real $d/other
ln -sf real $d/link
cd $d/link; echo "pwd=$(pwd)"; echo "PWD=$PWD"
cd ..; echo "after-dotdot=$(pwd)"
cd $d/link; echo "physical=$(pwd -P)"; echo "logical=$(pwd -L)"
cd -P $d/link; echo "cd -P=$(pwd)"
cd $d; cd ./real; echo "dot-slash=$(pwd)"
cd $d/./real/.; echo "dots=$(pwd)"
cd $d/link/..; echo "through-link=$(pwd)"
CDPATH=$d; cd other; echo "cdpath=$(pwd)"
CDPATH=/nonexistent:$d; cd real; echo "cdpath-second=$(pwd)"
unset CDPATH
cd $d; cd real; echo "no-cdpath=$(pwd)"
cd /; echo "root=$(pwd)"
cd /tmp; rm -rf $d
# CDPATH's two rules that were wrong until Iteration 381: it is not
# searched when the operand begins with `./` or `../`, and an operand
# found through an EMPTY entry - which means the current directory - is
# not announced. A fixed name, like the one above: the output is
# compared between two shells, so it cannot carry a pid.
c=/tmp/relf-381-fixed
rm -rf $c; mkdir -p $c/dev $c/p1/x $c/p2/dev
cd $c
CDPATH=$c/p1::$c/p2; cd dev; pwd
cd $c
CDPATH=$c/p2; cd ./dev; pwd
cd $c
CDPATH=$c/p2; cd ../relf-381-fixed/dev; pwd
cd $c
CDPATH=$c/p2; cd dev; pwd
cd $c
CDPATH=$c/p1; cd x; pwd
cd $c
CDPATH=:$c/p2; cd dev; pwd
cd /tmp; rm -rf $c
