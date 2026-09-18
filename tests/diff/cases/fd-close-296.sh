# fd-close-296.sh - `>&-` and `<&-` close a descriptor (XCU 2.7.6).
# Until Iteration 296 the target was read as a number, and "-" parses as
# 0, so `exec 3>&-` made fd 3 a duplicate of standard input and left it
# open; a script that did that could then block forever on a read.
# Writing to a descriptor that is not open is NOT checked here: this
# shell does not report it yet (see PROGRESS.md 296).
d=/tmp/relf-fd-296.$$
echo first > $d
exec 3>&1; echo via3 >&3; exec 3>&-
exec 4<$d; read l <&4; echo "read [$l]"; exec 4<&-
exec 5>$d; echo five >&5; exec 5>&-; cat $d
f() { cat <<HD
in-function
HD
}
f
exec 6>&1; echo via6 >&6; exec 6>&-; echo after
{ echo group >&2; } 2>&1
echo "2 still works" >&2
sh -c 'echo child sees fds' 
rm -f $d
