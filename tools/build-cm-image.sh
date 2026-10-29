#!/bin/sh
# tools/build-cm-image.sh [ENGINE] [KERNEL] [OUT] - the command model's image (863, docs/COMMAND-MODEL.md).
#
# rill2's image with its language part replaced: the kernel, the Forth libraries, Rill's runtime, the
# line editor, as tools/build-rill2-image.sh loads them; then of rill2/rill2.4 only its values - up to
# its library, the words cm's runtime and the Forth it is given use (D-NUM, D+, D-AT ...); then cm's
# runtime and cm/cmc.4, its front end in Forth. A script whose name ends .cm is read, made Forth by
# cm/cmc.4 and run: ./relf64 kernel64-cm.img script.cm. With no script, cm/prompt.4's prompt (869); the
# editor's shim is Rill 2's with the prompt's text cm's.
# The image's size, against rill2's, is what Q46 asked of the command model's front end.
cd "$(dirname "$0")/.." || exit 2
engine=${1:-./relf64} kernel=${2:-forth/kernel64.img} out=${3:-kernel64-cm.img}
tmp=$out.tmp.$$
python3 tools/rill-genes.py --forth > "$tmp.genes.4" || exit 1
python3 tools/rill-genes.py --source "$tmp.src" || exit 1
awk '/^\\ Characters. widths on screen/ {p = 1} p {print} p && /^: CHAR-COLS/ {c = 1} c && / ;$/ {exit}' shell/shell.4 > "$tmp.widths.4"
awk '/^\\ ---- completion: TAB ----/ {skip = 1} /^\\ ---- reverse incremental history search/ {skip = 0} !skip {print}' shell/edit.4 > "$tmp.edit.4"
awk '/^\\ ---- the library/ {exit} {print}' rill2/rill2.4 > "$tmp.values.4"
sed -e 's/S" rill2> "/S" cm> "/' -e 's/7 PS1-WIDTH/4 PS1-WIDTH/' rill2/edit-shim.4 > "$tmp.shim.4"
if ! grep -q '^: D-SET' "$tmp.values.4" || grep -q '^: R2-' "$tmp.values.4"; then
    echo "build-cm-image: rill2.4's values not found before its library" >&2; rm -rf "$tmp.genes.4" "$tmp.src" "$tmp.widths.4" "$tmp.edit.4" "$tmp.values.4" "$tmp.shim.4"; exit 1
fi
{
    for f in forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 "$tmp.genes.4" "$tmp.src/rt.4" "$tmp.src/regex.4" "$tmp.widths.4" "$tmp.shim.4" "$tmp.edit.4" "$tmp.values.4" cm/rt-cm.4 cm/out.4 cm/ctl.4 cm/lib.4 cm/pipe.4 cm/cmc.4 cm/prompt.4; do
        printf 'S" %s" INCLUDED\n' "$f"
    done
    printf ": CM-SUFFIX ( --- c-addr u )   S\" .cm\" ;  ' CM-COMPILE IS R-COMPILE  ' CM-SUFFIX IS R-SUFFIX  ' CM-REPL IS R-REPL-D\n"
    printf "' R-BOOT SET-BOOT\nS\" %s\" SAVE-SYSTEM\nBYE\n" "$tmp"
} | "$engine" "$kernel" > "$tmp.log" 2>&1
if [ ! -s "$tmp" ] || grep -qE 'Undefined word|[Uu]nderflow|[Oo]verflow|not unique|Incomplete control' "$tmp.log"; then
    echo "build-cm-image: $out not built; the build said:" >&2
    tr -d '\r' < "$tmp.log" | grep -vE '^(Redefining: |OK$|Welcome to Forth)' | grep -v '^[[:space:]]*$' | head -20 | sed 's/^/    /' >&2
    rm -rf "$tmp" "$tmp.log" "$tmp.genes.4" "$tmp.src" "$tmp.widths.4" "$tmp.edit.4" "$tmp.values.4" "$tmp.shim.4"; exit 1
fi
mv -f "$tmp" "$out"; rm -rf "$tmp.log" "$tmp.genes.4" "$tmp.src" "$tmp.widths.4" "$tmp.edit.4" "$tmp.values.4" "$tmp.shim.4"
echo "$out: $(wc -c < "$out") bytes"
