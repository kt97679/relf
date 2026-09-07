# XCU 2.14 break, continue. Both take an optional count naming how
# many enclosing loops to act on.
for i in 1 2 3 4; do
    [ "$i" = 3 ] && break
    printf 'i=%s\n' "$i"
done
for i in 1 2 3; do
    [ "$i" = 2 ] && continue
    printf 'j=%s\n' "$i"
done
for i in 1 2; do
    for k in a b; do
        [ "$k" = b ] && continue 2
        printf 'pair=%s%s\n' "$i" "$k"
    done
done
