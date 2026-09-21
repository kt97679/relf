# 07 — the repository is the handoff

**Fires when** a session will end and another will continue the work, or
when work is handed to a person on another machine.

**Skip when** the work is a single answer in the conversation with no
artifact.

## Why this exists

A session ends. The next one — another model instance, or the same
person a week later — starts with no memory of it. Everything that is
not in the repository is gone: what was tried, what was rejected and
why, which numbers are current, which bug is open and how far it was
narrowed.

In the project this came from, 400 sessions of work survived because
each one ended with a commit whose message explained the reasoning and a
`PROGRESS.md` entry that a future session could read instead of
rediscovering. The things that did NOT survive were the ones kept
outside it: a benchmark script in `/tmp` that every published figure was
measured on, and a habit of pointing at a log file on a machine the
reader did not have.

And a git bundle was handed over for 368 iterations before anyone tried
to pull one. `git bundle create FILE master TAG` writes those refs and
no `HEAD`, and `git pull FILE` asks for `HEAD`. Every handover had been
broken, and no test covered it, because the deliverable was the one
thing nobody tested.

The ignore file failed in both directions. Two compiled engines were
TRACKED for four hundred iterations, and the first time the checkout
reached an ARMv7 board `make` saw an x86-64 binary newer than its
source and handed it to the kernel: `Exec format error`. Three `.pyc`
files were tracked too, and turned up as modifications on every
machine with a different Python. And the opposite fault is as easy: an
ignore rule broad enough to catch `*.img` would have silently dropped
the one kind of binary the project cannot rebuild without.

## Do this

1. **Everything the work depends on is in the repository.** Scripts,
   test corpora runners, benchmark inputs, the tools that produced every
   published number. If a figure was measured on something in `/tmp`,
   the figure is not reproducible and the claim is not supported.

2. **Commit messages carry the reasoning, not the diff.** The diff is
   already in the commit. What is not recoverable later is why this
   approach and not the other one, what was measured, and what was
   rejected. Write the message for someone who has the code and not the
   conversation.

3. **Keep an append-only log** — one entry per session — with what was
   done, what it cost, what was learned, and what is open. Name the
   files that changed. A future session reads the last few entries and
   knows where it is. What goes in it, and how it stops the next
   session retrying a rejected idea, is `12-progress-log`.

4. **Record decisions where they will be found again**, not only in the
   log: a decision about the code belongs in a comment beside the code,
   with the date or iteration number that made it. A deferred decision
   belongs in the standing queue with the evidence that would settle it.

5. **Hand over a bundle, and test that it can be received:**

       git bundle create out.bundle HEAD master <tags>
       git clone -q out.bundle /tmp/check && \
         [ "$(git rev-parse HEAD)" = "$(git -C /tmp/check rev-parse HEAD)" ]

   `HEAD` in the ref list is what makes `git pull out.bundle` work. Put
   that check in the acceptance suite: a deliverable nobody tests is a
   deliverable nobody has tried.

6. **Build products are not repository contents.** A compiled binary in
   a checkout is a trap the moment the checkout reaches another
   architecture: it is newer than its source, so the build system skips
   it, and the kernel refuses it. Commit sources and the artifacts that
   genuinely cannot be regenerated — and say in the README which is
   which and why.

7. **Set up `.gitignore` before the first commit, and audit it when
   anything new starts being generated.** Everything a build, a test
   run or a tool leaves behind is either ignored or deliberately
   committed - never tracked by accident:

   - **Interpreter caches**: `__pycache__/`, `*.py[co]`, `.pytest_cache/`,
     `node_modules/`, `.mypy_cache/`. They are regenerated per machine
     and per interpreter version, so a tracked one is a spurious diff
     on every other machine.
   - **Build products**: compiled binaries, object files, generated
     headers - by exact name where the name is fixed (`relf`, `relf32`)
     rather than by a pattern that could catch something else.
   - **Machine-local state**: files a build writes about THIS machine
     (an architecture stamp, a "which image is native" marker). They
     are correct only where they were written.
   - **What an interrupted run leaves**: logs, `core`, temporary files,
     per-test result files (`*.trs`), scratch directories.
   - **Editor and patch debris**: `*~`, `.*.swp`, `*.orig`, `*.rej`.

   And the other half, which is the one that costs data:

   - **Never ignore what cannot be regenerated.** A self-hosting
     project's bootstrap image, test fixtures, recorded expectations,
     vendored inputs. If an ignore rule is a pattern (`*.img`, `*.bin`,
     `*.log`), check it against `git ls-files` - a pattern that matches
     a tracked file is a trap for the next person who deletes and
     re-adds it.
   - **Comment each block with why**, the way code is commented. A
     rule nobody can explain gets deleted, and a rule that is explained
     tells the next person which way to lean.

   Checks worth running, and worth putting in the acceptance suite:

       git ls-files -ci --exclude-standard   # tracked files an ignore rule matches
       git status --porcelain --ignored      # after a full build and test run:
                                             # every !! line should be expected,
                                             # and there should be no ?? lines
       git ls-files | grep -E '__pycache__|\.py[co]$|\.o$|~$'

   The first finds a rule that would hide a tracked file. The second,
   run after a complete build and test cycle, finds anything the cycle
   generates that nobody decided about: an untracked (`??`) file there
   is either a missing ignore rule or a missing `git add`.

## Artifact required

Before ending the session, produce:

- the log entry, with the iteration or session number;
- the commit message body (not just a subject line);
- the bundle command you ran **and** the output of the clone check;
- the output of `git status --porcelain` after the build and test run:
  empty, or each line explained;
- one line naming what a future session should pick up first.
