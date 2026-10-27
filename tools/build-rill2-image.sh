#!/bin/sh
# tools/build-rill2-image.sh [ENGINE] [KERNEL] [OUT] - Rill 2's image (Iteration 834, docs/RILL2.md).
#
# The kernel, the Forth libraries, Rill's runtime (rill/rt.4, rill/regex.4) and rill2/rill2.4 - no
# compiler of Rill's, no line editor - saved with R-BOOT as its boot word: the script R-RUN is given
# ends .r2 and rill2 reads and runs it; with no script, a usage. bin/rill2 builds it when it is old.
cd "$(dirname "$0")/.." || exit 2
engine=${1:-./relf64} kernel=${2:-forth/kernel64.img} out=${3:-kernel64-rill2.img}
tmp=$out.tmp.$$
python3 tools/rill-genes.py --forth > "$tmp.genes.4" || exit 1
python3 tools/rill-genes.py --source "$tmp.src" || exit 1
{
    for f in forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 "$tmp.genes.4" "$tmp.src/rt.4" "$tmp.src/regex.4" rill2/rill2.4; do
        printf 'S" %s" INCLUDED\n' "$f"
    done
    printf "' R2-COMPILE IS R-COMPILE  ' R2-SUFFIX IS R-SUFFIX  ' R2-USAGE IS R-REPL-D\n' R-BOOT SET-BOOT\nS\" %s\" SAVE-SYSTEM\nBYE\n" "$tmp"
} | "$engine" "$kernel" > "$tmp.log" 2>&1
if [ ! -s "$tmp" ] || grep -qE 'Undefined word|[Uu]nderflow|[Oo]verflow|not unique|Incomplete control' "$tmp.log"; then
    echo "build-rill2-image: $out not built; the build said:" >&2
    tr -d '\r' < "$tmp.log" | grep -vE '^(Redefining: |OK$|Welcome to Forth)' | grep -v '^[[:space:]]*$' | head -20 | sed 's/^/    /' >&2
    rm -rf "$tmp" "$tmp.log" "$tmp.genes.4" "$tmp.src"; exit 1
fi
mv -f "$tmp" "$out"; rm -rf "$tmp.log" "$tmp.genes.4" "$tmp.src"
echo "$out: $(wc -c < "$out") bytes"
