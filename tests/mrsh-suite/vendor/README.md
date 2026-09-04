# Vendored test files from mrsh

These `.sh` (and, in `conformance/`, `.stdout`) files are copied
verbatim from mrsh (https://github.com/emersion/mrsh), a minimal
POSIX shell, at commit `4c81598721bc5eeb28f9faa818b3102d0471b7f6`
(2024-03-10). `LICENSE` in this directory is mrsh's own MIT license,
included per its terms since these are substantial portions of that
project's own source.

Not vendored: mrsh's own `harness.sh` and `meson.build` files (its
build/test-running tooling, not test content - `../run.sh` in the
parent directory is this project's own harness, adapted from mrsh's
approach but pointed at `relfsh`/`bash` instead of `mrsh`/a reference
shell). See `GOALS.md`'s goal 8 and `PROGRESS.md`'s Iteration 14 entry
for why this suite was adopted, what it actually requires from a
shell (a feature list far beyond what `shell.4` implements as of this
writing), and the phased plan for closing that gap.

Do not hand-edit these files to make them pass - if a test needs to
change to fit `shell.4`'s scope, that's a sign the vendored copy has
drifted from upstream, not a fix. Where `shell.4` is missing a feature
a test depends on, that's tracked as a real, honest failure until the
feature exists.
