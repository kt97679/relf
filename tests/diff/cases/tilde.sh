# Tilde expansion. ~user reads /etc/passwd; an unknown user stays
# literal, as POSIX requires.
echo ~
echo ~/stuff
echo ~root
echo ~root/x
echo ~nosuchuser
echo "~/quoted"
echo '~/single'

# POSIX expands a tilde in an assignment after '=' and after each ':'.
a=~/stuff
echo "$a"
b=~/foo:~/bar:~/baz
echo "$b"
c=~root
echo "$c"
# ...but not when quoted.
echo "not=~/x"
# NOTE: 'echo other=~/y' is deliberately NOT tested here. bash expands
# it; dash does not, and neither do we. POSIX applies tilde-after-'='
# to assignment WORDS, and an argument to echo is not one. bash is
# being permissive (it treats any name=value-shaped word that way);
# this differential file uses bash as its oracle, so the case cannot
# live here. Recorded in GOALS.md instead.
