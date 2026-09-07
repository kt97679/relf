# XCU 2.7. A redirection may be applied to a compound command, and
# then applies to every command inside it.
f=/tmp/relf-posix-compound.txt
rm -f "$f"
for i in 1 2 3; do printf 'line%s\n' "$i"; done > "$f"
cat "$f"
while read -r l; do printf 'read=%s\n' "$l"; done < "$f"
rm -f "$f"
