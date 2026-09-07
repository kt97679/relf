# XCU 2.6.5. Field splitting applies to the results of unquoted
# expansions only.
v='a b c'
set -- $v
printf 'unquoted %s\n' "$#"
set -- "$v"
printf 'quoted %s\n' "$#"
