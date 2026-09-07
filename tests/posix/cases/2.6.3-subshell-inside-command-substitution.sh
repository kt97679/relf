# POSIX.1-2017 XCU 2.6.3 Command Substitution.
#
# "$((" begins an arithmetic expansion, so a command substitution
# whose first token is a subshell must be written with a space -
# "$( (list) )". The specification says exactly this: an application
# should separate them to avoid the ambiguity. A shell that ignores
# the space reads the whole thing as arithmetic.
x=$( (echo inner) )
echo "got=$x"
