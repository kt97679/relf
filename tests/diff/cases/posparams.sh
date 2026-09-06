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

# Text AFTER a quoted "$@" survives. The field break "$@" synthesises
# between parameters grows the token buffer by a byte with nothing
# consumed to pay for it, so without reserving room each break ate a
# byte of unread input (Iteration 103). Two or more parameters are
# needed to produce a break at all.
set -- a b c
echo "1  $@  2"
echo "[$@]"
echo "x$@y"
n "1  $@  2"
set -- one
echo "1  $@  2"
set -- a b c d e f
echo "start $@ end"
