# special-param-339.sh - special parameters with an operator. `${$+set}`
# and `${?+set}` read as unset until Iteration 339, because the operator
# forms looked the name up as an ordinary variable, and `${#+set}` was
# parsed as the length of `+set`.
echo "pid-set=[${$+SET}]"
echo "status-set=[${?+SET}]"
echo "count-set=[${#+SET}]"
echo "count=[${#}]"
set -- a b c
echo "count-three=[${#}] still-set=[${#+YES}]"
echo "first=[${1+YES}] fourth=[${4+YES}]"
x=abc; echo "length=[${#x}]"
echo "status-default=[${?-D}]"
false; echo "status-after-false=[${?+S}] value=[$?]"
true; echo "status-alt=[${?:+NONZERO}]"
false; echo "status-alt2=[${?:+NONZERO}]"
echo "dollar-numeric=[$(case ${$} in *[!0-9]*) echo no;; *) echo yes;; esac)]"
u=; echo "empty-plus=[${u+SET}] empty-colon-plus=[${u:+SET}]"
unset v; echo "unset-plus=[${v+SET}]"
