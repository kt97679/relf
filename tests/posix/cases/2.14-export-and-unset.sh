# XCU 2.14 export, unset. An exported variable appears in the
# environment of a child; unset removes it entirely, which is
# distinguishable from setting it to null.
v=exported
export v
sh -c 'printf "child=%s\n" "${v-UNSET}"'
unset v
sh -c 'printf "after=%s\n" "${v-UNSET}"'
n=
printf 'null=%s\n' "${n-UNSET}"
unset n
printf 'unset=%s\n' "${n-UNSET}"
