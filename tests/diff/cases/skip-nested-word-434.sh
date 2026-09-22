# A word that is not used - the word of ${a-word} when a is set, or of
# ${u+word} when u is unset - is skipped whole, however deeply nested
# (Iteration 434, yash param-p.tst:151). A nested parameter with its own
# word, or a leading tilde, ended the skip early, and the rest printed.
a=a
printf '[%s]' ${a-x${a-x}x}b}; echo
printf '[%s]' ${a-x${u:-y}x}b}; echo
printf '[%s]' ${a-x${u:-${u:-z}}x}b}; echo
printf '[%s]' ${a-x${u-${u-z}}x}b}; echo
printf '[%s]' ${a-x${#a}x}b}; echo
printf '[%s]' ${a-x$a$a}b}; echo
printf '[%s]' ${a-x${a%%a}x}b}; echo
printf '[%s]' ${a-~/p}b}; echo
printf '[%s]' ${a-x"${u-q}"$(echo c)$((1+1))`echo d`}e}; echo
printf '[%s]' ${u+x${a-${a-z}}x}f; echo
v=${a-x${u-${u-z}}x}; printf '[%s]\n' "$v"
unset u; printf '[%s]' ${u-x${u-${u-z}}x}b}; echo
