# builtins-269.sh - echo, printf, true and false as builtins (Iteration 269),
# compared with bash's. Error messages differ in wording and go to /dev/null.
printf '%s|%5s|%-5s|%.2s|%5.1s|\n' abc abc abc abc abc
printf '%d|%5d|%-5d|%05d|%+d|% d|%.3d|%8.3d|%-8.3d|\n' 42 42 42 42 42 42 42 42 42
printf '%d|%05d|%+d|%.3d|\n' -42 -42 -42 -42
printf '%i %u %o %x %X\n' 255 255 255 255 255
printf '%d %d %d %d\n' 010 0x1f "'A" -0x10
printf '%c%c%c|\n' hello w ''
printf '%s\n' a b c
printf '%s=%s\n' k1 v1 k2
printf 'no conversions\n' extra args
printf '%%|%5%|\n' 2>/dev/null; echo "st=$?"
printf 'tab\there\\back \101\102 \0101 \x41\n'
printf '%b|\n' 'a\tb' '\0101' 'stop\cnever'
echo after-stop
printf '%*d|%-*d|%.*s|\n' 6 7 6 7 2 abcdef
printf '%d\n' 12abc 2>/dev/null
echo "st=$?"
printf '%s\n'
printf '[%s]\n' ''
echo hello world
echo -n no-newline; echo
echo -e 'a\tb\nc' '\x41\0102'
echo -E 'a\tb'
echo -ne 'x\cy' z; echo
echo -- -n
echo -x
echo 'a\tb'
echo
echo -neE 'q\tq'
true; echo "true=$?"
false; echo "false=$?"
if true && ! false; then echo both; fi
x=echo; $x via-expansion
"printf" "%s\n" quoted-name
printf "%s\n" "a b" | while read -r l; do echo "[$l]"; done
echo to-file > /tmp/relf-b269.$$; cat /tmp/relf-b269.$$; rm -f /tmp/relf-b269.$$
v=$(printf "%05.1s" xyz); echo "[$v]"
