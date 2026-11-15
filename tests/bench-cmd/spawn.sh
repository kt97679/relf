# tests/bench-cmd/spawn.sh - process creation alone: an external command 400 times (Iteration 954).
# tests/bench-cmd/ holds scripts whose time is mostly other programs' - the shell's own
# work against fork, exec and I/O - where tests/bench-vm's are the shell's work alone.
i=0
while [ $i -lt 400 ]; do
  /bin/true
  i=$((i+1))
done
echo $i
