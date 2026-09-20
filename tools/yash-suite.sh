#!/bin/sh
# tools/yash-suite.sh - run yash's POSIX test files against this shell,
# and against a reference, and report where they differ.
#
# The suite is not vendored here: it is yash's, under its own licence.
# Fetch it first, e.g.
#   curl -sL -o yash.tgz \
#     https://codeload.github.com/magicant/yash/tar.gz/refs/tags/2.56.1
#   mkdir -p yash && tar xzf yash.tgz -C yash --strip-components=1
# then point this script at the resulting tests directory.
#
# Usage: tools/yash-suite.sh /path/to/yash/tests [shell] [reference]
#
# Two pieces of scaffolding, both about the harness rather than the
# shell under test (Iteration 375):
#
#   - it drives itself with ALIASES and $LINENO, so it must run under
#     `bash -O expand_aliases`. dash has no LINENO and bash ignores
#     aliases in scripts, so neither alone will do;
#   - it COPIES the testee into a temporary directory, so a relative
#     wrapper breaks. This script passes an absolute path, and writes a
#     small absolute-path wrapper for relfsh if it is given one.
#
# The `sig*`, `job`, `fg`, `bg` and `kill` files are skipped: they need
# a controlling terminal this has no way to give them.
set -e

DIR=${1:?usage: yash-suite.sh /path/to/yash/tests [shell] [reference]}
SH=${2:-$(pwd)/relfsh}
REF=${3:-dash}

case "$SH" in /*) ;; *) SH=$(pwd)/$SH ;; esac

# An absolute wrapper: the harness copies the testee, and relfsh finds
# its engine and image relative to its own location.
WRAP=$(mktemp)
cat > "$WRAP" <<WRAPPER
#!/bin/sh
exec $SH "\$@"
WRAPPER
chmod +x "$WRAP"

run() {   # run every -p file against $1, print "passed failed"
    pass=0; fail=0
    for t in "$DIR"/*-p.tst; do
        b=$(basename "$t")
        case $b in sig*|job-p.tst|fg-p.tst|bg-p.tst|testtty-p.tst|kill*) continue ;; esac
        ( cd "$DIR" && rm -f "${b%.tst}.trs" \
          && LANG=C LC_ALL=C timeout 25 bash -O expand_aliases \
               ./run-test.sh "$1" "$b" >/dev/null 2>&1 ) || true
        p=$(grep -c '^%%% PASSED' "$DIR/${b%.tst}.trs" 2>/dev/null) || p=0
        f=$(grep -c '^%%% FAILED' "$DIR/${b%.tst}.trs" 2>/dev/null) || f=0
        pass=$((pass + p)); fail=$((fail + f))
        if [ "$f" -gt 0 ]; then
            grep '^%%% FAILED' "$DIR/${b%.tst}.trs" >&3 2>/dev/null || true
        fi
        rm -f "$DIR/${b%.tst}.trs"
    done
    echo "$pass $fail"
}

OURS=${TMPDIR:-/tmp}/yash-ours.$$
REFS=${TMPDIR:-/tmp}/yash-ref.$$
ours=$(run "$WRAP" 3>"$OURS")
echo "$SH: $ours ($(grep -c . "$OURS" 2>/dev/null || echo 0) failing cases listed)"
if command -v "$REF" >/dev/null 2>&1; then
    theirs=$(run "$(command -v "$REF")" 3>"$REFS")
    echo "$REF: $theirs ($(grep -c . "$REFS" 2>/dev/null || echo 0) failing cases listed)"
    echo
    echo "tests $REF passes that this shell does not:"
    comm -13 "$(sort -o "$REFS.s" "$REFS"; echo "$REFS.s")" \
             "$(sort -o "$OURS.s" "$OURS"; echo "$OURS.s")" \
      | sed 's/^%%% FAILED: /  /'
    rm -f "$REFS" "$REFS.s" "$OURS.s"
fi
rm -f "$OURS" "$WRAP"
