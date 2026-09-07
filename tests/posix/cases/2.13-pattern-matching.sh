# XCU 2.13 Pattern Matching Notation, exercised through 'case' where
# no filesystem is involved. '*' matches any string including empty,
# '?' exactly one character, and a bracket expression one from the set.
for w in abc a '' xbc ab; do
    case $w in
        a*c) r=star ;;
        a?)  r=question ;;
        [ax]bc) r=bracket ;;
        '')  r=empty ;;
        *)   r=none ;;
    esac
    printf '%s=%s\n' "${w:-EMPTY}" "$r"
done
