# builtin-override-330.sh - a function overrides a regular builtin but
# not a special one (XCU 2.14's search order: special builtins, then
# functions, then everything else). Written from the description in
# tests/from-others/CATALOGUE.md entry 3. Until Iteration 330 this shell
# looked up every builtin before functions, so no function could
# override one.
true() { echo "function-true"; }
true
true | cat
(true)
echo "in-sub=$(true)"
unset -f true
true && echo "builtin-back"
echo() { printf "function-echo\n"; }
echo ignored
unset -f echo
echo builtin-echo
cd() { printf "function-cd\n"; }
cd /nonexistent-xyz
echo "cd-status=$?"
unset -f cd
cd /tmp && echo "real-cd=$(pwd)"
pwd() { echo "function-pwd"; }
pwd
unset -f pwd
# `type` on a function is left out: bash prints the body where dash
# prints a sentence, and this shell follows dash.
