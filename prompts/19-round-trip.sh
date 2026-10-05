#!/bin/sh
# 19-round-trip.sh - the template for prompts/19-round-trip.md: one
# command on the user's machine, one file back. Copy it into a project as,
# say, tools/round-trip.sh, and fill in the six places marked FILL - and
# this header, which --help prints; the rest is the protocol, and stays. A worked instance, with more
# steps: tools/pack-results.sh in the project this library came from.
#     sh tools/round-trip.sh             apply, clean, run the steps, pack
#     sh tools/round-trip.sh --no-apply  leave the checkout's commit alone
#     sh tools/round-trip.sh --no-clean  keep every untracked file
# 1. Apply: the newest bundle matching BUNDLES in $BUNDLE_DIR (~/Downloads
#    unless set) onto BRANCH, by fast-forward only - not over changed
#    tracked files, not when BRANCH has commits the bundle lacks, not off
#    BRANCH. If that changed this script, the new one runs from the start.
# 2. Clean: every untracked path, ignored or not, moved to .clean-trash/
#    (one run's worth kept - ignore it in .gitignore), except what keep
#    names: what came from elsewhere and is not in the repository yet.
# 3. The steps, each through `step NAME COMMAND...`: its output kept, its
#    exit status and time in the summary.
# 4. One file, printed last: NAME-results-HOST-COMMIT-UTC.tar.gz in the
#    checkout's top (ignore it in .gitignore too), with SUMMARY.txt first.
# The body is one function, called on the last line: the shell has read
# all of it before a bundle can change this file under it.

NAME=project                       # FILL: the packs' and bundles' prefix
BUNDLES="$NAME-claude-iter*.bundle"  # FILL: how the handed-over bundles are named
BRANCH=master                      # FILL: the branch the bundles carry
SELF=tools/round-trip.sh           # FILL: this file, from the repository's top

steps() {                          # FILL: what to run, in order
    step build make
    step check make check
    # copy any report the user should send back into "$stage/"
}

keep() {                           # FILL: untracked paths the clean leaves alone
    case $1 in
        "$NAME"-results-*.tar.gz|*.bundle) return 0 ;;
    esac
    return 1
}

main() {
set -u
cd "$(dirname "$0")/.." || exit 1
LC_ALL=C; export LC_ALL
exec < /dev/null
clean=1 apply=1
for a in "$@"; do
    case $a in
        --no-apply) apply=0 ;;
        --no-clean) clean=0 ;;
        -h|--help) sed -n '2,/^$/s/^# \{0,1\}//p' "$SELF"; exit 0 ;;
        *) echo "$SELF: unknown argument: $a" >&2; exit 2 ;;
    esac
done
git rev-parse --git-dir > /dev/null 2>&1 || { echo "$SELF: not a git checkout" >&2; exit 1; }

if [ $apply = 0 ]; then
    applied="not looked for (--no-apply)"
elif [ -n "${RT_REEXEC:-}" ]; then
    applied="${RT_APPLIED:-?}; this script changed with it, and ran again"
else
    changed=
    apply_bundle || exit 1
    if [ -n "$changed" ]; then
        echo "== $SELF changed with the bundle: running the new one ==" >&2
        RT_REEXEC=1 RT_APPLIED=$applied exec sh "$SELF" "$@"
    fi
fi

host=$(uname -n)
utc=$(date -u +%Y%m%dT%H%MZ)
pack="$PWD/$NAME-results-$host-$(git rev-parse --short HEAD)-$utc.tar.gz"
stage=$(mktemp -d) || exit 1
trap 'rm -rf "$stage"' EXIT
trap 'exit 130' INT TERM
sum="$stage/SUMMARY.txt"
failed=
note "$NAME results, $(date -u)"
note "host: $host ($(uname -srm))"
note "commit: $(git log -1 --format='%H %s' | cut -c1-120)"
note "bundle: $applied"
note "arguments: ${*:-none}"
note "checkout before - tracked files changed:"
git status --porcelain --untracked-files=no | sed 's/^/    /' >> "$sum"

