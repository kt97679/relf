# arith-expansions-286.sh - POSIX expands parameters and command
# substitutions inside $(( )) before evaluating it (XCU 2.6.4). Until
# Iteration 286 the expression reached the evaluator as written, so
# ${#v} and $(cmd) in it were ignored and $(($v)) read rubbish. The
# suites had only ever used bare names - $((i+1)) - which always worked.
v=abcd
n=3
empty=
echo $((1 + ${#v})) $(( ${#v} )) $((${#empty}))
echo $((1 + $(echo 2))) $(( $(echo 3) * $(echo 4) ))
echo $(( 1 + `echo 2` )) $(( `echo 5` ))
echo $(($n)) $(($n + 1)) $(( $n * $n ))
echo $((n)) $((n+1)) $((n*n))
echo $((2*(3+4))) $(( (1+2) * (3+4) )) $(( ((5)) ))
echo $(( ${n} + ${#v} )) $(( ${nope:-7} )) $(( ${n:+9} ))
echo $(( 7 / 2 )) $(( -7 / 2 )) $(( -7 % 3 )) $(( 1 << 4 )) $(( 255 >> 2 ))
echo $(( 1 && 0 )) $(( 1 || 0 )) $(( !0 )) $(( ~0 )) $(( 3 > 2 ))
x=$((n+1)); echo "$x"
y=$(( $(echo 2) + ${#v} )); echo "$y"
echo "quoted: $((n+1))" '$((n+1))'
i=0; while [ $i -lt 3 ]; do i=$((i + ${#n})); done; echo $i
echo $(( 010 + 0x10 ))
