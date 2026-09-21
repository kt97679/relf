# A case subject and a case pattern are not field-split (XCU 2.9.4.3;
# Iteration 423). Both were: the pattern lost leading, trailing and
# non-blank IFS characters, and the subject was split and joined back
# with single blanks, so `case $g in` changed $g. Found through
# busybox's many_ifs, whose driver skips rows with exactly this.
v=' '; case ' ' in $v) printf 'lone-blank pattern\n';; *) printf 'no\n';; esac
f1=''; d1=' '; case ' ' in $f1$d1) printf 'joined pattern\n';; *) printf 'no\n';; esac
v=' x'; case ' x' in $v) printf 'leading blank\n';; *) printf 'no\n';; esac
v='a b'; case 'a b' in $v) printf 'inner blank\n';; *) printf 'no\n';; esac
g='a  b'; case $g in 'a  b') printf 'double blank subject\n';; *) printf 'no\n';; esac
g=' x '; case $g in ' x ') printf 'padded subject\n';; *) printf 'no\n';; esac
r='()(:  :)'; g='()(:  :)'; case $g in "$r") printf 'quoted pattern\n';; *) printf 'no\n';; esac
v=; case '' in $v) printf 'empty pattern\n';; *) printf 'no\n';; esac
v='*'; case abc in $v) printf 'glob still globs\n';; *) printf 'no\n';; esac
IFS=:
v='a:b'; case 'a:b' in $v) printf 'IFS character in pattern\n';; *) printf 'no\n';; esac
g='a:b'; case $g in 'a:b') printf 'IFS character in subject\n';; *) printf 'no\n';; esac
IFS=' 	
'
case $(printf ' y ') in ' y ') printf 'command substitution subject\n';; *) printf 'no\n';; esac
