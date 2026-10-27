# SYNC.md — this library and its copies

forth-vm-evolution keeps a copy of this library: its `prompts/UPSTREAM`
says it was copied from here at e96185a (2026-10-03), and lists what it
changed since. Both sides go on adding prompts, so a sync is a three-way
merge with the last synced versions as the base - never one side copied
over the other: each has prompts the other lacks.

## Last sync: Iteration 844, from forth-vm-evolution 45903e4 (its Iteration 555)

One change there since 7da6566: its Iteration 552 (33c4f5e), `21` item 9 -
a sequence of steps that recurs becomes a script, tested like any change,
the judgment left to the session in TODO lines; a one-off analysis keeps
its script beside its result. Here it is `29` item 9: `git merge-file`
against 7da6566's `21`, no conflict, our title and renumbered references
kept. Its UPSTREAM still dates from e96185a - nothing of ours has gone
there since, so the list below stands. Every `prompt NN`, `prompt NN, item
M` and `` `NN` `` resolves (100 checked).

## Iteration 803's sync, from forth-vm-evolution 7da6566 (its Iteration 543)

Base e96185a. Carried here: every change its UPSTREAM lists (its
Iterations 19 to 543) - 03, 07, 08, 10, 11 and 12 changed, INDEX, README
and USAGE rows, and seven prompts new. Both sides numbered on from 15, so
what came from there has new numbers here:

| forth-vm-evolution | here |
|---|---|
| `15`-`21`: checks-that-can-fail, premortem, variants-as-data, does-it-generalize, address-by-name, ask-other-models, spend-tokens-where-they-buy-results | `23`-`29`, same names |
| `03` steps 8, 9 (a switch is not a feature; null rewrites) | steps 9, 10 - step 8 here is absence of output |
| `07` items 8-12 (a script that pulls itself; the present in one file; losing work a failing check; closing the old session; recovering a closed one) | items 10-14 - 8 and 9 here are a diverged branch and the start message |
| `10` items 6, 7 (price exactly; what it displaces) | items 8, 9 - 6 and 7 here are a ceiling and the small change |
| `11` item 10 (a report's size budget) | item 11 - 10 here is keeping the report |
| `12` item 7 (each fact once) | item 8 - 7 here is the log in volumes |

The cross-references inside the prompts use the numbers here, and since
Iteration 805 so do the seven prompts' own titles (`# 23 —` to `# 29 —`;
803 had left their `# 15 —` to `# 21 —`, the numbers of other prompts
here). In the next sync a title is ours: their side's change to a title's
number is not taken. In
USAGE's table the `14` row joins both sides' rows, and `20`-`22` got the
rows they lacked.

## Here, not there yet - to carry to forth-vm-evolution

`15`-`22` (repeat-slip, fail-before-fix, checks-outlive-a-turn,
session-start, round-trip with `19-round-trip.sh`, noise-floor-first,
race-needs-its-conditions, restated-claim); `01` and `09` changed;
`03` step 8, `07` items 8-9, `10` items 6-7, `11` item 10, `12` item 7;
INDEX, README and USAGE rows for them.

## The next sync

Base: forth-vm-evolution 45903e4's `prompts/` for their side, Iteration
844's for ours. A file changed on one side is taken; one changed on
both is merged (`git merge-file`), its items renumbered after ours; a new
prompt takes the next free number here. Check that every `prompt NN`,
`prompt NN, item M` and `` `NN` `` still resolves, and update this file.
