# numbers past 62 bits (837): rill2's tagged arithmetic wrapped without a word - 2^62-1 + 1 was -2^62,
# doubled it was -2 - since 831; now the overflow is looked at, and the number boxed
big = 4611686018427387903
print(big + 1, big * 2, -big - 2, big + 1 > big)
print(3037000499 * 3037000499, 9223372036854775807 - 1)
print(int("9223372036854775807"), -9223372036854775807 - 1)
l = [big + 1]
print(l[0] - 1 == big)
