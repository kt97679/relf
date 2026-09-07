# POSIX.1-2017 XCU 2.9.4.1 The if Conditional Construct.
#
# A compound command is a command: anything following its terminator
# on the same line runs exactly as it would after any other command.
# Nesting changes nothing about that - the outer "fi" ends the outer
# if, and "echo B" is the next command in the list.
if true; then if true; then echo A; fi; fi; echo B
