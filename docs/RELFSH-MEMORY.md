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
