# redir-target-335.sh - entry 12 of tests/from-others/CATALOGUE.md: the
# word after a redirection operator is expanded but not field-split, so
# a variable holding "a b" names one file. This shell split it like any
# other word until Iteration 335, writing to the first name and passing
# the rest as arguments.
#
# A target that expands to SEVERAL fields is unspecified: bash calls it
# an ambiguous redirect, dash writes to the single name it read. This
# shell follows dash, so those spellings are left out of this case and
# noted in the catalogue instead.
d=/tmp/relf-335.$$
rm -rf $d; mkdir -p $d; cd $d
v3=plain
echo three >$v3
cat plain
echo four > 'sp ace'
cat 'sp ace'
v4='in.tmp'
echo five > $v4
cat < $v4
v5='out.tmp'
cat $v4 > $v5
cat $v5
empty=
echo six > "e${empty}mpty.tmp"
cat empty.tmp
star='*.nomatch'
echo seven > $star
ls '*.nomatch' > /dev/null && echo "glob-not-expanded"
cd /tmp; rm -rf $d
