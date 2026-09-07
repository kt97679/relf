# XCU 2.9.4.2 The for Loop.
#
# "for name do ... done", with no "in" word list, iterates over the
# positional parameters - it is defined to behave as though the word
# list were "$@". Split out from the field-splitting cases in
# Iteration 147, where its absence was being read as a splitting bug.
set -- alpha beta gamma
for w
do
    printf '[%s]' "$w"
done
printf '\n'
for w; do printf '{%s}' "$w"; done
printf '\n'
