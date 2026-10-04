#!/bin/sh
# tools/bench-report.sh - the article's numbers, measured on THIS machine,
# into one report file (Iteration 577). From the repository's top:
#     sh tools/bench-report.sh
# Keep the machine otherwise idle while it runs: the numbers are CPU times
# and best-of-three wall times. About 10 minutes on a fast x86-64; on a
# slow one, smaller:   SCALE=10 ROUNDS=5 sh tools/bench-report.sh
# A static dash, for the memory and start rows, needs musl-gcc - Debian
# and Ubuntu: apt install musl-tools; Gentoo: emerge musl - and the
# network, to fetch dash's source. Without them that row is skipped.
set -u
cd "$(dirname "$0")/.." || exit 1
SCALE=${SCALE:-25}; ROUNDS=${ROUNDS:-7}
# REPORT names the file instead (657: tools/pack-results.sh, which packs it)
report=${REPORT:-"$PWD/bench-report-$(uname -n)-$(date -u +%Y%m%dT%H%MZ).txt"}
work=$(mktemp -d)
: > "$report"
say() { printf '%s\n' "$*" | tee -a "$report"; }
section() { say ""; say "== $* =="; }
run() { "$@" 2>&1 | tee -a "$report"; }

say "relf benchmark report, $(date -u)"
say "commit: $(git log -1 --format='%h %s' 2>/dev/null | cut -c1-72)"
say "SCALE=$SCALE ROUNDS=$ROUNDS"

section machine
run uname -a
cpu=$(grep -m1 -E '^(model name|Hardware|Processor)' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//')
say "cpu: ${cpu:-unknown}"
say "cores: $(nproc 2>/dev/null || echo unknown)"
g=/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
[ -r $g ] && say "governor: $(cat $g)"
say "memory: $(sed -n 's/^MemTotal: *//p' /proc/meminfo)"
for c in cc go python3 ruby gforth pforth bash dash busybox musl-gcc; do
    p=$(command -v $c 2>/dev/null) || { say "$c: not installed"; continue; }
    case $c in
        cc) v=$(cc --version 2>/dev/null | head -1) ;;
        go) v=$(go version 2>/dev/null) ;;
        python3|ruby|gforth) v=$($c --version 2>&1 | head -1) ;;
        pforth) v=$(echo BYE | pforth 2>&1 | grep -o 'V[0-9.]*' | head -1) ;;
        bash) v=$(bash --version | head -1) ;;
        dash) v=$(dpkg-query -W -f '${Version}' dash 2>/dev/null)   # no --version
              [ -n "$v" ] || v=$(ls -d /var/db/pkg/app-shells/dash-* 2>/dev/null | sed 's,.*/,,')
              [ -n "$v" ] || v=unknown ;;
        busybox) v=$(busybox 2>&1 | head -1) ;;
        *) v=present ;;
    esac
    say "$c: $v ($p)"
done

section build
run sh -c 'make 2>&1 | tail -2'
[ "$(uname -m)" = x86_64 ] && run sh -c 'make relfshasm64 2>&1 | tail -2'
# the native shell (Iteration 642): x86-64 only, as the native back end is
[ "$(uname -m)" = x86_64 ] && run sh -c 'make relfsh-native 2>&1 | tail -2'
run sh -c 'ls -l relfsh relfsh64 relfsh32 relfshasm64 relfsh-native 2>/dev/null'

section "a static dash"
sdash=
if command -v musl-gcc >/dev/null 2>&1; then
    url=http://archive.ubuntu.com/ubuntu/pool/main/d/dash/dash_0.5.12.orig.tar.gz
    if ( cd "$work" && { curl -s -f -O $url || wget -q $url; } &&
         tar xzf dash_0.5.12.orig.tar.gz && cd dash-0.5.12 &&
         CC=musl-gcc CFLAGS=-Os LDFLAGS=-static ./configure --quiet >/dev/null 2>&1 &&
         make -s >/dev/null 2>&1 && strip src/dash ); then
        sdash="$work/dash-0.5.12/src/dash"
        say "dash 0.5.12, musl-gcc -Os -static, stripped: $(wc -c < "$sdash") bytes"
    fi
fi
[ -n "$sdash" ] || say "skipped: no musl-gcc, or dash's source could not be fetched or built"

section "memory (tools/mem-profile.py)"
if [ -n "$sdash" ]; then run env STATIC_DASH="$sdash" python3 tools/mem-profile.py
else run python3 tools/mem-profile.py; fi

section "shell speed (tools/bench-vm.py: CPU time as a ratio to the first shell, SCALE=$SCALE, $ROUNDS rounds)"
cfg="$work/shells.cfg"; : > "$cfg"
if p=$(command -v dash); then echo "dash|/tmp|$p {w}" >> "$cfg"; else say "no dash: the ratios are to the first shell below"; fi
[ -n "$sdash" ] && echo "dash, static (musl)|/tmp|$sdash {w}" >> "$cfg"
p=$(command -v busybox) && echo "busybox ash|/tmp|$p ash {w}" >> "$cfg"
p=$(command -v bash) && echo "bash|/tmp|$p {w}" >> "$cfg"
[ -x ./relfshasm64 ] && echo "relfsh, asm engine|/tmp|$PWD/relfshasm64 {w}" >> "$cfg"
p=$(readlink -f ./relfsh) && echo "relfsh, C engine|/tmp|$p {w}" >> "$cfg"
[ -x ./relfsh-native ] && echo "relfsh, native|/tmp|$PWD/relfsh-native {w}" >> "$cfg"
run cat "$cfg"
run env SCALE="$SCALE" WL="loop fn str arith realistic start" python3 tools/bench-vm.py "$ROUNDS" "$cfg"

section "languages (bench/langs/run.py: ms, best of 3)"
run sh -c 'cd bench/langs && python3 run.py'

rm -rf "$work"
say ""
say "report: $report"
