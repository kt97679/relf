# heredoc-continuation-332.sh - two behaviours from
# tests/from-others/CATALOGUE.md entries 4 and 5, both implemented in
# Iteration 332.
#
# A command substitution inside a here-document is shell code, so the
# quotes in it are quotes; this shell handed the body to the expander as
# one double-quoted word and escaped every quote in it, including the
# ones inside a substitution, so `$(echo "x")` printed "x".
#
# A backslash-newline is removed before tokens are recognised, so an
# operator may be split across two lines; this was a syntax error here.
cat <<E1
plain "quotes" stay
$(echo "in a substitution")
`echo "in backquotes"`
$(echo "$(echo nested)")
$(printf '%s\n' 'single quotes')
E1
cat <<'E2'
$(echo "not run") "quoted"
E2
x=5
cat <<E3
value $x and $(echo "$x")
E3
echo one &\
& echo two
echo three |\
| echo NOT-SHOWN
case w in
  a) echo SKIP;\
; w) echo case-ok;; esac
true &\
& echo and-ok
false |\
| echo or-ok
