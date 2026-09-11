#!/bin/bash
# insns.sh BUILD XA - guest instructions per engine x workload x arch.
# Needs QEMU=<qemu build dir with plugins>. One line per run.
cd "$(dirname "$0")/../../.."
B=$1; X=$2; Q=${QEMU:?set QEMU to the plugin-enabled qemu build dir}
for a in aarch64:64 arm:32 riscv64:64; do
  n=${a%%:*}; w=${a#*:}
  [ $w = 64 ] && ci=kernel-shell.img || ci=kernel32-shell.img
  for p in "relf-old $ci" "relf-new $ci" "cv8t $B/cv8-$w.img" "spec $B/spec-$w.img"; do
    set -- $p
    for wl in start loop fn str arith; do
      [ $wl = start ] && args="-c true" || args="tests/bench-vm/$wl.sh"
      ins=$($Q/qemu-$n -plugin $Q/tests/plugin/libinsn.so -d plugin \
            "$X/$1-$n" "$2" $args 2>&1 | awk '/total insns/{print $3}')
      echo "$n $1 $wl insns=$ins"
    done
  done
done
