# A word captured aside - the expression of $((...)), a pattern - is
# expanded into the output and taken back out; what it recorded about
# output positions must go with it. A split region did not, so an
# arithmetic result inside a braced word was split even when quoted
# (Iteration 440, yash fsplit-p.tst:36; 371 fixed the same for glob marks).
bracket() { for b_; do printf '[%s]' "$b_"; done; echo; }
IFS=' 0' a='1 2'
bracket ${a+"$((708))"} ${a+"x$((708))y"} "${a+$((708))}"
bracket ${a+"-${a}-" "-$(echo '3 4')-" "-`echo '5 6'`-" "-$((708))-"}
bracket ${u-"-${a}-" "-$(echo '3 4')-" "-`echo '5 6'`-" "-$((708))-"}
bracket "${a+-${a}-   -$(echo '3 4')-   -`echo '5 6'`-   -$((708))-}"
bracket "${u--${a}-   -$(echo '3 4')-   -`echo '5 6'`-   -$((708))-}"
bracket ${a+$((708))} ${a+x$((708))y}
IFS=' '
bracket ${a#"$((1))"} ${a%$((2))}
