#!/bin/sh
# tools/embed.sh ENGINE IMAGE OUT - one executable: the engine, the image
# appended, and a 16-byte trailer - "RELFIMG1" and the image's length,
# eight bytes little-endian - by which the engine finds the image in
# itself (cv8.c, embedded_image; Iteration 506). This is how relfsh is
# built: the shell as one file. POSIX sh only; nothing else at build time.
set -e
engine=$1 image=$2 out=$3
n=$(wc -c < "$image" | tr -d ' ')
tmp=$out.tmp.$$
cat "$engine" "$image" > "$tmp"
{
    printf 'RELFIMG1'
    i=0
    while [ "$i" -lt 8 ]; do
        printf "\\$(printf '%03o' $((n % 256)))"
        n=$((n / 256)); i=$((i + 1))
    done
} >> "$tmp"
chmod +x "$tmp"
mv -f "$tmp" "$out"
