#!/bin/bash
# cache.sh BUILD XA - simulated 32 KB 4-way L1 (Cortex-A53/A7-like) per
# engine x arch, on scaled-down fn/str (the plugin is ~100x slower than
# plain qemu; miss RATES, not loop counts, are the point).
cd "$(dirname "$0")/../../.."
B=$1; X=$2; Q=${QEMU:?set QEMU}
sed 's/-lt 600/-lt 60/' tests/bench-vm/fn.sh  > /tmp/xa-fn60.sh
sed 's/-lt 400/-lt 40/' tests/bench-vm/str.sh > /tmp/xa-str40.sh
CP="dcachesize=32768,dassoc=4,dblksize=64,icachesize=32768,iassoc=4,iblksize=64,limit=1"
for a in aarch64:64 arm:32 riscv64:64; do
  n=${a%%:*}; w=${a#*:}
  [ $w = 64 ] && ci=kernel-shell.img || ci=kernel32-shell.img
  for p in "relf-old $ci" "relf-new $ci" "cv8t $B/cv8-$w.img" "spec $B/spec-$w.img"; do
    set -- $p
    for wl in fn60 str40; do
      r=$($Q/qemu-$n -plugin $Q/libcache.so,$CP -d plugin "$X/$1-$n" "$2" \
          /tmp/xa-$wl.sh 2>&1 | awk '/^0 /{print "dacc="$2, "dmiss="$3}')
      echo "$n $1 $wl $r"
    done
  done
done
