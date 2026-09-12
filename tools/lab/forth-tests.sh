#!/bin/bash
# forth-tests.sh BUILD - run the ANS CORE suite (tester.fr + tests/*.fth,
# 671 cases) on the CV8 images, at both cell widths.
#
# WHY THIS EXISTS: the shell suites (tests/shell, tests/diff) exercise
# the shell, and every CV8 image passed them long before the Forth
# COMPILER was correct. This suite is the one that compiles hundreds of
# definitions at RUN time, so it is what actually tests cv8.4. It was
# not being run for several iterations - see PROGRESS.md 204.
#
# Needs a CV8 image that boots into the INTERPRETER, not the shell: a
# shell image sends this input to the shell, which reports nothing
# useful. build-cv8.sh builds fkernel-64/-32 for exactly this.
set -e
cd "$(dirname "$0")/../.."
B=${1:?usage: forth-tests.sh BUILDDIR}
fail=0
run() {   # run ENGINE IMAGE LABEL
    local out st
    out=$( { cat tester.fr tests/*.fth; echo BYE; } | timeout 120 "$1" "$2" 2>&1 ) || true
    st=$?
    if echo "$out" | grep -qiE "incorrect result|wrong number of results|undefined word|segmentation"; then
        echo "FAIL $3"; echo "$out" | grep -iE "incorrect|wrong number|undefined" | head -5
        fail=1
    else
        echo "ok   $3 (671 cases)"
    fi
}
run "$B/spec-64" "$B/fkernel-64.img" "CORE suite, CV8 64-bit"
run "$B/spec-32" "$B/fkernel-32.img" "CORE suite, CV8 32-bit"
exit $fail
