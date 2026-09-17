while read l; do echo "$l"; done < in.txt
{ echo a; echo b; } > out 2>&1
if true; then echo x; fi >> log
