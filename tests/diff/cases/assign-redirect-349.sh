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
