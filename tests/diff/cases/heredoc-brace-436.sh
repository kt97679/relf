# A ${...} in an unquoted here-document is shell text: the quotes in its
# word are quotes, so ${foo%"oo"} trims "oo" (Iteration 436, yash
# redir-p.tst:335). The body's own quotes are literal, and \$ \\ \` are
# escapes the body honours.
foo=foooo x=1
cat <<END
parameter ${foo%"oo"}
default ${u:-"q r"} and ${x:+"set"}
"quoted" and 'single'
escaped \${x} and \$x and \\ and \`
command $(echo "s") and `echo "t"`
END
