# quoted-field-run-364.sh - quoting inside a run of IFS whitespace. The
# quoted part emits no characters, so the splitter has to be told when
# it happened rather than where: `${x:+b '' c}` is three fields,
# `${x:+b ''}` two, and `${x:+ '' }` one, because a field is only closed
# when there is something to close (Iteration 364).
f() { echo "count=$#"; for i; do echo "|$i|"; done; }
x=a
f ${x:+b '' c}
f ${x:+b ''}
f ${x:+'' b}
f ${x:+'' ''}
f ${x:+ '' }
f ${x:+'' }
f ${x:+ ''}
f ${x:+a b}
f ${x:+ a b }
b=" b "
f ""$b
f $b""
f "$e"$b"$e"
f $b
v="  x  "
f $v
f a  b
# A split left pending by an expansion is performed even when the text
# that ends it arrives in bulk: `H${x:+ }H` is two fields (Iteration 372).
x=1
f H${x:+ }H
f ${x:+b c}
f A${x:+ }B${x:+ }C
b=" b "
f A${b}C
f H${x:+ }
