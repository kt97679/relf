#!/bin/sh
# tools/native-self-build.sh [HOST] - N4 (docs/NATIVE.md 5, Iteration 670):
# the native kernel's own build script, forth/native-kernel.4, run by a
# native kernel - HOST, ./native-kernel unless given - instead of by CV8,
# and its output compared with ./native-kernel, which `make native-kernel`
# built hosted by CV8. Prints one line: `same`, `differ: N bytes`, or
# `not built: ...`. From the repository's top, after `make native-kernel`.
#
# It builds in a scratch directory - the script writes ./native-kernel
# and ./native-kernel.map where it runs - with forth/ engine/ tools/
# linked in and the three inputs the Makefile generates made again there.
set -u
cd "$(dirname "$0")/.." || exit 1
host=${1:-./native-kernel}
[ -x native-kernel ] || { echo "not built: no ./native-kernel to compare with (make native-kernel)"; exit 1; }
[ -x "$host" ] || { echo "not built: no host $host"; exit 1; }
d=$(mktemp -d) || exit 1
trap 'rm -rf "$d"' EXIT
cp "$host" "$d/host"
for x in forth engine tools; do ln -s "$PWD/$x" "$d/$x"; done
(
    cd "$d" || exit 1
    python3 tools/gen-native-os.py native-os.4 > /dev/null 2>&1 || exit 1
    sed '/^\\ PART 10: TOP LEVEL/,$d' forth/kernel.4 > native-kcut9.4 && echo END-CROSS >> native-kcut9.4
    { echo CROSS-COMPILE; sed -n '/^\\ PART 10: TOP LEVEL/,$p' forth/kernel.4; } > native-kcut10.4
    timeout 120 ./host < forth/native-kernel.4 > build.log 2>&1
) || { echo "not built: the inputs could not be made"; exit 1; }
log=$(tr -d '\r' < "$d/build.log")
if [ ! -s "$d/native-kernel" ] || printf '%s\n' "$log" | grep -q 'Undefined word\|native\(-cross\)*: \|asm64:' \
   || ! printf '%s\n' "$log" | grep -q 'forward calls waiting: *$'; then
    echo "not built: $(printf '%s\n' "$log" | grep -v -e '^OK$' -e '^Redefining' -e '^$' | tail -1)"; exit 1
fi
if cmp -s "$d/native-kernel" native-kernel && cmp -s "$d/native-kernel.map" native-kernel.map; then
    echo same
else
    echo "differ: $(cmp -l "$d/native-kernel" native-kernel 2>/dev/null | wc -l | tr -d ' ') bytes"
    exit 1
fi
