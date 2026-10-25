true; a=$?; false; b=$?; sh -c 'exit 7'; c=$?; echo $a $b $c
grep -q nothing-of-this /dev/null; echo grep said $?
sh -c 'echo to the log' > /dev/null; d=$?; sh -c 'exit 3' | cat; e=$?; echo $d $e
false; [ $? = 1 ] && echo false is 1
