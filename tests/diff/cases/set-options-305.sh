# set-options-305.sh - `set -a` (allexport) and `set -v` (verbose), both
# missing until Iteration 305. `set -C` is not here: it needs a stat
# primitive to tell a regular file from a device, which the engine does
# not have yet (GOALS.md).
set -a
exported=yes
sh -c 'echo "child sees [$exported]"'
set +a
notexported=no
sh -c 'echo "child sees [$notexported]"'
case $- in *a*) echo "a in dollar-minus";; *) echo "a gone";; esac
set -a; case $- in *a*) echo "a back";; esac; set +a
v=before; set -a; v=after; sh -c 'echo "reassigned [$v]"'; set +a
export -p >/dev/null 2>&1 || true
echo done
