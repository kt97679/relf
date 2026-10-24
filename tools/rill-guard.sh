#!/bin/sh
# tools/rill-guard.sh [BASE] - Rill's work has not touched relfsh (Iteration 731).
#
# The user's rule: building Rill must not break relfsh. Rill lives in its
# own image (SHELL-LANGUAGE.md Part 5), so a Rill iteration changes only
# Rill's own files and the docs. This lists what changed since BASE
# (default: the last commit that changed relfsh, 725) outside them, and
# fails if anything did. verify's image sums are the second guard: a
# Rill iteration must leave every row of tests/BASELINE where it was.
cd "$(dirname "$0")/.." || exit 2
base=${1:-270c9e8}
out=$(git diff --name-only "$base" HEAD -- . \
    ':!rill/' ':!examples/rill/' ':!tests/rill/' ':!docs/' \
    ':!tools/rill-*' ':!tools/size-research/' ':!tools/utf8/' ':!bench/reports/')
if [ -n "$out" ]; then
    echo "rill-guard: changed since $base outside Rill's files:" >&2
    printf '  %s\n' $out >&2
    exit 1
fi
echo "rill-guard: nothing of relfsh's changed since $base"
