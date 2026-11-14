#!/bin/sh
# tools/xarch-root.sh DIR - the AArch64 and RISC-V headers and libgcc.a that tools/xarch-check.sh's
# Clang build needs, fetched with apt-get download and unpacked into DIR - not installed, so nothing
# conflicts with gcc-multilib (Iteration 945). Then: XARCH_ROOT=DIR sh tools/xarch-check.sh
set -e
[ -n "$1" ] || { echo "usage: $0 DIR" >&2; exit 2; }
mkdir -p "$1/debs"
cd "$1/debs"
v=$(gcc -dumpversion | cut -d. -f1)
for a in arm64 riscv64; do
    apt-get download "libc6-dev-$a-cross" "linux-libc-dev-$a-cross" "libgcc-$v-dev-$a-cross"
done
for f in *.deb; do dpkg -x "$f" ..; done
echo "unpacked into $1"
