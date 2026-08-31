#!/bin/bash
# tests/run_tests.sh — build relf and run the full test suite against it.
#
# Requires a 32-bit-capable gcc (gcc -m32) — see PROGRESS.md, Bug 2:
# RelF's real-pointer addressing model needs the process's own pointer
# width to match the declared cell width, not just the C type width.
#
# Test suite = tester.fr (bundled, John Hayes 1993 CORE word suite,
# already adapted to RelF's own { -> } syntax) + anything in tests/*.fth
# (additional tests, currently core-extra.fth, adapted from
# forth2012-test-suite). tester.fr's harness (the { -> } words
# themselves) must be loaded before any file in tests/*.fth, since those
# words are defined inside tester.fr, not the base kernel.
#
# The engine does not exit cleanly on stdin EOF without reaching BYE
# (see PROGRESS.md, Bug 3) — this script appends BYE itself as a
# workaround.

set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Building relf =="
gcc -m32 -O2 -o relf relf.c

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
