#!/bin/sh
# tools/busybox-suite.sh - run busybox's ash test suite against this shell
# and against dash, and report the tests dash passes that we do not.
#
# The suite is not vendored here: it is busybox's, under its own licence.
# Fetch it first, e.g.
#   curl -sL -o bb.tgz https://codeload.github.com/mirror/busybox/tar.gz/refs/heads/master
#   tar xzf bb.tgz --strip-components=1 busybox-master/shell/ash_test
# then point this script at the resulting ash_test directory.
#
# Usage: tools/busybox-suite.sh /path/to/ash_test [shell]
set -e
DIR=${1:?usage: busybox-suite.sh /path/to/ash_test [shell]}
SH=${2:-$(pwd)/relfsh}
run() {  # run every test under $1, print "passed failed", list failures on fd 3
    p=0; f=0
    for t in "$DIR"/*/*.tests; do
        d=$(dirname "$t"); b=$(basename "$t" .tests)
        [ -f "$d/$b.right" ] || continue
        out=$( (cd "$d" && timeout 10 $1 "$b.tests" 2>&1) || true )
        if [ "$out" = "$(cat "$d/$b.right")" ]; then p=$((p+1))
        else f=$((f+1)); echo "$(basename "$d")/$b" >&3; fi
    done
    echo "$p $f"
}
ours=$(run "$SH" 3> /tmp/bb-ours.txt)
theirs=$(run dash 3> /tmp/bb-dash.txt)
echo "this shell: $ours (passed failed)"
echo "dash:       $theirs (passed failed)"
echo "--- tests dash passes and this shell does not:"
sort /tmp/bb-dash.txt > /tmp/bb-dash-s.txt
sort /tmp/bb-ours.txt | comm -13 /tmp/bb-dash-s.txt -
