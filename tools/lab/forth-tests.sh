#!/bin/bash
# forth-tests.sh BUILD - run the ANS CORE suite (tester.fr + tests/*.fth,
# 671 cases) on the CV8 images, at both cell widths.
#
# WHY THIS EXISTS: the shell suites (tests/shell, tests/diff) exercise
# the shell, and every CV8 image passed them long before the Forth
# COMPILER was correct. This suite is the one that compiles hundreds of
# definitions at RUN time, so it is what actually tests cv8.4. It was
# not being run for several iterations - see PROGRESS.md 204.
#
# Needs a CV8 image that boots into the INTERPRETER, not the shell: a
# shell image sends this input to the shell, which reports nothing
# useful. build-cv8.sh builds fkernel-64/-32 for exactly this.
set -e
cd "$(dirname "$0")/../.."

# Every engine below is a measured or tested subject, so it runs in a
# predictable environment rather than whatever the caller exported.
# LD_PRELOAD is the one that bites: a desktop session that preloads a
# library into every process has it loaded into every engine here too,
# and when the engine is a 32-bit binary and the library is 64-bit,
# ld.so cannot load it and writes a line of complaint PER PROCESS -
# straight into the output a dump or a test comparison is reading.
unset LD_PRELOAD

B=${1:?usage: forth-tests.sh BUILDDIR}
B=$(cd "$B" && pwd)
# The suite must run from the repo root: tests/locals.fth INCLUDEs
# pool.4 by relative path.
#
# But it must NEVER be handed an image that boots into the SHELL: the
# shell parses tester.fr as a script, and its `>` and `->` become
# REDIRECTIONS, creating one empty file per token in the repo root.
# That happened in Iteration 204 and 72 such files were committed.
# So check first that the image boots into the INTERPRETER.
interpreter_p() {
    printf '1 2 + . BYE\n' | timeout 10 "$1" "$2" 2>/dev/null | tr -d '\r' | grep -q '^3 '
}
fail=0
run() {   # run ENGINE IMAGE LABEL
    local out st
    if ! interpreter_p "$1" "$2"; then
        echo "FAIL $3: $2 does not boot into the Forth interpreter."
        echo "      Refusing to run: a shell image would turn tester.fr's"
        echo "      '>' into redirections and litter the repository."
        fail=1; return
    fi
    out=$( { cat tester.fr tests/*.fth; echo BYE; } | timeout 120 "$1" "$2" 2>&1 ) || true
    st=$?
    if echo "$out" | grep -qiE "incorrect result|wrong number of results|undefined word|segmentation"; then
        echo "FAIL $3"; echo "$out" | grep -iE "incorrect|wrong number|undefined" | head -5
        fail=1
    else
        echo "ok   $3 (671 cases)"
    fi
}
run "$B/spec-64" "$B/fkernel-64.img" "CORE suite, CV8 64-bit"
run "$B/spec-32" "$B/fkernel-32.img" "CORE suite, CV8 32-bit"
# s6, byte-granular dictionary headers. These are the images that
# exercise cv8b.4's replacement SEARCH-WORDLIST and NAME> - the ones
# that have to find a word through a 1-3 byte backward-read link - so
# without this the whole byte-header path is code nobody runs.
run "$B/cv8b-64" "$B/cv8b-64.img"    "CORE suite, CV8 byte headers 64-bit"
run "$B/cv8b-32" "$B/cv8b-32.img"    "CORE suite, CV8 byte headers 32-bit"
# The 16-bit encodings emitting their own encoding. These are what make
# sod16.4 and cpt16.4 more than dead files: the suite compiles hundreds
# of definitions at RUN time, which is the only thing that exercises a
# compiler overlay at all.
run "$B/sod16p-64" "$B/s16self-64.img"  "CORE suite, SOD16 self-hosting 64-bit"
run "$B/sod16p-32" "$B/s16self-32.img"  "CORE suite, SOD16 self-hosting 32-bit"
# The old numbering, WITHOUT the escaped band, which is the default
# everywhere else now. Kept so the two stay comparable and so the
# engine's refusal path has something to refuse. The CORE suite is what
# caught the escape fault in Iteration 204 and proved the fix in 210.
run "$B/noesc-64"    "$B/noesc-64.img"    "CORE suite, CV8 WITHOUT the escaped band 64-bit"
run "$B/noesc-32"    "$B/noesc-32.img"    "CORE suite, CV8 WITHOUT the escaped band 32-bit"
run "$B/cptf-64"   "$B/cptfself-64.img" "CORE suite, CPT16+fold self-hosting 64-bit"
run "$B/cptf-32"   "$B/cptfself-32.img" "CORE suite, CPT16+fold self-hosting 32-bit"
exit $fail
