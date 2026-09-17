trap 'echo bye $?' EXIT
trap
trap 'echo got-usr1' USR1
kill -USR1 $$
echo after-usr1
trap - USR1
trap '' HUP
trap
( trap; echo in-sub )
( trap 'echo sub-exit' EXIT; echo sub-body )
f() { local v=inner; echo "in f: $v"; local w; w=set-in-f; }
v=outer; w=outer-w
f
echo "after f: $v $w"
g() { local u=1; unset u; echo "g u=[${u-unset}]"; }
u=global; g; echo "u=$u"
kill -l 9; kill -l 143
kill -s TERM 99999999 2>/dev/null; echo "kill st=$?"
umask 022; umask; umask -S; umask u=rwx,g=,o=; umask; umask 0077; umask -S
times > /dev/null; echo "times st=$?"
set -- a
x=1; y='it'"'"'s'
set | grep -E '^(x|y)='
trap 'echo trapped-int; exit 7' INT
kill -INT $$
echo not-reached
