# fd-exec-297.sh - `exec` keeps its redirections on any descriptor, not
# just 0, 1 and 2 (Iteration 297). Opening a file for fd 3 lands ON fd 3
# when 3 is the lowest free one, so copying it onto itself did nothing
# and the close that followed shut it again: `exec 3>file` opened the
# file and then lost it, while `exec >file` worked. Writing to a
# descriptor that is not open fails now too, so the diagnostics are
# silenced here - the three shells word them differently.
d=/tmp/relf-297.$$
exec 3>$d
echo via3 >&3
echo "after write: [$(cat $d)]"
sh -c 'echo from-child >&3'
echo "child too: [$(cat $d)]"
exec 3>&-
echo "closed: [$( { echo more >&3; } 2>/dev/null || echo cannot )]" 2>/dev/null
exec 4<$d
read a <&4; read b <&4
echo "read back: [$a][$b]"
exec 4<&-
exec 5>>$d
echo appended >&5
exec 5>&-
cat $d
exec 6>$d.2 7>$d.3
echo six >&6; echo seven >&7
exec 6>&- 7>&-
cat $d.2 $d.3
{ echo group >&3; } 2>/dev/null || echo "3 is closed"
rm -f $d $d.2 $d.3
