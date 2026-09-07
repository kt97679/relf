# POSIX.1-2017 XCU 2.9.4.2 Case Conditional Construct.
#
# The grammar makes no distinction between a case written across
# several lines and the same case written on one. A newline is a
# token; ';' and newline are separators. Nothing in the specification
# licenses a shell to require the arms be on their own lines.
case x in x) echo matched ;; esac
echo after
