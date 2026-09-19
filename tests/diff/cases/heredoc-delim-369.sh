# heredoc-delim-369.sh - the delimiter of a here-document undergoes
# quote removal, not "drop every quote character": a backslash keeps the
# character after it, and inside double quotes it keeps itself unless
# what follows is one of the four it can quote there. This shell dropped
# every backslash, so `<<"\name"` waited for `name` and swallowed the
# rest of the script (Iteration 369).
cat <<"\name"
one
\name
echo "after-backslash=$?"
cat <<E\Nd
two
ENd
echo "after-escaped-letter=$?"
cat <<'\lit'
three
\lit
echo "after-single-quoted=$?"
cat <<"END"
four
END
cat <<'END'
five
END
cat <<E"N"D
six
END
cat <<\END
seven
END
echo done
# A backslash-newline may also sit between the two characters of `<<`,
# or before the `-` of `<<-`: the continuation is removed before tokens
# are recognised (Iteration 369 completed what 332 started).
cat <<\
 AAA
eight
AAA
cat <\
<\
BBB
nine
BBB
cat <<\
- CCC
	ten
CCC
echo continuations-done
