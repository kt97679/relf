#!/bin/sh
# build-native-shell.sh - the native shell, as build-shell-image.sh builds
# CV8's (Iteration 638): the native kernel loads the shell's sources with
# its own compiler, then forth/save-system-native.4's SAVE-SYSTEM writes the
# native system, an ELF executable, with MAIN as its boot word.
#   sh tools/build-native-shell.sh OUT     (needs ./native-kernel)
out=$1; tmp=$out.tmp.$$
{
    # (688) NATIVE_LAYOUT_PAD=N: N bytes of code space left empty before the
    # first source, so every word compiled after it lands N bytes further
    # on - tools/native-ab-layouts.py builds a change over several such
    # layouts, so that where the hot code falls averages out of an A/B.
    [ -n "${NATIVE_LAYOUT_PAD:-}" ] && printf '%d ALLOT\n' "$NATIVE_LAYOUT_PAD"
    for f in forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 \
             forth/save-system.4 forth/save-system-native.4 \
             shell/shell.4 shell/edit.4 shell/tree.4; do
        printf 'S" %s" INCLUDED\n' "$f"
    done
    printf "' MAIN SET-BOOT\nS\" %s\" SAVE-SYSTEM\nBYE\n" "$tmp"
} | ./native-kernel > "$tmp.log" 2>&1
complaint=$(tr -d '\r' < "$tmp.log" | grep -E 'Undefined word|[Uu]nderflow|[Oo]verflow|Can.t |not unique|native' | head -1)
if [ ! -s "$tmp" ] || [ -n "$complaint" ]; then
    echo "build-native-shell: $out not built${complaint:+: $complaint}" >&2
    tr -d '\r' < "$tmp.log" | grep -vE '^(Redefining: |OK$|Welcome to Forth)' | grep -v '^[[:space:]]*$' | tail -8 >&2
    rm -f "$tmp" "$tmp.log"; exit 1
fi
chmod 755 "$tmp"
case $tmp in /*) run=$tmp ;; *) run=./$tmp ;; esac      # (688) an absolute path too
probe=$("$run" -c 'echo relf-shell-ok' 2>&1 < /dev/null)
if [ "$probe" != relf-shell-ok ]; then
    echo "build-native-shell: $out built, but it does not start the shell: $probe" | head -3 >&2
    rm -f "$tmp" "$tmp.log"; exit 1
fi
rm -f "$tmp.log"; mv -f "$tmp" "$out"
