#!/bin/sh
# port/lab/build.sh DESIGN-DIR OUT - relfsh on a forth-vm-evolution design: its engine
# DESIGN-DIR/forth and kernel image DESIGN-DIR/image.img, relf's shell sources and the port
# loaded on it, and the result saved as OUT - the design's own header, then the image body
# SAVE-BODY writes. Run from relf's top. Prints OUT's size, or the build's complaints.
set -e
d=$1 out=$2
hdrlen=$(python3 port/lab/header.py "$d/image.img" "$d/Makefile")
tmp=$out.tmp.$$
first=port/lab/nojit.4 jit=0 jitwords=
grep -q -- '-DX_JIT=1' "$d/Makefile" && first=port/lab/jit.4 jit=1 jitwords=port/lab/jitwords.4
[ $jit = 1 ] && grep -q -- '-DJITEXEC=1' "$d/Makefile" && jit=2
{
    printf 'S" %s" INCLUDED\n' "$first"
    # compile.4: variables as literals - 0 none, 1 all, 2 the kernel's (a JIT takes ours itself;
    # an interpreter's LIT64 is a byte loop)
    printf 'VARIABLE PORT-VARLIT %s PORT-VARLIT !\n' "${VARLIT:-$((jit > 0 ? 2 : 0))}"
    printf 'VARIABLE PORT-JIT %s PORT-JIT !\n' $jit                    # 0, a JIT, one with jitexec
    [ "$first" = port/lab/jit.4 ] && printf 'S" %s" %s JIT-PRISTINE\n' "$d/image.img" "$hdrlen"
    for f in port/relf.4 port/lab/compile.4 port/lab/interp.4 port/lab/again.4 port/strings.4 $jitwords port/alloc.4 port/os.4 port/kernel-io.4 port/lab/host.4 forth/pool.4 port/shadow.4 port/lab/after.4 \
             shell/shell.4 shell/edit.4 shell/tree.4 port/lab/save.4; do printf 'S" %s" INCLUDED\n' "$f"; done
    printf "' PORT-BOOT SET-BOOT\nS\" %s.body\" SAVE-BODY\nBYE\n" "$tmp"
} | "$d/forth" "$d/image.img" > "$tmp.log" 2>&1 || true
if [ ! -s "$tmp.body" ] || grep -qE 'Undefined word|Not found|Error|out of memory|cannot' "$tmp.log"; then
    echo "port/lab/build.sh: $out not built; the build said:" >&2
    grep -vE '^(Redefining|OK$|Welcome)' "$tmp.log" | head -20 >&2
    rm -f "$tmp.body" "$tmp.log"; exit 1
fi
head -c "$hdrlen" "$d/image.img" > "$out"
cat "$tmp.body" >> "$out"
rm -f "$tmp.body" "$tmp.log"
wc -c < "$out"
