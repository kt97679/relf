# ai-prompts

Reusable prompts for AI-assisted technical work.

**Start here: [INDEX.md](INDEX.md)** — the dispatcher. Projects should
reference that file, not this one. [USAGE.md](USAGE.md) explains how to wire it
into a project.

## The library

Each prompt exists because of a specific failure in a real project, named under
"Why this exists", so it is not generic advice: you can check whether the
failure mode applies to your situation before spending a turn on it.

They were extracted from the postmortem of a hardware-measurement project
(comparing minimal CPU designs by synthesised gate count). That is provenance,
not prerequisite — nothing in the prompts is about CPUs, and the failures they
describe are ones any measurement or write-up project can reproduce.

| | use it | guards against |
|---|---|---|
| [01-problem-framing](01-problem-framing.md) | before starting a measurement project | optimising the wrong term; a benchmark with a degenerate answer |
| [02-escape-recall](02-escape-recall.md) | whenever the task is "find the best X" | a model proposing the options history already chose, and calling it a search |
| [03-audit-tooling](03-audit-tooling.md) | before reporting any measured result | measurement tools that quietly favour the answer you already have |
| [04-expert-review](04-expert-review.md) | when a technical write-up is nearly done | overclaiming; unstated modelling assumptions |
| [05-reader-review](05-reader-review.md) | after the expert review passes | unreadable structure, repetition, no problem statement |
| [06-handling-review](06-handling-review.md) | when review feedback arrives | accepting wrong criticism, rejecting right criticism, silent drift |
| [07-git-handoff](07-git-handoff.md) | when a session ends or work changes hands | knowledge that lived only in the conversation; a deliverable nobody tested |
| [08-run-it-elsewhere](08-run-it-elsewhere.md) | before calling a suite portable | a harness that measures its own environment |
| [09-baseline-discipline](09-baseline-discipline.md) | when a recorded value changes | a check quietly converted into a record of whatever happened last |
| [10-price-before-refactor](10-price-before-refactor.md) | before restructuring working code | paying for a prize nobody measured; a proxy metric mistaken for time |
| [11-report-from-elsewhere](11-report-from-elsewhere.md) | when writing or reading a remote failure report | a round trip spent asking what the output should have said |
| [12-progress-log](12-progress-log.md) | before trying an approach, and when any attempt ends | re-deriving and re-paying for an idea that was already tried and rejected |
| [13-severity-first](13-severity-first.md) | when working a list of failures | a segfault weighed the same as a reworded message; crashes found only by accident |

## The two that mattered most

In the originating project, five rounds of expert review improved the write-up
and caught three real errors. Two interventions from outside that cycle changed
the *work* itself:

* a reader asking for structure, a problem statement, and less repetition —
  which no expert reviewer had mentioned, because they were all reading for
  correctness rather than for whether anyone could follow it;
* a reader pointing out that all the candidates compared were the ones that
  historically existed, so a model with that history in its weights was
  recalling rather than searching. Acting on this produced a design that beats
  the hand-made one and resembles nothing in the historical record.

If you only take two, take `02` and `05`.

## A limitation, stated up front

`02` asks an assistant to notice that it is reciting known solutions rather
than searching. That is the thing a model is least equipped to notice about
itself — in the originating project it did not, and a human reader did. Every
step of `02` therefore demands a table with counts in it rather than a
reflection, and `INDEX.md` says how to check that the table is there. Treat
self-application as a weaker substitute for a second pair of eyes, not a
replacement.
