# XCU 2.6.2. ':=' assigns to the parameter as well as substituting;
# ':+' substitutes the alternative only when set and non-null.
unset u
printf '%s\n' "${u:=assigned}"
printf '%s\n' "$u"
s=val
printf '%s\n' "${s:+alt}"
e=
printf '%s\n' "${e:+alt}(empty)"
printf '%s\n' "${e+alt}(set-but-null)"
