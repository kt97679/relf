#!/bin/sh
# tools/selfhost-check.sh [SHELL] - relf builds itself with no compiler,
# assembler, linker, make or Python (Iteration 958).
#
# From the repository's top, after `make relfasm64 relfshasm64`. The seed is
# what any build starts from: the relfasm64 binary and the two committed
# kernels (forth/kernel64.img, kernel32.img - SELF-HOSTING.md). In a scratch
# copy of the tracked sources, with a PATH of POSIX utilities alone, relfasm64:
#
#   1. writes the engine's opcode tables (tools/gen-opcodes.sh, awk);
#   2. assembles itself from engine/relfasm64.4 (gen 2), and gen 2 itself
#      again (gen 3);
#   3. cross-compiles both kernels, 8- and 4-byte cells (forth/cross.4);
#   4. builds the shell image and rill3's image from their sources;
#   5. makes the single-file shell (tools/embed.sh);
#
# and each result must be the bytes `make` built with the C engine (and the
# committed kernels, for 3). SHELL runs the build scripts: /bin/sh unless
# given - give ./relfshasm64 and relfsh builds relf. Prints one line per step
# and `selfhost: N of N reproduce`; exits 1 if any differs.
#
# Not covered, by their nature: relf64 and relf32 are C (engine/cv8.c) and
# need a C compiler; kernel32-shell.img is the shell loaded into a running
# 32-bit system, so it needs relf32. The native shell's build runs
# tools/gen-native-os.py (Python), so it is reported, not built here.
set -u
cd "$(dirname "$0")/.." || exit 2
top=$PWD
shell=${1:-/bin/sh}
case $shell in /*) ;; *) shell=$top/${shell#./} ;; esac
for f in relfasm64 relfshasm64 kernel64-shell.img kernel64-cm.img; do
    [ -f "$f" ] || { echo "selfhost: no ./$f - run make all relfasm64 relfshasm64 first" >&2; exit 2; }
done
d=$(mktemp -d) || exit 2
trap 'rm -rf "$d"' EXIT
# the PATH: POSIX utilities and nothing else
mkdir "$d/bin"
for u in awk cat chmod cmp cp cut diff dirname env grep head ls mkdir mktemp mv rm sed sort tail tr wc; do
    p=$(command -v "$u") || { echo "selfhost: no $u on this machine" >&2; exit 2; }
    ln -s "$p" "$d/bin/$u"
done
ln -s "$shell" "$d/bin/sh"
for t in cc gcc as ld make python3 objcopy; do
    [ -e "$d/bin/$t" ] && { echo "selfhost: $t is on the sandbox's PATH" >&2; exit 2; }
done
# the tracked sources, and the seed: the engine binary and the kernels
mkdir "$d/src"
git ls-files -z | (cd "$top" && xargs -0 tar cf -) | (cd "$d/src" && tar xf -)
cp relfasm64 "$d/seed-relfasm64"
pass=0 all=0
step() {    # step NAME BUILT EXPECTED
    all=$((all + 1))
    if [ -f "$2" ] && cmp -s "$2" "$3"; then
        pass=$((pass + 1)); printf 'selfhost: %-26s reproduces (%s bytes)\n' "$1" "$(wc -c < "$2" | tr -d ' ')"
    elif [ -f "$2" ]; then printf 'selfhost: %-26s DIFFERS\n' "$1"
    else printf 'selfhost: %-26s not built\n' "$1"; fi
}
run() { env -i PATH="$d/bin" HOME="$d" "$shell" -c "cd '$d/src' && $1"; }
run "rm -f engine/relfasm-ops.4 engine/relfasm-consts.4 &&
     sh tools/gen-opcodes.sh --forth-ops > engine/relfasm-ops.4 &&
     sh tools/gen-opcodes.sh --forth-consts > engine/relfasm-consts.4" > "$d/ops.log" 2>&1
step engine/relfasm-ops.4 "$d/src/engine/relfasm-ops.4" engine/relfasm-ops.4
step engine/relfasm-consts.4 "$d/src/engine/relfasm-consts.4" engine/relfasm-consts.4
run "'$d/seed-relfasm64' forth/kernel64.img < engine/relfasm64.4 && mv relfasm64.forth relfasm64" > "$d/gen2.log" 2>&1
step "relfasm64 (gen 2)" "$d/src/relfasm64" relfasm64
run "./relfasm64 forth/kernel64.img < engine/relfasm64.4 && mv relfasm64.forth relfasm64-gen3" > "$d/gen3.log" 2>&1
step "relfasm64 (gen 3)" "$d/src/relfasm64-gen3" relfasm64
for bytes in 8 4; do
    case $bytes in 8) img=kernel64.img ;; 4) img=kernel32.img ;; esac
    run "mkdir k$bytes && cp forth/extend.4 forth/cross.4 forth/cross-core.4 forth/kernel.4 forth/kernel64.img relfasm64 k$bytes/ &&
         { [ $bytes = 8 ] || sed -i 's/^8 TARGET-CELL-BYTES !\$/$bytes TARGET-CELL-BYTES !/' k$bytes/cross.4; } &&
         cd k$bytes && printf 'S\" extend.4\" INCLUDED\nS\" cross.4\" INCLUDED\nBYE\n' | ./relfasm64 kernel64.img" > "$d/k$bytes.log" 2>&1
    step "forth/$img" "$d/src/k$bytes/built.img" "forth/$img"
done
srcs=$(sed -n 's/^SHELL_SOURCES *= *//p' Makefile)
run "sh tools/build-shell-image.sh ./relfasm64 forth/kernel64.img kernel64-shell.img $srcs" > "$d/shell.log" 2>&1
step kernel64-shell.img "$d/src/kernel64-shell.img" kernel64-shell.img
run "sh tools/build-cm-image.sh ./relfasm64 forth/kernel64.img kernel64-cm.img" > "$d/cm.log" 2>&1
step kernel64-cm.img "$d/src/kernel64-cm.img" kernel64-cm.img
run "sh tools/embed.sh ./relfasm64 kernel64-shell.img relfshasm64" > "$d/embed.log" 2>&1
step relfshasm64 "$d/src/relfshasm64" relfshasm64
# the rebuilt shell runs a script
all=$((all + 1))
if [ "$(env -i PATH="$d/bin" "$d/src/relfshasm64" -c 'i=0; while [ $i -lt 3 ]; do i=$((i + 1)); done; echo ok $i' 2>&1)" = "ok 3" ]
then pass=$((pass + 1)); echo "selfhost: the rebuilt relfshasm64     runs"
else echo "selfhost: the rebuilt relfshasm64     does not run"; fi
echo "selfhost: not here - relf64, relf32 (C), kernel32-shell.img (relf32), relfsh-native (tools/gen-native-os.py, Python)"
echo "selfhost: $pass of $all reproduce (sh: $(basename "$shell"))"
[ "$pass" = "$all" ]
