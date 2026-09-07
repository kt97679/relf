# XCU 2.6.6 Pathname Expansion. A pattern that matches nothing is
# left unchanged, matches are sorted, and a leading period is not
# matched by a leading '*'.
d=/tmp/relf-posix-glob-case
rm -rf "$d"; mkdir -p "$d"; cd "$d" || exit 1
: > b.txt; : > a.txt; : > c.dat; : > .hidden
printf '%s\n' *.txt
printf '%s\n' *
printf '%s\n' nomatch*
cd /; rm -rf "$d"
