# quoting-300.sh - parsing corners nothing had tested (Iteration 300):
# nested backquotes, where a backslash before ` \ or $ is removed from
# the command text (XCU 2.6.3), and line continuations in the places
# they are allowed - including inside $(( )), where one had stopped
# working when arithmetic started being encoded in Iteration 286.
v=abc; w='x y'
echo "[`echo \`echo deep\``]"
echo "[`echo \$v`] [`echo \\\\`]"
echo "[$(echo `echo mixed`)]"
echo "[`echo one; echo two`]"
echo "[$(( 1 +\
 2 ))] [$(( 2 *\
 3 ))]"
echo a\
b
echo "a\
b"
echo 'a\
b'
x=va\
lue; echo "[$x]"
echo "[${v}${v}] [${v}x] [x${v}]"
echo "[${w:+"$w"}] [${w:+$w}]"
echo "[${v#"a"}] [${v#'a'}] [${v#a}]"
echo "[$(echo '$notexpanded')] [$(echo "$v")]"
eval 'echo eval-one'
eval echo eval-two
eval 'y=set'; echo "[$y]"
eval 'false'; echo "rc=$?"
eval 'for i in 1 2; do echo loop$i; done'
case "a|b" in "a|b") echo quoted-pipe;; esac
case ")" in ")") echo paren;; esac
case abc in a"b"c) echo mixed-quote;; esac
! false; echo "neg rc=$?"
{ ! false; } && echo group-neg
