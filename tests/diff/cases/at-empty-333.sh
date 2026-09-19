# at-empty-333.sh - entry 6 of tests/from-others/CATALOGUE.md: "$@" with
# no positional parameters produces no field, but a quoted empty string
# beside it still produces one, so `"$@"""` is a single empty argument.
# This shell dropped the whole word (Iteration 333).
set --
for a in "$@"; do echo "bare:[$a]"; done
echo "after-bare"
for a in "$@"""; do echo "trailing:[$a]"; done
for a in """$@"; do echo "leading:[$a]"; done
for a in $@; do echo "unquoted:[$a]"; done
for a in "${@}"; do echo "braced:[$a]"; done
for a in x"$@"; do echo "with-text:[$a]"; done
for a in "$@"x; do echo "text-after:[$a]"; done
f() { echo "count=$#"; }
f "$@"
f "$@"""
f """$@"
f "" "$@"
set -- p q
for a in "$@"; do echo "two:[$a]"; done
for a in "$@"""; do echo "two-trailing:[$a]"; done
for a in x"$@"y; do echo "joined:[$a]"; done
f "$@"
set -- ""
for a in "$@"; do echo "one-empty:[$a]"; done
f "$@"
