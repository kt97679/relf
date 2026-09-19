# assign-order-357.sh - assignments in one command are expanded and
# applied left to right, so each sees the ones before it, while the
# command's own words still see the values from before the command
# (XCU 2.9.1). This shell expanded every word first and applied the
# assignments afterwards, so a later one saw the old value
# (Iteration 357).
X=usbdev1.2 X=${X#usbdev} B=${X%%.*} D=${X#*.}
echo "bus/usb/$B/$D"
A=1 B=$A; echo "standalone=[$A][$B]"
a=1; a=2 b=$a c=$b; echo "chain=$a$b$c"
x=old
x=new echo "command-word=$x"
echo "restored=$x"
A=1 B=$A true; echo "temporary=[$A][$B]"
unset u; u=1 v=$u true; echo "both-temporary=[$u][$v]"
p=1 q=2; echo "plain=$p$q"
m=first m=second; echo "overwritten=$m"
n=1 o=${n:-none}; echo "default-sees-it=$o"
r=; s=${r:-fallback}; echo "empty-uses-default=$s"
t=1 t=$t$t; echo "doubled=$t"
# A readonly variable refuses assignment: the message goes to standard
# error and the status is 2. The message itself is left out of this
# case, since the three shells word it differently, and the redirected
# form is catalogued as entry 37 - it still answers 0 here.
readonly ro=1
(ro=2) 2>/dev/null
echo "readonly-kept=$ro"
