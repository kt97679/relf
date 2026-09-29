#!/bin/sh
# tools/make-bundle.sh [DIR] - the handoff bundle, named and checked
# (Iteration 584). From the repository's top, after the iteration's
# commit:
#     sh tools/make-bundle.sh /mnt/user-data/outputs
# prints the bundle's path. DIR defaults to the current directory.
#
# The name is GOALS.md's convention, which Iterations 582-583 missed -
# they handed over relf-583.bundle, because prompts/07-git-handoff.md
# shows a generic name and GOALS.md was not read:
#     relf-claude-iterN-YYYYMMDD-HHMMSS.bundle      (UTC)
# N is the iteration of HEAD's commit, from its subject ("Iteration N:
# ..."); a handoff of several iterations is named by the last.
#
# The refs: HEAD, so a plain `git pull FILE` works (Iteration 369);
# master; and article-2026, the version the articles describe
# (Iteration 581), whenever the branch exists - the receiving end takes
# it with `git fetch FILE article-2026:article-2026`.
#
# The check: the bundle is cloned and the clone's HEAD must be ours -
# a deliverable nobody tests is one nobody has tried.
set -e
subject=$(git log -1 --format=%s)
n=$(printf '%s\n' "$subject" | sed -n 's/^Iteration \([0-9][0-9]*\):.*/\1/p')
if [ -z "$n" ]; then
    echo "make-bundle: HEAD's subject does not start with 'Iteration N:': $subject" >&2
    exit 1
fi
dir=${1:-.}
file="$dir/relf-claude-iter$n-$(date -u +%Y%m%d-%H%M%S).bundle"
refs="HEAD master"
if git rev-parse -q --verify refs/heads/article-2026 >/dev/null; then
    refs="$refs article-2026"
fi
git bundle create "$file" $refs 2>/dev/null
check=$(mktemp -d)
trap 'rm -rf "$check"' EXIT
git clone -q "$file" "$check/clone"
if [ "$(git rev-parse HEAD)" != "$(git -C "$check/clone" rev-parse HEAD)" ]; then
    echo "make-bundle: the clone's HEAD is not this HEAD - not pullable" >&2
    rm -f "$file"
    exit 1
fi
git bundle list-heads "$file" | sed 's/^/  /' >&2
echo "$file"
