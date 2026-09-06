# Tilde expansion. ~user reads /etc/passwd; an unknown user stays
# literal, as POSIX requires.
echo ~
echo ~/stuff
echo ~root
echo ~root/x
echo ~nosuchuser
echo "~/quoted"
echo '~/single'
