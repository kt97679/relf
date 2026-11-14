#!/bin/sh
# port/measure/cmsuite.sh RUNNER - tests/cm/run's three loops (the runtime's .4 tests, the scripts, the prompt's
# sessions) with RUNNER in place of "$E" image; prints the failures and a count
R=$1
cd "$(dirname "$0")/../.." || exit 2
export RILL3_PATH=$PWD/lib
pass=0 fail=0 t1=$(mktemp) t2=$(mktemp)
for t in tests/cm/*.4; do
    printf 'S" %s" INCLUDED\n' "$t" > $t2.4
    timeout 60 $R $t2.4 2>&1 | tr -d '\r' > $t1
    if cmp -s $t1 "${t%.4}.expected"; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL $t"; fi
done
for t in tests/cm/scripts/*.cm; do
    { timeout 60 $R "$t" 2>&1; echo "status $?"; } > $t1
    if cmp -s $t1 "${t%.cm}.expected"; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL $t"; fi
done
for t in tests/cm/prompt/*.in; do
    { timeout 60 $R < "$t" 2>&1; echo "status $?"; } > $t1
    if cmp -s $t1 "${t%.in}.expected"; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL $t"; fi
done
rm -f $t1 $t2 $t2.4
echo "$pass passed, $fail failed"
