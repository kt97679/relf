# 08 — a suite that has run in one place measures that place

**Fires when** a test suite, benchmark or build has only ever run in one
environment — your container, your laptop, your CI image — and you are
about to call it green.

**Skip when** the environment is genuinely fixed and shipped with the
product (a pinned container that is also the deployment target).

## Why this exists

A project with 420 construct tests, 92 differential cases, an
acceptance suite and a reproducible-build check was handed to someone
with two ordinary machines. Eleven reports later, **nine faults had been
found and only two were in the program under test.** The rest were in
the harness, and every one was something the original environment never
varied:

| what differed | what broke |
|---|---|
| `/bin/sh` was bash, not dash | a build step ran a bash script with `sh`; a wrapper lost `PS1`, which bash clears for non-interactive scripts |
| the locale was UTF-8, not C | glob ordering and `[a-z]` differ; a comparison against another implementation failed |
| stdin was a terminal, not `/dev/null` | a suite inherited it and waited for a keystroke that never came, with no output |
| no `dash` installed | three test files that quote its wording failed; a comparison scored every case inconclusive |
| the host was 32-bit | the native image was the other width; a whole half of the build was inverted |
| the compiler was different | recorded byte sizes differed, and were reported as regressions |
| `LD_PRELOAD` was set system-wide | the loader's complaint was captured into the compared output |
| `HOME` was not `/root` | a test asserted `${#HOME}` was 5 |
| the machine was busy | a pty harness's 80 ms timing assumption failed intermittently |

None of these is exotic. All of them are defaults on some common
distribution.

## Do this

Before calling a suite portable, ask each of these and fix what you
find. Most fixes are one line in the harness.

1. **Which `/bin/sh`?** Run every script under the interpreter its
   shebang names; check bashisms with `dash -n`.
2. **Which locale?** Anything that sorts, matches character classes, or
   compares against another implementation must pin `LC_ALL`.
3. **What is stdin?** A suite that may run a program interactively
   should close its own: `exec < /dev/null`. A container gives EOF; a
   terminal gives nothing at all.
4. **What is in the environment that you did not put there?**
   `LD_PRELOAD`, `PS1`, `CFLAGS`, `HOME`, `USER`. Unset or pin what
   changes what the test SEES rather than what the program DOES.
5. **Which tools are assumed?** Every absolute path and every reference
   implementation. Check once, name the missing one, and skip the
   comparisons that need it rather than failing them.
6. **Which numbers are the machine's?** Byte sizes are the compiler's,
   "inconclusive" counts are the installed references', timing is the
   load's. Record what produced them and compare only within it.
7. **How fast is the machine?** Every constant timeout is a guess about
   a clock. Measure a normal run and allow a multiple, or make it an
   environment variable.
8. **How wide is a pointer?** If the work has any notion of word size,
   a 32-bit host inverts native and cross.

## Artifact required

A checklist in the response with one line per item above: what the
answer is in your environment, whether the harness depends on it, and
what you did. Then either a portability check that asserts the ones that
matter, or a named reason each is safe.

A useful cheap version, when a second machine is not available: run the
suite again with the environment perturbed — a different locale, a
closed stdin, `HOME` set elsewhere, a hostile `LD_PRELOAD`, under load —
and require the same answer.
