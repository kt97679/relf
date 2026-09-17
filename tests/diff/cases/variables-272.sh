# variables-272.sh - the hashed variable table (Iteration 272): 300 variables
# made, a third unset, one made again, a local one, exported and unset ones.
i=0
while [ $i -lt 300 ]; do eval "v_$i=val_$i"; i=$((i+1)); done
echo "$v_0 $v_150 $v_299"
i=0
while [ $i -lt 300 ]; do if [ $((i % 3)) = 0 ]; then unset "v_$i"; fi; i=$((i+1)); done
echo "[${v_0-gone}] [$v_1] [${v_150-gone}] [$v_299] [${v_297-gone}]"
v_0=back; echo "$v_0"
f() { local v_1=local-one; echo "in f: $v_1"; }
f; echo "after: $v_1"
export E1=exported; sh -c 'echo "child: $E1"'
unset E1; sh -c 'echo "child after unset: [${E1-none}]"'
echo "HOME set: ${HOME:+yes}"
set | grep -c '^v_'