if [ $clean = 1 ]; then
    git clean -ndx | sed -n 's/^Would remove //p' > "$stage/untracked.txt"
    : > "$stage/cleaned.txt"
    rm -rf .clean-trash.old
    [ -d .clean-trash ] && mv .clean-trash .clean-trash.old
    mkdir -p .clean-trash
    while IFS= read -r p; do
        case $p in .clean-trash/|.clean-trash.old/) continue ;; esac
        if keep "$p"; then note "clean kept: $p"; continue; fi
        mkdir -p ".clean-trash/$(dirname "$p")"
        mv "./$p" ".clean-trash/${p%/}" && printf '%s\n' "$p" >> "$stage/cleaned.txt"
    done < "$stage/untracked.txt"
    rm -rf .clean-trash.old
    note "clean: $(wc -l < "$stage/cleaned.txt" | tr -d ' ') of $(wc -l < "$stage/untracked.txt" | tr -d ' ') untracked paths moved to .clean-trash/"
else
    note "clean: skipped (--no-clean)"
fi

steps

note "checkout after - each line should be explained:"
git status --porcelain | sed 's/^/    /' >> "$sum"
[ -n "$failed" ] && note "steps that failed:$failed"
tar czf "$pack" -C "$stage" . || { echo "$SELF: tar failed; the results are in $stage" >&2; trap - EXIT; exit 1; }
cat "$sum"
echo
[ -n "$failed" ] && echo "steps that failed:$failed - their logs are in the pack"
echo "pack: $pack"
}

note() { printf '%s\n' "$*" >> "$sum"; }

step() {   # NAME COMMAND...: the output into NAME.log, the status in the summary
    name=$1; shift
    echo "== $name ==" >&2
    t0=$(date +%s)
    "$@" > "$stage/$name.log" 2>&1
    st=$?
    note "step $name: status $st, $(( $(date +%s) - t0 )) s"
    [ $st = 0 ] || failed="$failed $name"
    return $st
}

apply_bundle() {   # sets applied, and changed when this script is not what it was
    dir=${BUNDLE_DIR:-$HOME/Downloads}
    best=$(ls -1t "$dir"/$BUNDLES 2> /dev/null | head -1)    # the newest download
    if [ -z "$best" ]; then applied="none in $dir"; return 0; fi
    b=$(basename "$best")
    git bundle verify "$best" > /dev/null 2>&1 || { echo "$SELF: $b: git cannot read it whole - not applied" >&2; return 1; }
    new=$(git bundle list-heads "$best" "refs/heads/$BRANCH" | cut -d' ' -f1)
    [ -n "$new" ] || { echo "$SELF: $b has no $BRANCH - not applied" >&2; return 1; }
    if git merge-base --is-ancestor "$new" HEAD 2> /dev/null; then applied="$b: $BRANCH already has it"; return 0; fi
    [ "$(git symbolic-ref -q --short HEAD)" = "$BRANCH" ] || { echo "$SELF: not on $BRANCH - $b not applied" >&2; return 1; }
    [ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "$SELF: tracked files are changed - $b not applied (commit, stash, or --no-apply)" >&2; return 1; }
    old=$(git rev-parse HEAD)
    before=$(git hash-object "$SELF")
    if ! git fetch -q "$best" "$BRANCH" 2> /dev/null || ! git merge -q --ff-only FETCH_HEAD > /dev/null 2>&1; then
        echo "$SELF: $b does not fast-forward $BRANCH - not applied" >&2; return 1
    fi
    applied="$b applied: $(git rev-parse --short "$old") -> $(git rev-parse --short HEAD)"
    echo "== $applied ==" >&2
    [ "$(git hash-object "$SELF")" = "$before" ] || changed=1
    return 0
}

main "$@"; exit $?
