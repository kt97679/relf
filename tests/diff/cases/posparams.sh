# $* and $@ joined and embedded. ("$@" as one field per parameter is
# a known gap - see PROGRESS.md - and is not asserted here.)
set -- a b
echo "[$*]"
set -- "a b" c
echo "[$*]"
echo "x$*y"
echo "n=$#"
echo "[$1][$2]"
set --
echo "empty=[$*] n=$#"
