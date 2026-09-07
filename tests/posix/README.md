# tests/posix — conformance derived from the specification

A differential suite whose cases are derived from POSIX.1 XCU
"Shell Command Language" rather than from another shell's test suite,
and which is scored against **the consensus of every reference shell
present** rather than against one.

`tests/mrsh-suite/` was the external yardstick until Iteration 125,
when it was fully passed. It is 21 files. Passing it says `shell.4`
handles what mrsh's acceptance tests exercise; it says nothing about
the rest of the specification. This directory is the successor, and
it is meant to grow to cover the spec section by section.

## The consensus rule, and why it exists

A case is **scored** only when every reference shell agrees on both
stdout and exit status. Where they disagree, the harness reports
`INCONCLUSIVE` and scores nothing.

The reason is `tests/diff/`'s weakness: it compares against bash
alone, so every case has to be hand-checked for forms where bash and
POSIX legitimately differ. `GOALS.md`'s "Where bash and POSIX
disagree" section lists two, and Iteration 124 found that the choice
of oracle had been silently costing the mrsh suite a genuine pass and
buying it a hollow one — for eighty iterations, undetected. **One
shell is not POSIX.** It is one implementation's reading of POSIX
plus its extensions.

Consensus scoring makes the oracle self-checking. A case that
accidentally encodes a bash-ism cannot quietly become the standard,
because dash will disagree and the case is flagged rather than the
shell failed.

Two consequences worth internalising:

- **More reference shells make this stricter about what it scores and
  more trustworthy about what it does.** With one reference it
  degrades to `tests/diff/`, and says so in its output. `dash` and
  `bash` are the minimum useful pair; `mksh`, `busybox sh`, `yash` and
  `ksh` each add a genuinely independent reading.
- **`INCONCLUSIVE` is a finding, not a skip.** Either the case needs
  narrowing to the behaviour POSIX actually specifies, or it has
  documented a real divergence between implementations — which is
  worth having written down either way.
  `2.6.1-tilde-after-equals-in-argument.sh` is kept deliberately as a
  worked example of the second.

## Running it

    tests/posix/run.sh                       # all reference shells found
    POSIX_VERBOSE=1 tests/posix/run.sh       # show the differing output
    POSIX_REF_SHELLS="dash bash" tests/posix/run.sh
    RELFSH=/path/to/relfsh tests/posix/run.sh

Reference shells are discovered, not configured: anything in the
candidate list that is not installed is skipped silently, so this runs
unmodified on a bare container and on a well-stocked machine. Symlinks
are resolved, so `/bin/sh -> dash` is not counted as a second opinion
alongside `dash` — two agreeing copies of one shell look exactly like
consensus and are exactly the false confidence this harness exists to
avoid.

Like `tests/mrsh-suite/run.sh`, this is **not** run by
`tests/run_tests.sh`. It is a tracked number of its own, reported
alongside the mrsh count.

## Writing a case

    cases/<xcu-section>-<name>.sh          stdout and exit status must
                                           match the consensus
    cases/<xcu-section>-<name>.fail.sh     every shell must REJECT it:
                                           nonzero status, and not by
                                           crashing

Name each file for the section of XCU it is derived from, matching the
vendored mrsh conformance tests' own convention
(`2.2.2-nested-single-quotes.fail.sh`). That makes coverage visible
against the specification's own structure rather than against a
wishlist.

Rules that have already cost time elsewhere in this project:

- **No hand-written expectations.** The reference shells are the
  expectation. That is the whole point, and it is why `tests/diff/`
  has caught bugs nobody would have thought to write a test for.
- **`stderr` is ignored.** Diagnostic wording is implementation
  defined; comparing it would test nothing about conformance. Same
  choice mrsh's own harness makes.
- **Prefer `printf` to `echo`.** `echo`'s handling of `-n`, `-e` and
  backslashes is implementation defined and will produce
  `INCONCLUSIVE` on content that has nothing to do with the section
  under test.
- **Keep a case to one section.** A case that exercises four features
  fails as one line and tells you nothing about which.
- **Write the case before the fix.** `PARSE-EXPAND-PLAN.md` and
  `FORTH-STYLE.md` §13 both say this; the differential layer is where
  it pays most.

## Reference shells

Seven, on a fully-provisioned machine: `dash` (as `sh`), `bash`,
`mksh`, `ksh93`, `yash`, `posh` and `busybox ash`. Install with

    apt-get install -y mksh yash posh ksh busybox-static

`zsh` is deliberately excluded - see `run.sh`'s comment at the
candidate list.

## Current state

Five seed cases, one per verdict path, written to prove the harness
rather than to cover anything:

| case | verdict | why |
|---|---|---|
| `2.6.2-parameter-expansion-defaults.sh` | PASS | |
| `2.5.2-special-parameters.sh` | PASS | |
| `2.2.2-unterminated-single-quote.fail.sh` | PASS | |
| `2.6.1-tilde-after-equals-in-argument.sh` | INCONCLUSIVE | bash expands, dash does not |
| `2.9.1-assignment-prefix.sh` | FAIL | `NAME=value command` is a real, recorded gap |

The corpus itself is not yet scoped. That is the next piece of work.
