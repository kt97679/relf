# Checking a checkout

Commands to run after pulling, and what each one would catch. Written at
Iteration 391, after two reports from a real checkout found faults this
project's own suites were not watching: a Makefile that ran a bash
script with `sh`, and a differential case that only passed in the C
locale.

Everything below is a `make` target; `make help` lists them all.

## The five-minute pass

    make                  # both engines, both shell images
    make verify           # every suite, against tests/BASELINE
    make portability      # the scaffolding: shebangs, locale pins, the bundle

`make verify` is the one that matters: it runs the core suites at both
cell widths, the differential cases, the matrix, POSIX and mrsh
acceptance, the shell's own assertions and the interactive pty cases,
then compares every count against `tests/BASELINE`. It prints
`VERIFIED: everything matches` or names what moved.

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
counts, the dead-word count, both image fixpoints, and whether the
bundle can be cloned.

## What the suites assume about your machine

    /usr/bin/true /usr/bin/false /usr/bin/test /usr/bin/env /bin/sh

named by absolute path in the shell tests, because that is where they
are on the machine the suite was written on. `tests/shell/lib.sh`
checks them once and says which is missing rather than failing
mysteriously. Nothing else about the environment should matter:
`make portability` runs the whole shell suite again with a foreign
`HOME`, `USER` and `TERM` and requires the same result.

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
put a new case in. `tests/from-others/CATALOGUE.md` is where behaviours
learned from other projects' suites are written down before they are
fixed.
