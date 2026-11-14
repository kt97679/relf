#!/bin/sh
# port/measure/scaled.sh N DIR - tests/bench-vm's five workloads with every loop bound times N, into DIR
# (as tools/bench-vm.py's SCALE does), and DIR/start.sh (one command: a start, for measure.py)
n=$1 dir=$2; mkdir -p "$dir"
for w in loop fn str arith realistic; do
    sed -E 's/-lt ([0-9]+)/-lt \1*'"$n"'/' "$(dirname "$0")/../../tests/bench-vm/$w.sh" | awk '{ while (match($0, /-lt [0-9]+\*[0-9]+/)) { s = substr($0, RSTART + 4, RLENGTH - 4); split(s, p, "*"); $0 = substr($0, 1, RSTART + 3) p[1] * p[2] substr($0, RSTART + RLENGTH) } print }' > "$dir/$w.sh"
done
echo true > "$dir/start.sh"
