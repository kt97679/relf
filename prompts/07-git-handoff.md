# 07 — the repository is the handoff

**Fires when** a session will end and another will continue the work, or
when work is handed to a person on another machine - and at the end of any
turn that changed the repository, because a session can end without
warning: a budget of turns or tool calls runs out, or the person starts a
new chat.

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

A project handed between chats every day (forth-vm-evolution) lost or nearly
lost work at every switch, and each time to a session boundary nobody had
announced. A pricing script lived in `/tmp` and went with its chat - recovered
only because that chat's machine was still up and could be asked. A turn ran
out of tool calls with a whole feature in a scratch clone and nothing
committed. The handoff was a log entry that the next chat's prompt named by
number, and it still said a run was going after the run had been processed.
And the new chat's setup lacked the commit identity, found only by doing the
setup.

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

   `out.bundle` is this prompt's placeholder, not a name. **If the
   project names its bundles, or has a script that makes them, use that
   — look in its goals or conventions file before the first handoff.**
   Otherwise name each so a folder of them sorts and says what it is:
   project, author, iteration, UTC time —
   `project-claude-iterN-YYYYMMDD-HHMMSS.bundle`. Best of all is a
   script in the repository that names the bundle, lists its refs and
   runs the clone check, so no session has to remember any of it: one
   session followed this placeholder and handed over a wrongly named
   bundle, with the project's convention written down in a file it had
   not read.

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
   - **What a tool writes on the machine that runs it** goes where
     nothing is tracked. A benchmark that writes its tables into
     committed files changes them on every machine that measures, and
     the next pull - or a script that refuses a dirty tree - stops
     there. Output goes to an ignored directory; a commit copies the
     chosen run into the tracked place. One project put this in its
     ignore file for a generated report, and met it again in three
     results files the rule had not been generalised to.
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

8. **A fix for a branch that has diverged is applied, not merged by
   hand.** When a fix must also go to a branch that left the main line
   long ago - a published release, say - and the cherry-pick conflicts,
   do not resolve the conflict by editing. Check, file by file, that
   every file the fix touched was identical on that branch to the fix's
   parent commit (`git diff --quiet FIX~1 BRANCH -- FILE`). Where all
   were, take the fixed files whole (`git checkout FIX -- FILES`): that
   is exactly the fix. Give the branch its own log entry, saying it was
   applied this way and from which commit; regenerate recorded results on
   the branch rather than copying them; run the branch's own acceptance
   suite. In the shell project the conflict was in the log file alone -
   the main line had fifty entries the branch did not - and every code
   file passed the identity check.

9. **Write the next session's start message, then find each line of it
   in the repository.** Where things stand, the newest figures, what to
   try next, the hazards to remember: whatever the next session will be
   told must be readable from the repository, and a line found only in
   the message is knowledge that dies with the message. In the shell
   project one start message carried five such lines - the last remote
   report's figures among them, from a report nobody had committed.
   `18` is the receiving side.

10. **A script that pulls its own repository runs the copy it pulled.**
   Pull, then `exec` the new file. Whatever it does before the pull runs
   from the OLD copy, so it must stay safe in every copy that will ever
   exist on the other machine - keep it to the pull and its checks. Test
   the upgrade itself: the copy they have now, the bundle you are
   sending.

11. **Keep the present in one file, apart from the log, and check that it is
   current.** A log entry is history the moment the next one is written, and
   a prompt that names one by number goes stale with it. One handoff file
   holds the state, the routine, the standing decisions and the open items,
   and is rewritten, not appended to; a check fails when it is older than the
   last commit that changed the state. Every other document points to it
   rather than restating it - two "where things stand" sections disagree.
   Keep it a card, with a size you check: every session reads it whole, so
   history and background move to a reference read on demand, verbatim
   (forth-vm-evolution: 59 KB, the present 12.5 KB of it; prompt 29).

12. **Make losing work a failing check, not a habit.** Before the bundle,
    fail on: changes not committed; a scratch clone holding changes or
    commits the repository does not; any script, patch or source outside the
    repository that matches no tracked file byte for byte - unless it is
    declared disposable, with a reason. Run the check from the bundle script,
    so every bundle handed over is a valid starting point; a safety copy made
    mid-work is named as one (`-checkpoint`) and is never started from.

13. **Close the old session before opening the new one.** The switch is two
    messages: to the old session - commit, track or discard what is outside
    the repository, bring the handoff file up to date, run the check, present
    the bundle; to the new one - start from the bundle the old one presented
    last. Test the second by doing it: run its setup, word for word, on a
    fresh clone. The missing step shows; reading the prompt does not show it.

14. **Recovering from a closed session.** While its machine lasts, ask it for
    every file it left outside the repository - for the whole range of work it
    did, not the range you remember (a request scoped to the wrong iterations
    came back with half) - as found, nothing reconstructed from memory, with a
    manifest mapping each file to the figure it produced. Transcripts of
    earlier sessions may be on one machine and not the next: never rely on
    them.

## Artifact required

Before ending the session, produce:

- the log entry, with the iteration or session number;
- the commit message body (not just a subject line);
- the bundle command you ran **and** the output of the clone check;
- the output of `git status --porcelain` after the build and test run:
  empty, or each line explained;
- one line naming what a future session should pick up first;
- the next session's start message, each line with where the
  repository holds it;
- for a fix applied to a diverged branch (step 8): the identity check
  per file, and the branch's own acceptance result.
- the handoff check's output, and the iteration the handoff file names.
