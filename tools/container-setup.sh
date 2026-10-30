#!/bin/sh
# tools/container-setup.sh - what a fresh container lacks for `make verify`, found and
# supplied, one line per gap (Iteration 889).
#
#   sh tools/container-setup.sh           install what is missing; set a commit identity if none
#   sh tools/container-setup.sh --check   only say what is missing: status 1 if anything is
#
# A session's container starts from a stock image: no 32-bit toolchain, none of the
# reference shells but bash and dash, no gforth, and no git identity (seen at 889, and in
# prompts/18-session-start.md's own story). Each had been found by failing - the first
# commit refused, or, worse, not at all: without cc -m32 `make verify` skips the 4-byte
# half and calls the run green (docs/CHECKING.md). A reminder handed from one session's
# message to the next is a check nobody wrote (prompts/15); this is that check, written.
#
# For a container only: the identity it sets is the one this repository's history uses,
# in this checkout's own config. On your own machine, install the packages yourself
# (docs/CHECKING.md) and keep your identity.
self=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")
cd "$(dirname "$0")/.." || exit 2
check=0
[ "$1" = --check ] && check=1
gaps=0
pkgs=
gap() { gaps=$((gaps + 1)); pkgs="$pkgs $2"; echo "gap: $1 - missing; package $2"; }

t=$(mktemp -d) || exit 2
printf 'int main(void){return 0;}\n' > "$t/t.c"
cc -m32 "$t/t.c" -o "$t/t" >/dev/null 2>&1 || gap "cc -m32 (the 4-byte engine's half of every check)" gcc-multilib
rm -rf "$t"
for c in python3:python3 bash:bash dash:dash timeout:coreutils \
         mksh:mksh yash:yash posh:posh ksh:ksh busybox:busybox-static gforth:gforth; do
    command -v "${c%%:*}" >/dev/null 2>&1 || gap "${c%%:*}" "${c#*:}"
done
noid=0
git config user.email >/dev/null 2>&1 || { noid=1; gaps=$((gaps + 1)); echo "gap: a git commit identity - missing"; }

if [ "$gaps" = 0 ]; then echo "container-setup: nothing missing"; exit 0; fi
[ "$check" = 1 ] && exit 1

if [ -n "$pkgs" ]; then
    if [ "$(id -u)" = 0 ]; then apt=apt-get; else apt="sudo -n apt-get"; fi
    if $apt update -qq >/dev/null 2>&1 &&
       DEBIAN_FRONTEND=noninteractive $apt install -y -qq $pkgs >/dev/null 2>&1; then
        echo "installed:$pkgs"
    else
        echo "not installed:$pkgs - install them by hand"
    fi
fi
if [ "$noid" = 1 ]; then
    git config user.name Claude && git config user.email claude@anthropic.com &&
        echo "identity: Claude <claude@anthropic.com>, this checkout's config"
fi
# Said again, after: what is still missing now.
exec sh "$self" --check
