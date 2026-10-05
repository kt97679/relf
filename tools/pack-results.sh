#!/bin/sh
# tools/pack-results.sh - one command on the user's machine, one file back
# (Iterations 657, 664; prompts/19-round-trip.md, whose template,
# prompts/19-round-trip.sh, this follows). From the repository's top:
#     sh tools/pack-results.sh               apply, clean, measure, pack
#     sh tools/pack-results.sh --no-apply    leave the checkout's commit as it is
#     sh tools/pack-results.sh --no-clean    keep every untracked file
#     sh tools/pack-results.sh --no-bench    skip tools/bench-report.sh
#     sh tools/pack-results.sh --no-profile  skip the native profile
#     sh tools/pack-results.sh --verify      tests/verify too, eight minutes more
# About three minutes on a fast x86-64, the machine otherwise idle. The
# acceptance suite runs here, on every commit; on the user's machine only
# when a reply asks for it (665: the user's time is the round trip's cost).
#
# 1. The newest bundle - relf-claude-iterN-*.bundle in $BUNDLE_DIR,
#    ~/Downloads unless set - is applied to master if it is new, and only
#    by fast-forward: not over changed tracked files, not when master has
#    commits the bundle lacks, not off master. If applying it changed this
#    script, the new one runs, from the start, with the same arguments.
# 2. The clean: every untracked path, ignored or not - build products,
#    caches, files of older layouts - moved to .clean-trash/, which keeps
#    one run's worth. Kept where they are: what came from elsewhere - a
#    report bench/reports/ does not hold byte for byte, a file in
#    bench/reports/, a pack, a bundle.
# 3. tools/bench-report.sh (SCALE and ROUNDS pass through to it),
#    tools/native-written.py, tools/native-prof.py on the bench-vm
#    workloads x100, and with --verify tests/verify - each output kept.
# 4. One file, printed last: relf-results-HOST-COMMIT-UTC.tar.gz in the
#    checkout's top. Send that back. In it: SUMMARY.txt - the bundle
#    applied, each step's exit status and time, the checkout before and
#    after, what the clean moved; reports/ - this run's report, and every
#    bench-report-*.txt in the top that bench/reports/ lacks, as they
#    came; each step's .log; untracked.txt and cleaned.txt.
#
# Receiving one: tar xzf PACK -C DIR; read SUMMARY.txt first; put
# reports/* into bench/reports/ as they came, and commit them (prompts/11).
#
# The body is one function, called on the last line: the shell has read
# all of it before a bundle can change this file under it.
main() {
set -u
cd "$(dirname "$0")/.." || exit 1
LC_ALL=C; export LC_ALL
exec < /dev/null
self=tools/pack-results.sh

clean=1 verify=0 profile=1 bench=1 apply=1
for a in "$@"; do
    case $a in
        --no-apply) apply=0 ;;
        --no-clean) clean=0 ;;
        --no-bench) bench=0 ;;
        --no-profile) profile=0 ;;
        --verify) verify=1 ;;
        --no-verify) verify=0 ;;     # the default since 665
        -h|--help) sed -n '2,/^main() {/s/^# \{0,1\}//p' "$self"; exit 0 ;;
        *) echo "pack-results: unknown argument: $a (--help lists them)" >&2; exit 2 ;;
    esac
done
git rev-parse --git-dir > /dev/null 2>&1 || { echo "pack-results: not a git checkout" >&2; exit 1; }

# 1. the newest bundle, applied by fast-forward; this script again, if changed
if [ $apply = 0 ]; then
    applied="not looked for (--no-apply)"
elif [ -n "${PACK_REEXEC:-}" ]; then
    applied="${PACK_APPLIED:-?}; this script changed with it, and ran again"
else
    changed=
    apply_bundle || exit 1
    if [ -n "$changed" ]; then
        echo "== $self changed with the bundle: running the new one ==" >&2
        PACK_REEXEC=1 PACK_APPLIED=$applied exec sh "$self" "$@"
    fi
fi

host=$(uname -n)
utc=$(date -u +%Y%m%dT%H%MZ)
commit=$(git rev-parse --short HEAD)
pack="$PWD/relf-results-$host-$commit-$utc.tar.gz"
stage=$(mktemp -d) || exit 1
trap 'rm -rf "$stage"' EXIT
trap 'exit 130' INT TERM
sum="$stage/SUMMARY.txt"
failed=

note "relf results, $(date -u)"
note "host: $host ($(uname -srm))"
note "commit: $(git log -1 --format='%H %s' | cut -c1-120)"
note "bundle: $applied"
note "arguments: ${*:-none}; SCALE=${SCALE:-25} ROUNDS=${ROUNDS:-7}"
note "checkout before - tracked files changed (results then are not the commit's):"
git status --porcelain --untracked-files=no | sed 's/^/    /' >> "$sum"

# The reports lying in the checkout's top: those bench/reports/ does not
# hold byte for byte go into the pack, and the clean keeps them.
mkdir -p "$stage/reports"
for r in bench-report-*.txt; do
    [ -f "$r" ] || continue
    if new_report "$r"; then cp "$r" "$stage/reports/"; note "report not in bench/reports/ yet, packed: $r"
    else note "report already in bench/reports/: $r"; fi
done

