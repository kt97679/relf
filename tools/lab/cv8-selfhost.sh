#!/bin/bash
# tools/lab/cv8-selfhost.sh BUILDDIR - can CV8 rebuild itself?
#
# build-cv8.sh checks that each image RUNS and agrees with dash, and
# forth-tests.sh checks that each one compiles hundreds of definitions
# correctly. Neither asks the question this file asks, which is the
# actual phase-3 goal: can the system reproduce ITSELF?
#
# Two different things are meant by that, and both are checked here
# because passing one says nothing about the other.
#
#   GATE 1, cross-compile. A CV8 image reads extend.4, cross.4 and
#   kernel.4 and writes a new kernel image. The output must be
#   BYTE-IDENTICAL to the committed reference. This exercises the whole
#   outer interpreter, the cross-compiler and the dictionary, and it
#   cannot be passed by a system that is subtly wrong: one byte out of
#   place anywhere and the comparison fails. It is also the gate that
#   correctness and speed are measured by in the article repository,
#   for the same reason.
#
#   GATE 2, save and re-save. A CV8 image SAVE-SYSTEMs a CV8 image
#   (gen2), gen2 SAVE-SYSTEMs another (gen3), and gen2 must equal gen3
#   byte for byte. A fixed point, not just a working save: gen2 being
#   runnable proves the save wrote something usable, and gen2 == gen3
#   proves the save does not accumulate state. The first version of
#   cv8-save.4 passed the first half and failed the second, because an
#   image is always saved in the MIDDLE of the command that saves it
#   and shell.4's parser cursors were still live - see PROGRESS.md 207.
#
# KNOWN, and not a failure of either gate: saving from a RUNNING shell
# writes a correct image and then segfaults, because RESET-BUFFERS
# releases pool buffers the shell goes on using. relfsh always follows
# SAVE-SYSTEM with BYE. The segfault is therefore expected here and the
# checks below look at the ARTIFACT, never at the exit status.
set -u

# Every engine here is a subject under test, so it runs in a predictable
# environment. See the note in build-cv8.sh for why LD_PRELOAD in
# particular matters with the 32-bit engines.
unset LD_PRELOAD

cd "$(dirname "$0")/../.."
ROOT=$PWD
B=${1:?usage: cv8-selfhost.sh BUILDDIR}
B=$(cd "$B" && pwd)
fail=0

# ---- gate 1: cross-compile the kernel, byte for byte ----------------
gate1() {   # gate1 ENGINE IMAGE CELLBYTES REFERENCE LABEL
    local eng=$1 img=$2 cb=$3 ref=$4 lbl=$5 d
    [ -x "$eng" ] && [ -r "$img" ] || {
        printf 'SKIP %-38s not built\n' "$lbl"; return; }
    d=$(mktemp -d)
    cp "$ROOT/extend.4" "$ROOT/cross.4" "$ROOT/kernel.4" "$d/"
    # Done in a copy, never by editing the tracked cross.4, so an
    # interrupted run cannot leave the tree modified.
    [ "$cb" = 4 ] && sed -i 's/^8 TARGET-CELL-BYTES !$/4 TARGET-CELL-BYTES !/' "$d/cross.4"
    ( cd "$d" && printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
        | timeout 300 "$eng" "$img" > boot.log 2>&1 )
    if grep -qiE "undefined word|segmentation" "$d/boot.log"; then
        printf 'FAIL %-38s cross-compile failed\n' "$lbl"
        head -3 "$d/boot.log"; fail=1
    elif [ ! -s "$d/kernel.img" ]; then
        printf 'FAIL %-38s no image produced\n' "$lbl"; fail=1
    elif cmp -s "$d/kernel.img" "$ROOT/$ref"; then
        printf 'ok   %-38s == %s\n' "$lbl" "$ref"
    else
        printf 'FAIL %-38s differs from %s (%s vs %s bytes)\n' "$lbl" "$ref" \
               "$(stat -c%s "$d/kernel.img")" "$(stat -c%s "$ROOT/$ref")"; fail=1
    fi
    rm -rf "$d"
}

echo "== gate 1: CV8 cross-compiles the kernel byte-identically =="
gate1 "$B/spec-64" "$B/fkernel-64.img" 8 kernel.img   "CV8 spec 64-bit"
gate1 "$B/spec-32" "$B/fkernel-32.img" 4 kernel32.img "CV8 spec 32-bit"
gate1 "$B/cv8b-64" "$B/cv8b-64.img"    8 kernel.img   "CV8 byte-headers 64-bit"
gate1 "$B/cv8b-32" "$B/cv8b-32.img"    4 kernel32.img "CV8 byte-headers 32-bit"

# ---- gate 2: SAVE-SYSTEM reaches a fixed point ----------------------
# The `forth` builtin's arguments arrive already tokenized, so S" has to
# be protected by shell quotes or the shell splits it and the image
# reports `Undefined word S`.
gate2() {   # gate2 ENGINE IMAGE LABEL
    local eng=$1 img=$2 lbl=$3 w
    [ -x "$eng" ] && [ -r "$img" ] || {
        printf 'SKIP %-38s not built\n' "$lbl"; return; }
    w=$(mktemp -d)
    # stderr of the whole subshell is discarded because the shell
    # announces the EXPECTED segfault described in the header, once per
    # save, and that noise is indistinguishable from a real problem.
    # Every check below looks at the artifact instead.
    ( cd "$w"
      printf 'forth "S\\" gen2.img\\" SAVE-SYSTEM"\n' > c2.sh
      timeout 300 "$eng" "$img" c2.sh >/dev/null 2>&1
      [ -s gen2.img ] || exit 1
      printf 'forth "S\\" gen3.img\\" SAVE-SYSTEM"\n' > c3.sh
      timeout 300 "$eng" gen2.img c3.sh >/dev/null 2>&1
      [ -s gen3.img ] || exit 2
      [ "$(timeout 60 "$eng" gen2.img -c 'echo alive' 2>&1 | tr -d '\r')" = alive ] || exit 3
      exit 0 ) 2>/dev/null
    case $? in
      1) printf 'FAIL %-38s gen2 not written\n' "$lbl"; fail=1; rm -rf "$w"; return;;
      2) printf 'FAIL %-38s gen3 not written\n' "$lbl"; fail=1; rm -rf "$w"; return;;
      3) printf 'FAIL %-38s gen2 does not run\n' "$lbl"; fail=1; rm -rf "$w"; return;;
    esac
    if cmp -s "$w/gen2.img" "$w/gen3.img"; then
        printf 'ok   %-38s gen2 == gen3, %s bytes\n' "$lbl" "$(stat -c%s "$w/gen2.img")"
    else
        printf 'FAIL %-38s gen2 %s vs gen3 %s bytes\n' "$lbl" \
               "$(stat -c%s "$w/gen2.img")" "$(stat -c%s "$w/gen3.img")"; fail=1
    fi
    rm -rf "$w"
}

echo
echo "== gate 2: CV8 SAVE-SYSTEM reaches a fixed point =="
gate2 "$B/spec-64" "$B/self-64.img" "CV8 shell image 64-bit"
gate2 "$B/spec-32" "$B/self-32.img" "CV8 shell image 32-bit"

echo
[ $fail = 0 ] && echo "CV8 rebuilds itself: both gates pass." \
              || echo "CV8 SELF-HOSTING BROKEN - see failures above."
exit $fail
