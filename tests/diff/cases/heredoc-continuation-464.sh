# With an unquoted delimiter a line ending in a backslash continues, and
# the line it continues into is not the terminator (Iteration 464,
# busybox ash-heredoc/heredoc_backslash1). `<<-` strips the tabs that
# start a LOGICAL line, so a continued line keeps its tab.
cat <<EOF
c\
EOF
EOF
echo "1 done"
cat <<'EOF'
c\
EOF
echo "2 done"
cat <<EOF
a\
b
EOF
cat <<-EOF
	x\
	EOF
	EOF
echo "3 done"
