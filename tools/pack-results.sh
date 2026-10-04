#!/bin/sh
# tools/pack-results.sh - what a run on another machine sends back, in one
# file (Iteration 657). From the repository's top, the machine otherwise
# idle:
#     sh tools/pack-results.sh               clean, measure, verify, pack
#     sh tools/pack-results.sh --no-verify   skip the acceptance suite
#     sh tools/pack-results.sh --no-clean    keep every untracked file
#     sh tools/pack-results.sh --no-profile  skip the native profile
# About twenty minutes on a fast x86-64: tools/bench-report.sh's ten -
# SCALE and ROUNDS pass through to it - then the profile, then
# tests/verify. It prints a summary, and the pack's path last:
#     relf-results-HOST-COMMIT-UTC.tar.gz, in the checkout's top
# Send that one file back. In it:
#     SUMMARY.txt        what ran, each step's exit status and time, the
#                        checkout before and after, what the clean removed
#     reports/           this run's tools/bench-report.sh report, and every
#                        bench-report-*.txt in the checkout's top that
#                        bench/reports/ does not hold yet - as they came
#     bench.log          bench-report.sh's own output
#     native-written.log tools/native-written.py: the image's written pages
#     profile-*.log      tools/native-prof.py on the bench-vm workloads x100
#     verify.log         tests/verify, with its exit status in SUMMARY.txt
#     untracked.txt, cleaned.txt   what the clean found, and removed
#
# The clean (prompts/18: a run starts from a known state) removes every
# untracked file, ignored or not - build products, caches, files of older
# layouts. It keeps what came from elsewhere: a report bench/reports/ does
# not hold byte for byte, a file in bench/reports/, a pack, a bundle.
#
# Receiving one: tar xzf PACK -C DIR; read SUMMARY.txt first; put
# reports/* into bench/reports/ as they came, and commit them (prompts/11).
set -u
cd "$(dirname "$0")/.." || exit 1
LC_ALL=C; export LC_ALL
exec < /dev/null

clean=1 verify=1 profile=1
for a in "$@"; do
    case $a in
        --no-clean) clean=0 ;;
        --no-verify) verify=0 ;;
        --no-profile) profile=0 ;;
        -h|--help) sed -n '2,/^set -u/s/^# \{0,1\}//p' "$0"; exit 0 ;;
        *) echo "pack-results: unknown argument: $a (--help lists them)" >&2; exit 2 ;;
    esac
done

host=$(uname -n)
utc=$(date -u +%Y%m%dT%H%MZ)
commit=$(git rev-parse --short HEAD) || { echo "pack-results: not a git checkout" >&2; exit 1; }
pack="$PWD/relf-results-$host-$commit-$utc.tar.gz"
stage=$(mktemp -d) || exit 1
trap 'rm -rf "$stage"' EXIT
trap 'exit 130' INT TERM
sum="$stage/SUMMARY.txt"
failed=
note() { printf '%s\n' "$*" >> "$sum"; }

# step NAME CMD... - CMD's output into NAME.log in the pack; its exit
# status and time named in the summary, never lost (prompts/11)
step() {
    name=$1; shift
    echo "== $name ==" >&2
    t0=$(date +%s)
    "$@" > "$stage/$name.log" 2>&1
    st=$?
    note "step $name: status $st, $(( $(date +%s) - t0 )) s"
    [ $st = 0 ] || failed="$failed $name"
    return $st
}

note "relf results, $(date -u)"
note "host: $host ($(uname -srm))"
note "commit: $(git log -1 --format='%H %s' | cut -c1-120)"
note "arguments: ${*:-none}; SCALE=${SCALE:-25} ROUNDS=${ROUNDS:-7}"
note "checkout before - tracked files changed (results then are not the commit's):"
git status --porcelain --untracked-files=no | sed 's/^/    /' >> "$sum"

# The reports lying in the checkout's top: those bench/reports/ does not
# hold byte for byte go into the pack, and the clean keeps them.
new_report() {   # path: true when the repository does not hold it yet
    held=bench/reports/$(basename "$1")
    ! { git ls-files --error-unmatch "$held" >/dev/null 2>&1 && cmp -s "$1" "$held"; }
}
mkdir -p "$stage/reports"
for r in bench-report-*.txt; do
    [ -f "$r" ] || continue
    if new_report "$r"; then cp "$r" "$stage/reports/"; note "report not in bench/reports/ yet, packed: $r"
    else note "report already in bench/reports/: $r"; fi
done

if [ $clean = 1 ]; then
    echo "== clean ==" >&2
    git clean -ndx | sed -n 's/^Would remove //p' > "$stage/untracked.txt"
    : > "$stage/cleaned.txt"
    while IFS= read -r p; do
        case $p in
            bench-report-*.txt) if new_report "$p"; then note "clean kept: $p"; continue; fi ;;
            bench/reports/*|relf-results-*.tar.gz|*.bundle) note "clean kept: $p"; continue ;;
        esac
        rm -rf "./$p" && printf '%s\n' "$p" >> "$stage/cleaned.txt"
    done < "$stage/untracked.txt"
    note "clean: $(wc -l < "$stage/untracked.txt" | tr -d ' ') untracked paths, $(wc -l < "$stage/cleaned.txt" | tr -d ' ') removed (cleaned.txt)"
else
    git status --porcelain --ignored | sed -n -e 's/^?? //p' -e 's/^!! //p' > "$stage/untracked.txt"
    note "clean: skipped (--no-clean); untracked paths: $(wc -l < "$stage/untracked.txt" | tr -d ' ') (untracked.txt)"
fi

# The measurements first, on a quiet machine and a fresh build: the
# report builds what it runs.
report="$PWD/bench-report-$host-$utc.txt"
echo "   (tools/bench-report.sh: about ten minutes)" >&2
step bench env REPORT="$report" sh tools/bench-report.sh
[ -f "$report" ] && cp "$report" "$stage/reports/" && note "this run's report: reports/$(basename "$report")"

if [ -x ./relfsh-native ]; then
    step native-written python3 tools/native-written.py ./relfsh-native
    if [ $profile = 1 ]; then
        wl=$(mktemp -d)
        python3 - "$wl" << 'EOF'
import os, re, sys
for f in os.listdir('tests/bench-vm'):        # bench-vm.py's SCALE, at 100
    if f.endswith('.sh'):
        t = open('tests/bench-vm/' + f).read()
        open(os.path.join(sys.argv[1], f), 'w').write(
            re.sub(r'-lt (\d+)', lambda m: '-lt %d' % (int(m.group(1)) * 100), t))
EOF
        for w in fn arith str realistic; do
            step "profile-$w" python3 tools/native-prof.py ./relfsh-native "$wl/$w.sh"
        done
        rm -rf "$wl"
    fi
else
    note "no relfsh-native (not x86-64, or its build failed): no memory decomposition, no profile"
fi

if [ $verify = 1 ]; then
    echo "   (tests/verify: some minutes)" >&2
    step verify sh tests/verify
    note "verify's lines other than ok, and its last line:"
    grep -v -e '^ok ' -e '^==' -e '^$' "$stage/verify.log" | sed 's/^/    /' >> "$sum"
fi

note "checkout after - each line should be explained (prompts/07):"
git status --porcelain | sed 's/^/    /' >> "$sum"
[ -n "$failed" ] && note "steps that failed:$failed"

tar czf "$pack" -C "$stage" . || { echo "pack-results: tar failed; the results were in $stage" >&2; trap - EXIT; exit 1; }
cat "$sum"
echo
[ -n "$failed" ] && echo "steps that failed:$failed - their logs are in the pack"
echo "pack: $pack"
