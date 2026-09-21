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
   knows where it is.

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

## Artifact required

Before ending the session, produce:

- the log entry, with the iteration or session number;
- the commit message body (not just a subject line);
- the bundle command you ran **and** the output of the clone check;
- one line naming what a future session should pick up first.
