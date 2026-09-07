#!/bin/sh
# tools/build-shells-i386.sh - build i386 versions of the comparison
# shells, so `tests/sizes` can compare the 4-byte-cell build against
# something of its own word size.
#
# Why this exists: until Iteration 138 `tests/sizes` put the i386
# shell.4 build in the same ranked table as the distro's x86-64 dash,
# bash and the rest, and concluded shell.4 was the smallest shell on
# the list. That comparison was not fair and the conclusion did not
# survive fixing it - see PROGRESS.md's Iteration 138 entry.
#
# The distro ships no i386 shells (Ubuntu dropped general i386 support
# after 19.10), so they have to be built. Needs deb-src enabled:
#
#   sed -i 's/^Types: deb$/Types: deb deb-src/' \
#       /etc/apt/sources.list.d/ubuntu.sources
#   apt-get update
#   apt-get install -y gcc-multilib autoconf automake libtool
#
# Each shell is also built for x86-64 from the SAME source with the
# SAME flags, into build/shells-x86-64/. Comparing a locally built
# i386 binary against a distro-built 64-bit one would swap one unfair
# comparison for another - the distro's compiler version, optimisation
# flags and hardening options are not this machine's.
#
# mksh is deliberately absent: its build asserts on -m32 ("Use the
# documented way to build this") and it was not worth fighting for one
# more row.

set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)
OUT32="$ROOT/build/shells-i386"
OUT64="$ROOT/build/shells-x86-64"
WORK="$ROOT/build/src"
mkdir -p "$OUT32" "$OUT64" "$WORK"

build_one() {
    # $1 = source package, $2 = path to the built binary within it
    pkg="$1"; bin="$2"
    cd "$WORK"
    rm -rf "$pkg"-*
    apt-get source "$pkg" >/dev/null 2>&1
    dir=$(ls -d "$pkg"-*/ | head -1)
    cd "$dir"
    autoreconf -fi >/dev/null 2>&1 || true

    ./configure --host=i686-linux-gnu CC="gcc -m32" >/dev/null 2>&1
    make -j4 >/dev/null 2>&1
    cp "$bin" "$OUT32/$pkg"
    strip "$OUT32/$pkg"

    make clean >/dev/null 2>&1
    ./configure >/dev/null 2>&1
    make -j4 >/dev/null 2>&1
    cp "$bin" "$OUT64/$pkg"
    strip "$OUT64/$pkg"

    printf '%-8s i386 %8d   x86-64 %8d\n' \
        "$pkg" "$(stat -c%s "$OUT32/$pkg")" "$(stat -c%s "$OUT64/$pkg")"
}

build_one dash src/dash
build_one posh posh

echo ""
echo "Built into build/shells-i386/ and build/shells-x86-64/."
echo "tests/sizes picks them up automatically."
