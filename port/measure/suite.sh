#!/bin/sh
# port/measure/suite.sh SHELL OUT - tests/shell against SHELL, each file under its own timeout; the last
# line of OUT the totals. SHELL: a wrapper script, as tests/shell runs THIS_SH by itself, e.g.
#   printf '#!/bin/sh\nRELF_ARGV0=${RELF_ARGV0:-$0} exec %s %s "$@"\n' DESIGN/forth OUT.img > sh
sh_=$1; out_=$2
cd "$(dirname "$0")/../../tests/shell" || exit 1
exec < /dev/null
LC_ALL=C; export LC_ALL; unset LD_PRELOAD
: > "$out_"
for t in run-*; do
  case "$t" in run-all|*.orig|*~) continue ;; esac
  [ -f "$t" ] && [ -x "$t" ] || continue
  THIS_SH=$sh_ timeout 180 ./"$t" >> "$out_" 2>&1
  [ $? = 124 ] && echo "TIMEOUT ($t)" >> "$out_"
done
grep -E '^[0-9]+ assertions, [0-9]+ failed|^TIMEOUT' "$out_" | awk '/TIMEOUT/ {t++; next} {s+=$1; f+=$3; n++} END {print n " files, " s " assertions, " f " failed, " t+0 " timeouts"}' >> "$out_"
tail -1 "$out_"
