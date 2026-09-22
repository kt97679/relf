# attic/pending - test cases for fixes that are not in yet

A case here documents a known bug precisely and is ready to move into
`tests/diff/cases/` in the same commit as its fix. It is NOT run by any
suite, because it fails today.

- `braced-word-split-430.sh` - fields out of order in a braced word
  (GOALS.md "Open now"; PROGRESS.md Iteration 430). Matches bash and
  dash; this shell fails the first two lines.
