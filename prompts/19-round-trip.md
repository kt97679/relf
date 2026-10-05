# 19 — a round trip through the user's machine

**Fires when** the work needs, more than once, what only the user's
machine can give: a benchmark on the reference hardware, a test on an
operating system you lack, a build with a toolchain you cannot install.

**Skip when** it is needed once, and one command the user can paste
produces it - then give that command, and say which output to send.

## Why this exists

A shell project measured its claims on the user's laptop. For a long
while the round trip was done by hand. The user pulled each git bundle
into the checkout, ran the benchmark script, and attached its report;
for anything else, they ran a loop pasted from a reply and pasted its
output back.

Every leg of that leaked:

- **The reports were never kept.** No report had been committed, and four
  were found lying in the laptop's checkout months later - the only copy
  of the figures two iterations rested on.
- **The figures travelled in messages.** The next session was told them
  in its start message, rather than finding them in the repository.
- **One test failure was never pinned down.** It came from a suite run
  inside a full check, and the report did not say which of two causes it
  was; the loop that measured its rate was a separate paste.
- **Stale state was a hazard.** Files of older layouts in the checkout
  could have shadowed new ones.

A script then took over the legs one at a time - clean, measure, check,
pack - and each step it made mechanical stopped leaking. Two hazards came
with it. Its clean deleted a file the user had made. And a script that
updates the checkout it runs from can change under the shell executing
it.

## Do this

1. **One script, versioned in the repository**, run by one command from
   the checkout's top: `sh tools/round-trip.sh`. Start from the template
   beside this file (`19-round-trip.sh`) - fill in the bundles' name, the
   branch, the steps, and what the clean keeps; leave the protocol alone.
2. **It applies the handoff first.** The newest bundle in the user's
   downloads, onto the branch by fast-forward only. It refuses, and says
   why, over changed tracked files, off the branch, or when the branch
   has commits the bundle lacks: a refusal costs a message, a wrong merge
   costs a session.
3. **It runs itself again when the handoff changed it.** The script's
   body is one function called on its last line, so the shell has read
   all of it before the update lands. Compare the script's hash before
   and after; if it changed, `exec` the new one with the same arguments,
   and a variable that says it already applied.
4. **It cleans to a known state, recoverably.** Every untracked path goes
   to a trash directory that keeps one run's worth - not deleted. Kept in
   place: what came from elsewhere and is not in the repository yet
   (reports, packs, bundles). The trash, the packs and the bundles are
   ignored in `.gitignore`, so the project's own untracked-file check
   stays quiet.
5. **Every step through one function** that keeps its output, and puts
   its exit status and time in a summary. A failed step does not stop the
   pack; it is named in it.
6. **One file back,** printed last, with `SUMMARY.txt` first in it: the
   bundle applied (from what commit to what), each step's status, the
   checkout before and after, what the clean moved. Raw reports go in as
   they came, so they can be committed byte for byte (`11`).
7. **A question that needs the user's machine becomes a step,** not a
   pasted loop: the next run carries it, its output comes back in the
   pack, and a failure there names its cause (`11`).
8. **Test the script where you can** before handing it over (`08`): a
   scratch clone, a scratch downloads directory, and the states it must
   handle planted - a bundle that changes the script, one already
   applied, local commits it lacks, a changed tracked file, an untracked
   file the user made.

## Artifact required

- the script's path in the repository, and its `--help`;
- its run in a scratch clone for each planted state, and what it did;
- for each pack received: the commit it measured, its steps' statuses,
  and where its raw reports went in the repository.
