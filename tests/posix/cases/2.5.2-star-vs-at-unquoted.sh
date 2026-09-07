# XCU 2.5.2. Unquoted, both expand to separate fields; the difference
# only shows when quoted, where "$*" joins with the first IFS
# character and "$@" keeps one field per parameter.
set -- 'a b' c
for w in $*; do printf '[%s]' "$w"; done; printf '\n'
for w in $@; do printf '[%s]' "$w"; done; printf '\n'
for w in "$*"; do printf '[%s]' "$w"; done; printf '\n'
for w in "$@"; do printf '[%s]' "$w"; done; printf '\n'
