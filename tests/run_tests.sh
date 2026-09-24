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
# the engine's TOS cache more than it saves (CV8.md 5.1).
#
# Images are native host endianness (see GOALS.md phase 5), not a
# portable on-disk format, and carry a CV8 header (CV8.md
# 4.1) recording the cell width, so a mismatched image fails cleanly at
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
# Byte order and byte classes for every shell this suite runs: pathname
# expansion sorts by LC_COLLATE, `[a-z]` is a collation range and
# `[[:alpha:]]` is a locale's own idea of a letter. This shell has no
# locale support - it is always the C locale - so a suite that compares
# it with another shell, or with recorded output, has to say which
# locale it means. A checkout in en_US.UTF-8 saw the difference
# (Iterations 390 and 393).
LC_ALL=C
export LC_ALL
# A preload library the loader cannot use prints a line to stderr on
# every exec - Ubuntu and Mint set one system-wide (libgtk3-nocsd), and
# it cannot be loaded into the 32-bit engine at all. The tests capture
# stderr, so that line became part of what they compared, and every
# i386 assertion failed with the right answer one line down
# (Iteration 396). No test here wants a preload.
unset LD_PRELOAD

# A cell is a pointer. On a 64-bit host the native engine runs the
# 8-byte image and the 4-byte one is a cross build; on a 32-bit host -
# ARMv7, i386 - it is the other way round and there is no cross build at
# all. This script assumed the first arrangement everywhere, so on an
# ARMv7 board it fed the 8-byte image to a 4-byte engine and stopped at
# "Cross-compiling an 8-byte-cell target image" (Iteration 398).
HOSTBITS=${HOSTBITS:-$(getconf LONG_BIT 2>/dev/null || echo 64)}
if [ "$HOSTBITS" = 32 ]; then
    NATIVE_BYTES=4; NATIVE_IMG=kernel32.img
    OTHER_BYTES=8;  OTHER_IMG=kernel.img
else
    NATIVE_BYTES=8; NATIVE_IMG=kernel.img
    OTHER_BYTES=4;  OTHER_IMG=kernel32.img
fi

