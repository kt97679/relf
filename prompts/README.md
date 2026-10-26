# ai-prompts

Reusable prompts for AI-assisted technical work.

**Start here: [INDEX.md](INDEX.md)** — the dispatcher. Projects should
reference that file, not this one. [USAGE.md](USAGE.md) explains how to wire it
into a project.
[SYNC.md](SYNC.md) is how this library and forth-vm-evolution's copy of
it are merged, and the numbers that differ between them.

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
| [03-audit-tooling](03-audit-tooling.md) | before reporting any measured result | measurement tools that quietly favour the answer you already have; options that silently did nothing |
| [04-expert-review](04-expert-review.md) | when a technical write-up is nearly done | overclaiming; unstated modelling assumptions |
| [05-reader-review](05-reader-review.md) | after the expert review passes | unreadable structure, repetition, no problem statement |
| [06-handling-review](06-handling-review.md) | when review feedback arrives | accepting wrong criticism, rejecting right criticism, silent drift |
| [07-git-handoff](07-git-handoff.md) | when a session ends or work changes hands, and at the end of any turn that changed the repository | knowledge that lived only in the conversation or outside the repository; a handoff that went stale; a deliverable nobody tested |
| [08-run-it-elsewhere](08-run-it-elsewhere.md) | before calling a suite portable | a harness that measures its own environment; a script that deletes what it never saw; privileges asked where no one can answer; results back in pieces |
| [09-baseline-discipline](09-baseline-discipline.md) | when a recorded value changes | a check quietly converted into a record of whatever happened last |
| [10-price-before-refactor](10-price-before-refactor.md) | before restructuring working code | paying for a prize nobody measured; a proxy metric mistaken for time |
| [11-report-from-elsewhere](11-report-from-elsewhere.md) | when writing or reading a remote failure report | a round trip spent asking what the output should have said; a log left on the other machine |
| [12-progress-log](12-progress-log.md) | before trying an approach, and when any attempt ends | re-deriving and re-paying for an idea that was already tried and rejected |
| [13-severity-first](13-severity-first.md) | when working a list of failures | a segfault weighed the same as a reworded message; crashes found only by accident |
| [14-audience-research](14-audience-research.md) | before drafting for a venue, and before choosing where to publish | writing for an imagined reader; a venue's known failure modes met only after publishing (added at Iteration 553 from kt97679/minimal-cpu-design, where it is 07) |
| [15-repeat-slip](15-repeat-slip.md) | when fixing a mistake made before | the same slip, fixed by care each time and recurring anyway - three times in a week (added at Iteration 631) |
| [16-fail-before-fix](16-fail-before-fix.md) | before claiming a fix or adding a regression test | a test that passes proves nothing unless it failed before; a claimed fix for a flaw that never existed (Iteration 631) |
| [17-checks-outlive-a-turn](17-checks-outlive-a-turn.md) | when starting a check longer than one call or turn | a cut-off log read as a pass; a commit one step from being made on it (Iteration 631) |
| [18-session-start](18-session-start.md) | at the start of a session that picks up someone else's work | a first turn spent reading; an environment's gaps found by failing; what only the start message knew (Iteration 656) |
| [19-round-trip](19-round-trip.md), with [its template script](19-round-trip.sh) | when the work needs, more than once, what only the user's machine can give | reports never kept, figures carried in messages, a loop pasted by hand, a script updating the checkout it ran from (Iteration 664) |
| [20-noise-floor-first](20-noise-floor-first.md) | before judging an A/B of two builds | a verdict that is layout luck: the same program moving as much as the change (Iteration 720) |
| [21-race-needs-its-conditions](21-race-needs-its-conditions.md) | when an intermittent failure is to be explained or closed | absence claimed from a machine that cannot produce the failure; a mechanism read from code and fixed unprobed (Iteration 720) |
| [22-restated-claim](22-restated-claim.md) | when someone restates your conclusion and asks you to confirm it | confirming your own overclaim because it came back in someone else's words (Iteration 720) |
| [23-checks-that-can-fail](23-checks-that-can-fail.md) | before calling anything green | checks that cannot fail: a skipped check counted as passed, a verdict read off a log line, a suite that never takes the changed path, a test harness whose leftovers turn other cases red; a stand-in kinder than the tool it replaces |
| [24-premortem](24-premortem.md) | before building a plan of more than a day | a plan attacked only after it is built; a promised gain above its own ceiling; "nobody has done this" |
| [25-variants-as-data](25-variants-as-data.md) | before adding a third variant by hand | every new variant touching many places, copies drifting apart
| [26-does-it-generalize](26-does-it-generalize.md) | before trusting what a long search found | winners flattered by the benchmarks they were picked on, tuned to one CPU, tested only on programs that fit every cache |
| [27-address-by-name](27-address-by-name.md) | before a script edits or reads part of a structured document | a numbered item edited in the wrong list, a table row given its neighbour's text, a column read by position |
| [28-ask-other-models](28-ask-other-models.md) | at every challenge: would another model help? | answers trusted unchecked, or a wrong premise sent - a sound answer to the wrong question |
| [29-spend-tokens-where-they-buy-results](29-spend-tokens-where-they-buy-results.md) | at a session's start, and at every record, report, input and question | whole files read by every session, facts written four times, dumps pasted where a summary answers |

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
