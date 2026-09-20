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
# `&&` and `||` evaluate their right operand only when they must, so an
# error or an assignment on the dead side never happens (Iteration 380).
x=0; echo "and-short=$((x && 1/0))"
x=1; echo "or-short=$((x || 1/0))"
y=5; echo "and-noassign=$((0 && (y=9))) $y"
y=5; echo "or-noassign=$((1 || (y=9))) $y"
y=5; echo "and-assign=$((1 && (y=9))) $y"
y=5; echo "or-assign=$((0 || (y=9))) $y"
echo "table=$((1 && 1))$((1 && 0))$((0 && 1))$((0 && 0))$((1 || 1))$((1 || 0))$((0 || 1))$((0 || 0))"
echo "nested=$((1 && 1 && 0 || 1))"
# Three more from yash's arith-p.tst (Iteration 380): a value with a
# leading `+` is a number, `>>` on a negative is an ARITHMETIC shift,
# and the bitwise compound assignments exist.
p=+1; m=-1; echo "signs=$((p)) $((m))"
echo "arshift=$((-14>>3)) $((14>>3)) $((-1>>1)) $((-8>>2)) $((0>>0))"
echo "lshift=$((3<<2)) $((5<<3)) $((1<<0))"
g=7;  echo "shl-assign=$((g<<=2)) $g"
h=30; echo "shr-assign=$((h>>=2)) $h"
i=3;  echo "and-assign=$((i&=5)) $i"
j=3;  echo "xor-assign=$((j^=5)) $j"
k=3;  echo "or-assign=$((k|=5)) $k"
x=2;  echo "not-an-assignment=$((x<=3)) $x"
y=8;  echo "still-compares=$((y>=8)) $y"
