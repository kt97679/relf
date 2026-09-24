# Checking a checkout

Commands to run after pulling, and what each one would catch. Written at
Iteration 391, after two reports from a real checkout found faults this
project's own suites were not watching: a Makefile that ran a bash
script with `sh`, and a differential case that only passed in the C
locale.

Everything below is a `make` target; `make help` lists them all.

This file is the project-specific part: the commands, and the facts about
this repository's suites. The reasoning behind them is stated once, in
`prompts/`: why a suite must not depend on the machine it runs on is
`08-run-it-elsewhere.md`, what a failure report must contain is
`11-report-from-elsewhere.md`, and why a recorded number is explained
before it is re-recorded is `09-baseline-discipline.md`.

## The five-minute pass

    make                  # both engines, both shell images
    make verify           # every suite, against tests/BASELINE
    make portability      # the scaffolding: shebangs, locale pins, the bundle

`make verify` is the one that matters: it runs the core suites at both
cell widths, the differential cases, the matrix, POSIX and mrsh
acceptance, the shell's own assertions and the interactive pty cases,
then compares every count against `tests/BASELINE`. It prints
`VERIFIED: everything matches` or names what moved.

## The suites, and what each is for

`make verify` runs them all against `tests/BASELINE`; `make help` lists
the targets that run each alone.

1. **The core suite** (`tests/run_tests.sh`, `make test`) - `tester.fr`,
   John Hayes's 1993 CORE tests in RelF's `{ -> }` form, and the
   Forth-level tests, on both cell widths; `tests/ext/` adds CORE EXT,
   Memory-Allocation and File-Access, and `tests/io/` how the kernel
   reads its terminal. Full Forth-2012 conformance is not a goal: cases
   are taken from its suite where they apply.
2. **The shell's own assertions** (`tests/shell/run-*`, `make shell`) -
   for what bash is the *wrong* oracle for: this shell's diagnostics,
   forms it rejects on purpose, its limits, and behaviour where the
   references disagree. A `run-*` file is picked up by `run-all`; run it
   through `run-all`, which sets `THIS_SH`.
3. **The differential cases** (`tests/diff/cases/`, `make diff`) - plain
   scripts run under this shell and bash, outputs compared, **no
   hand-written expectations at all**. The strongest layer, and the one
   to reach for first: add a case *before* changing behaviour. A case
   must avoid what the two shells legitimately disagree on.
4. **The construct matrix** (`tests/matrix/`, `make matrix`) - thirty
   construct templates, each in thirteen contexts, and 32 syntax errors,
   scored against bash in POSIX mode and dash; a case counts only when
   they agree. A failure not in `KNOWN-FAILING` is a regression.
5. **The parser** (`tests/parse/`) - expected trees, and every other
   suite's scripts checked to get the same syntax verdict as `dash -n`.
6. **POSIX and mrsh** (`tests/posix/`, `tests/mrsh-suite/`, `make posix
   mrsh`) - cases derived from XCU itself, scored against the
   *consensus* of the reference shells present, and mrsh's suite,
   vendored unmodified, the outside view.
7. **The pty transcripts** (`tests/interactive/`, `make interactive`) -
   the line editor, prompts, job control and signals, through a real
   pseudo-terminal (INTERACTIVE.md).
8. **The external corpora** (`make busybox`, `make yash`) - fetched, not
   vendored; each prints CRASH, HANG or wrong per failure, and what the
   reference passes and this shell does not.
9. **The fuzzers** (`tools/crashfuzz.py`, `tools/difffuzz.py`) - not in
   `make verify`: run them after changes to the parser, the expander or
   the job code (GOALS.md, "Tools for finding the next bug").

`tools/coverage.py` measures layers 2-6 against `shell.4`: which words
never run and which run only in part.

## When something fails

    make diff             # just the differential cases
    make matrix           # just the construct and error matrix
    make shell            # just tests/shell
    make test             # the core suites, both widths

