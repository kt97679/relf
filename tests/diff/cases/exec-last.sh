# exec-last.sh - a process with one command left execs it instead of forking
# (Iteration 269): pipeline stages, command substitutions, subshells, background
# jobs, and the statuses that must survive; plus a command with only a
# command substitution taking its status (XCU 2.9.1).
f() { /bin/echo in-f; echo after-ext-in-f; }
f | cat
x=$(/bin/echo cs; echo more)
echo "[$x]"
y=$(/bin/echo only)
echo "[$y]"
( /bin/echo sub1 )
( /bin/echo sub2; echo sub-after )
/bin/echo p1 | tr a-z A-Z
eval '/bin/echo ev1'; echo after-eval
z=$(f)
echo "[$z]"
/bin/false | /bin/true; echo "pipe st=$?"
v=$(/bin/false); echo "cs st=$?"
( /bin/false ); echo "sub st=$?"
a=1 /usr/bin/env | grep '^a=' 
/bin/echo bg & wait
echo last-builtin
/bin/echo final-external
