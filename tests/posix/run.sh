#!/bin/sh
# tests/posix/run.sh - a differential conformance harness for shell.4,
# scored against the *consensus of several reference shells* rather
# than against one.
#
# Why consensus, and not just bash or just sh:
#
#   tests/diff/ compares against bash alone, which means every case
#   has to be hand-checked to avoid forms where bash and POSIX
#   legitimately differ - GOALS.md's own "Where bash and POSIX
#   disagree" section lists two, and Iteration 124 found that the
#   choice of oracle had been silently costing a pass and buying a
#   hollow one for eighty iterations. One shell is not POSIX. It is
#   one implementation's reading of POSIX plus its extensions.
#
#   So a case is only *scored* when every reference shell present
#   agrees on both stdout and exit status. Where they disagree, the
#   behaviour is either unspecified by POSIX or contested between
#   implementations, and this harness says INCONCLUSIVE and scores
#   nothing rather than picking a winner. That makes the oracle
#   self-checking: a case that smuggles in a bash-ism cannot quietly
#   become the standard, because dash will disagree and the case will
#   be flagged instead of failed.
#
# Consequences worth knowing:
#
#   - More reference shells make the harness STRICTER about which
#     cases it scores, and more trustworthy about the ones it does.
#     With one reference it degrades to tests/diff/ and says so.
#   - An INCONCLUSIVE case is not a failure and not a pass. It is a
#     finding: either the case needs narrowing to the specified
#     behaviour, or it has documented a real divergence between
#     shells, which is interesting in its own right.
#
# Case conventions (see README.md):
#
#   cases/<xcu-section>-<name>.sh        stdout and status must match
#                                        the reference consensus
#   cases/<xcu-section>-<name>.fail.sh   every shell must REJECT it:
#                                        nonzero status, and not by
#                                        crashing
#
# Named for the section of POSIX.1 XCU "Shell Command Language" the
# case is derived from, matching the vendored mrsh conformance tests'
# own convention (2.2.2-nested-single-quotes.fail.sh).
#
# stderr is ignored throughout: diagnostic wording is implementation
# defined and comparing it would test nothing about conformance. Same
# choice mrsh's own harness makes.

# Byte order and byte classes for every shell this suite runs: pathname
# expansion sorts by LC_COLLATE, `[a-z]` is a collation range and
# `[[:alpha:]]` is a locale's own idea of a letter. This shell has no
# locale support - it is always the C locale - so a suite that compares
# it with another shell, or with recorded output, has to say which
# locale it means. A checkout in en_US.UTF-8 saw the difference
# (Iterations 390 and 393).
LC_ALL=C
export LC_ALL
cd "$(dirname "$0")" || exit 1
RELFSH="${RELFSH:-../../relfsh}"
TIMEOUT_SECS="${TIMEOUT_SECS:-10}"

# ------------------------------------------------------------------
# Reference shell discovery
# ------------------------------------------------------------------
# Override with POSIX_REF_SHELLS="dash bash mksh". Anything not
# installed is skipped silently - this is meant to run on a bare
# container and on a well-stocked machine without editing.
# zsh is deliberately absent. Invoked as "zsh script.sh" it runs in
# its own native mode, not sh emulation, and differs from POSIX on
# word splitting and much else - it would produce INCONCLUSIVE
# verdicts about zsh rather than about the specification. It is a
# fine shell and the wrong reference. Add it explicitly via
# POSIX_REF_SHELLS if you want to see what it says.
CANDIDATES="${POSIX_REF_SHELLS:-sh dash bash mksh ksh yash busybox-sh posh}"

REFS=""
REF_REAL=""
for c in $CANDIDATES; do
    case "$c" in
        busybox-sh) command -v busybox >/dev/null 2>&1 || continue
                    p="busybox sh"; real="busybox-sh" ;;
        *)          p=$(command -v "$c" 2>/dev/null) || continue
                    # Resolve symlinks so /bin/sh -> dash is not
                    # counted as two independent opinions. Two
                    # agreeing copies of one shell would look like
                    # consensus and is exactly the false confidence
                    # this harness exists to avoid.
                    real=$(readlink -f "$p" 2>/dev/null || echo "$p") ;;
    esac
    case " $REF_REAL " in *" $real "*) continue ;; esac
    REF_REAL="$REF_REAL $real"
    REFS="$REFS $c"
done

REF_COUNT=0
for r in $REFS; do REF_COUNT=$((REF_COUNT + 1)); done

if [ "$REF_COUNT" -eq 0 ]; then
    echo "ERROR: no reference shell found. Set POSIX_REF_SHELLS." >&2
    exit 2
fi

