#!/bin/sh
# tools/build-rill2-image.sh [ENGINE] [KERNEL] [OUT] - Rill 2's image (Iteration 834, docs/RILL2.md).
#
# The kernel, the Forth libraries, Rill's runtime (rill/rt.4, rill/regex.4), relfsh's line editor without its
# completion (835), rill2/rill2.4 and its prompt - no compiler of Rill's - saved with R-BOOT as its boot word: the script R-RUN is given
# ends .r2 and rill2 reads and runs it; with no script, the prompt. bin/rill2 builds it when it is old.
cd "$(dirname "$0")/.." || exit 2
engine=${1:-./relf64} kernel=${2:-forth/kernel64.img} out=${3:-kernel64-rill2.img}
tmp=$out.tmp.$$
python3 tools/rill-genes.py --forth > "$tmp.genes.4" || exit 1
python3 tools/rill-genes.py --source "$tmp.src" || exit 1
# the prompt's line editor (835): relfsh's shell/edit.4 without its TAB completion - that section cut out, as
# the characters' widths are cut out of shell.4 - after rill2/edit-shim.4; then rill2 and its prompt
awk '/^\\ Characters. widths on screen/ {p = 1} p {print} p && /WIDE-CHARS #WIDE-CHARS CP-IN\? IF 2 ELSE 1 THEN ;/ {exit}' shell/shell.4 > "$tmp.widths.4"
awk '/^\\ ---- completion: TAB ----/ {skip = 1} /^\\ ---- reverse incremental history search/ {skip = 0} !skip {print}' shell/edit.4 > "$tmp.edit.4"
if ! grep -q '^: CHAR-COLS' "$tmp.widths.4" || grep -q '^: CMP-' "$tmp.edit.4" || ! grep -q '^: ED-LINE' "$tmp.edit.4"; then
    echo "build-rill2-image: shell.4's widths or edit.4's completion section not found" >&2; rm -rf "$tmp.genes.4" "$tmp.src" "$tmp.widths.4" "$tmp.edit.4"; exit 1
fi
{
    for f in forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 "$tmp.genes.4" "$tmp.src/rt.4" "$tmp.src/regex.4" "$tmp.widths.4" rill2/edit-shim.4 "$tmp.edit.4" rill2/rill2.4 rill2/prompt.4; do
        printf 'S" %s" INCLUDED\n' "$f"
    done
    printf "' R2-COMPILE IS R-COMPILE  ' R2-SUFFIX IS R-SUFFIX  ' R2-REPL IS R-REPL-D\n' R-BOOT SET-BOOT\nS\" %s\" SAVE-SYSTEM\nBYE\n" "$tmp"
} | "$engine" "$kernel" > "$tmp.log" 2>&1
if [ ! -s "$tmp" ] || grep -qE 'Undefined word|[Uu]nderflow|[Oo]verflow|not unique|Incomplete control' "$tmp.log"; then
    echo "build-rill2-image: $out not built; the build said:" >&2
    tr -d '\r' < "$tmp.log" | grep -vE '^(Redefining: |OK$|Welcome to Forth)' | grep -v '^[[:space:]]*$' | head -20 | sed 's/^/    /' >&2
    rm -rf "$tmp" "$tmp.log" "$tmp.genes.4" "$tmp.src" "$tmp.widths.4" "$tmp.edit.4"; exit 1
fi
mv -f "$tmp" "$out"; rm -rf "$tmp.log" "$tmp.genes.4" "$tmp.src" "$tmp.widths.4" "$tmp.edit.4"
echo "$out: $(wc -c < "$out") bytes"
