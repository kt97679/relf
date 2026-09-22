# A word that is nothing but "$@" - however many of them - is no field
# at all when there are no positional parameters (Iteration 441, yash
# param-p.tst:570); beside anything else, even a quoted empty string, it
# is one.
bracket() { printf '[%s]' "$@"; echo; }
bracket "$@"
bracket "$@""$@" - "$@""$@""$@"
bracket "=$@="
null=
bracket "$null""$@"
bracket "$@""$null"
bracket "$null""$@""$null" - "$null""$null""$@" - "$@""$null""$null"
bracket "$null""$@$null" - "$null""$null$@" - "$@$null""$null" - "$null$@""$null"
set a
bracket "$@""$@"
set a 'b  b' cc
bracket "$@""$@"
