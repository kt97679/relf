# POSIX.1-2017 XCU 2.9.4.1 Grouping Commands.
#
# { compound-list; } groups commands in the current environment. The
# list is a list: newline separates commands within it exactly as ';'
# does, so a group written across lines runs every command in it.
{ echo first
  echo second
  echo third; }
echo after
