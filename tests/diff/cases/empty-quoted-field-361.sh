# empty-quoted-field-361.sh - an empty field made by quoting is a field.
# With e unset and b=" b ", `echo a "$e"$b c` prints an empty argument
# between a and b, and `$b"$e"` ends with one. The quoted part emits no
# characters, so the splitter had nothing to distinguish it from leading
# or trailing whitespace and absorbed it (Iteration 361).
b=" b "
echo "leading:" a "$e"$b c
echo "trailing:" a $b"$e" c
echo "both:" a "$e"$b"$e" c
echo "plain:" a $b c
f() { echo "count=$#"; }
f ""$b
f $b""
f "x"$b
f $b
f "  spaced  "
v="  x  "
f $v
echo "collapse:" x  y
u=
f "$u"$b
f $b"$u"
