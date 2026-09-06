# $* and $@, joined, embedded, and as fields.
set -- a b
echo "[$*]"
set -- "a b" c
echo "[$*]"
echo "x$*y"
echo "n=$#"
echo "[$1][$2]"
set --
echo "empty=[$*] n=$#"

n() {
  echo "count=$#"
}
set -- "a b" c
n $@
n "$@"
n $*
n "$*"
set --
n "$@"
n "x$@y"
