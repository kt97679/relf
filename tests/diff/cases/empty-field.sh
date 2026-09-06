# POSIX: an unquoted expansion producing nothing yields NO field;
# a quoted empty word still yields one.
echo A ${nope:-} B
echo "[" ${nope:-} "]"
echo "[" "" "]"
n=""
echo x $n y
echo x "$n" y
set -- p "" q
echo "count=$#"
