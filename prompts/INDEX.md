# Index — read this file, then fetch only what fires

This is the dispatcher. A project should reference **this file only**. It is
short on purpose: reading it costs little, and the individual prompts are
fetched lazily when their trigger conditions are met.

## Instructions to the assistant

1. Read this table at the start of the session.
2. Before each listed moment, check whether any trigger applies to what you are
   about to do.
3. If one does, fetch and follow that file *at that moment* — not at the start.
   These prompts are moment-specific; applying them all up front produces
   ceremony instead of effect.
4. Each prompt requires an artifact in the response. Produce it. Do not narrate
   having considered the prompt.
5. If a prompt's `skip-when` matches, say in one line that you skipped it and
   why. A silent skip is indistinguishable from not having looked.

| id | fires when you are about to... | skip if |
|---|---|---|
| `01-problem-framing` | produce the first numbers of a comparison, benchmark or optimisation | the cost model and metric are already fixed and stated |
| `02-escape-recall` | **name any candidate** approach, architecture or algorithm for a "which is best" question | the user fixed the candidate set, or the task is to implement one named thing |
| `03-audit-tooling` | report a measured number produced by tooling you wrote, *or* report a result that agrees with what you expected | no figure came from your own tooling |
| `04-expert-review` | publish a technical write-up whose claims have settled | the claims are still moving |
| `05-reader-review` | publish, after `04` has passed | the claims are still moving |
| `06-handling-review` | act on any review feedback | never skip |
| `07-git-handoff` | end a session, or hand work to another machine | the work leaves no artifact |
| `08-run-it-elsewhere` | call a suite, build or benchmark green | the environment ships with the product |
| `09-baseline-discipline` | re-record a recorded value that changed | nothing is recorded - then ask why not |
| `10-price-before-refactor` | restructure something that works, on the strength of a profile | the change is required for correctness |
| `11-report-from-elsewhere` | write output someone on another machine will paste back, or read one | the reader has the machine |

## The one that is hardest to self-apply

`02` asks you to notice that you are recalling known solutions rather than
searching. That is the thing a model is least able to notice about itself: in
the project these prompts came from, the assistant did not notice, and a human
reader did. This is why `02` demands two tables with counts in them rather than
a reflection. If you find yourself writing "I considered whether my candidates
were conventional" without a table above it, you have skipped the prompt.

The same applies to the human side: `05` is worth far more run on an actual
reader than on a model asked to simulate one, because a simulated reader is
more patient and better informed than any real one.

## Two families

`01`-`06` came from a hardware-measurement project and are about
choosing what to measure, searching rather than recalling, and
publishing. `07`-`11` came from a self-hosting shell written over four
hundred sessions and handed to someone with two ordinary machines; they
are about work that OUTLIVES a session and software that runs somewhere
other than where it was written. The second family's failures are
cheaper to hit and easier to miss: nine of the eleven faults that
sequence found were in the test harness rather than the program, and
every one was something the original environment never varied.

## Provenance

Every prompt's "Why this exists" section describes a specific failure in the
project that produced it. That context is provenance, not prerequisite — the
prompts are self-contained and none of them is about the original subject
matter.
