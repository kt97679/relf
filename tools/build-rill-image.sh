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
python3 tools/rill-genes.py --forth > "$tmp.genes.4" || exit 1     # the genome: rill/genes.tsv, RILL_GENES (749)
python3 tools/rill-genes.py --source "$tmp.src" || exit 1           # its sources: [gene] blocks kept or cut (751)
# the prompt's line editor (825): relfsh's shell/edit.4 as it is, after rill/edit-shim.4 and the
# characters' widths it measures with - shell.4's section, cut out here so that there is one source
awk '/^\\ Characters. widths on screen/ {p = 1} p {print} p && /^: CHAR-COLS/ {c = 1} c && / ;$/ {exit}' shell/shell.4 > "$tmp.widths.4"
grep -q '^: CHAR-COLS' "$tmp.widths.4" && [ "$(wc -l < "$tmp.widths.4")" -lt 300 ] || { echo "build-rill-image: shell/shell.4's widths section not found" >&2; rm -rf "$tmp.genes.4" "$tmp.src" "$tmp.widths.4"; exit 1; }
{
    for f in forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 "$tmp.genes.4" "$tmp.src/rt.4" "$tmp.src/regex.4" "$tmp.widths.4" rill/edit-shim.4 shell/edit.4 "$tmp.src/compile.4"; do
        printf 'S" %s" INCLUDED\n' "$f"
    done
    printf "' R-BOOT SET-BOOT\nS\" %s\" SAVE-SYSTEM\nBYE\n" "$tmp"
} | "$engine" "$kernel" > "$tmp.log" 2>&1
if [ ! -s "$tmp" ] || grep -qE 'Undefined word|[Uu]nderflow|[Oo]verflow|not unique|Incomplete control' "$tmp.log"; then
    echo "build-rill-image: $out not built; the build said:" >&2
    tr -d '\r' < "$tmp.log" | grep -vE '^(Redefining: |OK$|Welcome to Forth)' | grep -v '^[[:space:]]*$' | head -20 | sed 's/^/    /' >&2
    rm -rf "$tmp" "$tmp.log" "$tmp.genes.4" "$tmp.src" "$tmp.widths.4"; exit 1
fi
mv -f "$tmp" "$out"; rm -rf "$tmp.log" "$tmp.genes.4" "$tmp.src" "$tmp.widths.4"
echo "$out: $(wc -c < "$out") bytes"
