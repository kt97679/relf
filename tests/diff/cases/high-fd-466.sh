# A descriptor of two digits or more: the table of one-character words
# held nothing for them and the descriptor was dropped, so `exec 23>file`
# redirected stdout (Iteration 466, busybox ash-redir/redir2). dash
# refuses two digits outright, so this follows bash.
d=${TMPDIR:-/tmp}/relf-466.$$
mkdir -p "$d" || exit 1
exec 23>"$d/a"
echo via23 >&23
exec 23>&-
cat "$d/a"
exec 12>"$d/b"
echo via12 >&12
exec 12>&-
cat "$d/b"
{ echo grouped >&24; } 24>&1
( echo subshell >&22 ) 22>&1
echo plain 25>"$d/c"
cat "$d/c"; echo "c is empty: $?"
# ... and the single-digit ones are unchanged
exec 9>"$d/d"
echo via9 >&9
exec 9>&-
cat "$d/d"
echo err 1>&2
rm -rf "$d"
