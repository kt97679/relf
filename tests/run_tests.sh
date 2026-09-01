#!/bin/bash
# tests/run_tests.sh — build relf and run the full test suite against it.
#
# relf is a genuine x86-64 process, built -nostdlib -static (no libc, no
# crt0 — see GOALS.md phase 2). Cells are 8 bytes, matching the process's
# own pointer width, per RelF's real-pointer addressing model (see
# PROGRESS.md, Bug 2, for why cell width and host pointer width must
# match).
#
# Test suite = tester.fr (bundled, John Hayes 1993 CORE word suite,
# already adapted to RelF's own { -> } syntax) + anything in tests/*.fth
# (additional tests, currently core-extra.fth, adapted from
# forth2012-test-suite). tester.fr's harness (the { -> } words
# themselves) must be loaded before any file in tests/*.fth, since those
# words are defined inside tester.fr, not the base kernel.
#
# The engine now exits cleanly (code 0) on stdin EOF, even without an
# explicit BYE (see PROGRESS.md, Bug 3 — fixed in phase 2). This script
# still appends BYE itself, since that's the normal way to end a Forth
# session and it costs nothing.

set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Building relf =="
gcc -O2 -nostdlib -static -o relf relf.c

echo "== Running test suite =="
TESTFILES=(tester.fr)
for f in tests/*.fth; do
    TESTFILES+=("$f")
done

OUTPUT=$( { cat "${TESTFILES[@]}"; echo BYE; } | timeout 30 ./relf kernel.img 2>&1 )
STATUS=$?

echo "$OUTPUT"

if [ "$STATUS" -ne 0 ]; then
    echo "FAIL: relf exited with status $STATUS (timeout or crash)"
    exit 1
fi

if echo "$OUTPUT" | grep -qiE "incorrect result|wrong number of results|undefined word|segmentation fault"; then
    echo "FAIL: test suite reported an error (see output above)"
    exit 1
fi

OK_COUNT=$(echo "$OUTPUT" | grep -c "^OK" || true)
echo "== PASS: $OK_COUNT OK markers, no errors =="