A failing differential case prints a real diff, labelled with which side
is which - `-` is the reference shell, `+` is this one. If the two sides
look identical, it prints the first lines as bytes, which is what a
trailing space or a CR looks like from there.

## If a suite seems to hang

It is waiting for your terminal. A case that runs the shell without
redirecting stdin inherits whatever the suite inherited: `/dev/null` in
a container, and the terminal on a real machine, where it waits for ever
(Iteration 392 - reported from a checkout, invisible here). Every suite
closes its own stdin now, and `make portability` checks both that they
say so and that the differential suite finishes when stdin never
delivers.

If you hit one anyway, this says where it stopped:

    make verify 2>&1 | tail -20      # the last line is the step it is in
    sh -x tests/verify 2>&1 | tail -40   # every command, as it runs

## Lines `make verify` prints that are not failures

    machine  size:x86_64  174640 (baseline 139656, not compared here)

A byte size depends on the compiler that produced the binary, and
whether a POSIX case is inconclusive depends on which reference shells
are installed. `tests/verify` records the compiler it measured with, and
compares the size lines only against a baseline taken with that same
compiler; otherwise it prints them as `machine` and moves on. What it
always compares is what depends on the CODE: every suite's pass and fail
counts, the dead-word count, both image fixpoints, whether the bundle
can be cloned - and, since Iteration 489, the checksum of each rebuilt
shell image (`image-sum:`), so that a build on another machine is
compared byte for byte with the one recorded. A 32-bit host builds no
8-byte image, so its `image-sum:kernel-shell.img` reads `missing` and is
not compared; the 4-byte one is.

## What the suites take out of your environment

Before running anything they set `LC_ALL=C`, close their own stdin and
`unset LD_PRELOAD` - a collation order, a terminal that never answers,
and a loader message on every exec (`prompts/08-run-it-elsewhere.md`
explains the class). `make portability` checks that each suite does all
three, and then
proves it by running one of them with a hostile preload and in a second
locale.

## After a pull

    make

The engines are build products and are not in the repository - 40 KB of
C through `cc`. `make` builds them, and rebuilds them when `uname -m`
changes, so a checkout copied or shared between machines cannot end up
exec'ing a binary for the wrong architecture. The shell images are build
products too, since Iteration 489: `make` builds them, and `relfsh` does
if they are missing. `make clean` removes the engines, `make distclean`
the shell images as well. Only the two kernel images are committed,
being the bootstrap seed.

## A prompt through the environment

    PS1='[mine] ' relfsh          # works where /bin/sh is dash
                                  # does nothing where it is bash

`relfsh` is a `#!/bin/sh` script, and **bash, running a non-interactive
script, clears PS1 from the environment** before exec'ing anything. On
Debian and Ubuntu `/bin/sh` is dash and the prompt arrives; on Gentoo,
Arch and Fedora it is bash and it does not. Set it inside the shell
instead - `PS1='[mine] '` at the prompt - which works everywhere. (This
file used to suggest the file `$ENV` names as well; this shell reads no
startup file yet, which Iteration 499 found. GOALS.md's list for what
comes next has it, and a `relfsh` that is not a script would end the
PS1 problem.)

## The pty suite and a busy machine

`make interactive` drives the shell through a pseudo-terminal, so it is
the one suite whose answers depend on timing: it waits for a prompt and
then for a quiet moment, and on a loaded machine a redraw can arrive
after that moment has passed. If a single case fails and then passes on
a re-run, that is what happened. Both waits can be lengthened:

    RELF_PTY_SETTLE=0.5 RELF_PTY_TIMEOUT=20 make interactive

## Reference shells

The differential suite compares against `bash`; the matrix uses `bash
--posix` and `dash` and scores a case only where the ones present agree
(POSIX mode since Iteration 487: plain bash alone outvoted the standard
on a machine without dash); three
shell-test files quote `dash`'s exact wording and skip without it. None
of them is required - the suite says what it could use and adjusts -
but with both installed you are measuring what this project measures.

    make matrix                 # prints "matrix references: ..." first

