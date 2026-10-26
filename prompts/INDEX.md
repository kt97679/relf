# Index — read this file, then fetch only what fires

This is the dispatcher. A project should reference **this file only**. It is
short on purpose: reading it costs little, and the individual prompts are
fetched lazily when their trigger conditions are met.

## Instructions to the assistant

1. Read this table at the start of the session - this table, not the
   library: the prompts are fetched when they fire. A session that picks
   up someone else's work starts with `18`.
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
| `03-audit-tooling` | report a measured number produced by tooling you wrote, *or* report a result that agrees with what you expected, *or* credit a result to an option you switched on | no figure came from your own tooling |
| `04-expert-review` | publish a technical write-up whose claims have settled | the claims are still moving |
| `05-reader-review` | publish, after `04` has passed | the claims are still moving |
| `06-handling-review` | act on any review feedback | never skip |
| `07-git-handoff` | end a session or hand work to another machine - or end any turn that changed the repository: a session can end without warning | the work leaves no artifact |
| `08-run-it-elsewhere` | call a suite, build or benchmark green, *or* hand over a script that runs on someone else's machine - above all one that moves or deletes files, needs privileges there, or sends results back | the environment ships with the product |
| `09-baseline-discipline` | re-record a recorded value that changed | nothing is recorded - then ask why not |
| `10-price-before-refactor` | restructure something that works, on the strength of a profile | the change is required for correctness |
| `11-report-from-elsewhere` | write output someone on another machine will paste back, or read one | the reader has the machine |
| `12-progress-log` | try an approach, or finish an attempt that worked, failed or was reverted | nothing is being tried |
| `13-severity-first` | work through a list of failures, or decide whether a pass count is the goal | one failure, already understood |
| `14-audience-research` | draft a write-up for a specific venue, or choose where to publish it (upstream `07-audience-research`; renumbered here, where 07 was already `07-git-handoff`) | the artefact is internal, with one known reader |
| `15-repeat-slip` | fix a mistake you have made before, or write that one happened again | the mistake is new - then log it well |
| `16-fail-before-fix` | claim a fix, add a regression test, or add tests to a change that claims to change nothing | nothing is claimed and no test is added |
| `17-checks-outlive-a-turn` | start a check that may run longer than one call or turn | it finishes well inside one call |
| `18-session-start` | start a session on work another session, person or machine left - before reading anything else | the work starts from nothing |
| `19-round-trip` | the work needs, more than once, what only the user's machine can give | once, and one pasteable command gives it |
| `20-noise-floor-first` | call one build faster or slower than another | the difference is many times any spread seen between builds of one program |
| `21-race-needs-its-conditions` | explain, clear or close an intermittent failure, above all one seen on another machine | it reproduces on demand where you are |
| `22-restated-claim` | confirm, or build on, a conclusion of yours that someone has restated | it was measured here and the restatement says no more |
| `23-checks-that-can-fail` | call a check, test or suite green, rely on a check you just added, or report "all checks pass" | the check was shown to fail on a broken input since it last changed |
| `24-premortem` | start a plan of more than a day, above all one meant to prove a claim | the plan is one step whose failure is cheap and visible |
| `25-variants-as-data` | add one more variant (a machine, a backend, a gene) by editing several places | there will only ever be two |
| `26-does-it-generalize` | call the winners of a long search or optimisation better - selected on fixed benchmarks, on one machine | the workloads are the product's own, on the machine it ships on |
| `27-address-by-name` | edit or read one part of a structured document by script or pattern - a list item, a table row, a column | the document is regenerated from data each time |
| `28-ask-other-models` | settle a challenge alone that turns on knowledge outside the repository, a fresh reading of code, a field's methods, or a search for prior art - weigh it in one line at every challenge | a measurement, build or test here answers it faster and surer |
| `29-spend-tokens-where-they-buy-results` | start a session, write a record, report or reply, read a pasted input, or ask other models - in work that runs over many sessions | a one-off question in a fresh session |

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
publishing. `07`-`13` came from a self-hosting shell written over four
hundred sessions: `07`-`11` when it was handed to someone with two
ordinary machines, `12` and `13` later, from keeping its log honest and
from working its failures in the right order, and `15`-`17` later still,
from building a native compiler for it: repeated slips, a claimed fix
that had never failed, and checks longer than a turn; and `18` from the first turn of a session
that spent it all on reading; `19`, with a template script beside it,
from the round trips through the user's laptop; `20`-`22` from that
compiler's size work and its A/Bs, a race chased on a machine that could
not produce it, and a remedy confirmed because the user restated it.
`23`-`29` came back from forth-vm-evolution, an evolutionary search over
interpreter designs that kept a copy of this library: checks that can
fail, a premortem and variants as data, from an article on AI-built
Oberon systems and that project's own failures; then held-out tests for
what a long search found, addressing parts of a document by name, asking
other models, and spending tokens where they buy results.
They are about work that
OUTLIVES a session and software that runs somewhere other than where it
was written. That family's failures are cheaper to hit and easier to
miss: nine of the eleven faults the handover found were in the test
harness rather than the program, and every one was something the
original environment never varied.

## Provenance

Every prompt's "Why this exists" section describes a specific failure in the
project that produced it. That context is provenance, not prerequisite — the
prompts are self-contained and none of them is about the original subject
matter.
