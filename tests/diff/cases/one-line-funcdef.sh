# A function defined entirely on one line (Iteration 118). This used
# to hang, then to be a syntax error.
n() { echo "n=$#"; }
n a b c
n

f() { echo one; echo two; }
f

# arguments and the caller's own parameters
set -- outer
g() { echo "inner=$1 count=$#"; }
g inner-arg
echo "still=$1"

# the body is expanded when it runs, not when it is defined
v=first
h() { echo "v=$v"; }
h
v=second
h

# the subshell form
s() ( echo "sub=$$x" >/dev/null; echo sub-ran; )
s

# a return, and the status
r() { return 3; }
r
echo "r=$?"

# nesting: the inner definition belongs to the outer body
outer() { inner() { echo deep; }; inner; }
outer

# redefinition replaces
d() { echo old; }
d() { echo new; }
d

# and the multi-line form still works
m() {
  echo multi
}
m
