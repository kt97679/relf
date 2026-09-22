# Backquotes inside double quotes: \$ \\ \` are escapes of the backquoted
# text, and \" is one too - the enclosing double quotes' - while \' is
# not (Iteration 438, yash cmdsub-p.tst:79). "`echo \"1\"`" printed "1".
echoraw() { printf '%s\n' "$*"; }
echoraw "`echoraw "a"'b'`"
echoraw "`echoraw \$ "\$" '\$'`"
echoraw "`echoraw \\\\ "\\\\" '\\\\'`"
echoraw "`echoraw \"1\"`"
echoraw "`echoraw \'2\'`"
echoraw "`echoraw \`echo a\` "\`echo b\`" '\`echo c\`'`"
echoraw `echoraw \"3\"`
