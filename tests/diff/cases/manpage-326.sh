# manpage-326.sh - features taken from dash's own manual page rather than
# from a list of mine: control flow, functions, `unset -f`, and the
# parameter forms. `unset -f` removed nothing until Iteration 326 - the
# function stayed callable - and unsetting a readonly variable succeeded
# where POSIX says it must not.
for i in 1 2 3; do case $i in 2) continue;; esac; echo "loop$i"; done
f() { for x; do echo "noin:$x"; done; }; f a b
g() { echo "g:$1"; } 2>/dev/null; g one
! false; echo "neg=$?"
! true | grep -q x; echo "negpipe=$?"
h() { return 4; }; h; echo "ret=$?"
i2() { local v=in; echo "local=$v"; }; v=out; i2; echo "after=$v"
j() { local nov; nov=set; echo "novalue=$nov"; }; j
for a in 1 2; do for b in 1 2; do break 2; done; done; echo "break2=ok"
for a in 1 2; do for b in 1 2; do continue 2; done; done; echo "cont2=ok"
set -- p q r; shift 2; echo "shift2=$*"
k() { echo k-body; }; k2() { echo k2-body; }
unset -f k; k 2>/dev/null || echo "k gone"; k2
a1() { echo A; }; b1() { echo B; }; c1() { echo C; }
unset -f b1; a1; c1
v2=1; unset -v v2; echo "unset-v=[$v2]"
: ${undef=defaulted}; echo "assign=$undef"
echo "len=${#undef}"
echo "nested=${undef:-${HOME:+has-home}}"
until false; do break; done; echo "until=ok"
while true; do break; done; echo "while=ok"
{ echo group; } | cat
( echo subshell )
