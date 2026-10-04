#!/bin/sh
# verify-procs.sh - tests/verify's runs, found by their exact arguments.
# prompts/17 step 5 and prompts/15 (Iteration 638): a stale run was twice
# stopped by a pattern the stopping command's own line contained, and the
# command killed itself. A run is `/bin/sh tests/verify ...`, or the
# detached wrapper `sh -c cd DIR; tests/verify ...` - matched field by
# field, which no shell issuing this can look like.
#   tools/verify-procs.sh          list them: pid and arguments
#   tools/verify-procs.sh --stop   stop them, the wrappers first
ps -eo pid,args | awk '($2=="/bin/sh" && $3=="tests/verify") ||
                       ($2=="sh" && $3=="-c" && $4=="cd" && $6=="tests/verify")' > /tmp/verify-procs.$$
if [ "$1" = --stop ]; then
    awk '$2=="sh" {print $1}' /tmp/verify-procs.$$ | while read -r p; do kill "$p" 2>/dev/null; done
    awk '$2=="/bin/sh" {print $1}' /tmp/verify-procs.$$ | while read -r p; do kill "$p" 2>/dev/null; done
    sleep 2                     # a shell waiting on a child defers TERM:
    awk '{print $1}' /tmp/verify-procs.$$ | while read -r p; do kill -9 "$p" 2>/dev/null; done
    sleep 1
    ps -eo pid,args | awk '($2=="/bin/sh" && $3=="tests/verify")' | wc -l | sed 's/^/still running: /'
else
    cat /tmp/verify-procs.$$
fi
rm -f /tmp/verify-procs.$$
