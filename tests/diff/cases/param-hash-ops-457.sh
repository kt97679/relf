# `#` and `%` after `${#` name the parameter `#`, not a length: `${##1}`
# is `$#` without a leading 1, `${##x}` is `$#`, and `${##}` - brace
# right after - is the LENGTH of `$#` (Iteration 457, busybox
# ash-vars/param_expand_len). A trim of any special parameter came out
# empty: that branch looked only in the variables.
set -- a
echo "[${##1}] [${#%1}] [${##x}] [${##}]"
set -- a b c d e f g h i j k l
echo "[${##1}] [${##x}] [${##}] [${#}]"
echo "[${?#0}]"
v=xyz; echo "[${v#x}] [${v%z}]"
# a line continuation inside a function name (yash quote-p.tst:209)
f\
n() { echo "in fn"; }
fn
