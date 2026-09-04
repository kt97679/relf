# tests/shell/lib.sh - shared assertion helpers, sourced by each run-*
# test file in this directory.
#
# Structural pattern here - individual "run-<feature>" test files
# under a master driver ("run-all"), parameterized by a THIS_SH
# environment variable so any shell binary can be pointed at - is
# borrowed deliberately from bash's own tests/ directory (see
# PROGRESS.md for how that suite works and why its actual test
# *content* isn't usable against shell.4 yet: it assumes quoting,
# parameter expansion, control structures, and other features shell.4
# doesn't have). The content of these tests is written fresh, scoped
# to what shell.4 actually implements as of this writing, and is
# meant to grow feature-by-feature alongside shell.4 itself rather
# than testing ahead of it.
#
# Unlike bash's own tests/ (which diffs raw output against a fixed
# .right file), these use substring/status assertions instead of
# full-output diffing - RelF's own boot banner and CRLF line endings
# would make literal whole-output comparison fragile for little
# benefit here.

: "${THIS_SH:=../../relfsh}"

TESTS_RUN=0
TESTS_FAILED=0

assert_output_contains() {
    # $1 = description, $2 = expected substring, $3 = actual output
    TESTS_RUN=$((TESTS_RUN + 1))
    case "$3" in
        *"$2"*) ;;
        *)
            TESTS_FAILED=$((TESTS_FAILED + 1))
            echo "FAIL: $1"
            echo "  expected to contain: $2"
            echo "  actual output:"
            echo "$3" | sed 's/^/    /'
            return 1
            ;;
    esac
}

assert_status() {
    # $1 = description, $2 = expected status, $3 = actual status
    TESTS_RUN=$((TESTS_RUN + 1))
    if [ "$2" != "$3" ]; then
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "FAIL: $1"
        echo "  expected status: $2"
        echo "  actual status:   $3"
        return 1
    fi
}

report() {
    echo "$TESTS_RUN assertions, $TESTS_FAILED failed ($(basename "$0"))"
    [ "$TESTS_FAILED" -eq 0 ]
}
