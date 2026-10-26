# 08 — a suite that has run in one place measures that place

**Fires when** a test suite, benchmark or build has only ever run in one
environment — your container, your laptop, your CI image — and you are
about to call it green - or are about to hand over a script that will run
there, above all one that moves, overwrites or deletes files.

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

The same holds for what is already THERE. A run script handed to the
owner of a laptop kept four named result files and then removed the
build directory - tested on a replica made from what the development
machine had, which was one database. The laptop's build directory also
held two earlier runs' databases, a rehearsal's, their reports and five
benchmark archives; a `find .` the owner happened to send showed them
before the first run. The same script took its repository from a fixed
path, so from a second clone it would have pulled into, and cleaned, a
different directory.

And for what comes BACK. Work sent to a laptop came back, round after
round, in two to four archives, each made by a command of its own. A
measurement needing root ran in a chain that had detached from the
terminal: sudo could not read a password (`Input/output error`), and the
chain stopped. Chained after another, a second measurement failed,
because the helper holding its privilege held for one. Every step of a
chain fetched the newest code, so a version dropped in mid-run would
have changed the code between steps. And a failed step stopped the
chain with the earlier steps' results still on the laptop. There was no
way to stop a run but finding its processes by hand - and the evolver
started every engine in a session of its own, so killing the runner's
process group would have left them running. And the privileged helper
created its log as root, in the owner's home.

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
9. **What is already there?** A script that moves, overwrites or
   deletes meets files your environment never had: earlier runs'
   outputs, archives, notes saved by hand. Ask for a listing before
   writing it, and test it on a replica of that listing - including the
   upgrade from the copy they have now. Keep by kind, not by name: move
   everything a build cannot make again aside, with a manifest, and
   delete only what a build makes again.
10. **Where is it?** A script finds its repository from its own path
    (`git -C "$(dirname "$0")" rev-parse --show-toplevel`), never from
    a fixed one: run from another clone, a fixed path works on the
    wrong directory.
11. **One command in, one archive out.** The other machine runs one
    script, and gets one file to send back: every step's results and
    every log - the build's, the tests', each step's own output, the
    runner's - so a failure needs no second round to diagnose. Make it at
    the end even when a step failed, with the failure in it.
12. **Privileges at the start, while someone is there.** Ask before the
    run detaches; a detached run cannot ask. What needs them later goes
    to a privileged helper forked at the start, which polls for its
    condition and does only that: it restores what it changed on every
    exit - watching the process it serves, not only a "done" file -
    gives up having changed nothing if its condition never comes, takes
    a session of its own so a closed terminal does not end it, and
    chowns everything it creates to the user - no root-owned files in
    their home.
13. **Pin the code for the whole run.** Take it once, at the start; no
    step fetches a newer version mid-run.
14. **A failed step does not cost the others.** Steps that do not need
    its output still run; what exists is packed.
15. **A stop, and a start that repairs.** A run handed over has one
    documented way to stop it, which ends every process it started -
    children that took sessions of their own included, so stop by the
    process tree, not the process group - and still leaves the archive,
    saying it was stopped. And every start first finds what an earlier
    run left when the machine crashed or the run was killed: packs its
    logs, removes what was half written (write archives under a
    temporary name and rename), restores what it changed, and gives back
    files a privileged helper made.
16. **Where it is, without knowing where it lives.** A status that says
    whether it runs, its step and since when, and a monitor that follows
    its one log - read-only: interrupting the monitor never stops the
    run. During a long quiet step, the run writes a progress line now and
    then, so following it shows progress, not silence. Each command's
    output names the others.

## Artifact required

A checklist in the response with one line per item above: what the
answer is in your environment, whether the harness depends on it, and
what you did. Then either a portability check that asserts the ones that
matter, or a named reason each is safe.

A useful cheap version, when a second machine is not available: run the
suite again with the environment perturbed — a different locale, a
closed stdin, `HOME` set elsewhere, a hostile `LD_PRELOAD`, under load —
and require the same answer.

For a script that moves or deletes files on the other machine: the
listing it was tested against, and what it keeps, moves and deletes, by
kind.

For a run handed over: the one command; the archive's contents by step,
logs included; what a failed step leaves in it; and which steps need
privileges, and how they get them; how to see where it is, how to stop it,
and what the next start repairs after a crash.
