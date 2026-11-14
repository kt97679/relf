#!/bin/sh
# port/gforth/build.sh OUT - relfsh on gforth 0.7.3: the port and relf's shell
# sources loaded, saved by gforthmi as a relocatable image OUT, which runs on
# gforth and gforth-fast alike:
#     gforth-fast --appl-image OUT [shell arguments]
# (--appl-image: every argument after it is the shell's, none gforth's). The
# data and return stacks are the lab designs' (256 KB, 64 KB): gforth's 16 KB
# default is the size of the gap the forth command takes. The image records
# them. SYSCALL is C, port/gforth/relfsys.c, built here as OUT.so: the
# image opens it by its absolute path at boot. Run from relf's top; needs a
# C compiler.
set -e
out=$1
: "${GFORTHD:=$(ls /usr/lib/*/gforth/0.7.3/gforth-ditc /usr/lib/gforth/0.7.3/gforth-ditc 2>/dev/null | head -1)}"
export GFORTHD
here=$(pwd)
case $out in /*) ;; *) out=$here/$out ;; esac
tmp=$(mktemp -d)
${CC:-cc} -shared -fPIC -Os -s -o "$out.so" port/gforth/relfsys.c
RELFSYS=$out.so; export RELFSYS
cd "$tmp"
gforthmi "$out.tmp" -d 256k -r 64k \
    "$here/port/gforth/sys.fs" "$here/port/gforth/kernel.4" "$here/port/relf.4" "$here/port/os.4" \
    "$here/port/kernel-io.4" "$here/port/gforth/host.4" "$here/forth/pool.4" "$here/port/shadow.4" \
    "$here/shell/shell.4" "$here/shell/edit.4" "$here/shell/tree.4" "$here/port/gforth/boot.4" \
    > build.log 2>&1 || true
cd "$here"
if [ ! -s "$out.tmp" ] || grep -qE 'Undefined word|error|Error' "$tmp/build.log"; then
    echo "port/gforth/build.sh: $out not built; the build said:" >&2
    grep -vE '^redefined|^ +[0-9A-F]+ +[0-9A-F]+ +[0-9A-F]+$' "$tmp/build.log" | head -20 >&2
    rm -rf "$tmp" "$out.tmp"; exit 1
fi
mv "$out.tmp" "$out"
rm -rf "$tmp"
wc -c < "$out"
