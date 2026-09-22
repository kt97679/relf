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
# .right file), most assertions here are substring/status rather than
# full-output diffing. That was originally justified by "RelF's own
# boot banner and CRLF line endings", and BOTH of those reasons
# expired in Iteration 40, when the prebuilt image began booting
# straight into MAIN: the shell emits no banner and no CR. The
# justification went stale, the weakened assertions did not, and what
# they were hiding was real - the interactive prompt was going to
# STDOUT, so `... | relfsh` interleaved "$ " into the shell's own
# output and no substring assertion could see it (Iteration 153).
#
# assert_output_equals below is the strong form. New tests should
# prefer it wherever the exact bytes are known; the existing
# substring assertions are kept because rewriting 63 files at once
# would be a large untested change, not because they are preferred.

# The utilities these tests name by absolute path. They are Ubuntu's
# paths, which is where the suite was written; `true` lives in /bin on
# plenty of systems and in neither place on some. Checked once, here,
# so a machine without them is told which one is missing rather than
# shown a page of failures about the shell (Iteration 395).
# Three files compare this shell's wording against DASH's, because bash
# words the same messages differently. dash is not everywhere - a Gentoo
# ARM board has bash and no dash - so those comparisons are skipped
# rather than failed (Iteration 399).
if command -v dash >/dev/null 2>&1; then HAVE_DASH=1; else HAVE_DASH=0; fi

for _u in /usr/bin/true /usr/bin/false /usr/bin/test /usr/bin/env /bin/sh; do
    if [ ! -x "$_u" ]; then
        echo "SKIP: this suite names $_u by absolute path, and it is not here."
        echo "      (coreutils and a /bin/sh are what it expects; see CHECKING.md)"
        exit 77
    fi
done
unset _u


: "${THIS_SH:=../../relfsh}"
# ... made absolute, once, here. A relative THIS_SH stops resolving the
# moment a test changes directory, and three new tests in a row passed
# alone - run with an absolute path - and failed under run-all, which
# passes the default relative one (Iterations 432, 433, 439). A path
# with no slash is a command name and is left for PATH to find.
case $THIS_SH in
    /*) ;;
    */*) THIS_SH=$(cd "$(dirname "$THIS_SH")" && pwd)/$(basename "$THIS_SH") ;;
esac
export THIS_SH

TESTS_RUN=0
TESTS_FAILED=0

assert_output_equals() {
    # $1 = description, $2 = expected output (exact), $3 = actual output
    TESTS_RUN=$((TESTS_RUN + 1))
    if [ "$3" = "$2" ]; then
        return 0
    fi
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "FAIL: $1"
    echo "  expected exactly:"
    printf '%s\n' "$2" | sed 's/^/    /'
    echo "  actual:"
    printf '%s\n' "$3" | sed 's/^/    /'
    return 1
}

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
