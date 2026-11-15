# tests/bench-cmd/configure.sh - a configure script's shape, 10 rounds: programs looked up on
# PATH, headers tested, names turned into macros through tr, uname, a config file written by
# echo and here-documents (954)
dir=${TMPDIR:-/tmp}/relf-bench-cmd.$$
mkdir -p "$dir" && cd "$dir" || exit 1
: > config.h
round=0
while [ $round -lt 10 ]; do
  for prog in cc gcc sed awk grep tr sort make install no-such-tool; do
    if command -v $prog >/dev/null 2>&1; then
      name=$(echo $prog | tr 'a-z-' 'A-Z_')
      echo "#define HAVE_$name 1" >> config.h
    else
      echo "/* no $prog */" >> config.h
    fi
  done
  for hdr in stdio.h stdlib.h string.h unistd.h no-such.h; do
    up=$(echo $hdr | tr 'a-z.' 'A-Z_')
    if [ -f /usr/include/$hdr ]; then
      echo "#define HAVE_$up 1" >> config.h
    else
      echo "/* no $hdr */" >> config.h
    fi
  done
  os=$(uname -s)
  case $os in
    Linux) echo "#define OS_LINUX 1" >> config.h ;;
    *) echo "#define OS_OTHER 1" >> config.h ;;
  esac
  cat >> config.h <<END
/* round $round on $os */
END
  round=$((round+1))
done
wc -l < config.h
grep -c HAVE_ config.h
cd / && rm -rf "$dir"
