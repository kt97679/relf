# command-path.sh - finding commands along PATH (Iteration 269): the
# location cache follows PATH changes, including PATH=... prefixes and an
# assignment to the inherited PATH; a cached command that disappears; a
# directory and a non-executable file named like the command.
d=$(mktemp -d) || exit 1
mkdir -p "$d/c1/dirtool" "$d/c2"
printf '#!/bin/sh\necho one\n' > "$d/c1/tool"
printf '#!/bin/sh\necho two\n' > "$d/c2/tool"
printf 'x\n' > "$d/c2/plain"
chmod +x "$d/c1/tool" "$d/c2/tool"
OLD=$PATH
PATH=$d/c1:$d/c2:$OLD
tool
PATH=$d/c2:$d/c1:$OLD
tool
PATH=$d/c1:$PATH tool
tool
cp "$d/c1/tool" "$d/c1/tool2"; tool2; rm "$d/c1/tool2"
PATH=$d/c1:$OLD
tool2 2>/dev/null; echo "gone st=$?"
dirtool 2>/dev/null; echo "dir st=$?"
PATH=$d/c2:$OLD
plain 2>/dev/null; echo "plain st=$?"
nosuch 2>/dev/null; echo "missing st=$?"
x=$(tool); echo "[$x]"
tool | cat
PATH=$OLD
rm -rf "$d"
