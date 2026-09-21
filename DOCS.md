# The documents in this repository

What each file is for, so that a reader can tell a live document from a
record of how something came to be. Written at Iteration 368, when ten
historical documents moved to `attic/docs/`.

## Current

| file | what it is |
|------|------------|
| `README.md` | what this project is, how to build and run it |
| `GOALS.md` | the standing queue: what is wrong, what is next, what was decided and why |
| `PROGRESS.md` | the iteration log, one entry per session, oldest first |
| `PERFORMANCE.md` | where the time goes, measured, and what was done about it |
| `VERSUS-DASH.md` | how this shell compares with dash, feature by feature and measured |
| `DASH-COMPARISON.md` | how dash itself works inside, read from its source, and what was taken from it |
| `INTERACTIVE.md` | everything the shell does at a prompt: editing, history, signals, job control |
| `RESEARCH-VM.md` | standing questions about the virtual machine, and the assessments that answered some |
| `CV8.md` | the design of the current engine encoding |
| `CV8-REFERENCE.md` | the byte-by-byte reference for a CV8 image |
| `XARCH.md` | whether the engine's choices hold on other architectures |
| `FORTH-STYLE.md` | the practices that have prevented bugs here, and the ones that have not |
| `ARTICLE.md` | working notes for a write-up of the VM's evolution |
| `tests/from-others/CATALOGUE.md` | behaviours learned from other shells' suites, in this project's own words |
| `Makefile` | the index of the builds and suites; `make help` lists them |
| `CHECKING.md` | what to run after pulling, and what each check would catch |
| `prompts/` | reusable prompts for this kind of work; `prompts/INDEX.md` is the dispatcher. `01`-`06` are from another project, `07`-`11` were written here (Iteration 407) |
| `tools/busybox-suite.sh`, `tools/yash-suite.sh` | run the two external corpora and report what the reference passes and this shell does not |

## Retired, in `attic/docs/`

Each carries a banner saying when it was superseded and by what. They
are kept because the reasoning in them is often still the best record of
why the current design is what it is.

| file | superseded by |
|------|---------------|
| `SOD16.md` | CV8, Iteration 189 |
| `TOKEN-THREADING.md` | CV8, Iteration 189 |
| `INNER-INTERPRETER.md` | answered in `CV8.md`, Iteration 189 |
| `DENSITY-PLAN.md` | CV8 and byte-granular headers |
| `ENCODING-COMPARISON.md` | the ladder it measured was retired at Iteration 218 |
| `VM-RESEARCH.md` | the survey it fed became `VM-SURVEY.md` and then CV8 |
| `VM-SURVEY.md` | checked on other architectures by `XARCH.md` |
| `PARSE-EXPAND-PLAN.md` | its Stage 2 by `COMMAND-TREE-PLAN.md`; the rest is done |
| `COMMAND-TREE-PLAN.md` | done: the command tree landed at Iteration 269 |
| `EXPANSION-PLAN.md` | done: word encodings landed at Iterations 273-283 |
