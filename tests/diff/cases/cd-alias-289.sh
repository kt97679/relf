# cd-alias-289.sh - `cd -` with OLDPWD and PWD, cd's diagnostics on
# standard error, and `alias` printing definitions (Iteration 289: `cd -`
# was unsupported and said so on stdout, and `alias` with no operands or
# with a plain name printed nothing). bash writes `alias ll='...'` where
# dash writes `ll='...'`, so the listing is normalised here.
cd /tmp && cd /etc && cd - > /dev/null && pwd
cd /tmp; echo "PWD=$PWD OLD=$OLDPWD"
cd /etc; echo "PWD=$PWD OLD=$OLDPWD"
cd /nonexistent-dir 2>/dev/null; echo "rc=$?"
cd /nonexistent-dir 2>&1 >/dev/null | grep -c 'cd'
alias ll='echo AL' zz='echo ZZ'
alias ll | sed 's/^alias //'
alias | sed 's/^alias //' | sort
alias nosuch 2>/dev/null; echo "rc=$?"
unalias ll; alias | sed 's/^alias //' | sort
unalias -a 2>/dev/null; alias | wc -l
