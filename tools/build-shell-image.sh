#!/bin/sh
# tools/build-shell-image.sh ENGINE KERNEL OUT SOURCE... - build a shell
# image: KERNEL with each SOURCE loaded in order, MAIN made the boot word,
# saved as OUT. Run it where the sources are, with relative names: the
# kernel reads its input 256 columns at a time (80 until Iteration 514),
# and a long absolute path once stopped the build (Iteration 150's
# long-path check guards that).
#
# An image is installed only if it starts the shell AND its build said
# nothing that sounds like an error - either failure leaves OUT as it
# was and says why. Moved here from the relfsh script at Iteration 506,
# when relfsh became a binary; the Makefile passes SHELL_SOURCES, so the
# list of sources is kept in one place.
engine=$1 kernel=$2 out=$3
shift 3
tmp=$out.tmp.$$
{
    for f in "$@"; do printf 'S" %s" INCLUDED\n' "$f"; done
    printf "' MAIN SET-BOOT\nS\" %s\" SAVE-SYSTEM\nBYE\n" "$tmp"
} | "$engine" "$kernel" > "$tmp.log" 2>&1
if [ ! -s "$tmp" ]; then
    echo "build-shell-image: $out was not written; the build said:" >&2
    tr -d '\r' < "$tmp.log" | grep -v '^[[:space:]]*$' | tail -20 | sed 's/^/    /' >&2
    rm -f "$tmp" "$tmp.log"
    exit 1
fi
probe=$("$engine" "$tmp" -c 'echo relf-shell-ok' 2>/dev/null </dev/null)
complaint=$(tr -d '\r' < "$tmp.log" |
    grep -E 'Undefined word|[Uu]nderflow|[Oo]verflow|Can.t |not unique' | head -1)
if [ "$probe" != relf-shell-ok ] || [ -n "$complaint" ]; then
    if [ "$probe" != relf-shell-ok ]; then
        echo "build-shell-image: $out built, but it does not start the shell." >&2
    else
        echo "build-shell-image: $out built, but the build reported errors." >&2
    fi
    [ -n "$complaint" ] && echo "build-shell-image: first complaint: $complaint" >&2
    echo "build-shell-image: the build said:" >&2
    tr -d '\r' < "$tmp.log" | grep -vE '^(Redefining: |OK$|Welcome to Forth)' |
        grep -v '^[[:space:]]*$' | head -20 | sed 's/^/    /' >&2
    rm -f "$tmp" "$tmp.log"
    exit 1
fi
mv -f "$tmp" "$out"
rm -f "$tmp.log"
