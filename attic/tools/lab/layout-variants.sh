#!/bin/sh
# tools/lab/layout-variants.sh SRC OUTPREFIX [CFLAGS...] - build SRC four
# times with different code-alignment flags, as OUTPREFIX-1..4.
#
# Why: the same engine moves +/-4-5% with alignment alone (CV8.md 2.2).
# Compare DESIGNS by the range over these four builds, never by one.
src=$1; out=$2; shift 2
i=0
for fl in "" "-falign-labels=32" "-O3" "-falign-jumps=32 -falign-labels=8"; do
    i=$((i + 1))
    cc -O2 $fl "$@" -o "$out-$i" "$src" || exit 1
done