TESTFILES=(tester.fr)
for f in tests/*.fth; do
    TESTFILES+=("$f")
done

run_suite() {
    # $1 = engine binary, $2 = image, $3 = label
    local engine="$1" image="$2" label="$3"
    local output ok_count
    # `output=$(...)` under `set -e` exits the script the moment the
    # command fails - BEFORE the next line can read its status, and
    # before anything is echoed. A failing step then looks like the
    # script stopping for no reason, which is exactly what a checkout
    # reported: the log ended after the passing step and said nothing
    # (Iteration 394). `|| status=$?` keeps the failure local.
    local status=0
    output=$( { cat "${TESTFILES[@]}"; echo BYE; } | timeout 30 "$engine" "$image" 2>&1 ) || status=$?

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
    local output
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
    local status=0
    output=$(RELF_BIN="$PWD/$engine" RELF_IMG="$PWD/$image" THIS_SH="$PWD/relfsh" \
        timeout 180 tests/shell/run-all 2>&1) || status=$?
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
    # The HOST's image, whatever width that is: cross.4 targets either
    # width, but it has to RUN somewhere first (Iteration 398).
    cp extend.4 cross.4 kernel.4 "$NATIVE_IMG" relf "$wd/"
    if [ "$bytes" != 8 ]; then
        sed -i "s/^8 TARGET-CELL-BYTES !\$/$bytes TARGET-CELL-BYTES !/" "$wd/cross.4"
    fi
    (
        cd "$wd"
        printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
            | timeout 60 ./relf "$NATIVE_IMG" > boot.log 2>&1
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

echo "== Building relf (native, $NATIVE_BYTES-byte cells) =="
# ${CC} rather than a bare `cc`, so a 64-bit machine can be told to
# build and test as a 32-bit one: CC='cc -m32 -fno-pie -no-pie'
# HOSTBITS=32 tests/run_tests.sh (Iteration 398).
${CC:-cc} -O2 -Wall -o relf cv8.c
# The compare-on-every-push build, for a target without an MMU, is not
# what runs here - so check at least that it still compiles cleanly.
${CC:-cc} -O2 -Wall -Werror -DGUARD=0 -o /tmp/relf-noguard cv8.c
rm -f /tmp/relf-noguard

# The native half: cross-compile the host's own image, check it is the
# one committed, and run everything against it. The labels stay
# width-based, because that is what they measure and what tests/verify
# reads (Iteration 398).
echo "== Cross-compiling a $NATIVE_BYTES-byte-cell target image =="
# Regenerated BEFORE the suites, so the tests below run against an
# image built from the sources in the tree rather than against a
# committed binary that may no longer match them.
cross_compile_image "$NATIVE_BYTES" /tmp/relf-regen-native.img "$NATIVE_BYTES-byte cells"
check_image_reproduces /tmp/relf-regen-native.img "$NATIVE_IMG" "$NATIVE_BYTES-byte cells"

echo "== Running test suite ($NATIVE_BYTES-byte cells) =="
run_suite ./relf /tmp/relf-regen-native.img "$NATIVE_BYTES-byte cells"
run_ext_suites ./relf /tmp/relf-regen-native.img "$NATIVE_BYTES-byte cells"
run_io_suite ./relf /tmp/relf-regen-native.img "$NATIVE_BYTES-byte cells"
run_shell_test_suite relf "$NATIVE_IMG" "$NATIVE_BYTES-byte cells"

# RUNNING the other width needs an engine for it: on a 64-bit host the
# -m32 cross build, on a 32-bit host nothing at all. Its IMAGE can still
# be cross-compiled and checked either way - cross.4 targets either
# width - which on a 32-bit host is the only thing that can be said
# about the 8-byte side.
if [ "$HOSTBITS" = 32 ]; then
    echo "== Cross-compiling a $OTHER_BYTES-byte-cell target image =="
    cross_compile_image "$OTHER_BYTES" /tmp/relf-regen-other.img "$OTHER_BYTES-byte cells"
    check_image_reproduces /tmp/relf-regen-other.img "$OTHER_IMG" "$OTHER_BYTES-byte cells"
    echo "SKIP: this host is 32-bit, so the 8-byte half cannot be run here"
    echo "      (its image was cross-compiled and checked just above)"
else

echo "== Building relf32 (i386, 4-byte cells) =="
if ! cc -m32 -O2 -Wall -fno-pie -no-pie -o relf32 cv8.c 2>/tmp/relf32_build.log; then
    echo "SKIP: gcc -m32 not available on this host (32-bit dev libs missing?) - see /tmp/relf32_build.log"
    echo "      install gcc-multilib (Debian/Ubuntu) to run the i386 half"
else
    echo "== Cross-compiling a 4-byte-cell target image =="
    # Compiling for i386 is not the same as being able to RUN an i386
    # binary: a host can have the compiler and not the loader. Checked
    # here, so a missing loader is a SKIP with a reason rather than a
    # cascade of failures (Iteration 394).
    if ! ./relf32 kernel32.img -c ':' >/dev/null 2>&1 &&
       ! echo BYE | ./relf32 kernel32.img >/dev/null 2>&1; then
        echo "SKIP: the i386 engine cannot run here (no 32-bit loader?)"
        echo "      install libc6-i386 (Debian/Ubuntu) to run the i386 half"
    else
    cross_compile_image 4 /tmp/relf-regen-kernel32.img "4-byte cells, i386"
    check_image_reproduces /tmp/relf-regen-kernel32.img kernel32.img "4-byte cells, i386"
    cp /tmp/relf-regen-kernel32.img kernel32.img

    # The widening direction, from a narrow host: the 32-bit engine
    # cross-compiling the 8-byte image. It differed until Iteration 415 -
    # LITERAL-T sent every literal that was not tiny through a test
    # whose constant a 32-bit cell cannot hold, and kernel.4's own
    # LITERAL contained two such constants - and nothing checked it
    # except an ARMv7 board. Checked here now, on every run that has an
    # i386 engine.
    wd=$(mktemp -d)
    cp extend.4 cross.4 kernel.4 kernel32.img relf32 "$wd/"
    ( cd "$wd" && printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
        | timeout 120 ./relf32 kernel32.img > boot.log 2>&1 ) || true
    check_image_reproduces "$wd/kernel.img" kernel.img "8-byte cells, from a 4-byte host"
    rm -rf "$wd"

    # ... and the fourth combination, the 4-byte engine building its own
    # width. On a 32-bit host that is the native fixpoint; here it was
    # the one combination nothing ran, which FORTH-STYLE.md 15 claimed
    # was covered until the claim was checked (Iteration 417).
    wd=$(mktemp -d)
    cp extend.4 cross.4 kernel.4 kernel32.img relf32 "$wd/"
    sed -i "s/^8 TARGET-CELL-BYTES !\$/4 TARGET-CELL-BYTES !/" "$wd/cross.4"
    ( cd "$wd" && printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
        | timeout 120 ./relf32 kernel32.img > boot.log 2>&1 ) || true
    check_image_reproduces "$wd/kernel.img" kernel32.img "4-byte cells, from a 4-byte host"
    rm -rf "$wd"

    echo "== Running test suite (4-byte cells, i386) =="
    run_suite ./relf32 kernel32.img "4-byte cells, i386"
    run_ext_suites ./relf32 kernel32.img "4-byte cells, i386"
    run_io_suite ./relf32 kernel32.img "4-byte cells, i386"
    run_shell_test_suite relf32 kernel32.img "4-byte cells, i386"
    fi
fi
fi   # HOSTBITS

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