# 2. the clean, to .clean-trash/: one run's worth recoverable
if [ $clean = 1 ]; then
    echo "== clean ==" >&2
    git clean -ndx | sed -n 's/^Would remove //p' > "$stage/untracked.txt"
    : > "$stage/cleaned.txt"
    rm -rf .clean-trash.old
    [ -d .clean-trash ] && mv .clean-trash .clean-trash.old
    mkdir -p .clean-trash
    while IFS= read -r p; do
        case $p in
            .clean-trash/|.clean-trash.old/) continue ;;
            bench-report-*.txt) if new_report "$p"; then note "clean kept: $p"; continue; fi ;;
            bench/reports/*|relf-results-*.tar.gz|*.bundle) note "clean kept: $p"; continue ;;
        esac
        mkdir -p ".clean-trash/$(dirname "$p")"
        mv "./$p" ".clean-trash/${p%/}" && printf '%s\n' "$p" >> "$stage/cleaned.txt"
    done < "$stage/untracked.txt"
    rm -rf .clean-trash.old
    note "clean: $(wc -l < "$stage/untracked.txt" | tr -d ' ') untracked paths, $(wc -l < "$stage/cleaned.txt" | tr -d ' ') moved to .clean-trash/ (cleaned.txt)"
else
    git status --porcelain --ignored | sed -n -e 's/^?? //p' -e 's/^!! //p' > "$stage/untracked.txt"
    note "clean: skipped (--no-clean); untracked paths: $(wc -l < "$stage/untracked.txt" | tr -d ' ') (untracked.txt)"
fi

# 3. the measurements first, on a quiet machine and a fresh build: the
# report builds what it runs
if [ $bench = 1 ]; then
    report="$PWD/bench-report-$host-$utc.txt"
    echo "   (tools/bench-report.sh: about ten minutes)" >&2
    step bench env REPORT="$report" sh tools/bench-report.sh
    [ -f "$report" ] && cp "$report" "$stage/reports/" && note "this run's report: reports/$(basename "$report")"
else
    note "bench: skipped (--no-bench)"
    step build make all relfsh-native
fi

if [ -x ./relfsh-native ]; then
    step native-written python3 tools/native-written.py ./relfsh-native
    if [ $profile = 1 ]; then
        wl=$(mktemp -d)
        python3 - "$wl" << 'PYEOF'
import os, re, sys
for f in os.listdir('tests/bench-vm'):        # bench-vm.py's SCALE, at 100
    if f.endswith('.sh'):
        t = open('tests/bench-vm/' + f).read()
        open(os.path.join(sys.argv[1], f), 'w').write(
            re.sub(r'-lt (\d+)', lambda m: '-lt %d' % (int(m.group(1)) * 100), t))
PYEOF
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

# 4. one file
tar czf "$pack" -C "$stage" . || { echo "pack-results: tar failed; the results were in $stage" >&2; trap - EXIT; exit 1; }
cat "$sum"
echo
[ -n "$failed" ] && echo "steps that failed:$failed - their logs are in the pack"
echo "pack: $pack"
}

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

new_report() {   # path: true when the repository does not hold it yet
    held=bench/reports/$(basename "$1")
    ! { git ls-files --error-unmatch "$held" >/dev/null 2>&1 && cmp -s "$1" "$held"; }
}

# apply_bundle - the newest relf-claude-iterN-*.bundle in $BUNDLE_DIR, by N
# then by name, onto master by fast-forward; sets applied, and changed when
# this script is not what it was. Refuses - a message, status 1, nothing
# touched - when it cannot apply safely.
apply_bundle() {
    dir=${BUNDLE_DIR:-$HOME/Downloads}
    best= bestkey=
    for f in "$dir"/relf-claude-iter*.bundle; do
        [ -f "$f" ] || continue
        n=$(basename "$f" | sed -n 's/^relf-claude-iter\([0-9][0-9]*\)-.*/\1/p')
        [ -n "$n" ] || continue
        key=$(printf '%09d %s' "$n" "$(basename "$f")")
        if [ -z "$bestkey" ] || [ "$(printf '%s\n%s\n' "$bestkey" "$key" | sort | tail -1)" = "$key" ]; then
            best=$f bestkey=$key
        fi
    done
    if [ -z "$best" ]; then applied="none in $dir"; return 0; fi
    b=$(basename "$best")
    if ! git bundle verify "$best" > /dev/null 2>&1; then
        echo "pack-results: $best: git cannot read it whole - not applied" >&2; return 1
    fi
    new=$(git bundle list-heads "$best" refs/heads/master | cut -d' ' -f1)
    if [ -z "$new" ]; then echo "pack-results: $best has no master - not applied" >&2; return 1; fi
    if git merge-base --is-ancestor "$new" HEAD 2> /dev/null; then
        applied="$b: master already has it"; return 0
    fi
    if [ "$(git symbolic-ref -q --short HEAD)" != master ]; then
        echo "pack-results: the checkout is not on master - $b not applied" >&2; return 1
    fi
    if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
        echo "pack-results: tracked files are changed - $b not applied; commit or stash them, or --no-apply" >&2
        git status --short --untracked-files=no >&2; return 1
    fi
    old=$(git rev-parse HEAD)
    before=$(git hash-object "$self")
    if ! git fetch -q "$best" master 2> /dev/null || ! git merge -q --ff-only FETCH_HEAD > /dev/null 2>&1; then
        echo "pack-results: $b does not fast-forward master (master has commits it lacks?) - not applied" >&2; return 1
    fi
    git fetch -q "$best" article-2026:article-2026 2> /dev/null    # its other branch, where it fast-forwards
    applied="$b applied: $(git rev-parse --short "$old") -> $(git rev-parse --short HEAD)"
    echo "== $applied ==" >&2
    [ "$(git hash-object "$self")" = "$before" ] || changed=1
    return 0
}

main "$@"; exit $?
