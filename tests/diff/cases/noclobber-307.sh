# noclobber-307.sh - `set -C` refuses to overwrite an existing REGULAR
# file, while `>|` overrides it and a device is unaffected (XCU 2.7.2).
# It needed FILE-KIND, the engine primitive added in Iteration 307:
# O_EXCL alone also refuses `> /dev/null`, which no reference shell does.
# The diagnostics are silenced - every shell words them differently.
d=/tmp/relf-307.$$
set -C
echo first > $d
echo second > $d 2>/dev/null; echo "refused rc=$?"
cat $d
echo third >| $d 2>/dev/null; echo "override rc=$?"
cat $d
echo fourth >> $d 2>/dev/null; echo "append rc=$?"
cat $d
echo to-device > /dev/null 2>/dev/null; echo "device rc=$?"
echo new-file > $d.2 2>/dev/null; echo "new rc=$?"; cat $d.2
case $- in *C*) echo "C in dollar-minus";; *) echo "C missing";; esac
set +C
echo overwritten > $d; cat $d
case $- in *C*) echo "still C";; *) echo "C gone";; esac
rm -f $d $d.2
