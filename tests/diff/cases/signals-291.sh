# signals-291.sh - trap conditions given as numbers as well as names, and
# kill by number, name and -s (Iteration 291: a numeric condition ate one
# of the shell's own stack items and the next command died with a return
# stack overflow). dash and bash agree on all of this.
# signal conditions by number and by name
trap 'echo T-num' 2; trap > /tmp/relf-trap-list.$$; wc -l < /tmp/relf-trap-list.$$; rm -f /tmp/relf-trap-list.$$; kill -2 $$; echo after-num; trap - 2
trap 'echo T-name' INT; kill -INT $$; echo after-name; trap - INT
trap 'echo T-usr' USR1; kill -s USR1 $$; echo after-usr; trap - USR1
trap 'echo T-zero' 0; trap > /tmp/relf-trap-list.$$; wc -l < /tmp/relf-trap-list.$$; rm -f /tmp/relf-trap-list.$$; trap - 0; echo after-zero
trap '' 15; trap > /tmp/relf-trap-list.$$; wc -l < /tmp/relf-trap-list.$$; rm -f /tmp/relf-trap-list.$$; trap - 15
trap 'echo bad' 99 2>/dev/null; echo "bad-num rc=$?"
trap 'echo bad' NOSUCH 2>/dev/null; echo "bad-name rc=$?"
trap 'echo k' KILL 2>/dev/null; echo "kill-trap rc=$?"
kill -l 9; kill -l 15; kill -l 1
kill -0 $$; echo "kill0 rc=$?"
kill -s TERM 99999999 2>/dev/null; echo "kill-bad rc=$?"
kill -TERM 99999999 2>/dev/null; echo "kill-bad2 rc=$?"
( trap 'echo sub-exit' EXIT; echo sub-body )
( trap - EXIT; echo no-exit-trap )
echo done
