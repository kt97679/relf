# ifs-fields-358.sh - unquoted "$*" and "$@" make one field per
# positional parameter, whatever IFS holds; quoted "$*" joins with IFS's
# first character, or with nothing when IFS is set and empty; and inside
# an assignment nothing is split, so both forms join. This shell emitted
# a space between parameters and left the splitting to IFS, which only
# worked while IFS contained a space (Iteration 358).
set -- abc "d e"
IFS=""
for a in $*; do echo "empty-ifs-star:[$a]"; done
for a in $@; do echo "empty-ifs-at:[$a]"; done
for a in "$@"; do echo "empty-ifs-quoted-at:[$a]"; done
v=$*; echo "empty-ifs-assign-star:[$v]"
# `v="$@"` with IFS set empty is left out: bash joins with a space,
# dash and this shell join with nothing, and busybox's own suite notes
# the same split between them.
IFS=:
for a in $*; do echo "colon-star:[$a]"; done
for a in "$@"; do echo "colon-quoted-at:[$a]"; done
v="$*"; echo "colon-assign-quoted-star:[$v]"
v=$*; echo "colon-assign-star:[$v]"
unset IFS
for a in $*; do echo "default-star:[$a]"; done
v="$@"; echo "default-assign-quoted-at:[$v]"
v="$*"; echo "default-assign-quoted-star:[$v]"
set -- one
for a in $*; do echo "single:[$a]"; done
set --
for a in $*; do echo "none:[$a]"; done
echo "done"
