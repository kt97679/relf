# bg-stdin-355.sh - an asynchronous command reads /dev/null unless it
# redirects its own input (XCU 2.9.3). Without that, `cat &` in a script
# competes with the shell for the rest of the file and the script hangs,
# which is how busybox's suite catches it (Iteration 355).
cat & wait; echo "bare-cat=$?"
echo piped | cat & wait; echo "pipe=$?"
cat < /etc/hostname > /dev/null & wait; echo "explicit-input=$?"
{ read line; echo "read=[$line]"; } & wait
sh -c 'read x; echo "child-read=[$x]"' & wait
echo still-here
