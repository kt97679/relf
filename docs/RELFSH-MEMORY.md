# Does relfsh give back what it no longer needs? (Iteration 777)

Checked by measurement: tools/relfsh-memcheck.py runs each shell feature in a
loop N times and 10 N times and compares the peak resident memory of the two
runs. Memory kept per round shows as growth that scales with the rounds;
memory given back does not. Both builds: ./relfsh (on the VM) and
./relfsh-native. The checker changes nothing in relfsh.

## The answer

Yes, with one deferred case. Every feature measured stays flat - the same
peak, about 11 MB, at 2,000 rounds and at 20,000 (within a few bytes a
round, the noise of the measure): assignment, arithmetic, parameter
expansion, string building, for over words, case, function calls, local,
eval, unset, set --, export, here-documents, trap, alias, cd, printf, read,
command substitution, pipelines and subshells (the last four fork, and ran
300 and 3,000 rounds).

The one that grows: redefining a function, again and again, inside one
long-running command.

| | relfsh-native | relfsh (VM) |
|---|---:|---:|
| `g() { echo "$i" >/dev/null; }` redefined each round | 629 B a round | 336 B a round |
| `g() { :; }` redefined each round | 58 B a round | 4 B a round |
| one, two, three such loops of 20,000, one after another | 21, 21, 21 MB | 16, 16, 16 MB |

This is by design (shell.4, before SET-FUNC; forth/pool.4's BUF-RETIRE): a
redefined function's old body is retired, not freed, because the function
may be redefining itself while its old body is still being replayed; the
top-level loop frees everything retired once the command in hand ends. The
last row shows it working: a second and a third loop reach the same peak as
the first, on the memory the first gave back. So the old bodies are held for
as long as the command that made them runs - a while loop, here - and no
longer. Shell variables' old values take the same path, but a value that
still fits reuses its block, which is why plain assignment stayed flat.

## What could be done

The retired list could also be freed at the start of each round of a
top-level loop when no function is running (FUNC-DEPTH 0): nothing retired
can be in use then. That would bound the case above to one round. It is a
change to relfsh, left untouched through the Rill work (rill-guard); it
would want relfsh's own suites. Real scripts seldom redefine a function
thousands of times inside one loop.

## The change (Iteration 778, at the user's request)

A redefined function's old body now goes on a list of its own (FN-RETIRE,
forth/pool.4) - the tree evaluator's compiled block (tree.4) and the raw body
(shell.4's SET-FUNC) alike. That list is freed with the general one between
top-level commands, and also at the start of each round of a while, until
or for loop while no function runs (FUNC-DEPTH 0): only a running function
replays an old body. The general list - token buffers ARGV points into,
variables' old values - keeps its rule: freed only between top-level
commands.

| 20,000 redefinitions in one loop | before | after |
|---|---:|---:|
| relfsh-native | 22 MB | 10 MB |
| relfsh (VM) | 17 MB | 10 MB |

The same at 2,000 rounds as at 20,000, on both builds. relfsh's suites, run
after the change: tests/run_tests.sh (all eight parts, the 132 differential
cases against bash, none failed), posix (47 passed, 0 failed, 1
inconclusive - as before the change), tests/shell (every file), mrsh (21
passed, 0 failed, 3 skipped). The full `make verify` runs longer than this
session's commands may; it is the user's to run.

## The check, from now on

`make memcheck`: tools/relfsh-memcheck.py --check, both builds, each feature
at N and 10 N rounds; it fails if any keeps more than 48 bytes a round (more
where few rounds make the measure's noise larger). 39 seconds.
