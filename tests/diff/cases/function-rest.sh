# function-rest.sh - what follows a function call on the same line
# (Iteration 255). The rest of a line after `;`, `&&` or `||` was kept
# as pointers into the token buffers, which a function's body overwrites:
# `f; echo after` lost "after", and `f && echo after` ran a leftover word
# of f's body as a command.
f() { echo "in $1"; }
g() { echo "g1"; echo "g2"; }
f a; echo after
f b && echo and-after
false || f c; echo x
f d || echo no; echo after2
true && f e && echo after3
f 1; f 2; f 3; echo end
g; g && echo gg || echo never; echo last
h() { f inner; echo h-after; }
h; echo top-after
f x > /tmp/relf-diff-fx.$$; echo "fx=$(cat /tmp/relf-diff-fx.$$)"; rm -f /tmp/relf-diff-fx.$$
k() { false; }
k && echo no || echo k-failed; echo fin
