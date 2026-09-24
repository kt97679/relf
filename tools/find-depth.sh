#!/bin/bash
# tools/find-depth.sh [OUTDIR] - how many dictionary entries does a
# lookup visit?
#
# This is the instrument that found the hashed-word-list regression, in
# kt97679/forth-vm-evolution. It is kept here because the fix now lives
# in this tree and the claim behind it should be re-measurable rather
# than quoted from a commit message.
#
# METHOD: add ONE counter to the outer loop of SEARCH-WORDLIST in a COPY
# of kernel.4, cross-compile a kernel with it, run a parse-heavy
# workload, print the counter. Nothing is modelled and nothing is
# shared between runs except the workload.
#
# WHY A COUNTER AND NOT A TIMER. A timer says a change helped; it does
# not say why, and it cannot distinguish "the dictionary search got
# cheaper" from "the machine was quieter". This counts the thing the
# change was supposed to affect, and it is exact - the same input gives
# the same number on any machine, so it needs no error bar and no
# repetitions.
#
# WHERE THE COUNTER GOES. The outer loop of SEARCH-WORDLIST runs once
# per dictionary entry examined, and its first act is to compare the
# candidate's name length. Incrementing there counts entries
# EXAMINED, which is the quantity the hash was supposed to reduce - not
# lookups performed, which it does not change.
#
# The instrumented tree is built in a scratch directory. Editing the
# tracked kernel.4 in place would leave the repository dirty if this
# script were interrupted, and a stale instrumented kernel that then got
# committed would be very hard to notice.
set -e

# Every engine here is a measured subject, so it runs in a predictable
# environment rather than whatever the caller exported. LD_PRELOAD is
# the one that bites: a session that preloads a library into every
# process has it loaded into the engine too, which is unwanted work
# inside the thing being measured - and a 64-bit library against the
# 32-bit engine makes ld.so write a complaint per process.
unset LD_PRELOAD

cd "$(dirname "$0")/.."
ROOT=$PWD
O=${1:-/tmp/find-depth}
rm -rf "$O"; mkdir -p "$O"

for f in "$ROOT"/*.4 "$ROOT"/kernel64.img "$ROOT"/relf64; do cp -L "$f" "$O/"; done

# The workload: interpreted arithmetic, half of whose tokens are
# NUMBERS. A number is the worst case for a dictionary search because it
# is never found, so the whole thread is walked before the system gives
# up and converts it. Generated here rather than committed - it is 4000
# identical lines and carrying them as a file earns nothing.
{
    i=0
    while [ $i -lt 4000 ]; do echo '1 2 + 3 4 + XOR DROP'; i=$((i + 1)); done
    printf 'FINDITER @ . CR\nBYE\n'
} > "$O/work.fth"

python3 - "$O/kernel.4" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
# Declared next to NAMEBUF so it is an ordinary kernel variable and gets
# cross-compiled, relocated and saved like any other.
a = "VARIABLE NAMEBUF ( --- a-addr)"
b = "    DUP C@ 31 AND NAMEBUF C@ = IF"
for t in (a, b):
    if s.count(t) != 1:
        sys.exit("find-depth: %r appears %d times in kernel.4; the "
                 "instrumentation point has moved" % (t, s.count(t)))
s = s.replace(a, "VARIABLE FINDITER ( --- a-addr)\n" + a, 1)
s = s.replace(b, "   1 FINDITER +!\n" + b, 1)
open(p, 'w').write(s)
PY

( cd "$O" && printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\n' \
    | ./relf64 kernel64.img >/dev/null 2>&1 )

N=$( cd "$O" && ./relf64 kernel64.img < "$O/work.fth" 2>&1 \
     | tr -d '\r' | grep -oE '[0-9]{3,}' | tail -1 )

[ -n "$N" ] || { echo "find-depth: no counter in the output - did the "\
"instrumented kernel build?"; exit 1; }

echo
printf '%-28s %14s\n' "workload" "4000 lines"
printf '%-28s %14s\n' "dictionary entries visited" "$N"
echo
echo "Measured in THIS tree with this script, same workload:"
printf '  %-26s %14s\n' "single chain (pre-hash)" "8,052,327"
printf '  %-26s %14s\n' "32 threads (now)" "288,009"
echo
echo "For scale, kt97679/forth-vm-evolution measured SOD32 - which never"
echo "lost the hash - at 397,720 on its own equivalent workload. RelF"
echo "now examines fewer entries than its ancestor, because its"
echo "dictionary is smaller at the same thread count."