# A reference is carried through the loops as a single word (the lists
# here are space-separated), but some are invoked as two - busybox is
# a multi-call binary and its shell is "busybox sh". The label and the
# command line are therefore not the same string, and this maps one to
# the other at the point of use.
#
# Getting this wrong is instructive: the first version stored the
# label and ran it verbatim, so every busybox case exec'd a
# nonexistent "busybox-sh", returned 127 with no output, and was
# reported as busybox DISAGREEING with every other shell on every
# case. The harness surfaced its own defect as four INCONCLUSIVE
# verdicts rather than as a silent wrong answer, which is the design
# working - but a disagreement that lands on one shell and every case
# is a harness bug, not a finding. Check the invocation first.
ref_cmd() {
    case "$1" in
        busybox-sh) echo "busybox sh" ;;
        *)          echo "$1" ;;
    esac
}

run_shell() {
    # $1 = shell label, $2 = script
    # shellcheck disable=SC2086
    timeout "$TIMEOUT_SECS" $(ref_cmd "$1") "$2" < /dev/null 2>/dev/null
}

# A status of 128+signum is what timeout and a crashing process both
# produce. It must never count as "rejected the input cleanly" for a
# .fail.sh case - the same distinction tests/mrsh-suite/run.sh makes,
# for the same reason (an earlier harness there scored a segfault as
# a pass).
is_crash_status() { [ "$1" -ge 128 ] 2>/dev/null; }

PASS=0; FAIL=0; INCONCL=0; FAILED_NAMES=""; INCONCL_NAMES=""

echo "=== POSIX conformance (differential, consensus-scored) ==="
echo "relfsh:     $RELFSH"
echo "references:$REFS"
if [ "$REF_COUNT" -lt 2 ]; then
    echo "NOTE: only one reference shell is available, so 'consensus' is"
    echo "      that shell's opinion alone and this run is no stronger"
    echo "      than tests/diff/. Install a second (dash and bash differ"
    echo "      usefully) before trusting a green result."
fi
echo ""

for f in cases/*.sh; do
    [ -e "$f" ] || continue
    name=$(basename "$f")

    case "$name" in
    *.fail.sh)
        # Every reference must reject it, or the case is wrong.
        disagree=""
        for r in $REFS; do
            run_shell "$r" "$f" > /dev/null
            st=$?
            if [ "$st" = 0 ] || is_crash_status "$st"; then
                disagree="$disagree $r(status=$st)"
            fi
        done
        if [ -n "$disagree" ]; then
            echo "INCONCLUSIVE: $name (references do not all reject it:$disagree)"
            INCONCL=$((INCONCL + 1)); INCONCL_NAMES="$INCONCL_NAMES $name"
            continue
        fi
        run_shell "$RELFSH" "$f" > /dev/null
        rst=$?
        if is_crash_status "$rst"; then
            echo "FAIL: $name (relfsh CRASHED, status=$rst - a crash is not a rejection)"
            FAIL=$((FAIL + 1)); FAILED_NAMES="$FAILED_NAMES $name"
        elif [ "$rst" != 0 ]; then
            echo "PASS: $name"
            PASS=$((PASS + 1))
        else
            echo "FAIL: $name (relfsh accepted input every reference rejects)"
            FAIL=$((FAIL + 1)); FAILED_NAMES="$FAILED_NAMES $name"
        fi
        ;;
    *)
        # Establish the consensus first, then judge relfsh against it.
        first=""; first_out=""; first_st=""; split=""
        for r in $REFS; do
            out=$(run_shell "$r" "$f"); st=$?
            if [ -z "$first" ]; then
                first="$r"; first_out="$out"; first_st="$st"
            elif [ "$out" != "$first_out" ] || [ "$st" != "$first_st" ]; then
                split="$split $r"
            fi
        done
        if [ -n "$split" ]; then
            echo "INCONCLUSIVE: $name ($first disagrees with:$split)"
            INCONCL=$((INCONCL + 1)); INCONCL_NAMES="$INCONCL_NAMES $name"
            continue
        fi
        rout=$(run_shell "$RELFSH" "$f"); rst=$?
        if [ "$rout" = "$first_out" ] && [ "$rst" = "$first_st" ]; then
            echo "PASS: $name"
            PASS=$((PASS + 1))
        else
            if is_crash_status "$rst"; then
                echo "FAIL: $name (relfsh CRASHED, status=$rst)"
            else
                echo "FAIL: $name (relfsh status=$rst, reference status=$first_st)"
            fi
            FAIL=$((FAIL + 1)); FAILED_NAMES="$FAILED_NAMES $name"
            if [ -n "$POSIX_VERBOSE" ]; then
                printf '  --- reference (%s)\n' "$first"
                printf '%s\n' "$first_out" | sed 's/^/  | /'
                printf '  --- relfsh\n'
                printf '%s\n' "$rout" | sed 's/^/  | /'
            fi
        fi
        ;;
    esac
done

echo ""
echo "=== Summary ==="
echo "$PASS passed, $FAIL failed, $INCONCL inconclusive"
echo "  (scored against the consensus of$REFS)"
[ -n "$FAILED_NAMES" ] && echo "Failed:$FAILED_NAMES"
[ -n "$INCONCL_NAMES" ] && echo "Inconclusive:$INCONCL_NAMES"
echo ""
echo "Re-run with POSIX_VERBOSE=1 to see the differing output of each failure."

[ "$FAIL" -eq 0 ]
