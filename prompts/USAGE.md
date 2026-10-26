# Using this library from another project

## Referencing it

Put one line in the consuming project's top-level instruction file — its
`README.md`, `CLAUDE.md`, `AGENTS.md` or equivalent:

```
Prompt library: https://github.com/USER/ai-prompts/blob/COMMIT/INDEX.md
Read INDEX.md at the start of the session and follow its dispatch rules.
```

Two details matter more than they look.

**Pin a commit, not a branch.** A result produced under one version of a prompt
is not reproducible under a later one. Pinning also means a change to the
library cannot silently change the behaviour of a project you are not currently
looking at.

**Reference the index, not the directory.** A bare link to a repository is a
suggestion; a link to a file with dispatch instructions in it is an
instruction. If the assistant has no way to fetch URLs, vendor `INDEX.md` into
the project instead and keep the prompts remote.

## Per-project overrides

Add to the same instruction file, if needed:

```
Prompt overrides:
  - skip 05-reader-review (internal tooling, no external audience)
  - 02-escape-recall applies to the scheduling design only, not to the parser
```

An override is worth recording even when obvious, because "not applicable here"
and "never looked" are indistinguishable six weeks later.

## Checking that it actually happened

Each prompt names a required artifact. To audit compliance, look for the
artifact, not for a claim:

| prompt | look for |
|---|---|
| `01` | a written cost model and a stated degenerate answer |
| `02` | an axis table with completeness counts, and candidates nobody uses |
| `03` | figures labelled modelled or measured, a calibration case, and the footprint of every option a result is credited to |
| `04` | quoted text with concrete fixes, not general impressions |
| `05` | the first three places a reader stopped |
| `06` | a per-finding accepted/rejected line with reasons |
| `07` | the log entry, a commit message body, and the bundle's clone check |
| `08` | one line per environmental assumption: its value here, and whether the harness depends on it; for a script that deletes there, the listing it was tested against ; for a run handed over, the one command, the archive's contents with every log, what a failed step leaves, how privileged steps get their privileges |
| `09` | per changed value: old, new, one sentence of cause, and a verdict |
| `10` | the prize measured before the change, what it displaces, and the achieved value beside it after |
| `11` | the name, expected and actual values in the output itself; or a local reproduction |
| `12` | the search for a prior attempt, and the log entry saying how this one ended |
| `13` | every failure classed, the order they will be worked in, and each crash's reproducer |
| `14` | a named-audience note - who is there, what the venue punishes, the metric optimised, its formatting mechanics - found before the draft, and the draft checked against it |
| `15` | the search for earlier occurrences of the class, and the check, with its failing run on the broken version |
| `16` | per claimed fix, the test's failing run without the fix and passing run with it; for a change that promises nothing, the broken versions tried |
| `17` | the detached command, the log's path, and the marker line read back before the commit |
| `18` | the baseline check's marker before the first change; the environment's gaps; what only the message knew, and where it went |
| `19` | the script's path and `--help`, its scratch runs for each planted state, and each pack's commit, step statuses and where its reports went |
| `20` | the A/A spread and how it was produced; each side's figures per layout; the ratio with the floor beside it, and the verdict in those terms |
| `21` | the conditions; whether this machine can produce them, and why; the probe for any mechanism claimed; the closing count and where it ran |
| `22` | the original sentence, the evidence checked, each part answered, and the correction where it did not hold - in the reply and in the record |
| `23` | a mutation table - each injected fault, the check meant to catch it, caught or not - and checks that cannot run counted as failures |
| `24` | an objections table per reviewer, a ceiling for every claimed gain, the revised plan with its stopping points |
| `25` | the variant as one data record, the shared code that reads it, a test with a fictional extra variant |
| `26` | per round the held-out rank correlation and the flattered designs; per other machine the same binaries' rank correlation; speed against program size |
| `27` | for each structured edit, the name it was found by, the count showing it occurs once, the changed unit read back with its neighbours |
| `28` | at each challenge, one line: other models useful or not, and why; when useful, the self-contained prompts; when answered, the verification file - every claim, how it was checked, its verdict |
| `29` | the size of what a session reads whole, and each cut with its before and after |

If a response says the prompt was considered but shows none of these, the
prompt was not applied.

## Growing the library

Add a prompt when a project produces a failure that would have been prevented
by one, and write the failure into the file. A prompt without a "Why this
exists" section tends to be generic advice, which gets skimmed; a prompt that
says "this exact mistake cost a week" gets read.

Keep the count low. Six files the assistant will actually consult beat thirty
it will skim.
