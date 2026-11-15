# tests/bench-cmd/textproc.sh - text through pipelines: a 1,000-line file written by a loop,
# then grep, cut, sort, uniq, head, sed, tr and wc over it, and a while-read loop (954)
dir=${TMPDIR:-/tmp}/relf-bench-cmd.$$
mkdir -p "$dir" && cd "$dir" || exit 1
i=0
while [ $i -lt 1000 ]; do
  echo "user$((i % 37)):x:$i:$((i % 7)):name $i:/home/user$i:/bin/sh"
  i=$((i+1))
done > passwd.txt
grep -c ':3:' passwd.txt
cut -d: -f1 passwd.txt | sort | uniq -c | sort -rn | head -3
sed -n 's/^user\([0-9]*\):.*/\1/p' passwd.txt | sort -n | uniq | wc -l
tr ':' '\n' < passwd.txt | grep -c '^/bin/sh$'
n=0
while IFS=: read -r user pw uid gid gecos home sh; do
  case $gid in
    0|1) n=$((n + uid)) ;;
  esac
done < passwd.txt
echo $n
cd / && rm -rf "$dir"
