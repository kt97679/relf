# Three field-splitting bugs, all found by tools/difffuzz.py in its
# first real run (Iteration 471).
# 1. Quotes INSIDE a trim's pattern do not make the word around it quoted:
#    with z empty, ${z#"*"} is no field at all.
z=
printf '[%s]' 1 ${z#"*"} ${z#'a'*} ${z#a\*}; echo
set -- ${z:=""}; echo "assign-form fields: $#"
set -- ${z:-""}; echo "default-form fields: $#"
# 2. An empty parameter in an unquoted $@ or $* is no field, while "$@"
#    keeps it and IFS splitting's own empty fields stay.
set -- a '' b
printf '[%s]' $@; echo
printf '[%s]' $*; echo
printf '[%s]' "$@"; echo
set -- '' a
printf '[%s]' pre$@; echo
set -- a ''
printf '[%s]' $@post; echo
IFS=:; v='a::b'; printf '[%s]' $v; echo; unset IFS
# 3. A command substitution does not inherit the word around it: as a case
#    subject, which is not split, the commands INSIDE still split. And a
#    case subject that is $@ or $* joins its parameters and keeps blanks.
v=' '
case "$(printf %s $v)" in "") echo "empty subject";; *) echo "other subject";; esac
set -- '' a
case $* in " a") echo "joined with a space";; *) echo "not joined";; esac
set -- ' lead'
case $@ in " lead") echo "blank kept";; *) echo "blank lost";; esac
