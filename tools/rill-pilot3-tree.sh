#!/bin/sh
# tools/rill-pilot3-tree.sh DIR - a stand-in tree for the third pilot (Iteration 760).
#
# tools/native-ab-layouts.py builds eight native kernels and shells and
# times them - minutes of work, and a result that differs run to run. The
# three versions are held to one another in a git repository where every
# expensive step is a stub: the builds touch their outputs, and the stub
# tools/bench-vm.py prints, for each configuration it is given, ratios made
# from the configuration's name - so a run is quick and its table the same
# every time. Everything the tool does between the commands - the pads,
# the worktree, the configuration file, reading the bench's lines, the
# geometric means, the table - is done for real.
set -e
d=$1; rm -rf "$d"; mkdir -p "$d/tools" "$d/forth"; cd "$d"
git init -q; git config user.email pilot@example; git config user.name pilot
cp /home/claude/relf/tools/native-ab-layouts.py tools/
printf '#!/bin/sh\ntouch "$1"; chmod +x "$1"\n' > tools/build-native-shell.sh
printf 'import sys\nopen(sys.argv[1], "w").write("")\n' > tools/gen-native-os.py
cat > tools/bench-vm.py << 'PY'
import sys, os
wl = os.environ.get('WL', 'loop fn str arith realistic').split()
for line in open(sys.argv[2]):
    name = line.split('|')[0]
    side, pad = name.split('-p')
    k = int(pad) // 16
    base = 1.0 if side == 'base' else 0.95
    rs = ['%.3f [x]' % (base + 0.007 * k + 0.011 * j + (0.004 if side == 'now' and j % 2 else 0.0)) for j in range(len(wl))]
    print('%-10s %s' % (name, '  '.join(rs)))
PY
printf 'N>A  S" forth/native-rt.4" INCLUDED  A>N\n' > forth/native-kernel.4
printf 'the kernel\n\\ PART 10: TOP LEVEL\nthe top level\n' > forth/kernel.4
: > forth/kernel64.img
printf '#!/bin/sh\ncat > /dev/null; touch native-kernel; chmod +x native-kernel\n' > relf64; chmod +x relf64
printf 'native-kernel:\n\ttouch native-kernel; chmod +x native-kernel\n' > Makefile
git add -A; git commit -q -m 'the stand-in tree'
echo "$d: the stand-in tree"
