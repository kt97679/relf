#!/bin/sh
# tests/mrsh-suite/run.sh - runs mrsh's own (vendored, unmodified) test
# files against relfsh, adapted from mrsh's own two harnesses (see
# vendor/README.md for exactly what was and wasn't copied):
#
#   - vendor/*.sh (mrsh's top-level test/*.sh): differential testing,
#     matching mrsh's own harness.sh - run the same script through
#     relfsh and through the reference shell ($REF_SH, default sh),
#     PASS only if
#     stdout and exit status both match. stderr is intentionally
#     ignored, matching mrsh's own harness.
#   - vendor/conformance/*.sh (mrsh's test/conformance/*.sh): three
#     categories, matching mrsh's own meson.build classification -
#     a fixed-output test (compared against its own vendored .stdout
#     file, expects exit status 0), an expected-failure test (PASS
#     means relfsh's own exit status is nonzero *and not a crash* -
#     i.e. it correctly rejects invalid syntax rather than segfaulting
#     on it; see is_crash_status below and PROGRESS.md's Iteration 15
#     entry for why that distinction matters), and undefined-behavior
#     tests (not scored - POSIX doesn't specify a required result for
#     these).
#
# relfsh gained real file-argument invocation in Iteration 16 (phase
# A's last item), so each vendored test is fed to it the same way
# the reference is: `relfsh testcase` / `$REF_SH testcase`, no more
# asymmetry.
#
# This script deliberately reports failures rather than hiding them -
# the whole point of adopting mrsh's suite is an honest, trackable
# gap against a more complete shell (see PROGRESS.md's Iteration 14
# entry for the baseline this produced and GOALS.md goal 8 for the
# plan to close it).

cd "$(dirname "$0")" || exit 1
VENDOR_DIR="./vendor"
RELFSH="${RELFSH:-../../relfsh}"
# Reference shell for the differential half. Upstream's own
# meson_options.txt defaults 'reference-shell' to 'sh', and this
# harness followed bash instead until Iteration 124 - which cost a
# genuine pass and bought a hollow one, because bash deviates from
# POSIX on alias expansion in non-interactive shells (GOALS.md, "Where
# bash and POSIX disagree") and reports ulimit in 1024-byte blocks
# where POSIX says 512. Override to compare against another shell:
#   REF_SH=bash tests/mrsh-suite/run.sh
REF_SH="${REF_SH:-sh}"
TIMEOUT_SECS=10

PASS=0
FAIL=0
SKIP=0
FAILED_NAMES=""

run_relfsh() {
    # $1 = script path; prints stdout, returns relfsh's exit status
    timeout "$TIMEOUT_SECS" "$RELFSH" "$1" < /dev/null 2>/dev/null
}

run_ref() {
    # $1 = script path; prints stdout, returns the reference shell's status
    timeout "$TIMEOUT_SECS" "$REF_SH" "$1" < /dev/null 2>/dev/null
}

record_pass() { PASS=$((PASS + 1)); }
record_fail() {
    FAIL=$((FAIL + 1))
    FAILED_NAMES="$FAILED_NAMES $1"
}
record_skip() { SKIP=$((SKIP + 1)); }

# A status in 128+signum (POSIX shell convention for "killed by a
# signal", which is what `timeout` and a crashing process both
# produce) means relfsh crashed rather than cleanly rejecting the
# input - these must never be scored as "correctly rejects invalid
# input" for the *.fail.sh category below, even though a crash's exit
# status is technically nonzero too. Found the hard way: an earlier
# run of this harness (see PROGRESS.md's crash-hardening entry) scored
# 2.2.3-alias-expansion.fail.sh as a pass because relfsh's segfault
# (status 139) happened to satisfy a cruder "nonzero means pass" check
# - it wasn't rejecting the input at all, it was crashing on it.
is_crash_status() {
    [ "$1" -ge 128 ] 2>/dev/null
}

echo "=== Differential tests (relfsh vs $REF_SH) ==="
for f in "$VENDOR_DIR"/*.sh; do
    name=$(basename "$f")
    relfsh_out=$(run_relfsh "$f")
    relfsh_ret=$?
    ref_out=$(run_ref "$f")
    ref_ret=$?
    if [ "$relfsh_ret" = "$ref_ret" ] && [ "$relfsh_out" = "$ref_out" ]; then
        echo "PASS: $name"
        record_pass
    elif is_crash_status "$relfsh_ret"; then
        echo "FAIL: $name (relfsh CRASHED, status=$relfsh_ret; ref status=$ref_ret)"
        record_fail "$name"
    else
        echo "FAIL: $name (relfsh status=$relfsh_ret ref status=$ref_ret)"
        record_fail "$name"
    fi
done

echo ""
echo "=== Conformance: fixed-output test ==="
for f in "$VENDOR_DIR"/conformance/*.sh; do
    case "$f" in
        *.fail.sh|*.undefined.sh) continue ;;
    esac
    name=$(basename "$f")
    stdout_file="${f%.sh}.stdout"
    relfsh_out=$(run_relfsh "$f")
    relfsh_ret=$?
    if [ -f "$stdout_file" ]; then
        expected=$(cat "$stdout_file")
        if [ "$relfsh_ret" = 0 ] && [ "$relfsh_out" = "$expected" ]; then
            echo "PASS: $name"
            record_pass
        else
            echo "FAIL: $name (status=$relfsh_ret)"
            record_fail "$name"
        fi
    fi
done

echo ""
echo "=== Conformance: expected-failure tests (PASS means relfsh rejects the input cleanly, not by crashing) ==="
for f in "$VENDOR_DIR"/conformance/*.fail.sh; do
    [ -e "$f" ] || continue
    name=$(basename "$f")
    run_relfsh "$f" > /dev/null
    relfsh_ret=$?
    if is_crash_status "$relfsh_ret"; then
        echo "FAIL: $name (relfsh crashed, status=$relfsh_ret - a crash is not a rejection)"
        record_fail "$name"
    elif [ "$relfsh_ret" != 0 ]; then
        echo "PASS: $name"
        record_pass
    else
        echo "FAIL: $name (relfsh accepted invalid input with status 0)"
        record_fail "$name"
    fi
done

echo ""
echo "=== Conformance: undefined-behavior tests (not scored) ==="
for f in "$VENDOR_DIR"/conformance/*.undefined.sh; do
    [ -e "$f" ] || continue
    echo "SKIP (undefined behavior, not scored): $(basename "$f")"
    record_skip
done

echo ""
echo "=== Summary ==="
echo "$PASS passed, $FAIL failed, $SKIP skipped (not scored)"
if [ -n "$FAILED_NAMES" ]; then
    echo "Failed:$FAILED_NAMES"
fi

[ "$FAIL" -eq 0 ]
