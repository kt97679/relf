# XCU 2.7.6. '2>&1' makes fd 2 a duplicate of whatever fd 1 is AT
# THAT MOMENT, so order matters: the two orderings below differ.
f=/tmp/relf-posix-dup.txt
rm -f "$f"
{ printf 'to-stdout\n'; printf 'to-stderr\n' >&2; } > "$f" 2>&1
cat "$f"
rm -f "$f"
