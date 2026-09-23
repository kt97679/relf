# A descriptor is read when the command is TOKENIZED, so a word that
# merely looks like one is never a descriptor, however it is followed
# (Iteration 467, busybox ash-signals/reap1). The runtime re-read tested
# the TEXT, so `echo hi $P >f` with P=5 lost the 5, and `kill -0 $PID
# >/dev/null` lost its operand.
d=${TMPDIR:-/tmp}/relf-467.$$
mkdir -p "$d" || exit 1
P=5
echo hi $P >"$d/a"; cat "$d/a"
Q=23
echo two $Q >"$d/b"; cat "$d/b"
# ... while a real descriptor, with no blank before the operator, is one
echo lost 5>"$d/c"; cat "$d/c"; echo "c: [$(cat "$d/c")]"
echo kept 5 >"$d/d"; cat "$d/d"
# and the loop that found this: an operand that is a pid
sleep 0.2 &
PID=$!
while kill -0 $PID >/dev/null 2>&1; do :; done
echo "loop ended"
rm -rf "$d"
