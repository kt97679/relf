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
# ...but not elsewhere in a word, and not when quoted
echo "not=~/x"
echo other=~/y
