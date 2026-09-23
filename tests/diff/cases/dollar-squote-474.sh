# $'...' (POSIX.1-2024): single quotes in which a backslash escape stands
# for the byte it names (Iteration 474). bash is the reference - dash
# 0.5.12, installed here, predates it and reads `$'` as a dollar and a
# quote, which is why `dash -n` rejects this file at `\'`, by design.
show() { printf '[%s]' "$@" | od -An -c | tr -s ' '; }
show $'a\tb' $'n\nl' $'e\ez' $'bell\a' $'ff\fvt\v' $'cr\r'
show $'it\'s' $'q\"q' $'back\\slash'
show $'x\x41y' $'x\x4' $'o\101p' $'o\7' $'c\cAd'
show $'unknown\qz' $'cut\0gone' $''
show pre$'mid'post
show "dq$'stays'"
v=$'two\nlines'
printf '%s|' "$v"; echo
case $'\t' in "	") echo "tab matches";; *) echo "no match";; esac
