# assign-redirect-349.sh - a command of assignments and redirections
# only sets the variables in the shell itself. This shell tested for
# "assignments only" before the redirection words were taken out of the
# argument list, so `> f var=ok` ran the assignment as a command
# (Iteration 349).
#
# `var=ok > f` - the assignment FIRST - was fixed in Iteration 350: the
# prefix count has to be taken before TEMP-ASSIGN removes the prefixes
# from the list.
#
# The `v3=tmp :` line matches BASH: POSIX has an assignment before a
# SPECIAL builtin persist, which dash does and bash does not outside
# POSIX mode. This shell follows bash, as it does for the other special
# builtin differences (GOALS.md 5k).
d=/tmp/relf-349.$$
rm -rf $d; mkdir -p $d; cd $d
var=first >f0
echo "assignment-first=$var"
>f var=ok
echo "after-redirect=$var"
>g x=1 y=2
echo "two=$x$y"
test -f f && test -f g && echo "files-made"
var2=tmp true
echo "temporary=[$var2]"
# `v3=tmp :` used to be checked here. Since Iteration 379 an assignment
# before a SPECIAL builtin persists (XCU 2.9.1), which bash does only in
# POSIX mode - so it moved to tests/shell/run-special-error, where the
# reference is the standard rather than bash.
>h a=1 b=2 c=3
echo "three=$a$b$c"
cd /tmp; rm -rf $d
# A redirection may come BEFORE the assignments, and the words after it
# are still a prefix: `</dev/null foo=bar echo hi` runs echo, not
# foo=bar. The redirections travel through ARGV as words, and the prefix
# was counted before they were taken out (Iteration 385).
cd /tmp
</dev/null lead1=one echo "lead=$lead1"
>/tmp/relf-385.out lead2=two echo redirected
cat /tmp/relf-385.out
</dev/null a1=1 b1=2 echo "two=$a1$b1"
</dev/null lead3=three </dev/null echo </dev/null "interleaved=$lead3"
rm -f /tmp/relf-385.out
