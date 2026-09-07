# POSIX.1-2017 XCU 2.9.1 Simple Commands - a variable assignment
# preceding a command name is exported to that command's environment
# for the duration of the command only, and must not persist in the
# executing shell afterwards.
FOO=prefixed sh -c 'printf "%s\n" "${FOO-unset-in-child}"'
printf '%s\n' "${FOO-unset-after}"
