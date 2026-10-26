---
id: 23-checks-that-can-fail
when: before calling any check, test or suite green
applies-when:
  - you are about to say a check, a test or a suite passed
  - you added a check and are about to rely on it
  - a run reported "all green" on work you expected to be hard
  - a failure would have to travel through a log line, an exit code or a summary to be seen
skip-when:
  - this check has already been shown to fail on a deliberately broken input, in this project, since it last changed
produces: a mutation table - each injected fault, the check expected to catch it, caught or not - and the list of checks that cannot run counted as failures
cost: low to medium
---
# 23 — A check that has never failed has not been tested

**Use it** before calling anything green, and whenever a new check is about to
carry weight.

**Why this exists.** Two projects, the same failure:

* The Paleocomputing project (an Oberon system and Wirth's RISC5 processor
  rebuilt by AI agents in nine days - Habr, 2026) ran a mutation audit on its
  own test suite: plausible faults planted in the processor one at a time (a
  comparison flipped, one instruction broken). The suite caught 10 of 30. A
  check that could not run was counted as passed; a failed build did not
  stop the test run and success was read off the last line of output, so
  zero tests run came out green; a boot check reported success on a machine
  that hung at the first instruction; and every one of two hundred tests
  silently skipped the program's first instruction, because each began with
  one whose result did not matter. The author's summary: most of the nine
  days went into making the checks able to turn red.
* In this project the kernel workload's gate passed designs that died before
  writing their kernel: the work directory began with a copy of the right
  one, and the comparison found it. And when the engine's terminal input
  was rewritten, the test suite passed an engine that lost whole lines -
  every input it gives is a file, and only a pipe took the broken path; the
  hand-made stages' check, which feeds a pipe, caught it.

The pattern: the check and the thing checked shared an assumption, so the
check could not see the thing break.

---

```
Before calling this green, show that each check carrying the claim can fail.

1. PLANT A FAULT. For each check, make the smallest plausible break in the
   thing it guards - flip a comparison, drop a line, return a constant,
   feed the input the change was about - and run the check. It must go red.
   Table: fault, check, caught or not. A check that stays green on a broken
   thing guards nothing; fix it or stop citing it. Plant each fault from a
   clean state and confirm that only its own check went red: a fault that
   trips several, or a reset that does not restore the clean state, means
   the harness is contaminated and its verdicts are not evidence (files a
   root shell made inside a user's clone survived its resets and turned
   later cases red for the wrong reason).

2. CANNOT RUN IS RED. A check that could not execute - missing tool, failed
   build, timeout, zero cases collected - is a failure, never a pass and
   never a skip that counts towards green. Count the cases each check
   actually ran and print the count.

3. NO VERDICT FROM A LOG LINE. Success read from the last line of output, a
   smiley, a "done" banner or an exit status the harness ignores is not a
   verdict. Compare the artefact itself - bytes, values, a hash - with the
   expected one, and remove whatever stands in the way of that comparison
   (a reference copy already in place, a cached result).

4. COVER THE CHANGED PATH. List the inputs the suite actually gives - files,
   pipes, terminals; first and last elements; empty, one, many - and check
   that the path you changed is among them. A suite that never takes the
   path cannot fail on it, however large it is.

5. KEEP THE FAULTS. Planted faults that were caught become permanent
   negative tests where they are cheap: the check must stay able to fail
   after the next refactoring too.
6. A STAND-IN REFUSES WHAT THE REAL ONE REFUSES. A fake tool, service or
   privilege in a test - a stand-in perf, a stand-in sudo - is part of the
   check: it must fail where the real one fails, and behave as the real one
   does, or name each difference. A stand-in perf that invented source
   lines hid that the real one, given a stripped binary, finds none - the
   first run on the real machine attributed nothing; a stand-in sudo let a
   hang-up kill the command it backgrounded, where the real one keeps it
   apart - a failure the real thing would never give.
```

## Artifact required

The mutation table (fault, check, caught), the count of cases each check ran,
and one line per check naming the input path it exercises.
