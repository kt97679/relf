#!/bin/bash
# tests/run_tests.sh — build relf and run the full test suite against it,
# for both the default (8-byte) cell width and the 32-bit (4-byte,
# i386) target.
#
# relf is built from cv8.c, the CV8 engine - portable, libc-based C,
# built with a plain `cc`. Cell width is the host's pointer width,
# chosen at compile time (GOALS.md phase 6), so a 32-bit compiler
# (`cc -m32`) produces the 4-byte-cell engine with no source changes.
# The i386 build is non-PIE: PIE spends ebx on the GOT, which costs
# the engine's TOS cache more than it saves (CV8.md 3.3).
#
# Images are native host endianness (see GOALS.md phase 5), not a
# portable on-disk format, and carry a CV8 header (CV8-REFERENCE.md
# 5.1) recording the cell width, so a mismatched image fails cleanly at
# load instead of silently misbehaving. The 4-byte-cell image is a genuinely different
# image from kernel.img (not just a different engine build of the same
# image) - it's cross-compiled separately, each run, from the same
# cross.4/kernel.4 source with TARGET-CELL-BYTES set to 4 instead of
# cross.4's own default of 8. That's done here via a temporary copy of
# cross.4, not by editing the committed one - see README.md for the
# manual (permanent) equivalent.
#
# Test suite = tester.fr (bundled, John Hayes 1993 CORE word suite,
# already adapted to RelF's own { -> } syntax) + anything in tests/*.fth
# (additional tests, currently core-extra.fth, adapted from
# forth2012-test-suite). tester.fr's harness (the { -> } words
# themselves) must be loaded before any file in tests/*.fth, since those
# words are defined inside tester.fr, not the base kernel.
#
# The engine exits cleanly (code 0) on stdin EOF, even without an
# explicit BYE (see PROGRESS.md, Bug 3 — fixed in phase 2). This script
# still appends BYE itself, since that's the normal way to end a Forth
# session and it costs nothing.

set -euo pipefail
cd "$(dirname "$0")/.."
# The suite's own stdin is closed: a case that runs this shell without
# redirecting stdin would otherwise inherit the TERMINAL and wait there
# for ever - which is what `make verify` did on a real checkout, while
# in a container, where stdin is /dev/null, it had never once hung
# (Iteration 392). The interactive pty harness makes its own terminal
# and is unaffected.
exec < /dev/null

