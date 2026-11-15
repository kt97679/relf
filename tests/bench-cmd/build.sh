# tests/bench-cmd/build.sh - an install step's shape: 60 files written, then each copied into
# a directory by mkdir -p and cp and compared by cmp; ls, cat, find and wc over the result (954)
dir=${TMPDIR:-/tmp}/relf-bench-cmd.$$
mkdir -p "$dir/src" && cd "$dir" || exit 1
i=0
while [ $i -lt 60 ]; do
  echo "file $i contents" > src/f$i.c
  i=$((i+1))
done
for f in src/*.c; do
  b=${f##*/}; b=${b%.c}
  d=out/$((${#b} % 3))
  mkdir -p $d
  cp $f $d/$b.o
  cmp -s $f $d/$b.o || echo "differ $f"
done
ls out | wc -l
cat out/*/*.o | wc -l
find out -type f | wc -l
cd / && rm -rf "$dir"
