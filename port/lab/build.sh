#!/bin/sh
# port/lab/build.sh DESIGN-DIR OUT - relfsh on a forth-vm-evolution design: its engine
# DESIGN-DIR/forth and kernel image DESIGN-DIR/image.img, relf's shell sources and the port
# loaded on it, and the result saved as OUT - the design's own header, then the image body
# SAVE-BODY writes. Run from relf's top. Prints OUT's size, or the build's complaints.
set -e
d=$1 out=$2
# PROGRAM=rill3: rill3's sources in place of the shell's, as tools/build-cm-image.sh loads them
# (shell.4's character widths and edit.4 less its TAB completion cut out), R-BOOT its boot word
program=${PROGRAM:-relfsh}
hdrlen=$(python3 port/lab/header.py "$d/image.img" "$d/Makefile")
tmp=$out.tmp.$$
case $program in
relfsh) sources="shell/shell.4 shell/edit.4 shell/tree.4" boot=MAIN hooks= ;;
rill3)
    awk '/^\\ Characters. widths on screen/ {p = 1} p {print} p && /^: CHAR-COLS/ {c = 1} c && / ;$/ {exit}' shell/shell.4 > "$tmp.widths.4"
    awk '/^\\ ---- completion: TAB ----/ {skip = 1} /^\\ ---- reverse incremental history search/ {skip = 0} !skip {print}' shell/edit.4 > "$tmp.edit.4"
    sources="port/rill.4 $tmp.widths.4 cm/edit-shim.4 $tmp.edit.4 cm/values.4 cm/rt-cm.4 cm/out.4 cm/ctl.4 cm/case.4 cm/lib.4 cm/pipe.4 cm/ir.4 cm/cmc.4 cm/complete.4 cm/prompt.4"
    boot=R-BOOT
    hooks=": CM-SUFFIX ( --- c-addr u )   S\" .cm\" ;  ' CM-COMPILE IS R-COMPILE  ' CM-SUFFIX IS R-SUFFIX  ' CM-REPL IS R-REPL-D" ;;
*) echo "port/lab/build.sh: PROGRAM is relfsh or rill3" >&2; exit 2 ;;
esac
first=port/lab/nojit.4 jit=0 jitwords=
grep -q -- '-DX_JIT=1' "$d/Makefile" && first=port/lab/jit.4 jit=1 jitwords=port/lab/jitwords.4
[ $jit = 1 ] && grep -q -- '-DJITEXEC=1' "$d/Makefile" && jit=2
# MAP=1: port/measure/map.4 first, and OUT.map - each definition's offset, its defining word and its
# file, and the bytes of the strings compiled (port/measure/README.md); the image a few hundred bytes larger
{
    printf 'S" %s" INCLUDED\n' "$first"
    [ -n "$MAP" ] && printf 'S" port/measure/map.4" INCLUDED\n'
    # compile.4: variables as literals - 0 none, 1 all, 2 the kernel's (a JIT takes ours itself;
    # an interpreter's LIT64 is a byte loop)
    printf 'VARIABLE PORT-VARLIT %s PORT-VARLIT !\n' "${VARLIT:-$((jit > 0 ? 2 : 0))}"
    printf 'VARIABLE PORT-JIT %s PORT-JIT !\n' $jit                    # 0, a JIT, one with jitexec
    [ "$first" = port/lab/jit.4 ] && printf 'S" %s" %s JIT-PRISTINE\n' "$d/image.img" "$hdrlen"
    for f in port/relf.4 port/lab/compile.4 port/lab/interp.4 port/lab/again.4 port/strings.4 $jitwords port/alloc.4 port/os.4 port/kernel-io.4 port/lab/host.4 forth/pool.4 port/shadow.4 port/lab/after.4 \
             $sources port/lab/save.4; do
        [ "$f" = port/lab/save.4 ] && { [ -n "$hooks" ] && printf '%s\n' "$hooks"
            printf ': PORT-MAIN ( --- )  %s ;\n' "$boot"; }              # save.4's PORT-BOOT ends with it
        [ -n "$MAP" ] && printf '.( FILE %s) CR ' "$f"
        printf 'S" %s" INCLUDED\n' "$f"
    done
    [ -n "$MAP" ] && printf 'STR-REPORT\n'
    printf "' PORT-BOOT SET-BOOT\nS\" %s.body\" SAVE-BODY\nBYE\n" "$tmp"
} | "$d/forth" "$d/image.img" > "$tmp.log" 2>&1 || true
if [ ! -s "$tmp.body" ] || grep -qE 'Undefined word|Not found|Error|out of memory|cannot' "$tmp.log"; then
    echo "port/lab/build.sh: $out not built; the build said:" >&2
    grep -vE "^(Redefining|OK$|Welcome)" "$tmp.log" | head -${BUILD_ERRS:-20} >&2
    rm -f "$tmp.body" "$tmp.log" "$tmp.widths.4" "$tmp.edit.4"; exit 1
fi
head -c "$hdrlen" "$d/image.img" > "$out"
cat "$tmp.body" >> "$out"
[ -n "$MAP" ] && grep -E '^(MAP|FILE|STRBYTES) ' "$tmp.log" > "$out.map"
rm -f "$tmp.body" "$tmp.log" "$tmp.widths.4" "$tmp.edit.4"
wc -c < "$out"
