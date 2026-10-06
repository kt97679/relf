#!/bin/sh
# tools/intrfuzz-stress.sh [ROUNDS] [JOBS] - the interrupt fuzzer under parallel load (Iteration 713)
#
# For GOALS.md 8c: intrfuzz case 4 (seed 598) gave no answer once, on
# fury, inside a full verify - where the fuzzer and the shell ran at once
# on different cores. A one-CPU machine cannot show that (711-712 tried),
# so this runs JOBS fuzzers at once, ROUNDS times, on each shell: the
# first job of each round on seed 598, the rest on fresh seeds. Every
# failure is printed with intrfuzz's report - the failed line's status
# among it, 130 if a ^C stopped it, 0 if it ran and printed nothing.
# The report goes to bench/reports/, to send back with the pack.
cd "$(dirname "$0")/.." || exit 2
ROUNDS=${1:-5}
JOBS=${2:-$(nproc)}
out=bench/reports/intrfuzz-stress-$(hostname)-$(date -u +%Y%m%dT%H%MZ).txt
tmp=$(mktemp -d)
{
echo "intrfuzz stress, $(date -u '+%Y-%m-%d %H:%M UTC'), $(git log --oneline -1 | cut -c1-72)"
echo "cpu: $(nproc) cores; ROUNDS=$ROUNDS JOBS=$JOBS; 20 cases a run"
for sh in relfsh relfshasm64 relfsh-native; do
  [ -x "./$sh" ] || { echo "$sh: not built, skipped"; continue; }
  runs=0; bad=0; r=1
  while [ "$r" -le "$ROUNDS" ]; do
    j=1; pids=""
    while [ "$j" -le "$JOBS" ]; do
      if [ "$j" -eq 1 ]; then seed=598; else seed=$((598 + (r - 1) * JOBS + j - 1)); fi
      echo "$seed" > "$tmp/seed.$j"
      (timeout 600 python3 tools/intrfuzz.py 20 "$seed" "./$sh" > "$tmp/out.$j" 2>&1) &
      pids="$pids $!"; j=$((j + 1))
    done
    wait $pids
    j=1
    while [ "$j" -le "$JOBS" ]; do
      runs=$((runs + 1))
      f=$(sed -n 's/.*cases, \([0-9]*\) failures.*/\1/p' "$tmp/out.$j")
      if [ "$f" != "0" ]; then
        bad=$((bad + 1))
        echo "--- $sh, round $r, seed $(cat "$tmp/seed.$j"): ${f:-no summary (timed out?)} failures"
        grep -A14 '^FAIL' "$tmp/out.$j" | head -45
      fi
      j=$((j + 1))
    done
    r=$((r + 1))
  done
  echo "$sh: $runs runs ($((runs * 20)) cases), $bad with failures"
done
} 2>&1 | tee "$out"
rm -rf "$tmp"
echo "report: $out"
