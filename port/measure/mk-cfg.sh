#!/bin/sh
# port/measure/mk-cfg.sh PROGRAM LAB OUT > CFG - tools/bench-vm.py's config (name|cwd|command) for every
# build of PROGRAM (relfsh or rill3): relf's own first (the base), then each design in LAB (built, an
# engine LAB/NAME/forth) with OUT/NAME.img (port/lab/build.sh's), and gforth's OUT/relfsh-gforth.fi.
# Paths absolute. Run from relf's top, its engines and images built (make; for rill3-native see README).
R=$(pwd)
p=$1 lab=$2 out=$3
designs="fastest-x86-64 fastest-x86-32 best-all-round small-jit portable-fastest portable-arm portable-knee portable-small least-memory smallest"
case $p in
relfsh)
    for e in relfsh64 relfsh32 relfshasm64 relfsh-native; do echo "$e|/tmp|$R/$e {w}"; done
    for d in $designs; do echo "$d|/tmp|$lab/$d/forth $out/$d.img {w}"; done
    echo "gforth-fast|/tmp|/usr/bin/gforth-fast --appl-image $out/relfsh-gforth.fi {w}"
    echo "gforth|/tmp|/usr/bin/gforth --appl-image $out/relfsh-gforth.fi {w}" ;;
rill3)
    echo "relf64|/tmp|RILL3_PATH=$R/lib $R/relf64 $R/kernel64-cm.img {w}"
    echo "relfasm64|/tmp|RILL3_PATH=$R/lib $R/relfasm64 $R/kernel64-cm.img {w}"
    [ -x "$out/rill3-native" ] && echo "rill3-native|/tmp|RILL3_PATH=$R/lib $out/rill3-native {w}"
    for d in $designs; do echo "$d|/tmp|RILL3_PATH=$R/lib $lab/$d/forth $out/$d.img {w}"; done ;;
esac