## What the suites assume about your machine

    /usr/bin/true /usr/bin/false /usr/bin/test /usr/bin/env /bin/sh

named by absolute path in the shell tests, because that is where they
are on the machine the suite was written on. `tests/shell/lib.sh`
checks them once and says which is missing rather than failing
mysteriously. Nothing else about the environment should matter:
`make portability` runs the whole shell suite again with a foreign
`HOME`, `USER` and `TERM` and requires the same result.

## Pretending to be a 32-bit machine

    CC='cc -m32 -fno-pie -no-pie' HOSTBITS=32 make verify

builds and tests as a 32-bit host would - native 4-byte engine, 4-byte
image, no cross half. On a 64-bit machine with `gcc-multilib` that is a
faithful rehearsal of an ARMv7 board, and it is how the 32-bit support
here was written.

## On a 32-bit machine

A cell is a pointer, so the native engine on ARMv7 or i386 runs the
4-byte image, `kernel32.img` - `kernel.img` is the 8-byte one and that
engine will call it "not a RelF image, or built for a different encoding
or cell width". `make` works this out from `getconf LONG_BIT` and builds
the native pair; `relfsh` reads the answer from `.relf-native-img`,
which `make` writes. `make HOSTBITS=32` shows a 64-bit machine what a
32-bit one does.

One thing that build cannot do: hold a limit or a size that needs more
than 32 bits. `ulimit -l` on a machine with more than 2 GB of lockable
memory reads back wrapped. GOALS.md records it.

## The i386 half

Half of `make verify` builds and runs a 4-byte-cell engine, which needs
a 32-bit toolchain and a 32-bit loader:

    sudo apt install gcc-multilib libc6-i386     # Debian/Ubuntu

Without them the suite skips that half and says so; the `*:4byte` lines
then read `skipped` and the i386 sizes read `missing`, and neither
counts as a difference. With them, the i386 half is a second complete
run of everything at a different cell width, which is where several of
this project's worst bugs were caught.

## Things that depend on your machine rather than on the code

    locale                              # C? UTF-8? see below
    make portability                    # runs the differential suite in
                                        # a second locale and compares
    ls -l /bin/sh                       # dash, or bash?
    echo "$LD_PRELOAD"                  # set system-wide on Ubuntu/Mint

This shell has no locale support: character classes, ranges and the
order pathname expansion returns matches in are all byte-based, which is
the C locale's behaviour. The suites pin `LC_ALL=C` so they compare like
with like. If you run a case by hand in a UTF-8 locale, the reference
shell may sort `a1 b2 ZZ` where this one sorts `ZZ a1 b2`, and that is
the locale talking, not a bug.

`LD_PRELOAD` is set system-wide by some desktops (Ubuntu and Mint ship
`libgtk3-nocsd`). The loader refuses to put a 64-bit library into the
32-bit engine and says so, with `ignored` at the end of the line - it is
noise, not a failure. `make` clears it for the i386 build.

## The external corpora

Neither is vendored; each script's header says how to fetch it.

    BUSYBOX_TESTS=/path/to/busybox/shell/ash_test make busybox
    YASH_TESTS=/path/to/yash/tests                make yash

Both print this shell's score, the reference's, and the list of tests
the reference passes and this shell does not. That list is the worklist.

## The engine and the images

    make check-images     # kernel.img and kernel32.img still reproduce
    make images IMAGES_FORCE=1
                          # ... and replace them, for an engine change

`kernel.img` is both what `cross.4` produces and what `cross.4` runs on,
so rebuilding it is a fixpoint step rather than a compile. `make` never
does it by itself.

## Measuring

    make bench            # speed against the reference shells
    make sizes            # size against every shell installed
    make profile          # dispatch counts per word, on a realistic script

## If you find something

A failing case, with the diff the runner prints, is the whole bug
report: it names the construct, both shells' answers, and the file to
put a new case in (`prompts/11-report-from-elsewhere.md` says why that
is enough). `tests/from-others/CATALOGUE.md` is where behaviours
learned from other projects' suites are written down before they are
fixed.
