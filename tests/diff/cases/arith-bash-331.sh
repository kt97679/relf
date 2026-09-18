# arith-bash-331.sh - arithmetic behaviour established by asking bash and
# dash directly, from the areas bash's own suite covers. Written from
# entries 7 and 8 of tests/from-others/CATALOGUE.md.
#
# This case matches BASH: dash rejects ++, -- and base#digits outright,
# where bash implements them and this shell now does too. What it
# replaces is worse than either - the operators parsed and silently
# assigned nothing.
echo "bases: $((2#101)) $((16#ff)) $((8#17)) $((36#z)) $((10#42))"
echo "prefixes: $((0x10)) $((0X10)) $((010)) $((42))"
echo "sum: $((2#101 + 16#0f))"
a=5; echo "post-inc: $((a++)) $a"
a=5; echo "pre-inc: $((++a)) $a"
a=5; echo "post-dec: $((a--)) $a"
a=5; echo "pre-dec: $((--a)) $a"
a=-3; echo "negative: $((a++)) $a"
a=5; echo "twice: $((a++)) $((a++)) $a"
a=5; echo "untaken: $((1?2:a++)) $a"
a=5; echo "taken: $((0?2:a++)) $a"
echo "signs: $((3 - -2)) $((- -2)) $((3 + +2))"
a=1; echo "spaced: $((a + +2))"
i=0; while [ $i -lt 3 ]; do i=$((i+1)); done; echo "loop: $i"
a=5; b=$((a++ + 1)); echo "expr: $b $a"
