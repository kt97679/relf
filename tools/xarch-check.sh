#!/bin/sh
# tools/xarch-check.sh - cv8.c on AArch64 and RISC-V, under qemu (Iteration 937).
#
# RELF.md's criteria for what forth-vm-evolution's findings bring (phase 2): portable - both cell
# widths, and AArch64 and RISC-V as relf checks them. The verify covers x86-64 and i386; this covers
# the other two, for any change to engine/cv8.c. For each: cv8.c built static by the cross compiler;
# Forth's CORE suite with relf's +LOOP tests (tests/tester.fr, core-extra.fth, coreplus-loop.fth) on
# forth/kernel64.img - the x86 image, as images are portable - its output compared line for line with
# relf64's; then rill3's suite (tests/cm/run) on that engine. qemu's time measures nothing (CV8.md 10).
#
# The engine is built as the Makefile builds it: without the C library, on engine/rt-linux.c (945);
# XARCH_RT=libc builds it static with the library instead, as 937 did. Needs qemu-user, and one of two
# compilers. gcc-aarch64-linux-gnu and gcc-riscv64-linux-gnu (apt) - which on Debian and Ubuntu conflict
# with gcc-multilib, the i386 half of every verify: installing them removes it, and the verify then
# skips the 4-byte engine and fails (found at 937); or, with no library to link, Clang and ld.lld with
# the targets' headers and libgcc.a unpacked, not installed - tools/xarch-root.sh DIR fetches and
# unpacks them, and XARCH_ROOT=DIR points here (945). tools/container-setup.sh installs neither. Prints a line per
# architecture and exits 1 if any differs or fails. The shell's suite runs too with XARCH_SHELL=1:
# under qemu six of its assertions fail on any engine, 933's as well - $0 and re-exec see the qemu
# wrapper, PATH=. cannot find qemu, qemu dies on SIGQUIT, and AArch64 and RISC-V do not trap on a zero
# divisor - so it is reported, not judged.
cd "$(dirname "$0")/.." || exit 2
d=$(mktemp -d) || exit 2
trap 'rm -rf "$d"' EXIT
bad=0
# the Makefile's RT_CFLAGS (no -no-pie: Clang ignores it, and a static link is not PIE)
RT="-static -nostdlib -fno-stack-protector -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -fno-asynchronous-unwind-tables"
RT="$RT -ffunction-sections -fdata-sections -Wl,--gc-sections"
{ cat tests/tester.fr tests/core-extra.fth tests/coreplus-loop.fth; echo BYE; } > "$d/core.fth"
./relf64 forth/kernel64.img < "$d/core.fth" 2>&1 | tr -d '\r' > "$d/core-x86.txt"
for a in aarch64 riscv64; do
    if ! command -v "qemu-$a" >/dev/null; then echo "$a: skipped - qemu-$a missing"; continue; fi
    if [ "${XARCH_RT:-nolibc}" = libc ]; then
        cc="$a-linux-gnu-gcc -O2 -Wall -static"; src=engine/cv8.c; lib=
        command -v "$a-linux-gnu-gcc" >/dev/null || { echo "$a: skipped - $a-linux-gnu-gcc missing"; continue; }
    elif command -v "$a-linux-gnu-gcc" >/dev/null; then
        cc="$a-linux-gnu-gcc -O2 -Wall $RT"; src="engine/cv8.c engine/rt-linux.c"; lib=-lgcc
    elif [ -n "$XARCH_ROOT" ] && [ -d "$XARCH_ROOT/usr/$a-linux-gnu/include" ] && command -v clang >/dev/null; then
        inc=$(clang -print-resource-dir)/include
        cc="clang --target=$a-linux-gnu -O2 -Wall -nostdinc -isystem $inc -isystem $XARCH_ROOT/usr/$a-linux-gnu/include"
        cc="$cc $RT -fuse-ld=lld"; src="engine/cv8.c engine/rt-linux.c"
        lib=$(ls "$XARCH_ROOT"/usr/lib/gcc-cross/$a-linux-gnu/*/libgcc.a | head -1)
    else echo "$a: skipped - neither $a-linux-gnu-gcc nor XARCH_ROOT with clang"; continue; fi
    # shellcheck disable=SC2086
    if ! $cc -o "$d/relf-$a" $src $lib 2>"$d/cc.log"; then
        echo "$a: cv8.c does not build"; head -5 "$d/cc.log"; bad=1; continue; fi
    printf '#!/bin/sh\nexec qemu-%s %s "$@"\n' "$a" "$d/relf-$a" > "$d/run-$a"; chmod +x "$d/run-$a"
    "$d/run-$a" forth/kernel64.img < "$d/core.fth" 2>&1 | tr -d '\r' > "$d/core-$a.txt"
    if cmp -s "$d/core-x86.txt" "$d/core-$a.txt"; then core=same; else core=DIFFERS; bad=1; fi
    cm=$(CM_ENGINE="$d/run-$a" sh tests/cm/run 2>&1 | tail -1)
    case $cm in *" 0 failed"*) ;; *) bad=1 ;; esac
    line="$a: CORE $core as x86's; rill3: $cm"
    if [ -n "$XARCH_SHELL" ]; then
        sh tools/embed.sh "$d/relf-$a" kernel64-shell.img "$d/relfsh-$a.bin"
        printf '#!/bin/sh\nexec qemu-%s %s "$@"\n' "$a" "$d/relfsh-$a.bin" > "$d/relfsh-$a"; chmod +x "$d/relfsh-$a"
        sh=$(THIS_SH="$d/relfsh-$a" bash tests/shell/run-all 2>/dev/null | awk '{s+=$1; f+=$3} END {print s+0 " assertions, " f+0 " failed"}')
        line="$line; shell: $sh (six fail under qemu on any engine)"
    fi
    echo "$line"
done
exit $bad