TESTFILES=(tester.fr)
for f in tests/*.fth; do
    TESTFILES+=("$f")
done

run_suite() {
    # $1 = engine binary, $2 = image, $3 = label
    local engine="$1" image="$2" label="$3"
    local output status ok_count
    output=$( { cat "${TESTFILES[@]}"; echo BYE; } | timeout 30 "$engine" "$image" 2>&1 )
    status=$?

    echo "$output"

    if [ "$status" -ne 0 ]; then
        echo "FAIL ($label): engine exited with status $status (timeout or crash)"
        exit 1
    fi

    if echo "$output" | grep -qiE "incorrect result|wrong number of results|undefined word|segmentation fault"; then
        echo "FAIL ($label): test suite reported an error (see output above)"
        exit 1
    fi

    ok_count=$(echo "$output" | grep -c "^OK" || true)
    echo "== PASS ($label): $ok_count OK markers, no errors =="
}

run_shell_test_suite() {
    # $1 = engine binary, $2 = image, $3 = label
    # Runs tests/shell/run-all (see that directory's lib.sh for the
    # bash-tests/-inspired THIS_SH convention this follows) against
    # this engine/image pair, via relfsh with RELF_BIN/RELF_IMG
    # overridden so the same wrapper script drives either cell width.
    local engine="$1" image="$2" label="$3"
    local output status
    # 180s, not 60s. It measured 59.3s on the machine this was raised on,
    # close enough to the old limit to fail intermittently.
    #
    # The reason is NOT fork/exec, which an earlier version of this
    # comment claimed: measured directly, 50 `relfsh -c true` runs take
    # 12.68s while 50 bare `relf kernel.img` runs take 0.061s and 50
    # /bin/true take 0.040s. So ~99.5% of every relfsh invocation is
    # spent COMPILING shadow.4 + shell.4 from source, which relfsh's
    # bootstrap does afresh every single time it starts. ~253ms per
    # invocation, against ~1.2ms of actual engine startup.
    #
    # A prebuilt shell image would remove essentially all of it - see
    # GOALS.md. Unrelated to Iteration 39's locals conversion either
    # way: timed at 59.3s both with the conversion and with it stashed
    # out entirely.
    output=$(RELF_BIN="$PWD/$engine" RELF_IMG="$PWD/$image" THIS_SH="$PWD/relfsh" \
        timeout 180 tests/shell/run-all 2>&1)
    status=$?
    echo "$output"
    if [ "$status" -ne 0 ]; then
        echo "FAIL ($label shell test suite): see failures above"
        exit 1
    fi
    echo "== PASS ($label shell test suite) =="
}

run_ext_suites() {
    # $1 = engine binary, $2 = image, $3 = label
    #
    # The CORE EXT, Memory-Allocation and File-Access suites. They need
    # extend.4, which the CORE suite above deliberately does not load,
    # and tester.fr's harness must be in place before extend.4 changes
    # the search order - so each is fed as a script file, one engine
    # run per suite: chained, one suite's leftovers become the next
    # one's "WRONG NUMBER OF RESULTS". Until Iteration 243 these ran
    # only on the CV8 lab images (tools/lab/forth-tests.sh).
    local engine="$1" image="$2" label="$3" t ext out n=0
    for t in tests/ext/*.fth; do
        ext=$(mktemp)
        printf 'S" tester.fr" INCLUDED\nS" extend.4" INCLUDED\nS" %s" INCLUDED\n' "$t" > "$ext"
        out=$( printf 'S" %s" INCLUDED\nBYE\n' "$ext" | timeout 60 "$engine" "$image" 2>&1 ) || true
        rm -f "$ext"
        if echo "$out" | grep -qiE "incorrect result|wrong number of results|undefined word|segmentation fault"; then
            echo "$out" | grep -iE "incorrect|wrong number|undefined" | head -5
            echo "FAIL ($label): $t"
            exit 1
        fi
        n=$((n + 1))
    done
    echo "== PASS ($label extension suites): $n files =="
}

run_io_suite() {
    # $1 = engine binary, $2 = image, $3 = label
    # KEY, KEY?, MS and FD-POLL against pipes, a non-blocking stdin,
    # files and a directory - see tests/io/run.
    local out
    if ! out=$(bash tests/io/run "$1" "$2" 2>&1); then
        echo "$out"
        echo "FAIL ($3 I/O suite)"
        exit 1
    fi
    echo "== PASS ($3 I/O suite): $(echo "$out" | tail -1 | tr -d '=') =="
}

cross_compile_image() {
    # $1 = target cell bytes, $2 = destination path, $3 = label
    #
    # Regenerates a target image from cross.4 + kernel.4, using the
    # COMMITTED kernel.img as the host the cross-compiler runs on.
    #
    # Both widths are built the same way and from the same sources.
    # Until Iteration 155 only the 4-byte image was regenerated; the
    # 8-byte kernel.img was a committed artifact that nothing ever
    # rebuilt, so "cross.4 still produces the image we ship" was
    # unverified for the width the project actually develops on - and
    # that is the width whose image is also the host, which makes it
    # the fixpoint the whole bootstrap rests on.
    #
    # Done in a temp copy rather than by editing the committed cross.4,
    # so a failed or interrupted run cannot leave the tree modified.
    local bytes="$1" dest="$2" label="$3"
    local wd
    wd=$(mktemp -d)
    cp extend.4 cross.4 kernel.4 kernel.img relf "$wd/"
    if [ "$bytes" != 8 ]; then
        sed -i "s/^8 TARGET-CELL-BYTES !\$/$bytes TARGET-CELL-BYTES !/" "$wd/cross.4"
    fi
    (
        cd "$wd"
        printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
            | timeout 60 ./relf kernel.img > boot.log 2>&1
        if grep -qiE "undefined word|segmentation fault" boot.log; then
            echo "FAIL: $label cross-compile failed (see boot.log below)"
            cat boot.log
            exit 1
        fi
    )
    cp "$wd/kernel.img" "$dest"
    rm -rf "$wd"
}

check_image_reproduces() {
    # $1 = freshly cross-compiled image, $2 = committed image, $3 = label
    #
    # The committed image must be exactly what today's sources produce.
    # If it is not, either the committed artifact is stale or the
    # cross-compiler is nondeterministic, and both are silent failures
    # that would otherwise surface much later as inexplicable runtime
    # behaviour. Prints a line tests/verify greps.
    if [ ! -e "$2" ]; then
        echo "== IMAGE-FIXPOINT ($3): missing =="
    elif cmp -s "$1" "$2"; then
        echo "== IMAGE-FIXPOINT ($3): reproduces =="
    else
        echo "== IMAGE-FIXPOINT ($3): DIFFERS =="
    fi
}

echo "== Building relf (default, 8-byte cells) =="
cc -O2 -Wall -o relf cv8.c
# The compare-on-every-push build, for a target without an MMU, is not
# what runs here - so check at least that it still compiles cleanly.
cc -O2 -Wall -Werror -DGUARD=0 -o /tmp/relf-noguard cv8.c
rm -f /tmp/relf-noguard

echo "== Cross-compiling an 8-byte-cell target image =="
# Regenerated BEFORE the suites, so the tests below run against an
# image built from the sources in the tree rather than against a
# committed binary that may no longer match them.
cross_compile_image 8 /tmp/relf-regen-kernel.img "8-byte cells"
check_image_reproduces /tmp/relf-regen-kernel.img kernel.img "8-byte cells"

echo "== Running test suite (8-byte cells) =="
run_suite ./relf /tmp/relf-regen-kernel.img "8-byte cells"
run_ext_suites ./relf /tmp/relf-regen-kernel.img "8-byte cells"
run_io_suite ./relf /tmp/relf-regen-kernel.img "8-byte cells"
run_shell_test_suite relf kernel.img "8-byte cells"

echo "== Building relf32 (i386, 4-byte cells) =="
if ! cc -m32 -O2 -Wall -fno-pie -no-pie -o relf32 cv8.c 2>/tmp/relf32_build.log; then
    echo "SKIP: gcc -m32 not available on this host (32-bit dev libs missing?) - see /tmp/relf32_build.log"
else
    echo "== Cross-compiling a 4-byte-cell target image =="
    cross_compile_image 4 /tmp/relf-regen-kernel32.img "4-byte cells, i386"
    check_image_reproduces /tmp/relf-regen-kernel32.img kernel32.img "4-byte cells, i386"
    cp /tmp/relf-regen-kernel32.img kernel32.img

    echo "== Running test suite (4-byte cells, i386) =="
    run_suite ./relf32 kernel32.img "4-byte cells, i386"
    run_ext_suites ./relf32 kernel32.img "4-byte cells, i386"
    run_io_suite ./relf32 kernel32.img "4-byte cells, i386"
    run_shell_test_suite relf32 kernel32.img "4-byte cells, i386"
fi

# ------------------------------------------------------------------
# Size report. Tracked deliberately, not decoratively: shell.4 is going
# to keep growing through phases E/F, and the point is that growth is
# visible as it happens rather than discovered later. See GOALS.md's
# "Tracked numbers" section for the baseline and what the figures mean.
# ------------------------------------------------------------------
report_sizes() {
    local eng="$1" img="$2" label="$3" tmp
    [ -f "$eng" ] && [ -f "$img" ] || return 0
    tmp=$(mktemp) || return 0
    cp "$eng" "$tmp"; strip "$tmp" 2>/dev/null || true
    printf '   %-16s engine %7d + image %7d = %7d bytes\n' \
        "$label" "$(stat -c %s "$tmp")" "$(stat -c %s "$img")" \
        "$(( $(stat -c %s "$tmp") + $(stat -c %s "$img") ))"
    rm -f "$tmp"
}

# Differential suite: scripts checked against a reference shell rather
# than against expectations written by hand. Skipped silently if no
# reference shell is present.
if [ -x /bin/bash ]; then
    echo "== Running differential suite (vs /bin/bash) =="
    THIS_SH="$PWD/relfsh" tests/diff/run-all || exit 1
fi

echo "== Sizes (stripped engine + prebuilt shell image) =="
report_sizes ./relf   kernel-shell.img   "x86-64 (8-byte)"
report_sizes ./relf32 kernel32-shell.img "i386 (4-byte)"
