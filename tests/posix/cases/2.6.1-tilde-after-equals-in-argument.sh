# POSIX.1-2017 XCU 2.6.1 Tilde Expansion - tilde expansion after an
# unquoted '=' applies to assignment WORDS. An argument to a command
# that merely looks like name=value is not an assignment word.
#
# Included deliberately as a case the reference shells disagree on:
# bash expands here, dash does not. See GOALS.md's "Where bash and
# POSIX disagree". This is what an INCONCLUSIVE verdict looks like,
# and it is the harness working, not a defect.
printf '%s\n' other=~/y
