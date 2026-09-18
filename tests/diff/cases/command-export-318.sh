# command-export-318.sh - `command -V` and `$PPID` (Iteration 318).
# `-V` printed nothing at all, and PPID was never set. Two things are
# deliberately absent: `command -V` on a function (bash prints the body,
# dash a sentence, and this shell follows dash) and `export -p`, whose
# format differs between the references - tests/shell/run-export covers
# that against dash.
command -V echo
command -V if
command -V /bin/sh
command -v echo
command -v /bin/sh
echo "PPID set: $([ -n "$PPID" ] && echo yes)"
echo "PPID numeric: $(case $PPID in *[!0-9]*) echo no;; *) echo yes;; esac)"
[ "$PPID" != "$$" ] && echo "PPID differs from PID"
