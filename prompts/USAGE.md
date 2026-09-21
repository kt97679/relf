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
| `03` | figures labelled modelled or measured, and a calibration case |
| `04` | quoted text with concrete fixes, not general impressions |
| `05` | the first three places a reader stopped |
| `06` | a per-finding accepted/rejected line with reasons |

If a response says the prompt was considered but shows none of these, the
prompt was not applied.

## Growing the library

Add a prompt when a project produces a failure that would have been prevented
by one, and write the failure into the file. A prompt without a "Why this
exists" section tends to be generic advice, which gets skimmed; a prompt that
says "this exact mistake cost a week" gets read.

Keep the count low. Six files the assistant will actually consult beat thirty
it will skim.
