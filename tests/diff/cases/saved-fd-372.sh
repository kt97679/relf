# saved-fd-372.sh - the descriptors a redirection keeps so it can put
# things back are the shell's business, not the command's. A redirected
# command could see fd 64 open (Iteration 372); real shells mark those
# copies close-on-exec, and this shell has no fcntl, so the child closes
# the range before it execs.
{ ls /proc/self/fd; } > /tmp/relf-372-a.txt
tr '\n' ' ' < /tmp/relf-372-a.txt; echo
ls /proc/self/fd | tr '\n' ' '; echo
{ { ls /proc/self/fd; } > /tmp/relf-372-b.txt; } 2>/dev/null
tr '\n' ' ' < /tmp/relf-372-b.txt; echo
exec 3>/tmp/relf-372-c.txt
ls /proc/self/fd | tr '\n' ' '; echo
exec 3>&-
ls /proc/self/fd | tr '\n' ' '; echo
rm -f /tmp/relf-372-a.txt /tmp/relf-372-b.txt /tmp/relf-372-c.txt
