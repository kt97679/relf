#!/bin/bash
# tests/run_tests.sh — build relf and run the full test suite against it,
# for both the default (8-byte) cell width and the 32-bit (4-byte,
# i386) target.
#
# relf is portable, libc-based C (see GOALS.md phase 5) - built with a
# plain `cc`, no special flags. Cell width is parameterized (see
# GOALS.md phase 6): relf.c picks 4 or 8 bytes at compile time from the
# host's own UINTPTR_MAX, matching the process's own pointer width, per
# RelF's real-pointer addressing model (see PROGRESS.md, Bug 2, for why
# cell width and host pointer width must match). Building with a 32-bit
# compiler (e.g. `gcc -m32`) therefore automatically produces a
# 4-byte-cell engine - no source changes needed for the engine itself.
#
# Images are native host endianness (see GOALS.md phase 5), not a
# portable on-disk format, and carry an 8-byte magic header (cell width
# + a fixed tag) so a mismatched image fails cleanly at load instead of
# silently misbehaving. The 4-byte-cell image is a genuinely different
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
    # spent COMPILING locals.4 + shell.4 from source, which relfsh's
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

echo "== Building relf (default, 8-byte cells) =="
cc -O2 -Wall -o relf relf.c

echo "== Running test suite (8-byte cells) =="
run_suite ./relf kernel.img "8-byte cells"
run_shell_test_suite relf kernel.img "8-byte cells"

echo "== Building relf32 (i386, 4-byte cells) =="
if ! cc -m32 -O2 -Wall -o relf32 relf.c 2>/tmp/relf32_build.log; then
    echo "SKIP: gcc -m32 not available on this host (32-bit dev libs missing?) - see /tmp/relf32_build.log"
else
    echo "== Cross-compiling a 4-byte-cell target image =="
    WORKDIR=$(mktemp -d)
    trap 'rm -rf "$WORKDIR"' EXIT
    cp extend.4 cross.4 kernel.4 kernel.img "$WORKDIR/"
    sed -i 's/^8 TARGET-CELL-BYTES !$/4 TARGET-CELL-BYTES !/' "$WORKDIR/cross.4"
    cp relf "$WORKDIR/"
    ( cd "$WORKDIR"
      printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
        | timeout 60 ./relf kernel.img > boot.log 2>&1
      if grep -qiE "undefined word|segmentation fault" boot.log; then
          echo "FAIL: 4-byte-cell cross-compile failed (see boot.log below)"
          cat boot.log
          exit 1
      fi
    )
    cp "$WORKDIR/kernel.img" kernel32.img

    echo "== Running test suite (4-byte cells, i386) =="
    run_suite ./relf32 kernel32.img "4-byte cells, i386"
    run_shell_test_suite relf32 kernel32.img "4-byte cells, i386"
fi
