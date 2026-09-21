# arith-audit-287.sh - the arithmetic evaluator, operator by operator
# (Iteration 287). Written after 286 found three faults in one corner:
# every operator POSIX lists, precedence, the constant forms, the
# assignment forms, and the ternary - which was missing entirely.
# The comma operator is bash-compatible here; dash rejects it, so the
# expectations come from bash for that line only (marked).
n=7; z=0; neg=-3
echo A1 $((1+2)) $((7-9)) $((3*4)) $((7/2)) $((7%2)) $((-7/2)) $((-7%2))
echo A2 $((1<2)) $((2<=2)) $((3>4)) $((4>=4)) $((5==5)) $((5!=5))
echo A3 $((1&&0)) $((0||3)) $((!5)) $((!0)) $((~5)) $((-~5))
echo A4 $((6&3)) $((6|3)) $((6^3)) $((1<<3)) $((64>>3))
echo A5 $((2+3*4)) $(((2+3)*4)) $((2*3%4)) $((1<<2+1)) $((~0&255))
echo A6 $((010)) $((0x1f)) $((0X1F)) $((0)) $((00))
echo A7 $((n)) $((n+1)) $((z||n)) $((n>0?1:2))
echo A8 $((1?2:3)) $((0?2:3)) $((n>3?n*2:n/2))
echo A9 $((n+=1)) $n $((n-=2)) $n $((n*=3)) $n
echo A10 $((n/=2)) $n $((n%=4)) $n
echo A11 $((1,2)) $((z=5)) $z
echo A12 $(( +5 )) $(( - -5 )) $(( !!5 ))
# A13 asked what happens one past 2^31, which is a question about the
# CELL rather than about arithmetic: an 8-byte build answers
# 2147483648, a 4-byte build wraps, and both are right for their width
# (Iteration 403 - an ARMv7 board). Asked of the shell's own boundary
# instead, so the answer is the same everywhere: one past the largest
# value is negative, and one before the smallest is positive.
big=1; while [ $((big*2)) -gt 0 ]; do big=$((big*2)); done
echo A13 $([ $((big*2-1+1)) -lt 0 ] && echo wraps-negative) \
        $([ $((0-big*2+1-1)) -gt 0 ] && echo wraps-positive)
echo A14 "$((1+1))" '$((1+1))'
# A15, a division by zero, was here; it ends the shell now, as POSIX and
# dash have it, where bash carries on - see tests/shell/run-special-error
# and GOALS.md (Iteration 427).
