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
        st=0
        # ash-z_slow is slow by design - many_ifs runs 6856 cases and
        # takes dash 7.5 s here - so it gets a minute rather than ten
        # seconds, or a correct run is reported as a hang (Iteration 423).
        lim=10; case $d in *z_slow*) lim=60 ;; esac
        # THIS_SH is what busybox's own harness gives a test to invoke
        # the shell under test with; 44 of these tests use it, and
        # without it they failed here for both shells, which is a fault
        # of this runner and not of either shell (Iteration 457).
        out=$( (cd "$d" && THIS_SH="$1" timeout $lim $1 "$b.tests" 2>&1) ) || st=$?
        if [ "$out" = "$(cat "$d/$b.right")" ]; then p=$((p+1))
        else
            f=$((f+1))
            # Severity first (Iteration 421): a pass count weighs a crash
            # the same as a reworded message, so each failure says which.
            sev=wrong
            [ "$st" = 124 ] && sev=HANG
            case $out in *"segmentation fault"*|*"stack guard"*|*"stack overflow"*|*"stack underflow"*|*Aborted*|*"core dumped"*) sev=CRASH ;; esac
            echo "$(basename "$d")/$b $sev" >&3
        fi
    done
    echo "$p $f"
}
ours=$(run "$SH" 3> /tmp/bb-ours.txt)
theirs=$(run dash 3> /tmp/bb-dash.txt)
echo "this shell: $ours (passed failed)"
echo "dash:       $theirs (passed failed)"
echo "--- tests dash passes and this shell does not:"
cut -d' ' -f1 /tmp/bb-dash.txt | sort > /tmp/bb-dash-s.txt
sort /tmp/bb-ours.txt | join -v1 - /tmp/bb-dash-s.txt 2>/dev/null || sort /tmp/bb-ours.txt
echo "--- by severity (all of this shell's failures):"
for sev in CRASH HANG wrong; do
    printf '%-6s %s\n' "$sev" "$(grep -c " $sev\$" /tmp/bb-ours.txt)"
done
grep -E ' (CRASH|HANG)$' /tmp/bb-ours.txt | sed 's/^/  /' || true
