#!/bin/sh
# tools/build-rill-image.sh [ENGINE] [KERNEL] [OUT] - Rill's own image (Iteration 736).
#
# SHELL-LANGUAGE.md Part 5: the kernel, the Forth libraries the shell's
# image also loads, and rill/'s sources - none of shell.4, tree.4 or
# edit.4 - saved with R-BOOT as its boot word. Not in the Makefile, so
# that nothing of relfsh's build changes (RILL-LEDGER.md 731).
cd "$(dirname "$0")/.." || exit 2
engine=${1:-./relf64} kernel=${2:-forth/kernel64.img} out=${3:-kernel64-rill.img}
tmp=$out.tmp.$$
{
    for f in forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 rill/rt.4; do
        printf 'S" %s" INCLUDED\n' "$f"
    done
    printf "' R-BOOT SET-BOOT\nS\" %s\" SAVE-SYSTEM\nBYE\n" "$tmp"
} | "$engine" "$kernel" > "$tmp.log" 2>&1
if [ ! -s "$tmp" ] || grep -qE 'Undefined word|[Uu]nderflow|[Oo]verflow|not unique' "$tmp.log"; then
    echo "build-rill-image: $out not built; the build said:" >&2
    tr -d '\r' < "$tmp.log" | grep -vE '^(Redefining: |OK$|Welcome to Forth)' | grep -v '^[[:space:]]*$' | head -20 | sed 's/^/    /' >&2
    rm -f "$tmp" "$tmp.log"; exit 1
fi
mv -f "$tmp" "$out"; rm -f "$tmp.log"
echo "$out: $(wc -c < "$out") bytes"
