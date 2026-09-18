# dollar-zero-295.sh - $0 is the script's name (XCU 2.5.1). It expanded
# to nothing at all until Iteration 295: unchanged inside a function and
# inside a subshell, usable with the parameter operators, and counted by
# ${#0}. The paths are stripped so the case does not depend on where it
# is run from.
echo "[${0##*/}]"
f() { echo "f [${0##*/}]"; }
f
( echo "sub [${0##*/}]" )
echo "len-nonzero [$([ ${#0} -gt 0 ] && echo yes)]"
echo "op [${0##*/}] [${0:+set}] [${nope:-${0##*/}}]"
g() { h() { echo "nested [${0##*/}]"; }; h; }
g
for i in 1; do echo "loop [${0##*/}]"; done
case ${0##*/} in *.sh) echo "case matched" ;; *) echo "case no" ;; esac
