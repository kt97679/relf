# large-expansion.sh - expansions far past the buffers they used to be cut
# at (Iteration 251): command substitution output was 256 bytes, the
# expanded words of a line 4 KB, and a for list 256 bytes - all dropped
# without a word. Variable values (255 characters) are still limited, so
# nothing here is assigned a long value.
echo $(seq 1 3000) | wc -w
echo "$(seq 1 20000)" | tail -1
x=$(seq 1 50); echo ${#x}
for i in $(seq 1 3000); do n=$i; done; echo n=$n
for w in a b c; do for v in $(seq 1 300); do m=$w$v; done; echo $m; done
set -- $(seq 1 400); for a in "$@"; do k=$a; done; echo $k $#
echo $(seq 1 2000) ${nope:-default} $(echo tail) | wc -w
y=abc; echo $(seq 1 3000 | tr '\n' ' ' | wc -c) ${y%c} ${nope:-$(echo word)}
echo "$(head -c 100000 /dev/zero | tr '\0' a)" | wc -c
