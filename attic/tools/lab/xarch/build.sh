#!/bin/bash
# build.sh BUILD OUT - cross-compile the four engines for AArch64, ARMv7
# (armhf) and RISC-V 64, statically, and smoke-test each against dash
# under qemu. BUILD is a tools/lab/build-cv8.sh output directory.
set -e
cd "$(dirname "$0")/../../.."
B=$1; X=$2; mkdir -p "$X"
HOT='+,=,!,@,LSHIFT,RSHIFT,C@,C!,AND,OR,XOR,LIT,<,U<,OVER,DROP,DUP,SWAP,ROT,>R,R>,R@,NEGATE'
git show token16:relf.c > "$X/relf-old.c" 2>/dev/null || cp relf.c "$X/relf-old.c"
cp relf.c "$X/relf-new.c"
cp tools/lab/vm-lab.c "$X/"
python3 tools/lab/gen-tos.py "$X/vm-lab.c" > "$X/vm-lab-tos.c"
python3 tools/lab/gen-fold.py "$X/vm-lab-tos.c" "$HOT" v8 > /dev/null
cd "$X"
for a in aarch64:aarch64-linux-gnu:3 arm:arm-linux-gnueabihf:2 riscv64:riscv64-linux-gnu:3; do
  IFS=: read n cc sc <<< "$a"
  C="$cc-gcc -O2 -static -w"
  $C -o relf-old-$n relf-old.c 2>/dev/null
  $C -o relf-new-$n relf-new.c 2>/dev/null
  $C -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=$sc -o cv8t-$n vm-lab-tos.c 2>/dev/null
  $C -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=$sc -DSPEC=1 -DSHAREDCALL=1 \
     -o spec-$n vm-lab-tos.c 2>/dev/null
done
cd - > /dev/null
want=$(for w in fn str arith; do dash tests/bench-vm/$w.sh; done)
for a in aarch64:64 arm:32 riscv64:64; do
  n=${a%%:*}; w=${a#*:}
  [ $w = 64 ] && ci=kernel-shell.img || ci=kernel32-shell.img
  for p in "relf-old $ci" "relf-new $ci" "cv8t $B/cv8-$w.img" "spec $B/spec-$w.img"; do
    set -- $p
    got=$(for wl in fn str arith; do qemu-$n "$X/$1-$n" "$2" tests/bench-vm/$wl.sh; done)
    [ "$got" = "$want" ] && echo "ok    $1-$n" || { echo "WRONG $1-$n"; exit 1; }
  done
done
