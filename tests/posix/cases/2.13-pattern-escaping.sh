# XCU 2.13.1. A quoted or backslash-escaped special pattern character
# matches itself literally.
for w in 'a*b' 'axb'; do
    case $w in
        'a*b') r=literal-star ;;
        a\*b)  r=escaped-star ;;
        a?b)   r=any-char ;;
        *)     r=none ;;
    esac
    printf '%s=%s\n' "$w" "$r"
done
