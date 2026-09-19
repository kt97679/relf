# bash-manual-328.sh - behaviour taken from bash's manual where bash and
# dash agree, which is the part this shell should match. Two faults came
# out of it (Iteration 328): `getopts` ignored its own operands, where
# POSIX has `getopts optstring name [arg...]` use them in place of the
# positional parameters, and silent mode (a leading ':') did not name the
# offending option in OPTARG. `${#*}` and `${#@}` printed 0 where they
# count the positional parameters.
#
# This case matches BASH, not dash: on `${#*}` the two disagree - dash
# prints the length of "$*" where bash and XCU 2.6.2 count the
# parameters - and the standard decides it.
set -- a b c
echo "count=${#*} ${#@} ${#}"
set --; echo "empty-count=${#*} ${#@}"
set -- a b c; echo "at=[$(printf '<%s>' "$@")] star=[$(printf '<%s>' "$*")]"
u=; echo "defaults=[${u:-d}][${u-d}][${u:+s}][${u+s}]"
unset v; echo "unset-plus=[${v+set}]"
getopts "ab" o -a 2>/dev/null; echo "operand=$o $OPTIND"
OPTIND=1; getopts "ab:" o -b val 2>/dev/null; echo "operand-arg=$o [$OPTARG] $OPTIND"
OPTIND=1; getopts ":ab:" o -b 2>/dev/null; echo "silent-missing=$o [$OPTARG]"
OPTIND=1; getopts ":ab" o -x 2>/dev/null; echo "silent-unknown=$o [$OPTARG]"
OPTIND=1; getopts "ab" o -x 2>/dev/null; echo "loud-unknown=$o [$OPTARG]"
OPTIND=1; set -- -a -b v rest
while getopts "ab:" o 2>/dev/null; do echo "opt=[$o:$OPTARG]"; done
shift $((OPTIND-1)); echo "after=$*"
cat <<-'EOF2'
	literal $HOME in a stripped heredoc
EOF2
x=5; cat <<EOF2
expanded $x $(echo sub) $((2+3))
EOF2
false | true; echo "pipe-status=$?"
umask 022; echo "umask=$(umask) $(umask -S)"
echo "signame=$(kill -l 9)"
echo "len=${#x} missing=${#nosuch}"
