#!/bin/sh
# tools/build-cm-image.sh [ENGINE] [KERNEL] [OUT] - the command model's image (863, docs/COMMAND-MODEL.md).
#
# The kernel, the Forth libraries, the runtime (rill/rt.4 - Rill's, the command model's since 871)
# and relfsh's line editor, its TAB completion cut out, with cm/edit-shim.4; then cm/values.4, cm's runtime
# (rt-cm, out, ctl, lib, pipe), cm/cmc.4 - the front end - and cm/prompt.4. A script whose name ends .cm is
# read, made Forth by cm/cmc.4 and run: ./relf64 kernel64-cm.img script.cm; with no script, the prompt.
# (Built at 863 as rill2's image with its language replaced; its own since Rill 2 was retired, 871.)
cd "$(dirname "$0")/.." || exit 2
engine=${1:-./relf64} kernel=${2:-forth/kernel64.img} out=${3:-kernel64-cm.img}
tmp=$out.tmp.$$
awk '/^\\ Characters. widths on screen/ {p = 1} p {print} p && /^: CHAR-COLS/ {c = 1} c && / ;$/ {exit}' shell/shell.4 > "$tmp.widths.4"
awk '/^\\ ---- completion: TAB ----/ {skip = 1} /^\\ ---- reverse incremental history search/ {skip = 0} !skip {print}' shell/edit.4 > "$tmp.edit.4"
{
    for f in forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 rill/rt.4 "$tmp.widths.4" cm/edit-shim.4 "$tmp.edit.4" cm/values.4 cm/rt-cm.4 cm/out.4 cm/ctl.4 cm/case.4 cm/lib.4 cm/pipe.4 cm/cmc.4 cm/complete.4 cm/prompt.4; do
        printf 'S" %s" INCLUDED\n' "$f"
    done
    printf ": CM-SUFFIX ( --- c-addr u )   S\" .cm\" ;  ' CM-COMPILE IS R-COMPILE  ' CM-SUFFIX IS R-SUFFIX  ' CM-REPL IS R-REPL-D\n"
    printf "' R-BOOT SET-BOOT\nS\" %s\" SAVE-SYSTEM\nBYE\n" "$tmp"
} | "$engine" "$kernel" > "$tmp.log" 2>&1
if [ ! -s "$tmp" ] || grep -qE 'Undefined word|[Uu]nderflow|[Oo]verflow|not unique|Incomplete control' "$tmp.log"; then
    echo "build-cm-image: $out not built; the build said:" >&2
    tr -d '\r' < "$tmp.log" | grep -vE '^(Redefining: |OK$|Welcome to Forth)' | grep -v '^[[:space:]]*$' | head -20 | sed 's/^/    /' >&2
    rm -rf "$tmp" "$tmp.log" "$tmp.widths.4" "$tmp.edit.4" "$tmp.values.4"; exit 1
fi
mv -f "$tmp" "$out"; rm -rf "$tmp.log" "$tmp.widths.4" "$tmp.edit.4" "$tmp.values.4"
echo "$out: $(wc -c < "$out") bytes"
