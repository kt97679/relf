#!/bin/sh
# tools/self-harness.sh [SHELL] - the shell runs its own test harness.
# Every tests/shell/run-* file is interpreted BY the shell under test, not
# by /bin/sh - lib.sh, the assertions, the quoting, the temporary files:
# thousands of lines of real shell nobody wrote as a test - and tests the
# shell through THIS_SH as always. Every file must pass as under dash.
# TESTING-IDEAS.md 8; Iteration 558: 84 files, 940 assertions, 0 failed,
# on both engines.
S=$(cd "$(dirname "${1:-relfsh}")" && pwd)/$(basename "${1:-relfsh}")
cd "$(dirname "$0")/../tests/shell" || exit 1
files=0 asserts=0 bad=0
for t in run-*; do
    [ "$t" = run-all ] && continue
    out=$(THIS_SH=$S RELFSH=$S timeout 300 "$S" "./$t" < /dev/null 2>&1); st=$?
    last=$(printf '%s\n' "$out" | tail -1)
    files=$((files + 1))
    case $last in
        *" assertions, 0 failed"*) n=${last%% *}; asserts=$((asserts + n)) ;;
        *) bad=$((bad + 1)); echo "not passing: $t (status $st): $last" ;;
    esac
    [ "$st" = 0 ] || case $last in *" 0 failed"*) bad=$((bad + 1)); echo "status $st: $t" ;; esac
done
echo "$files files, $asserts assertions, $bad not passing - $S interpreting its own harness"
[ "$bad" = 0 ]
