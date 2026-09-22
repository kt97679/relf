# Iteration 445 (busybox bkslash_newline4, quote_in_varexp1): a
# continuation straight after `${` does not hide a `#`, and a nested
# ${...} does not leave its value-word quoting behind for the pattern
# around it.
set -- 1 22 333
echo 1:$\
1
echo 3:$\
{\
#\
3\
}
x="''''"; echo "${x#"${x+''}"''}"
x=abc; echo "${x#'a'}" "${u-'a'}" "${x#"${u-'q'}"}" "${x%'c'}"
