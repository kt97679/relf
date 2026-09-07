# XCU 2.7 Redirection. '>' truncates, '>>' appends, '<' redirects
# input, and redirections are processed left to right.
f=/tmp/relf-posix-redir.txt
rm -f "$f"
printf 'one\n' > "$f"
printf 'two\n' >> "$f"
cat "$f"
printf 'three\n' > "$f"
cat < "$f"
rm -f "$f"
