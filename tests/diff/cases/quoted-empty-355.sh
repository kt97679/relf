# quoted-empty-355.sh - an empty field is dropped only when nothing in
# the word was quoted. `${x:+''}` and `${x:+""}` are quoted empty
# strings and each makes one argument; this shell dropped them, because
# it consulted only the parser's flag for a quote at the START of a word
# and not the quoting that appeared during expansion (Iteration 355).
f() { echo "count=$#"; for i; do echo "|$i|"; done; }
x=a
f ${x:+''}
f ${x:+""}
f ${x:+'' }
f ${x:+ ''}
f ${x:+a''}
f ${x:+''a}
f "${x:+}"
f ${x:+}
u=
f $u
f "$u"
f ${u:-''}
f ${u:-}
set --
f "$@"
f ""
